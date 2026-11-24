"""Strict deeply-frozen Pydantic v2 base and rpds-py persistent container bridges."""

from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING, Annotated, Self, dataclass_transform, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    PrivateAttr,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from rpds import HashTrieMap, HashTrieSet


def _from_mapping(value: object) -> HashTrieMap[object, object]:
    if isinstance(value, HashTrieMap):
        return value
    if isinstance(value, Mapping):
        return HashTrieMap(value)
    msg = f"Expected Mapping or HashTrieMap, got {type(value).__name__}"
    raise ValueError(msg)


def _serialize_map(value: HashTrieMap[object, object]) -> dict[object, object]:
    return {k: value[k] for k in sorted(value.keys(), key=str)}


def _from_iterable(value: object) -> HashTrieSet[object]:
    if isinstance(value, HashTrieSet):
        return value
    if isinstance(value, (frozenset, tuple, list)):
        return HashTrieSet(value)
    msg = f"Expected HashTrieSet or sequence, got {type(value).__name__}"
    raise ValueError(msg)


def _serialize_set(value: HashTrieSet[object]) -> list[object]:
    return sorted(value, key=str)


class _HashTrieMapPydanticAnnotation:
    """Pydantic v2 core-schema & JSON-schema bridge for rpds.HashTrieMap[K, V]."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: object,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        args = get_args(source_type)
        key_schema = (
            handler.generate_schema(args[0]) if len(args) >= 1 else core_schema.str_schema()
        )
        val_schema = (
            handler.generate_schema(args[1]) if len(args) >= 2 else core_schema.any_schema()
        )

        dict_schema = core_schema.dict_schema(keys_schema=key_schema, values_schema=val_schema)
        python_schema = core_schema.union_schema(
            [
                core_schema.is_instance_schema(HashTrieMap),
                core_schema.no_info_after_validator_function(_from_mapping, dict_schema),
            ]
        )
        json_schema = core_schema.no_info_after_validator_function(_from_mapping, dict_schema)

        return core_schema.json_or_python_schema(
            json_schema=json_schema,
            python_schema=python_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_map,
                return_schema=dict_schema,
                when_used="json-unless-none",
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return handler(schema)


class _HashTrieSetPydanticAnnotation:
    """Pydantic v2 core-schema & JSON-schema bridge for rpds.HashTrieSet[T]."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: object,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        args = get_args(source_type)
        item_schema = handler.generate_schema(args[0]) if args else core_schema.str_schema()
        seq_schema = core_schema.list_schema(items_schema=item_schema)

        return core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(_from_iterable, seq_schema),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(HashTrieSet),
                    core_schema.no_info_after_validator_function(_from_iterable, seq_schema),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_set,
                return_schema=seq_schema,
                when_used="json-unless-none",
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return handler(schema)


# PyO3 rpds.HashTrieMap / HashTrieSet provide generic .pyi stubs for static checkers
# but are not subscriptable at runtime; Mapping/AbstractSet preserve runtime type args
# for Pydantic v2 schema generation while keeping HashTrieMap/HashTrieSet statically.
if TYPE_CHECKING:
    type PersistentMap[K, V] = Annotated[HashTrieMap[K, V], _HashTrieMapPydanticAnnotation]
    type PersistentSet[T] = Annotated[HashTrieSet[T], _HashTrieSetPydanticAnnotation]
else:
    type PersistentMap[K, V] = Annotated[Mapping[K, V], _HashTrieMapPydanticAnnotation]
    type PersistentSet[T] = Annotated[AbstractSet[T], _HashTrieSetPydanticAnnotation]


def empty_persistent_map[K, V]() -> HashTrieMap[K, V]:
    """Typed zero-cost empty persistent map factory for Pydantic Field(default_factory=...)."""
    return HashTrieMap()


def empty_persistent_set[T]() -> HashTrieSet[T]:
    """Typed zero-cost empty persistent set factory for Pydantic Field(default_factory=...)."""
    return HashTrieSet()


type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | tuple[JsonValue, ...] | PersistentMap[str, JsonValue]


if TYPE_CHECKING:
    from pydantic._internal._model_construction import ModelMetaclass

    @dataclass_transform(
        kw_only_default=True,
        frozen_default=True,
        field_specifiers=(Field, PrivateAttr),
    )
    class _FrozenModelMeta(ModelMetaclass):
        pass
else:
    _FrozenModelMeta = type(BaseModel)


class FrozenModel(BaseModel, metaclass=_FrozenModelMeta):
    """Strict, deeply immutable domain base with validated fluent evolution."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        validate_default=True,
        populate_by_name=True,
        arbitrary_types_allowed=False,
    )

    def _evolve(self, **updates: object) -> Self:
        """Return a new validated frozen instance without bypassing @model_validator hooks."""
        state: dict[str, object] = {
            field_name: getattr(self, field_name) for field_name in type(self).model_fields
        }
        state.update(updates)
        return type(self).model_validate(state)

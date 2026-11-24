"""Algebraic FP primitives backed by Expression 6.0.1 and Draft 2020-12 wire bridge."""

from __future__ import annotations

from typing import Annotated, Literal, final, get_args, get_origin

from expression import NOTHING, Error, Nothing, Ok, Option, Result, Some, TaggedUnion, case, tag
from expression.collections import Block, Map
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

__all__ = [
    "NOTHING",
    "Block",
    "Either",
    "Error",
    "Left",
    "Map",
    "Nothing",
    "NullableOption",
    "Ok",
    "Option",
    "Result",
    "Right",
    "Some",
    "TaggedUnion",
    "case",
    "tag",
]


@final
@case
class Left[L]:
    """Left branch of a symmetric non-error binary sum."""

    tag: Literal["left"] = tag()
    value: L


@final
@case
class Right[R]:
    """Right branch of a symmetric non-error binary sum."""

    tag: Literal["right"] = tag()
    value: R


type Either[L, R] = TaggedUnion[Left[L] | Right[R]]


def _extract_option_inner_type(source_type: object) -> object:
    """Extract T from Expression's Option[T] (Annotated[Some[T] | Nothing, UnionSchema()])."""
    candidate = source_type
    if get_origin(candidate) is Annotated:
        candidate = get_args(candidate)[0]
    for arm in get_args(candidate):
        if get_origin(arm) is Some:
            arm_args = get_args(arm)
            if arm_args:
                return arm_args[0]
    msg = f"NullableOption expected Option[T], got {source_type!r}"
    raise TypeError(msg)


def _unwrap_python_option(val: object) -> object:
    if isinstance(val, Some):
        return val.value
    if isinstance(val, Nothing):
        return None
    return val


def _from_wire_option(val: object) -> Option[object]:
    if val is None or isinstance(val, Nothing):
        return NOTHING
    if isinstance(val, Some):
        return val
    return Some(val)


def _to_wire_option(opt: Option[object]) -> object:
    match opt:
        case Some(inner):
            return inner
        case _:
            return None


class _NullableOptionAnnotation:
    """Draft 2020-12 JSON wire bridge keeping Option[T] in Python and T | null on the wire."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: object,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        inner_type = _extract_option_inner_type(source_type)
        inner_schema = handler.generate_schema(inner_type)
        wire_union = core_schema.union_schema([inner_schema, core_schema.none_schema()])

        python_unwrapped = core_schema.no_info_before_validator_function(
            _unwrap_python_option,
            wire_union,
        )
        return core_schema.json_or_python_schema(
            json_schema=core_schema.no_info_after_validator_function(_from_wire_option, wire_union),
            python_schema=core_schema.no_info_after_validator_function(
                _from_wire_option,
                python_unwrapped,
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                _to_wire_option,
                when_used="json",
            ),
        )


type NullableOption[T] = Annotated[Option[T], _NullableOptionAnnotation]

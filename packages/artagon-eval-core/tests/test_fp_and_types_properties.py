"""Hypothesis property tests for Expression 6.0.1 algebraic laws and FrozenModel containers."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from expression import NOTHING, Error, Ok, Option, Result, Some
from hypothesis import given
from hypothesis import strategies as st
from pydantic import Field, ValidationError, model_validator
from rpds import HashTrieMap, HashTrieSet

from artagon_eval_core.domain.fp import Either, Left, NullableOption, Right
from artagon_eval_core.domain.primitives import NonEmptyStr
from artagon_eval_core.domain.types import (
    FrozenModel,
    JsonValue,
    PersistentMap,
    PersistentSet,
    empty_persistent_map,
    empty_persistent_set,
)

if TYPE_CHECKING:
    import strategies as strat
else:
    _STRAT_MOD = "artagon_eval_core_test_strategies"
    if _STRAT_MOD in sys.modules:
        strat = sys.modules[_STRAT_MOD]
    else:
        _spec = importlib.util.spec_from_file_location(
            _STRAT_MOD, Path(__file__).resolve().with_name("strategies.py")
        )
        assert _spec is not None
        assert _spec.loader is not None
        strat = importlib.util.module_from_spec(_spec)
        sys.modules[_STRAT_MOD] = strat
        _spec.loader.exec_module(strat)


def _int_options() -> st.SearchStrategy[Option[int]]:
    return st.one_of(
        st.just(NOTHING),
        st.integers(min_value=-10_000, max_value=10_000).map(Some),
    )


def _int_results() -> st.SearchStrategy[Result[int, str]]:
    return st.one_of(
        st.integers(min_value=-10_000, max_value=10_000).map(Ok),
        st.text(min_size=1, max_size=24).map(Error),
    )


class _EitherDistinctBox(FrozenModel):
    branch: Either[int, str]


class _EitherSameBox(FrozenModel):
    branch: Either[str, str]


class _NullableScalarsBox(FrozenModel):
    opt_int: NullableOption[int] = NOTHING
    opt_bool: NullableOption[bool] = NOTHING
    opt_str: NullableOption[str] = NOTHING
    opt_float: NullableOption[float] = NOTHING


class _StrictEvolvableModel(FrozenModel):
    label: NonEmptyStr
    low: int
    high: int
    mapping: PersistentMap[str, int] = Field(default_factory=empty_persistent_map)
    tags: PersistentSet[str] = Field(default_factory=empty_persistent_set)

    @model_validator(mode="after")
    def _check_bounds(self) -> _StrictEvolvableModel:
        if self.low > self.high:
            msg = f"low ({self.low}) must be <= high ({self.high})"
            raise ValueError(msg)
        return self


class _JsonValueBox(FrozenModel):
    payload: JsonValue


# ---------------------------------------------------------------------------
# Option[T] Functor & Monad Laws
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(opt=_int_options())
def test_option_functor_identity_law(opt: Option[int]) -> None:
    assert opt.map(lambda x: x) == opt


@pytest.mark.property
@given(
    opt=_int_options(),
    add_k=st.integers(min_value=-50, max_value=50),
    mul_k=st.integers(min_value=-10, max_value=10),
)
def test_option_functor_composition_law(opt: Option[int], add_k: int, mul_k: int) -> None:
    def f(x: int) -> int:
        return x + add_k

    def g(x: int) -> int:
        return x * mul_k

    assert opt.map(lambda x: g(f(x))) == opt.map(f).map(g)


@pytest.mark.property
@given(
    x=st.integers(min_value=-1_000, max_value=1_000),
    threshold=st.integers(min_value=-500, max_value=500),
)
def test_option_monad_left_identity_law(x: int, threshold: int) -> None:
    def f_opt(v: int) -> Option[int]:
        return Some(v * 2 + 1) if v >= threshold else NOTHING

    assert Some(x).bind(f_opt) == f_opt(x)


@pytest.mark.property
@given(opt=_int_options())
def test_option_monad_right_identity_law(opt: Option[int]) -> None:
    assert opt.bind(Some) == opt


@pytest.mark.property
@given(
    opt=_int_options(),
    t1=st.integers(min_value=-500, max_value=500),
    t2=st.integers(min_value=-500, max_value=500),
)
def test_option_monad_associativity_law(opt: Option[int], t1: int, t2: int) -> None:
    def f_opt(v: int) -> Option[int]:
        return Some(v + 7) if v >= t1 else NOTHING

    def g_opt(v: int) -> Option[int]:
        return Some(v * 3) if v <= t2 else NOTHING

    lhs = opt.bind(f_opt).bind(g_opt)
    rhs = opt.bind(lambda v: f_opt(v).bind(g_opt))
    assert lhs == rhs


@pytest.mark.property
@given(falsy=st.sampled_from((0, False, "", 0.0, ())))
def test_option_never_confuses_falsy_values_with_nothing(falsy: object) -> None:
    wrapped: Option[object] = Some(falsy)
    assert wrapped != NOTHING
    assert wrapped.is_some()
    assert wrapped.value == falsy


# ---------------------------------------------------------------------------
# Result[T, E] Functor, Monad & map_error Laws
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(res=_int_results())
def test_result_functor_identity_law(res: Result[int, str]) -> None:
    assert res.map(lambda x: x) == res


@pytest.mark.property
@given(
    res=_int_results(),
    add_k=st.integers(min_value=-50, max_value=50),
    mul_k=st.integers(min_value=-10, max_value=10),
)
def test_result_functor_composition_law(
    res: Result[int, str],
    add_k: int,
    mul_k: int,
) -> None:
    def f(x: int) -> int:
        return x + add_k

    def g(x: int) -> int:
        return x * mul_k

    assert res.map(lambda x: g(f(x))) == res.map(f).map(g)


@pytest.mark.property
@given(
    x=st.integers(min_value=-1_000, max_value=1_000),
    threshold=st.integers(min_value=-500, max_value=500),
)
def test_result_monad_left_identity_law(x: int, threshold: int) -> None:
    def f_res(v: int) -> Result[int, str]:
        return Ok(v - 3) if v >= threshold else Error(f"below:{threshold}")

    assert Ok(x).bind(f_res) == f_res(x)


@pytest.mark.property
@given(res=_int_results())
def test_result_monad_right_identity_law(res: Result[int, str]) -> None:
    assert res.bind(Ok) == res


@pytest.mark.property
@given(
    res=_int_results(),
    t1=st.integers(min_value=-500, max_value=500),
    t2=st.integers(min_value=-500, max_value=500),
)
def test_result_monad_associativity_law(res: Result[int, str], t1: int, t2: int) -> None:
    def f_res(v: int) -> Result[int, str]:
        return Ok(v + 5) if v >= t1 else Error("err_f")

    def g_res(v: int) -> Result[int, str]:
        return Ok(v * 2) if v <= t2 else Error("err_g")

    lhs = res.bind(f_res).bind(g_res)
    rhs = res.bind(lambda v: f_res(v).bind(g_res))
    assert lhs == rhs


@pytest.mark.property
@given(
    res=_int_results(),
    prefix=st.text(min_size=1, max_size=8),
    suffix=st.text(min_size=1, max_size=8),
)
def test_result_map_error_preserves_ok_and_transforms_error(
    res: Result[int, str],
    prefix: str,
    suffix: str,
) -> None:
    def h1(e: str) -> str:
        return f"{prefix}:{e}"

    def h2(e: str) -> str:
        return f"{e}:{suffix}"

    assert res.map_error(lambda e: e) == res
    assert res.map_error(lambda e: h2(h1(e))) == res.map_error(h1).map_error(h2)
    match res:
        case Ok(val):
            assert res.map_error(h1) == Ok(val)
        case Error(err):
            assert res.map_error(h1) == Error(h1(err))


# ---------------------------------------------------------------------------
# Either[L, R] TaggedUnion Laws
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(
    is_left=st.booleans(),
    left_val=st.integers(min_value=-10_000, max_value=10_000),
    right_val=st.text(max_size=40),
)
def test_either_tag_preservation_match_symmetry_and_json_roundtrip(
    is_left: bool,
    left_val: int,
    right_val: str,
) -> None:
    val: Either[int, str] = Left(left_val) if is_left else Right(right_val)

    def swap(e: Either[int, str]) -> Either[str, int]:
        match e:
            case Left(lv):
                return Right(lv)
            case Right(rv):
                return Left(rv)

    def swap_back(e: Either[str, int]) -> Either[int, str]:
        match e:
            case Left(rv):
                return Right(rv)
            case Right(lv):
                return Left(lv)

    assert swap_back(swap(val)) == val
    if is_left:
        assert val.tag == "left"
    else:
        assert val.tag == "right"

    box = _EitherDistinctBox(branch=val)
    raw_json = box.model_dump_json()
    reloaded = _EitherDistinctBox.model_validate_json(raw_json)
    assert reloaded == box
    assert reloaded.branch.tag == val.tag


@pytest.mark.property
@given(is_left=st.booleans(), text=st.text(max_size=40))
def test_either_same_inner_type_preserves_tag_across_json_roundtrip(
    is_left: bool,
    text: str,
) -> None:
    val: Either[str, str] = Left(text) if is_left else Right(text)
    box = _EitherSameBox(branch=val)
    reloaded = _EitherSameBox.model_validate_json(box.model_dump_json())
    assert reloaded == box
    assert reloaded.branch.tag == ("left" if is_left else "right")


# ---------------------------------------------------------------------------
# NullableOption[T] JSON Wire Round-Trip Law
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(
    opt_int=st.one_of(st.none(), st.integers(min_value=-100_000, max_value=100_000)),
    opt_bool=st.one_of(st.none(), st.booleans()),
    opt_str=st.one_of(st.none(), st.text(max_size=40)),
    opt_float=st.one_of(
        st.none(),
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    ),
)
def test_nullable_option_json_wire_roundtrip_all_scalars(
    opt_int: int | None,
    opt_bool: bool | None,
    opt_str: str | None,
    opt_float: float | None,
) -> None:
    box = _NullableScalarsBox(
        opt_int=NOTHING if opt_int is None else Some(opt_int),
        opt_bool=NOTHING if opt_bool is None else Some(opt_bool),
        opt_str=NOTHING if opt_str is None else Some(opt_str),
        opt_float=NOTHING if opt_float is None else Some(opt_float),
    )
    wire = box.model_dump_json()
    decoded = json.loads(wire)
    assert (decoded["opt_int"] is None) is (opt_int is None)
    assert (decoded["opt_bool"] is None) is (opt_bool is None)
    assert (decoded["opt_str"] is None) is (opt_str is None)
    assert (decoded["opt_float"] is None) is (opt_float is None)

    reloaded = _NullableScalarsBox.model_validate_json(wire)
    assert reloaded == box
    if opt_int is not None:
        assert reloaded.opt_int == Some(opt_int)
        assert reloaded.opt_int != NOTHING
    else:
        assert reloaded.opt_int is NOTHING
    if opt_bool is not None:
        assert reloaded.opt_bool == Some(opt_bool)
        assert reloaded.opt_bool != NOTHING
    else:
        assert reloaded.opt_bool is NOTHING
    if opt_str is not None:
        assert reloaded.opt_str == Some(opt_str)
        assert reloaded.opt_str != NOTHING
    else:
        assert reloaded.opt_str is NOTHING


@pytest.mark.property
@given(flag=st.booleans())
def test_nullable_option_int_strictly_rejects_bool(flag: bool) -> None:
    with pytest.raises(ValidationError):
        _ = _NullableScalarsBox.model_validate({"opt_int": flag})
    with pytest.raises(ValidationError):
        _ = _NullableScalarsBox.model_validate({"opt_int": Some(flag)})


# ---------------------------------------------------------------------------
# FrozenModel, PersistentMap, PersistentSet & Recursive JsonValue Laws
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(
    label=strat.non_empty_strs(max_size=24),
    new_label=strat.non_empty_strs(max_size=24),
    low=st.integers(min_value=-1_000, max_value=1_000),
    span=st.integers(min_value=0, max_value=1_000),
    delta=st.integers(min_value=1, max_value=500),
)
def test_frozen_model_evolve_never_mutates_original_and_revalidates(
    label: str,
    new_label: str,
    low: int,
    span: int,
    delta: int,
) -> None:
    high = low + span
    original = _StrictEvolvableModel(label=label, low=low, high=high)
    evolved = original._evolve(label=new_label, high=high + delta)

    assert original.label == label
    assert original.low == low
    assert original.high == high
    assert evolved.label == new_label
    assert evolved.low == low
    assert evolved.high == high + delta

    # _evolve must re-run @model_validator hooks (unlike bypassed model_copy)
    with pytest.raises(ValidationError):
        _ = original._evolve(low=high + delta)

    # Frozen assignment must fail
    with pytest.raises(ValidationError):
        original.label = new_label  # type: ignore[misc]


@pytest.mark.property
@given(
    label=strat.non_empty_strs(max_size=20),
    flag=st.booleans(),
    unknown_key=st.text(min_size=1, max_size=20).filter(
        lambda k: k not in _StrictEvolvableModel.model_fields
    ),
    extra_val=strat.json_scalars(),
)
def test_frozen_model_strict_rejects_bool_as_int_and_unknown_keys(
    label: str,
    flag: bool,
    unknown_key: str,
    extra_val: object,
) -> None:
    with pytest.raises(ValidationError):
        _ = _StrictEvolvableModel.model_validate({"label": label, "low": flag, "high": 10})
    with pytest.raises(ValidationError):
        _ = _StrictEvolvableModel.model_validate(
            {"label": label, "low": 0, "high": 10, "mapping": {"k": flag}}
        )
    with pytest.raises(ValidationError):
        _ = _StrictEvolvableModel.model_validate(
            {"label": label, "low": 0, "high": 10, unknown_key: extra_val}
        )


@pytest.mark.property
@given(
    entries=st.dictionaries(
        st.text(min_size=1, max_size=16),
        st.integers(min_value=-1_000, max_value=1_000),
        max_size=10,
    ),
    extra_key=st.text(min_size=1, max_size=16),
    extra_val=st.integers(min_value=-1_000, max_value=1_000),
)
def test_persistent_map_sorted_json_roundtrip_and_immutability(
    entries: dict[str, int],
    extra_key: str,
    extra_val: int,
) -> None:
    fwd = HashTrieMap(entries)
    rev = HashTrieMap(reversed(list(entries.items())))
    m_fwd = _StrictEvolvableModel(label="map", low=0, high=1, mapping=fwd)
    m_rev = _StrictEvolvableModel(label="map", low=0, high=1, mapping=rev)

    # Deterministic sorted JSON output regardless of insertion order
    json_fwd = m_fwd.model_dump_json()
    json_rev = m_rev.model_dump_json()
    assert json_fwd == json_rev
    parsed_keys = list(json.loads(json_fwd)["mapping"].keys())
    assert parsed_keys == sorted(entries.keys())

    # Round-trip equality
    reloaded = _StrictEvolvableModel.model_validate_json(json_fwd)
    assert reloaded == m_fwd
    assert isinstance(reloaded.mapping, HashTrieMap)

    # Persistent immutability on insert
    snapshot = dict(fwd.items())
    updated = fwd.insert(extra_key, extra_val)
    assert dict(fwd.items()) == snapshot
    assert updated[extra_key] == extra_val


@pytest.mark.property
@given(
    items=st.frozensets(st.text(min_size=1, max_size=16), max_size=10),
    extra_item=st.text(min_size=1, max_size=16),
)
def test_persistent_set_sorted_json_roundtrip_and_immutability(
    items: frozenset[str],
    extra_item: str,
) -> None:
    fwd = HashTrieSet(sorted(items))
    rev = HashTrieSet(sorted(items, reverse=True))
    m_fwd = _StrictEvolvableModel(label="set", low=0, high=1, tags=fwd)
    m_rev = _StrictEvolvableModel(label="set", low=0, high=1, tags=rev)

    json_fwd = m_fwd.model_dump_json()
    json_rev = m_rev.model_dump_json()
    assert json_fwd == json_rev
    assert json.loads(json_fwd)["tags"] == sorted(items)

    reloaded = _StrictEvolvableModel.model_validate_json(json_fwd)
    assert reloaded == m_fwd
    assert isinstance(reloaded.tags, HashTrieSet)

    snapshot = frozenset(fwd)
    updated = fwd.insert(extra_item)
    assert frozenset(fwd) == snapshot
    assert extra_item in updated


def _assert_json_value_structurally_equal(left: JsonValue, right: JsonValue) -> None:
    assert type(left) is type(right)
    if isinstance(left, tuple) and isinstance(right, tuple):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _assert_json_value_structurally_equal(a, b)
        return
    if isinstance(left, HashTrieMap) and isinstance(right, HashTrieMap):
        assert set(left.keys()) == set(right.keys())
        for k in left:
            _assert_json_value_structurally_equal(left[k], right[k])
        return
    assert left == right


@pytest.mark.property
@given(payload=strat.json_values(max_leaves=16))
def test_recursive_json_value_json_roundtrip(payload: JsonValue) -> None:
    box = _JsonValueBox(payload=payload)
    reloaded = _JsonValueBox.model_validate_json(box.model_dump_json())
    _assert_json_value_structurally_equal(reloaded.payload, payload)

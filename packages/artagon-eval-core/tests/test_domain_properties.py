"""Hypothesis property-based tests for core domain invariants and secret redaction."""

from __future__ import annotations

import pytest
from expression import NOTHING, Ok, Some
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import Field
from rpds import HashTrieMap

from artagon_eval_core.domain.fp import NullableOption
from artagon_eval_core.domain.primitives import SPLIT_ALIASES, NonEmptyStr, parse_task_split
from artagon_eval_core.domain.types import FrozenModel, PersistentMap, empty_persistent_map
from artagon_eval_core.runtime.redact import SecretVault
from artagon_eval_core.shims.scrub import REDACTED_PLACEHOLDER


class _PropModel(FrozenModel):
    label: NonEmptyStr
    opt_val: NullableOption[int] = NOTHING
    kv: PersistentMap[str, int] = Field(default_factory=empty_persistent_map)


@pytest.mark.property
@settings(max_examples=50, deadline=None)
@given(
    opt=st.one_of(st.none(), st.integers(min_value=-10_000, max_value=10_000)),
    kv=st.dictionaries(st.text(min_size=1, max_size=12), st.integers(-100, 100), max_size=6),
)
def test_nullable_option_and_persistent_map_json_roundtrip_property(
    opt: int | None,
    kv: dict[str, int],
) -> None:
    model = _PropModel(
        label="prop",
        opt_val=NOTHING if opt is None else Some(opt),
        kv=HashTrieMap(kv),
    )
    reloaded = _PropModel.model_validate_json(model.model_dump_json())
    assert reloaded == model


@pytest.mark.property
@settings(max_examples=50, deadline=None)
@given(alias=st.sampled_from(sorted(SPLIT_ALIASES.keys())))
def test_parse_task_split_case_and_whitespace_invariant(alias: str) -> None:
    expected = SPLIT_ALIASES[alias]
    assert parse_task_split(f"  {alias.upper()}  ") == Ok(expected)


@pytest.mark.property
@settings(max_examples=50, deadline=None)
@given(
    secret=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
        min_size=12,
        max_size=32,
    ),
    prefix=st.text(alphabet="abc123 ", max_size=20),
    suffix=st.text(alphabet="xyz789 ", max_size=20),
)
def test_secret_vault_never_leaks_registered_exact_secret(
    secret: str,
    prefix: str,
    suffix: str,
) -> None:
    vault = SecretVault(exact_secrets=(secret,), enable_detect_secrets=False)
    scrubbed = vault.scrub(f"{prefix}{secret}{suffix}")
    assert secret not in scrubbed
    assert REDACTED_PLACEHOLDER in scrubbed

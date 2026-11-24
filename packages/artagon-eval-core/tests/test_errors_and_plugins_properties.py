"""Hypothesis property tests for closed EvalError ADT, CLI Envelopes, and lazy adapter loader."""

from __future__ import annotations

import importlib.util
import json
import string
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from expression import Error, Ok
from hypothesis import given
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError
from rpds import HashTrieMap

from artagon_eval_core.domain.errors import (
    AdapterUnavailableError,
    ErrEnvelope,
    EvalError,
    MutationScope,
    NormativeExitCode,
    OkEnvelope,
    SchemaUsageError,
    map_error_to_exit_code,
    parse_model,
)
from artagon_eval_core.domain.primitives import NonEmptyStr, RedactedJsonValue
from artagon_eval_core.domain.types import FrozenModel, JsonValue
from artagon_eval_core.plugins.contracts import (
    EP_BENCHMARKS,
    EP_OPTIMIZERS,
    EP_SINKS,
    is_benchmark_adapter,
    is_optimizer_adapter,
    is_telemetry_sink_adapter,
    list_installed_adapters,
    load_adapter,
)
from artagon_eval_core.runtime.redact import SecretVault

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


_EXPECTED_KIND_TO_EXIT: dict[str, NormativeExitCode] = {
    "gate_rejected": NormativeExitCode.GATE_REJECTED,
    "schema_usage": NormativeExitCode.SCHEMA_USAGE,
    "credential_unavailable": NormativeExitCode.CREDENTIAL_UNAVAILABLE,
    "billing_guard": NormativeExitCode.BILLING_GUARD,
    "isolation_tamper": NormativeExitCode.ISOLATION_TAMPER,
    "verifier_cassette": NormativeExitCode.VERIFIER_CASSETTE,
    "quota_censored": NormativeExitCode.QUOTA_CENSORED,
    "multiplexer": NormativeExitCode.MULTIPLEXER,
    "cli_usage": NormativeExitCode.CLI_USAGE,
    "split_data": NormativeExitCode.DATA_SPLIT_ERROR,
    "adapter_unavailable": NormativeExitCode.ADAPTER_UNAVAILABLE,
}

_JSON_VALUE_ADAPTER: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)
_REDACTED_JSON_ADAPTER: TypeAdapter[RedactedJsonValue] = TypeAdapter(RedactedJsonValue)


class _StrictPayload(FrozenModel):
    name: NonEmptyStr
    count: int


# ---------------------------------------------------------------------------
# Closed 11-Variant EvalError ADT & ErrEnvelope Properties
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(err=strat.eval_errors())
def test_eval_error_exit_code_and_redacted_invariants(err: EvalError) -> None:
    assert err.redacted is True
    projected = map_error_to_exit_code(err)
    assert projected == err.exit_code
    assert projected == _EXPECTED_KIND_TO_EXIT[err.kind]
    assert projected != NormativeExitCode.OK


@pytest.mark.property
@given(
    cmd=strat.safe_ids(max_size=24),
    err=strat.eval_errors(),
    mutations=strat.mutation_scopes(),
)
def test_err_envelope_json_wire_and_scrubbed_roundtrip(
    cmd: str,
    err: EvalError,
    mutations: MutationScope,
) -> None:
    env = ErrEnvelope.from_eval_error(cmd, err, mutations=mutations)
    assert env.ok is False
    assert env.redacted is True
    assert env.command == cmd
    assert env.exit_code == err.exit_code
    assert env.reason_code == err.reason_code
    assert env.mutations == mutations
    assert env.error == err.message
    assert env.details == err.details
    assert env.log_paths == err.log_paths

    wire_json = env.model_dump_json()
    decoded = json.loads(wire_json)
    assert decoded["schema_version"] == "harness-eval-envelope/v1"
    assert decoded["ok"] is False
    assert decoded["redacted"] is True
    assert decoded["command"] == cmd
    assert decoded["exit_code"] == int(err.exit_code)
    assert decoded["reason_code"] == err.reason_code
    assert decoded["mutations"] == mutations
    assert decoded["error"] == str(err.message)
    assert decoded["log_paths"] == [str(p) for p in err.log_paths]
    expected_details = _REDACTED_JSON_ADAPTER.dump_python(err.details, mode="json")
    assert decoded["details"] == expected_details

    # Security boundary: raw JSON strings cannot bypass RedactedStr capability seal
    with pytest.raises(ValidationError):
        _ = ErrEnvelope.model_validate_json(wire_json)

    # Round-trip rehydration through SecretVault reproduces the exact ErrEnvelope wire payload
    vault = SecretVault(enable_detect_secrets=False)
    wire_details = _JSON_VALUE_ADAPTER.validate_json(json.dumps(decoded["details"]))
    scrubbed_details = vault.scrub_json(wire_details)
    assert isinstance(scrubbed_details, HashTrieMap)
    rebuilt = ErrEnvelope(
        command=decoded["command"],
        exit_code=err.exit_code,
        reason_code=decoded["reason_code"],
        mutations=decoded["mutations"],
        error=vault.scrub(decoded["error"]),
        details=scrubbed_details,
        log_paths=tuple(decoded["log_paths"]),
    )
    assert rebuilt == env
    assert rebuilt.model_dump_json() == wire_json


@pytest.mark.property
@given(
    cmd=strat.safe_ids(max_size=24),
    name=strat.non_empty_strs(max_size=24),
    count=st.integers(min_value=-10_000, max_value=10_000),
    mutations=strat.mutation_scopes(),
)
def test_ok_envelope_json_roundtrip(
    cmd: str,
    name: str,
    count: int,
    mutations: MutationScope,
) -> None:
    payload = _StrictPayload(name=name, count=count)
    env = OkEnvelope[_StrictPayload](command=cmd, mutations=mutations, data=payload)
    reloaded = OkEnvelope[_StrictPayload].model_validate_json(env.model_dump_json())
    assert reloaded == env
    assert reloaded.ok is True
    assert reloaded.exit_code == NormativeExitCode.OK


@pytest.mark.property
@given(
    secret=strat.high_entropy_secrets(),
    bad_count=st.one_of(st.booleans(), st.text(max_size=12), st.none()),
)
def test_parse_model_rejects_invalid_payloads_without_leaking_raw_input(
    secret: str,
    bad_count: object,
) -> None:
    result = parse_model(_StrictPayload, {"name": secret, "count": bad_count})
    match result:
        case Error(err):
            assert isinstance(err, SchemaUsageError)
            assert err.exit_code == NormativeExitCode.SCHEMA_USAGE
            assert secret not in err.message
        case Ok(val):
            pytest.fail(f"Expected SchemaUsageError for bad_count={bad_count!r}, got {val!r}")


# ---------------------------------------------------------------------------
# Lazy Pluggy Adapter Registry Fail-Closed Properties
# ---------------------------------------------------------------------------


_INSTALLED_BY_GROUP: dict[str, frozenset[str]] = {
    EP_OPTIMIZERS: frozenset(list_installed_adapters(EP_OPTIMIZERS)),
    EP_BENCHMARKS: frozenset(list_installed_adapters(EP_BENCHMARKS)),
    EP_SINKS: frozenset(list_installed_adapters(EP_SINKS)),
}


@pytest.mark.property
@given(
    group=st.sampled_from((EP_OPTIMIZERS, EP_BENCHMARKS, EP_SINKS)),
    adapter_name=st.text(
        alphabet=string.ascii_lowercase + string.digits + "-_",
        min_size=1,
        max_size=32,
    ).filter(lambda name: all(name not in installed for installed in _INSTALLED_BY_GROUP.values())),
    install_extra=strat.non_empty_strs(max_size=24),
)
def test_load_adapter_unknown_name_always_returns_exit_69(
    group: str,
    adapter_name: str,
    install_extra: str,
) -> None:
    if group == EP_OPTIMIZERS:
        res: object = load_adapter(
            group,
            adapter_name,
            install_extra=install_extra,
            protocol_guard=is_optimizer_adapter,
        )
    elif group == EP_BENCHMARKS:
        res = load_adapter(
            group,
            adapter_name,
            install_extra=install_extra,
            protocol_guard=is_benchmark_adapter,
        )
    else:
        res = load_adapter(
            group,
            adapter_name,
            install_extra=install_extra,
            protocol_guard=is_telemetry_sink_adapter,
        )

    assert isinstance(res, Error)
    err = res.error
    assert isinstance(err, AdapterUnavailableError)
    assert err.exit_code == NormativeExitCode.ADAPTER_UNAVAILABLE
    assert int(err.exit_code) == 69
    assert err.adapter_name == adapter_name
    assert err.install_extra == install_extra
    assert err.redacted is True

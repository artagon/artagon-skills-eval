"""Unit tests verifying Phase 0/1 core domain, FP, redaction, shims, logging, data, and CLI."""

from __future__ import annotations

import importlib.resources
import io
import json
from pathlib import Path

import pytest
from expression import NOTHING, Error, Ok, Some
from pydantic import Field, TypeAdapter, ValidationError
from rpds import HashTrieMap, HashTrieSet
from typer.testing import CliRunner

from artagon_eval_core.cli.app import app as harness_app
from artagon_eval_core.cli.app import emit_cli_result
from artagon_eval_core.domain.errors import (
    AdapterUnavailableError,
    BillingGuardError,
    CliUsageError,
    CredentialUnavailableError,
    ErrEnvelope,
    EvalError,
    GateRejectedError,
    IsolationTamperError,
    MultiplexerError,
    NormativeExitCode,
    OkEnvelope,
    QuotaCensoredError,
    SchemaUsageError,
    SplitDataError,
    VerifierCassetteError,
    map_error_to_exit_code,
    parse_model,
)
from artagon_eval_core.domain.fp import Either, Left, NullableOption, Right
from artagon_eval_core.domain.primitives import (
    CampaignId,
    CatalogHarnessName,
    ConfinedScratchPath,
    HarnessName,
    NonEmptyStr,
    RedactedStr,
    parse_safe_newtype,
    parse_task_split,
    static_redacted_literal,
)
from artagon_eval_core.domain.types import (
    FrozenModel,
    PersistentMap,
    PersistentSet,
    empty_persistent_map,
    empty_persistent_set,
)
from artagon_eval_core.runtime.logging import configure_stderr_logger
from artagon_eval_core.runtime.redact import SecretVault
from artagon_eval_core.shims.scrub import REDACTED_PLACEHOLDER
from artagon_eval_core.shims.wire import (
    HotPathShimDescriptor,
    decode_descriptor_bytes,
    encode_json_bytes,
)


class _SampleRecord(FrozenModel):
    name: NonEmptyStr
    optional_tag: NullableOption[NonEmptyStr] = NOTHING
    labels: PersistentMap[str, int] = Field(default_factory=empty_persistent_map)
    tags: PersistentSet[str] = Field(default_factory=empty_persistent_set)


def test_frozen_model_strict_immutability_and_evolve() -> None:
    rec = _SampleRecord(
        name="baseline",
        optional_tag=Some("v1"),
        labels=HashTrieMap({"a": 1}),
        tags=HashTrieSet({"alpha"}),
    )
    evolved = rec._evolve(optional_tag=NOTHING)
    assert rec.optional_tag == Some("v1")
    assert evolved.optional_tag is NOTHING
    assert evolved.labels["a"] == 1

    with pytest.raises(ValidationError):
        _SampleRecord.model_validate({"name": "x", "unknown_field": 1})
    with pytest.raises(ValidationError):
        _SampleRecord.model_validate({"name": "x", "labels": {"a": True}})


def test_nullable_option_and_persistent_containers_json_roundtrip() -> None:
    parsed = _SampleRecord.model_validate_json(
        '{"name":"demo","optional_tag":null,"labels":{"b":2,"a":1},"tags":["z","a"]}'
    )
    assert parsed.optional_tag is NOTHING
    assert parsed.labels["a"] == 1
    assert "z" in parsed.tags

    dumped = json.loads(parsed.model_dump_json())
    assert dumped == {
        "name": "demo",
        "optional_tag": None,
        "labels": {"a": 1, "b": 2},
        "tags": ["a", "z"],
    }


def test_expression_either_and_result_chaining() -> None:
    def branch(flag: bool) -> Either[str, int]:
        return Left("cached") if flag else Right(42)

    match branch(True):
        case Left(val):
            assert val == "cached"
        case Right(_):
            pytest.fail("Expected Left")

    chained = (
        parse_model(_SampleRecord, {"name": "alpha", "optional_tag": "tag-1"})
        .map(lambda r: r.name)
        .bind(lambda name: Ok(f"{name}-ok"))
    )
    assert chained == Ok("alpha-ok")


def test_redacted_str_runtime_seal_and_secret_vault() -> None:
    with pytest.raises(TypeError):
        _ = RedactedStr("raw-secret", _cap=object())

    with pytest.raises(ValidationError):
        _ = SchemaUsageError.model_validate({"reason_code": "bad", "message": "raw-string"})

    vault = SecretVault(exact_secrets=("my-super-secret-value",))
    synthetic_key = "sk-ant-" + "api03-ABCDEF1234567890"
    scrubbed = vault.scrub(f"leak={synthetic_key} and my-super-secret-value")
    assert isinstance(scrubbed, RedactedStr)
    assert synthetic_key not in scrubbed
    assert "my-super-secret-value" not in scrubbed
    assert REDACTED_PLACEHOLDER in scrubbed
    assert vault.redacted_count >= 2

    scrubbed_json = vault.scrub_json(
        HashTrieMap({"api_key": "plain-secret", "note": f"bearer {synthetic_key}"})
    )
    assert isinstance(scrubbed_json, HashTrieMap)
    assert scrubbed_json["api_key"] == REDACTED_PLACEHOLDER
    assert synthetic_key not in str(scrubbed_json["note"])


def test_confined_scratch_path_enforces_boundary(tmp_path: Path) -> None:
    cid = parse_safe_newtype(CampaignId, "camp-01")
    valid = ConfinedScratchPath.from_validated(
        tmp_path, tmp_path / "scratch" / "skill-eval" / "camp-01", cid
    )
    assert valid.run_id == cid
    assert valid.child_rel("traces/out.json") == valid.path / "traces/out.json"

    with pytest.raises(ValueError, match="out_dir_inside_plugins"):
        _ = ConfinedScratchPath.from_validated(tmp_path, tmp_path / "plugins" / "camp-01", cid)
    with pytest.raises(ValueError, match="run_dir_outside_scratch"):
        _ = ConfinedScratchPath.from_validated(tmp_path, tmp_path / "other" / "camp-01", cid)


def test_all_eval_error_variants_map_exhaustively() -> None:
    msg = static_redacted_literal("static error")
    variants: tuple[tuple[EvalError, NormativeExitCode], ...] = (
        (GateRejectedError(reason_code="r", message=msg), NormativeExitCode.GATE_REJECTED),
        (SchemaUsageError(reason_code="r", message=msg), NormativeExitCode.SCHEMA_USAGE),
        (
            CredentialUnavailableError(reason_code="r", message=msg),
            NormativeExitCode.CREDENTIAL_UNAVAILABLE,
        ),
        (BillingGuardError(reason_code="r", message=msg), NormativeExitCode.BILLING_GUARD),
        (IsolationTamperError(reason_code="r", message=msg), NormativeExitCode.ISOLATION_TAMPER),
        (VerifierCassetteError(reason_code="r", message=msg), NormativeExitCode.VERIFIER_CASSETTE),
        (QuotaCensoredError(reason_code="r", message=msg), NormativeExitCode.QUOTA_CENSORED),
        (MultiplexerError(reason_code="r", message=msg), NormativeExitCode.MULTIPLEXER),
        (CliUsageError(reason_code="r", message=msg), NormativeExitCode.CLI_USAGE),
        (SplitDataError(reason_code="r", message=msg), NormativeExitCode.DATA_SPLIT_ERROR),
        (
            AdapterUnavailableError(
                reason_code="r", message=msg, adapter_name="waza", install_extra="waza"
            ),
            NormativeExitCode.ADAPTER_UNAVAILABLE,
        ),
    )
    for err, expected_code in variants:
        assert map_error_to_exit_code(err) == expected_code
        env = ErrEnvelope.from_eval_error("cmd", err)
        assert env.exit_code == expected_code
        assert env.redacted is True


def test_emit_cli_result_always_logs_redacted_stderr_on_error() -> None:
    vault = SecretVault(exact_secrets=("topsecret999",))
    stderr_buf = io.StringIO()
    stdout_buf = io.StringIO()
    logger = configure_stderr_logger(vault, stream=stderr_buf)

    err = SchemaUsageError(
        reason_code="invalid_input",
        message=vault.scrub("bad payload containing topsecret999"),
    )
    code = emit_cli_result("validate", Error(err), logger=logger, stdout=stdout_buf)
    assert code == int(NormativeExitCode.SCHEMA_USAGE)
    assert "topsecret999" not in stderr_buf.getvalue()
    assert "invalid_input" in stderr_buf.getvalue()
    err_payload = json.loads(stdout_buf.getvalue())
    assert err_payload["ok"] is False
    assert err_payload["redacted"] is True

    ok_stdout = io.StringIO()
    ok_code = emit_cli_result(
        "check", Ok(_SampleRecord(name="ok")), logger=logger, stdout=ok_stdout
    )
    assert ok_code == 0
    ok_env = OkEnvelope[_SampleRecord].model_validate_json(ok_stdout.getvalue())
    assert ok_env.data.name == "ok"


def test_hotpath_wire_descriptor_redacts_secrets_in_repr(tmp_path: Path) -> None:
    raw_map: dict[str, object] = {
        "schema_version": "harness-eval-descriptor/v1",
        "trial_id": "t-1",
        "campaign_id": "c-1",
        "arm_id": "a-1",
        "task_id": "task-1",
        "harness": "claude",
        "auth_mode": "subscription",
        "pin_mode": "nix",
        "execution_mode": "headless",
        "trial_root": str(tmp_path / "trial"),
        "workspace_dir": str(tmp_path / "ws"),
        "real_binary": "/nix/store/demo/bin/claude",
        "expected_binary_sha256": "a" * 64,
        "shim_receipt_path": str(tmp_path / "receipt.json"),
        "child_execs_path": str(tmp_path / "execs.jsonl"),
        "hook_socket_path": str(tmp_path / "hook.sock"),
        "hook_fallback_path": str(tmp_path / "hook.jsonl"),
        "hook_hmac_key_hex": "deadbeef" * 8,
        "otlp_bearer_token": "secret-bearer-value-xyz",
    }
    encoded = encode_json_bytes(raw_map)
    desc = decode_descriptor_bytes(encoded)
    assert isinstance(desc, HotPathShimDescriptor)
    assert "deadbeef" not in repr(desc)
    assert "secret-bearer-value-xyz" not in repr(desc)
    assert (
        decode_descriptor_bytes(encode_json_bytes(raw_map, force_stdlib=True), force_stdlib=True)
        == desc
    )


def test_canonical_packaged_data_assets_present() -> None:
    data_root = importlib.resources.files("artagon_eval_core.data")
    schemas = sorted(
        p.name for p in data_root.joinpath("schemas").iterdir() if p.name.endswith(".json")
    )
    harnesses = sorted(
        p.name for p in data_root.joinpath("harnesses").iterdir() if p.name.endswith(".yaml")
    )
    assert len(schemas) == 10
    assert "skill-eval-result.schema.json" in schemas
    assert len(harnesses) == 5
    assert harnesses == ["agy.yaml", "claude.yaml", "codex.yaml", "copilot.yaml", "grok.yaml"]
    assert data_root.joinpath("providers.json").is_file()
    assert data_root.joinpath("keychain-services.json").is_file()


def test_active_and_catalog_harness_names_reject_removed_cli() -> None:
    harness_adapter: TypeAdapter[HarnessName] = TypeAdapter(HarnessName)
    catalog_adapter: TypeAdapter[CatalogHarnessName] = TypeAdapter(CatalogHarnessName)

    for active in ("claude", "codex", "agy", "copilot"):
        assert harness_adapter.validate_python(active) == active
        assert catalog_adapter.validate_python(active) == active

    assert catalog_adapter.validate_python("grok") == "grok"
    with pytest.raises(ValidationError):
        _ = harness_adapter.validate_python("grok")
    with pytest.raises(ValidationError):
        _ = harness_adapter.validate_python("kimi")
    with pytest.raises(ValidationError):
        _ = catalog_adapter.validate_python("kimi")


def test_harness_eval_cli_commands() -> None:
    runner = CliRunner()
    ver_res = runner.invoke(harness_app, ["version"])
    assert ver_res.exit_code == 0
    assert json.loads(ver_res.stdout)["data"]["version"] == "0.2.0"

    adp_res = runner.invoke(harness_app, ["adapters"])
    assert adp_res.exit_code == 0
    adp_data = json.loads(adp_res.stdout)["data"]
    assert "waza" in adp_data["benchmarks"]
    assert "dspy-gepa" in adp_data["optimizers"]
    assert "phoenix" in adp_data["sinks"]


def test_parse_task_split_aliases() -> None:
    assert parse_task_split("development") == Ok("train")
    assert parse_task_split("selection") == Ok("val")
    assert parse_task_split("holdout") == Ok("test")
    assert parse_task_split("unknown").is_error()

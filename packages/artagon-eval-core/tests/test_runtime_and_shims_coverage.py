"""Focused unit tests covering SecretVault, shims/{scrub,wire}, primitives, plugins, and CLI edges."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from expression import Error, Ok
from pydantic import ValidationError
from rpds import HashTrieMap
from typer.testing import CliRunner

from artagon_eval_core.cli.app import app as harness_app
from artagon_eval_core.cli.skillopt_proxy import app as skillopt_proxy_app
from artagon_eval_core.domain.errors import AdapterUnavailableError, NormativeExitCode
from artagon_eval_core.domain.primitives import (
    CampaignId,
    ConfinedScratchPath,
    ModelId,
    RelativeRepoPath,
    SkillId,
    parse_arm_id,
    parse_block_id,
    parse_campaign_id,
    parse_hmac_key_id,
    parse_safe_newtype,
    parse_task_family_id,
    parse_task_id,
    parse_task_split,
    parse_trial_id,
)
from artagon_eval_core.domain.types import FrozenModel
from artagon_eval_core.packaging.nix_check import app as nix_check_app
from artagon_eval_core.plugins.contracts import (
    EP_OPTIMIZERS,
    is_optimizer_adapter,
    load_adapter,
)
from artagon_eval_core.runtime.redact import SecretVault
from artagon_eval_core.shims.scrub import (
    REDACTED_PLACEHOLDER,
    StdlibSecretScrubber,
    is_sensitive_field_name,
)
from artagon_eval_core.shims.wire import decode_descriptor_bytes, encode_json_bytes


class _PrimitiveBox(FrozenModel):
    skill_id: SkillId
    rel_path: RelativeRepoPath
    model_id: ModelId
    scratch: ConfinedScratchPath


def test_primitives_validation_and_newtype_constructors(tmp_path: Path) -> None:
    cid = parse_campaign_id("camp-1")
    tid = parse_trial_id("trial-1")
    aid = parse_arm_id("arm-1")
    task_id = parse_task_id("task-1")
    bid = parse_block_id("block-1")
    fid = parse_task_family_id("fam-1")
    kid = parse_hmac_key_id("key-1")
    assert (cid, tid, aid, task_id, bid, fid, kid) == (
        "camp-1",
        "trial-1",
        "arm-1",
        "task-1",
        "block-1",
        "fam-1",
        "key-1",
    )

    with pytest.raises(ValueError, match="Invalid SafeId"):
        _ = parse_safe_newtype(CampaignId, "../bad")
    with pytest.raises(ValueError, match="Invalid SafeId"):
        _ = parse_campaign_id("bad/id")

    scratch = ConfinedScratchPath.from_validated(
        tmp_path, tmp_path / "scratch" / "skill-eval" / "camp-1", cid
    )
    scratch_dup = ConfinedScratchPath.from_validated(
        tmp_path, tmp_path / "scratch" / "skill-eval" / "camp-1", cid
    )
    assert str(scratch) == str(scratch.path)
    assert scratch == scratch_dup
    assert hash(scratch) == hash(scratch_dup)
    with pytest.raises(TypeError, match="from_validated"):
        _ = ConfinedScratchPath(tmp_path, cid, _token=object())

    box = _PrimitiveBox(
        skill_id="my-skill-1",
        rel_path="skills/my-skill-1/SKILL.md",
        model_id="claude-sonnet-4-6",
        scratch=scratch,
    )
    dumped = json.loads(box.model_dump_json())
    assert dumped["scratch"] == str(scratch.path)

    for bad_skill in ("", "UPPER", "a--b", "a" * 65):
        with pytest.raises(ValidationError):
            _ = _PrimitiveBox(
                skill_id=bad_skill,
                rel_path="ok/file.txt",
                model_id="m-1",
                scratch=scratch,
            )

    for bad_rel in ("", "/abs/path", "../escape", "a//b", "a\\b", "dir/", "C:win", "bad\x01char"):
        with pytest.raises(ValidationError):
            _ = _PrimitiveBox(
                skill_id="ok-skill",
                rel_path=bad_rel,
                model_id="m-1",
                scratch=scratch,
            )

    for sentinel in ("", "default", "AUTO"):
        with pytest.raises(ValidationError):
            _ = _PrimitiveBox(
                skill_id="ok-skill",
                rel_path="ok/file.txt",
                model_id=sentinel,
                scratch=scratch,
            )

    assert parse_task_split(123).is_error()
    assert parse_task_split("   ").is_error()


def test_stdlib_scrubber_and_secret_vault_branches() -> None:
    assert is_sensitive_field_name("api_key") is True
    assert is_sensitive_field_name("clientSecret") is True
    assert is_sensitive_field_name("api_key_ref") is False
    assert is_sensitive_field_name("harness") is False
    assert is_sensitive_field_name("input_tokens") is False

    scrubber = StdlibSecretScrubber(("exact-secret-1",))
    scrubber.register_secret("short")
    scrubber.register_secret("exact-secret-1")
    scrubber.register_secret("exact-secret-2")
    assert "exact-secret-2" in scrubber.exact_secrets
    assert scrubber.scrub_text("") == ""
    assert REDACTED_PLACEHOLDER in scrubber.scrub_text("Authorization: Bearer abcdefghijklmnop")

    mapped = scrubber.scrub_mapping_strings(
        {
            "api_key": "raw-val",
            "password": "",
            "auth_token": REDACTED_PLACEHOLDER,
            "note": "has exact-secret-2",
        }
    )
    assert mapped["api_key"] == REDACTED_PLACEHOLDER
    assert mapped["password"] == ""
    assert mapped["auth_token"] == REDACTED_PLACEHOLDER
    assert "exact-secret-2" not in mapped["note"]

    vault = SecretVault(enable_detect_secrets=True)
    vault.register_exact_secrets(("registered-secret-value",))
    assert vault.scrub_text("") == ""
    gh_sample = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    scrubbed_gh = vault.scrub(f"leak={gh_sample} and registered-secret-value")
    assert gh_sample not in scrubbed_gh
    assert "registered-secret-value" not in scrubbed_gh

    nested = vault.scrub_json(
        HashTrieMap(
            {
                "count": 3,
                "flag": True,
                "empty": None,
                "items": ("ok", "registered-secret-value", 1.5),
                "api_key": "",
                "auth_token": REDACTED_PLACEHOLDER,
                "secret_list": ("raw-a", "raw-b"),
                "secret_nested": HashTrieMap({"inner": "raw-c", "num": 5}),
            }
        )
    )
    assert isinstance(nested, HashTrieMap)
    assert nested["count"] == 3
    assert nested["empty"] is None
    assert nested["api_key"] == ""
    assert nested["auth_token"] == REDACTED_PLACEHOLDER
    assert nested["secret_list"] == (REDACTED_PLACEHOLDER, REDACTED_PLACEHOLDER)
    nested_sec = nested["secret_nested"]
    assert isinstance(nested_sec, HashTrieMap)
    assert nested_sec["inner"] == REDACTED_PLACEHOLDER
    assert nested_sec["num"] == 5

    ex1 = vault.scrub_excerpt(stdout_text=b"out registered-secret-value", stderr_text=None)
    assert "registered-secret-value" not in ex1
    ex2 = vault.scrub_excerpt(stdout_text="ok", stderr_text="err " + ("x" * 60), max_chars=25)
    assert len(ex2) == 25
    assert ex2.endswith("...")


def test_wire_descriptor_validation_error_branches(tmp_path: Path) -> None:
    base: dict[str, object] = {
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
        "model": "claude-sonnet-4-6",
        "expected_binary_size": 1024,
        "expected_binary_mtime_ns": 99999,
        "extra_argv": ["--quiet"],
        "injected_env": {"FOO": "bar"},
        "scrubbed_env_keys": ["OPENAI_API_KEY"],
        "hook_stdout_acks": {"pre": "ok"},
    }
    desc = decode_descriptor_bytes(encode_json_bytes(base))
    assert desc.expected_binary_size == 1024
    assert desc.injected_env["FOO"] == "bar"

    with pytest.raises(TypeError, match="Expected string field"):
        _ = decode_descriptor_bytes(encode_json_bytes({**base, "trial_id": 123}))
    with pytest.raises(ValueError, match="Expected string or None"):
        _ = decode_descriptor_bytes(encode_json_bytes({**base, "model": 123}))
    with pytest.raises(ValueError, match="Expected int or None"):
        _ = decode_descriptor_bytes(encode_json_bytes({**base, "expected_binary_size": True}))
    with pytest.raises(ValueError, match="Expected sequence of strings"):
        _ = decode_descriptor_bytes(encode_json_bytes({**base, "extra_argv": [1, 2]}))
    with pytest.raises(TypeError, match="Expected mapping"):
        _ = decode_descriptor_bytes(encode_json_bytes({**base, "injected_env": ["bad"]}))
    with pytest.raises(TypeError, match="Expected string mapping"):
        _ = decode_descriptor_bytes(encode_json_bytes({**base, "injected_env": {"k": 1}}))
    with pytest.raises(TypeError, match="root must be an object"):
        _ = decode_descriptor_bytes(b"[1, 2, 3]", force_stdlib=True)


def test_load_adapter_missing_and_cli_proxies(tmp_path: Path) -> None:
    missing = load_adapter(
        EP_OPTIMIZERS,
        "nonexistent-adapter",
        install_extra="nonexistent",
        protocol_guard=is_optimizer_adapter,
    )
    assert isinstance(missing, Error)
    assert isinstance(missing.error, AdapterUnavailableError)
    assert missing.error.exit_code == NormativeExitCode.ADAPTER_UNAVAILABLE

    runner = CliRunner()
    proxy_res = runner.invoke(skillopt_proxy_app, [])
    assert proxy_res.exit_code == 0
    assert json.loads(proxy_res.stdout)["data"]["available"] is True

    text_res = runner.invoke(harness_app, ["--output", "text", "version"])
    assert text_res.exit_code == 0

    missing_nix = runner.invoke(nix_check_app, ["--repo-root", str(tmp_path)])
    assert missing_nix.exit_code == int(NormativeExitCode.SCHEMA_USAGE)

    (tmp_path / "nix").mkdir()
    _ = (tmp_path / "nix" / "locked-versions.json").write_text("{bad json", encoding="utf-8")
    bad_json = runner.invoke(nix_check_app, ["--repo-root", str(tmp_path)])
    assert bad_json.exit_code == int(NormativeExitCode.SCHEMA_USAGE)

    _ = (tmp_path / "nix" / "locked-versions.json").write_text("[]", encoding="utf-8")
    non_obj = runner.invoke(nix_check_app, ["--repo-root", str(tmp_path)])
    assert non_obj.exit_code == int(NormativeExitCode.SCHEMA_USAGE)

    _ = (tmp_path / "nix" / "locked-versions.json").write_text(
        '{"python":"3.12"}', encoding="utf-8"
    )
    missing_keys = runner.invoke(nix_check_app, ["--repo-root", str(tmp_path)])
    assert missing_keys.exit_code == int(NormativeExitCode.SCHEMA_USAGE)

    _ = (tmp_path / "nix" / "locked-versions.json").write_text(
        '{"nixpkgs_rev":"abc","python":"3.12.15","packages":{"click":"8.3.1"},"tools":{"ruff":"0.15.14"}}',
        encoding="utf-8",
    )
    ok_nix = runner.invoke(nix_check_app, ["--repo-root", str(tmp_path)])
    assert ok_nix.exit_code == 0
    assert isinstance(Ok(ok_nix.exit_code), Ok)

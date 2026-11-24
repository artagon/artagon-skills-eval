"""Hypothesis property tests for constrained domain value objects and security boundaries."""

from __future__ import annotations

import importlib.util
import json
import string
import sys
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from expression import Error, Ok
from hypothesis import example, given
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError
from rpds import HashTrieMap

from artagon_eval_core.domain.errors import SchemaUsageError
from artagon_eval_core.domain.primitives import (
    CampaignId,
    ConfinedScratchPath,
    ModelId,
    RedactedJsonValue,
    RedactedStr,
    RelativeRepoPath,
    Sha256Hex,
    SkillId,
    TaskSplit,
    parse_task_split,
)
from artagon_eval_core.domain.types import FrozenModel, JsonValue
from artagon_eval_core.runtime.redact import SecretVault
from artagon_eval_core.shims.scrub import REDACTED_PLACEHOLDER

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


class _RelPathBox(FrozenModel):
    path: RelativeRepoPath


class _SkillIdBox(FrozenModel):
    skill_id: SkillId


class _Sha256Box(FrozenModel):
    digest: Sha256Hex


class _ModelIdBox(FrozenModel):
    model: ModelId


class _RedactedBox(FrozenModel):
    msg: RedactedStr


_FULLWIDTH_OFFSET = 0xFEE0


def _to_fullwidth_ascii(text: str) -> str:
    return "".join(
        chr(ord(ch) + _FULLWIDTH_OFFSET) if ("a" <= ch <= "z" or "0" <= ch <= "9") else ch
        for ch in text
    )


def _assert_all_leaves_redacted_and_clean(
    value: RedactedJsonValue,
    secrets: tuple[str, ...],
) -> None:
    if isinstance(value, str):
        assert isinstance(value, RedactedStr)
        for sec in secrets:
            assert sec not in value
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_all_leaves_redacted_and_clean(item, secrets)
        return
    if isinstance(value, HashTrieMap):
        for key, item in value.items():
            for sec in secrets:
                assert sec not in key
            _assert_all_leaves_redacted_and_clean(item, secrets)


# ---------------------------------------------------------------------------
# RelativeRepoPath
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(rel=strat.valid_relative_repo_paths())
def test_relative_repo_path_accepts_valid_posix_paths(rel: str) -> None:
    box = _RelPathBox(path=rel)
    assert box.path == rel
    assert _RelPathBox.model_validate_json(box.model_dump_json()) == box


@pytest.mark.property
@given(bad=strat.invalid_relative_repo_paths())
def test_relative_repo_path_rejects_adversarial_paths(bad: str) -> None:
    with pytest.raises(ValidationError):
        _ = _RelPathBox(path=bad)


# ---------------------------------------------------------------------------
# SkillId
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(skill_id=strat.valid_skill_ids(), use_fullwidth=st.booleans())
def test_skill_id_accepts_valid_kebab_and_nfkc_normalizes(
    skill_id: str,
    use_fullwidth: bool,
) -> None:
    candidate = _to_fullwidth_ascii(skill_id) if use_fullwidth else skill_id
    box = _SkillIdBox(skill_id=candidate)
    assert box.skill_id == unicodedata.normalize("NFKC", candidate)
    assert box.skill_id == skill_id
    assert 1 <= len(box.skill_id) <= 64
    assert _SkillIdBox(skill_id=box.skill_id).skill_id == box.skill_id


@pytest.mark.property
@given(bad=strat.invalid_skill_ids())
def test_skill_id_rejects_invalid_forms(bad: str) -> None:
    with pytest.raises(ValidationError):
        _ = _SkillIdBox(skill_id=bad)


# ---------------------------------------------------------------------------
# Sha256Hex
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(digest=strat.valid_sha256_hex())
def test_sha256_hex_accepts_64_lowercase_hex(digest: str) -> None:
    box = _Sha256Box(digest=digest)
    assert box.digest == digest


@pytest.mark.property
@given(bad=strat.invalid_sha256_hex())
def test_sha256_hex_rejects_invalid_digests(bad: str) -> None:
    with pytest.raises(ValidationError):
        _ = _Sha256Box(digest=bad)


# ---------------------------------------------------------------------------
# ModelId
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(sentinel=strat.sentinel_model_ids())
def test_model_id_rejects_sentinels_arbitrary_case_and_whitespace(sentinel: str) -> None:
    with pytest.raises(ValidationError):
        _ = _ModelIdBox(model=sentinel)


@pytest.mark.property
@given(raw=strat.valid_model_ids())
def test_model_id_accepts_and_trims_non_sentinels(raw: str) -> None:
    box = _ModelIdBox(model=raw)
    assert box.model == raw.strip()
    assert _ModelIdBox(model=box.model).model == box.model


# ---------------------------------------------------------------------------
# parse_task_split
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(alias_pair=strat.task_split_alias_inputs())
def test_parse_task_split_maps_all_aliases_deterministically(
    alias_pair: tuple[str, TaskSplit],
) -> None:
    raw, expected = alias_pair
    assert parse_task_split(raw) == Ok(expected)


@pytest.mark.property
@given(
    bad=st.one_of(
        strat.invalid_task_split_strings(),
        st.none(),
        st.integers(-100, 100),
        st.booleans(),
        st.floats(allow_nan=False, allow_infinity=False),
    )
)
def test_parse_task_split_rejects_non_alias_and_non_string_inputs(bad: object) -> None:
    res = parse_task_split(bad)
    match res:
        case Error((code, detail)):
            assert code == "invalid_task_split"
            assert bool(detail)
        case Ok(val):
            pytest.fail(f"Expected invalid_task_split error for {bad!r}, got Ok({val!r})")


# ---------------------------------------------------------------------------
# ConfinedScratchPath
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(
    repo_segs=st.lists(
        st.text(alphabet=string.ascii_lowercase + string.digits + "-", min_size=1, max_size=10),
        min_size=1,
        max_size=3,
    ),
    run_id=strat.campaign_ids(max_size=24),
    child_rel=strat.valid_relative_repo_paths(),
)
def test_confined_scratch_path_allows_valid_root_and_confines_child_rel(
    repo_segs: list[str],
    run_id: CampaignId,
    child_rel: str,
) -> None:
    repo_real = Path("/", *repo_segs)
    candidate = repo_real / "scratch" / "skill-eval" / str(run_id)
    confined = ConfinedScratchPath.from_validated(repo_real, candidate, run_id)

    assert confined.path == candidate
    assert confined.run_id == run_id
    child = confined.child_rel(child_rel)
    assert child.is_relative_to(confined.path)
    assert child != confined.path
    assert (repo_real / "plugins") not in child.parents


@pytest.mark.property
@given(
    repo_segs=st.lists(
        st.text(alphabet=string.ascii_lowercase + string.digits, min_size=1, max_size=8),
        min_size=1,
        max_size=3,
    ),
    run_id=strat.campaign_ids(max_size=20),
    other_id=strat.campaign_ids(max_size=20),
    sub_rel=strat.valid_relative_repo_paths(),
)
def test_confined_scratch_path_rejects_plugins_and_outside_scratch(
    repo_segs: list[str],
    run_id: CampaignId,
    other_id: CampaignId,
    sub_rel: str,
) -> None:
    repo_real = Path("/", *repo_segs)

    # Direct constructor without capability token must always fail
    with pytest.raises(TypeError, match="from_validated"):
        _ = ConfinedScratchPath(
            repo_real / "scratch" / "skill-eval" / str(run_id), run_id, _token=object()
        )

    # Inside plugins/ must ALWAYS fail with out_dir_inside_plugins
    for bad_plugin_path in (
        repo_real / "plugins",
        repo_real / "plugins" / str(run_id),
        repo_real / "plugins" / sub_rel,
    ):
        with pytest.raises(ValueError, match="out_dir_inside_plugins"):
            _ = ConfinedScratchPath.from_validated(repo_real, bad_plugin_path, run_id)

    # Outside <repo>/scratch/skill-eval/<run_id> must ALWAYS fail with run_dir_outside_scratch
    outside_candidates = [
        repo_real / "scratch" / str(run_id),
        repo_real / "scratch" / "skill-eval" / "nested" / str(run_id),
        repo_real / "other" / str(run_id),
        Path("/outside-repo") / "scratch" / "skill-eval" / str(run_id),
    ]
    if other_id != run_id:
        outside_candidates.append(repo_real / "scratch" / "skill-eval" / str(other_id))
    for bad_outside in outside_candidates:
        with pytest.raises(ValueError, match="run_dir_outside_scratch"):
            _ = ConfinedScratchPath.from_validated(repo_real, bad_outside, run_id)


# ---------------------------------------------------------------------------
# RedactedStr & SecretVault Security Boundary Laws
# ---------------------------------------------------------------------------


@pytest.mark.property
@given(raw=st.text(max_size=40))
def test_redacted_str_blocks_direct_construction_and_raw_pydantic_str(raw: str) -> None:
    with pytest.raises(TypeError, match="RedactedStr"):
        _ = RedactedStr(raw, _cap=object())
    with pytest.raises(TypeError):
        _ = RedactedStr(raw)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        _ = _RedactedBox.model_validate({"msg": raw})
    with pytest.raises(ValidationError):
        _ = SchemaUsageError.model_validate({"reason_code": "bad", "message": raw})


@pytest.mark.property
@given(
    secrets=st.lists(strat.high_entropy_secrets(), min_size=1, max_size=3, unique=True),
    prefix=st.text(alphabet=string.ascii_letters + string.digits + " :=/\n", max_size=24),
    middle=st.text(alphabet=string.ascii_letters + string.digits + " ,;\n", max_size=16),
    suffix=st.text(alphabet=string.ascii_letters + string.digits + " :=/\n", max_size=24),
)
def test_secret_vault_scrub_never_leaks_registered_secrets(
    secrets: list[str],
    prefix: str,
    middle: str,
    suffix: str,
) -> None:
    vault = SecretVault(exact_secrets=secrets, enable_detect_secrets=False)
    payload = f"{prefix}{middle.join(secrets)}{suffix}"
    scrubbed = vault.scrub(payload)

    assert isinstance(scrubbed, RedactedStr)
    for secret in secrets:
        assert secret not in scrubbed
    assert REDACTED_PLACEHOLDER in scrubbed


def _build_pattern_sample(pattern_kind: str, tail: str) -> tuple[str, str]:
    seg = tail[:12]
    builders = {
        "anthropic": (f"sk-ant-{tail}", f"sk-ant-{tail}"),
        "openai": (f"sk-proj-{tail}", f"sk-proj-{tail}"),
        "github_pat": (f"ghp_{tail}", f"ghp_{tail}"),
        "google_api": (f"AIza{tail}", f"AIza{tail}"),
        "jwt": (f"eyJ{seg}.eyJ{seg}.{seg}", f"eyJ{seg}.eyJ{seg}.{seg}"),
        "bearer": (f"Bearer {tail}", tail),
    }
    return builders[pattern_kind]


@pytest.mark.property
@given(
    pattern_kind=st.sampled_from(
        ("anthropic", "openai", "github_pat", "google_api", "jwt", "bearer")
    ),
    tail=st.text(alphabet=string.ascii_letters + string.digits, min_size=24, max_size=32),
    prefix=st.text(alphabet="xyz ", max_size=12),
    suffix=st.text(alphabet="xyz ", max_size=12),
)
def test_secret_vault_scrubs_unregistered_known_token_patterns(
    pattern_kind: str,
    tail: str,
    prefix: str,
    suffix: str,
) -> None:
    rendered_token, must_not_contain = _build_pattern_sample(pattern_kind, tail)
    raw = f"{prefix} {rendered_token} {suffix}"

    vault = SecretVault(enable_detect_secrets=False)
    scrubbed = vault.scrub(raw)
    assert isinstance(scrubbed, RedactedStr)
    assert must_not_contain not in scrubbed
    assert REDACTED_PLACEHOLDER in scrubbed


@pytest.mark.property
@given(
    secret=strat.high_entropy_secrets(),
    extra_tree=strat.json_values(max_leaves=8),
    sensitive_key=st.sampled_from(("api_key", "auth_token", "client_secret", "password")),
)
def test_secret_vault_scrub_json_never_leaks_and_seals_every_string(
    secret: str,
    extra_tree: JsonValue,
    sensitive_key: str,
) -> None:
    vault = SecretVault(exact_secrets=(secret,), enable_detect_secrets=False)
    tree: JsonValue = HashTrieMap(
        {
            f"key_{secret}": f"embedded={secret}",
            sensitive_key: f"raw_credential_{secret}",
            "nested": (extra_tree, HashTrieMap({"deep": f"before {secret} after"})),
        }
    )
    scrubbed = vault.scrub_json(tree)
    _assert_all_leaves_redacted_and_clean(scrubbed, (secret,))

    dumped = json.dumps(
        TypeAdapter(RedactedJsonValue).dump_python(scrubbed, mode="json"),
        sort_keys=True,
    )
    assert secret not in dumped


@pytest.mark.property
@given(
    secret=strat.high_entropy_secrets(),
    lead_len=st.integers(min_value=0, max_value=40),
    max_chars=st.integers(min_value=1, max_value=80),
    as_bytes=st.booleans(),
    in_stderr=st.booleans(),
)
def test_secret_vault_scrub_excerpt_never_leaks_at_clip_boundary(
    secret: str,
    lead_len: int,
    max_chars: int,
    as_bytes: bool,
    in_stderr: bool,
) -> None:
    vault = SecretVault(exact_secrets=(secret,), enable_detect_secrets=False)
    # Place secret directly across or near max_chars clip boundary
    lead = "a" * lead_len
    raw_stream = f"{lead}{secret}zzzzzz"
    payload: str | bytes = raw_stream.encode("utf-8") if as_bytes else raw_stream

    excerpt = vault.scrub_excerpt(
        stderr_text=payload if in_stderr else "ok-stderr",
        stdout_text="ok-stdout" if in_stderr else payload,
        max_chars=max_chars,
    )
    assert isinstance(excerpt, RedactedStr)
    assert len(excerpt) <= max_chars
    assert secret not in excerpt
    # Verify even a partial clip of the secret cannot leak (since scrubbing precedes clipping)
    probe_prefix = secret[:8]
    if probe_prefix not in "stderr= | stdout=ok-stdraazzz...[REDACTED_SECRET]":
        assert probe_prefix not in excerpt


@pytest.mark.property
@example(
    secrets=["SECRET", "REDACTED"],
    text="leak SECRET and REDACTED and [REDACTED_SECRET]",
)
@given(
    secrets=st.lists(
        st.one_of(
            strat.high_entropy_secrets(),
            st.sampled_from(("SECRET", "REDACTED", "TED_SE", REDACTED_PLACEHOLDER)),
        ),
        max_size=3,
    ),
    text=st.text(
        alphabet=string.ascii_letters + string.digits + " []_-:/.\n",
        max_size=80,
    ),
)
def test_secret_vault_scrub_is_idempotent(secrets: list[str], text: str) -> None:
    vault = SecretVault(exact_secrets=secrets, enable_detect_secrets=False)
    once = str(vault.scrub(text))
    twice = str(vault.scrub(once))
    assert twice == once

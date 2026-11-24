"""Hypothesis property tests for agentskills.io skills-ref spec_adapter Tier-0 validation."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from expression import NOTHING, Error, Ok, Some
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError
from rpds import HashTrieMap

from artagon_eval_core.domain.errors import NormativeExitCode, SchemaUsageError
from artagon_eval_core.domain.primitives import RedactedStr
from artagon_eval_core.runtime.redact import SecretVault
from artagon_eval_skills.spec_adapter import SkillFrontmatter, load_and_validate_spec_tier0

if TYPE_CHECKING:
    import strategies as strat
else:
    _STRAT_MOD = "artagon_eval_core_test_strategies"
    if _STRAT_MOD in sys.modules:
        strat = sys.modules[_STRAT_MOD]
    else:
        _strategies_file = (
            Path(__file__).resolve().parents[2] / "artagon-eval-core" / "tests" / "strategies.py"
        )
        _spec = importlib.util.spec_from_file_location(_STRAT_MOD, _strategies_file)
        assert _spec is not None
        assert _spec.loader is not None
        strat = importlib.util.module_from_spec(_spec)
        sys.modules[_STRAT_MOD] = strat
        _spec.loader.exec_module(strat)


@pytest.mark.property
@given(
    doc=strat.valid_skill_doc_inputs(),
    skill_rel_dir=st.one_of(st.none(), strat.valid_relative_repo_paths()),
)
def test_valid_generated_skill_md_always_parses_into_exact_frozen_frontmatter(
    doc: strat.SkillDocInput,
    skill_rel_dir: str | None,
) -> None:
    scrubber = SecretVault(enable_detect_secrets=False)
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp) / doc.name
        skill_dir.mkdir()
        _ = (skill_dir / "SKILL.md").write_text(strat.render_skill_md(doc), encoding="utf-8")

        result = load_and_validate_spec_tier0(
            skill_dir,
            skill_rel_dir=skill_rel_dir,
            scrubber=scrubber,
        )
        match result:
            case Ok(fm):
                assert isinstance(fm, SkillFrontmatter)
                assert fm.name == doc.name
                assert fm.description == doc.description
                assert fm.license == (
                    Some(doc.license_text) if doc.license_text is not None else NOTHING
                )
                assert fm.compatibility == (
                    Some(doc.compatibility) if doc.compatibility is not None else NOTHING
                )
                assert fm.allowed_tools == doc.allowed_tools
                assert fm.metadata == HashTrieMap(dict(doc.metadata))
                assert fm.body_markdown == doc.body
                assert fm.skill_dir == skill_dir
                assert fm.skill_rel_dir == (
                    Some(skill_rel_dir) if skill_rel_dir is not None else NOTHING
                )
                with pytest.raises(ValidationError):
                    fm.name = "mutated"  # type: ignore[misc]
            case Error(err):
                pytest.fail(f"Expected Ok(SkillFrontmatter) for {doc!r}, got Error({err!r})")


@pytest.mark.property
@given(
    doc=strat.valid_skill_doc_inputs(),
    other_dir_name=strat.valid_skill_ids(),
)
def test_mismatched_directory_name_always_returns_schema_usage_error(
    doc: strat.SkillDocInput,
    other_dir_name: str,
) -> None:
    dir_name = other_dir_name if other_dir_name != doc.name else f"{doc.name[:62]}-x"
    if dir_name == doc.name:
        dir_name = "alt-dir-name"
    scrubber = SecretVault(enable_detect_secrets=False)
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp) / dir_name
        skill_dir.mkdir()
        _ = (skill_dir / "SKILL.md").write_text(strat.render_skill_md(doc), encoding="utf-8")

        result = load_and_validate_spec_tier0(skill_dir, scrubber=scrubber)
        match result:
            case Error(err):
                assert isinstance(err, SchemaUsageError)
                assert err.exit_code == NormativeExitCode.SCHEMA_USAGE
                assert isinstance(err.message, RedactedStr)
                assert err.redacted is True
            case Ok(fm):
                pytest.fail(f"Expected dir mismatch failure for {dir_name!r} vs {doc.name!r}: {fm}")


@pytest.mark.property
@given(
    dir_name=strat.valid_skill_ids(),
    malformed=st.one_of(
        st.text(max_size=80).filter(lambda s: not s.startswith("---")),
        st.text(max_size=60).map(lambda s: f"---\n{s.replace('---', '')}"),
        st.just("---\n- not-a-mapping\n---\nbody\n"),
        st.just("---\nname: only-name\n---\nbody\n"),
        st.just("---\ndescription: missing-name\n---\nbody\n"),
        strat.invalid_skill_ids().map(
            lambda bad: f"---\nname: '{bad.replace(chr(39), '')}'\ndescription: ok\n---\n"
        ),
        st.just("---\nname: valid-name\ndescription: ok\nunknown-extra: nope\n---\n"),
    ),
)
def test_invalid_frontmatter_always_returns_schema_usage_error(
    dir_name: str,
    malformed: str,
) -> None:
    scrubber = SecretVault(enable_detect_secrets=False)
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp) / dir_name
        skill_dir.mkdir()
        _ = (skill_dir / "SKILL.md").write_text(malformed, encoding="utf-8")

        result = load_and_validate_spec_tier0(skill_dir, scrubber=scrubber)
        match result:
            case Error(err):
                assert isinstance(err, SchemaUsageError)
                assert err.exit_code == NormativeExitCode.SCHEMA_USAGE
                assert isinstance(err.message, RedactedStr)
                assert err.redacted is True
            case Ok(fm):
                pytest.fail(f"Expected SchemaUsageError for malformed content, got {fm!r}")


@pytest.mark.property
@given(
    dir_name=strat.valid_skill_ids(),
    bad_bytes=st.binary(min_size=1, max_size=32).map(lambda b: b"\xff\xfe" + b),
)
def test_invalid_utf8_bytes_always_returns_schema_usage_error(
    dir_name: str,
    bad_bytes: bytes,
) -> None:
    scrubber = SecretVault(enable_detect_secrets=False)
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp) / dir_name
        skill_dir.mkdir()
        _ = (skill_dir / "SKILL.md").write_bytes(bad_bytes)

        result = load_and_validate_spec_tier0(skill_dir, scrubber=scrubber)
        match result:
            case Error(err):
                assert isinstance(err, SchemaUsageError)
                assert err.reason_code == "skill_md_unreadable"
                assert err.exit_code == NormativeExitCode.SCHEMA_USAGE
                assert isinstance(err.message, RedactedStr)
            case Ok(fm):
                pytest.fail(f"Expected unreadable UTF-8 error, got {fm!r}")


@pytest.mark.property
@given(
    name=strat.valid_skill_ids(),
    excess=st.integers(min_value=1, max_value=200),
    check_compatibility=st.booleans(),
)
def test_overlong_description_or_compatibility_always_returns_schema_usage_error(
    name: str,
    excess: int,
    check_compatibility: bool,
) -> None:
    scrubber = SecretVault(enable_detect_secrets=False)
    if check_compatibility:
        content = (
            f"---\nname: {name}\ndescription: valid desc\n"
            f"compatibility: {'c' * (500 + excess)}\n---\n"
        )
    else:
        content = f"---\nname: {name}\ndescription: {'d' * (1024 + excess)}\n---\n"

    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp) / name
        skill_dir.mkdir()
        _ = (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

        result = load_and_validate_spec_tier0(skill_dir, scrubber=scrubber)
        match result:
            case Error(err):
                assert isinstance(err, SchemaUsageError)
                assert err.exit_code == NormativeExitCode.SCHEMA_USAGE
                assert isinstance(err.message, RedactedStr)
            case Ok(fm):
                pytest.fail(f"Expected length limit failure, got {fm!r}")


@pytest.mark.property
@given(dir_name=strat.valid_skill_ids())
def test_missing_skill_md_always_returns_schema_usage_error(dir_name: str) -> None:
    scrubber = SecretVault(enable_detect_secrets=False)
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp) / dir_name
        skill_dir.mkdir()

        result = load_and_validate_spec_tier0(skill_dir, scrubber=scrubber)
        match result:
            case Error(err):
                assert isinstance(err, SchemaUsageError)
                assert err.reason_code == "skill_md_missing"
                assert err.exit_code == NormativeExitCode.SCHEMA_USAGE
                assert isinstance(err.message, RedactedStr)
            case Ok(fm):
                pytest.fail(f"Expected missing SKILL.md error, got {fm!r}")

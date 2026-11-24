"""Unit tests for official agentskills.io `skills-ref` spec_adapter and skill-lint CLI."""

from __future__ import annotations

import json
from pathlib import Path

from expression import NOTHING, Error, Ok, Some
from typer.testing import CliRunner

from artagon_eval_core.domain.errors import NormativeExitCode, SchemaUsageError
from artagon_eval_core.domain.primitives import RedactedStr
from artagon_eval_skills.cli.app import app as skill_eval_app
from artagon_eval_skills.cli.lint import app as skill_lint_app
from artagon_eval_skills.spec_adapter import SkillFrontmatter, load_and_validate_spec_tier0

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_load_and_validate_valid_skill_with_bom(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    _ = (skill_dir / "SKILL.md").write_text(
        "\ufeff---\n"
        "name: demo-skill\n"
        "description: Validate demo skill frontmatter parsing.\n"
        "license: MIT\n"
        "allowed-tools: Read Grep\n"
        "metadata:\n"
        "  owner: artagon\n"
        "---\n\n"
        "# Demo Skill\n",
        encoding="utf-8",
    )

    result = load_and_validate_spec_tier0(skill_dir, skill_rel_dir="skills/demo-skill")
    match result:
        case Ok(fm):
            assert isinstance(fm, SkillFrontmatter)
            assert fm.name == "demo-skill"
            assert fm.license == Some("MIT")
            assert fm.compatibility is NOTHING
            assert fm.allowed_tools == ("Read", "Grep")
            assert fm.metadata["owner"] == "artagon"
            assert "# Demo Skill" in fm.body_markdown
        case Error(err):
            raise AssertionError(f"Unexpected error: {err}")


def test_invalid_skill_returns_redacted_schema_usage_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir()
    _ = (skill_dir / "SKILL.md").write_text(
        "---\nname: WRONG_NAME\ndescription: Broken name.\n---\nBody\n",
        encoding="utf-8",
    )

    result = load_and_validate_spec_tier0(skill_dir)
    match result:
        case Error(err):
            assert isinstance(err, SchemaUsageError)
            assert err.exit_code == NormativeExitCode.SCHEMA_USAGE
            assert isinstance(err.message, RedactedStr)
        case Ok(fm):
            raise AssertionError(f"Expected validation failure, got {fm}")


def test_missing_skill_md_returns_error(tmp_path: Path) -> None:
    result = load_and_validate_spec_tier0(tmp_path)
    assert result.is_error()


def test_repo_bundled_skills_validate_via_cli() -> None:
    runner = CliRunner()
    res = runner.invoke(skill_lint_app, ["--skills-dir", str(REPO_ROOT / "skills")])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.stdout)
    assert payload["ok"] is True
    assert payload["data"]["passed_count"] == 3
    assert set(payload["data"]["validated_skills"]) == {
        "harness-eval",
        "harness-eval-author",
        "harness-eval-trace",
    }

    ver = runner.invoke(skill_eval_app, ["version"])
    assert ver.exit_code == 0
    assert json.loads(ver.stdout)["data"]["package"] == "artagon-eval-skills"

    lint_via_eval = runner.invoke(
        skill_eval_app, ["lint", "--skills-dir", str(REPO_ROOT / "skills")]
    )
    assert lint_via_eval.exit_code == 0
    assert json.loads(lint_via_eval.stdout)["data"]["passed_count"] == 3


def test_skill_lint_error_and_single_skill_branches(tmp_path: Path) -> None:
    runner = CliRunner()

    missing_dir = runner.invoke(skill_lint_app, ["--skills-dir", str(tmp_path / "nope")])
    assert missing_dir.exit_code == int(NormativeExitCode.SCHEMA_USAGE)

    empty_dir = runner.invoke(skill_lint_app, ["--skills-dir", str(tmp_path)])
    assert empty_dir.exit_code == int(NormativeExitCode.SCHEMA_USAGE)

    single = tmp_path / "single-skill"
    single.mkdir()
    _ = (single / "SKILL.md").write_text(
        "---\nname: single-skill\ndescription: Single skill test.\n---\n# Body\n",
        encoding="utf-8",
    )
    single_ok = runner.invoke(skill_lint_app, ["--skills-dir", str(single)])
    assert single_ok.exit_code == 0
    assert json.loads(single_ok.stdout)["data"]["validated_skills"] == ["single-skill"]

    broken = tmp_path / "broken-yaml"
    broken.mkdir()
    _ = (broken / "SKILL.md").write_text("no frontmatter header here\n", encoding="utf-8")
    broken_res = runner.invoke(skill_lint_app, ["--skills-dir", str(broken)])
    assert broken_res.exit_code == int(NormativeExitCode.SCHEMA_USAGE)

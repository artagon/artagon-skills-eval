"""Typer CLI entrypoint for `skill-lint` (Tier-0 agentskills.io validation via spec_adapter)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from expression import Error, Ok

from artagon_eval_core.cli.app import emit_cli_result
from artagon_eval_core.domain.errors import EvalResult, SchemaUsageError
from artagon_eval_core.domain.primitives import static_redacted_literal
from artagon_eval_core.domain.types import FrozenModel
from artagon_eval_core.ports.effects import SecretScrubberPort
from artagon_eval_core.runtime.logging import configure_stderr_logger
from artagon_eval_core.runtime.redact import SecretVault
from artagon_eval_skills.spec_adapter import load_and_validate_spec_tier0

app = typer.Typer(
    name="skill-lint",
    help="Validate Agent Skills against official agentskills.io specification via skills-ref.",
    no_args_is_help=False,
)


class LintSummaryPayload(FrozenModel):
    skills_dir: str
    validated_skills: tuple[str, ...]
    passed_count: int


def lint_skills_directory(
    skills_dir: Path,
    *,
    scrubber: SecretScrubberPort | None = None,
) -> EvalResult[LintSummaryPayload]:
    """Validate every skill folder containing SKILL.md under skills_dir."""
    if not skills_dir.is_dir():
        return Error(
            SchemaUsageError(
                reason_code="skills_dir_missing",
                message=static_redacted_literal("Skills directory does not exist"),
            )
        )
    skill_dirs = sorted(p.parent for p in skills_dir.glob("*/SKILL.md"))
    if (skills_dir / "SKILL.md").is_file():
        skill_dirs = [skills_dir]
    if not skill_dirs:
        return Error(
            SchemaUsageError(
                reason_code="no_skills_found",
                message=static_redacted_literal("No SKILL.md files found under target directory"),
            )
        )
    validated: list[str] = []
    for sdir in skill_dirs:
        match load_and_validate_spec_tier0(sdir, scrubber=scrubber):
            case Ok(frontmatter):
                validated.append(frontmatter.name)
            case Error(err):
                return Error(err)
    return Ok(
        LintSummaryPayload(
            skills_dir=str(skills_dir),
            validated_skills=tuple(validated),
            passed_count=len(validated),
        )
    )


@app.command()
def check(
    skills_dir: Annotated[
        Path,
        typer.Option("--skills-dir", help="Directory containing skill folders or a single skill."),
    ] = Path("skills"),
) -> None:
    """Validate all SKILL.md manifests under --skills-dir."""
    vault = SecretVault()
    logger = configure_stderr_logger(vault)
    result = lint_skills_directory(skills_dir.resolve(), scrubber=vault)
    code = emit_cli_result("skill-lint", result, logger=logger)
    raise typer.Exit(code=code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

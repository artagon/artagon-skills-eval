"""Typer CLI entrypoint for `skill-eval`."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from expression import Ok

from artagon_eval_core.cli.app import emit_cli_result
from artagon_eval_core.domain.types import FrozenModel
from artagon_eval_core.runtime.logging import configure_stderr_logger
from artagon_eval_core.runtime.redact import SecretVault
from artagon_eval_skills import __version__
from artagon_eval_skills.cli.lint import lint_skills_directory

app = typer.Typer(
    name="skill-eval",
    help="Subscription-first Agent Skill evaluation, static linting, and gate workflows.",
    no_args_is_help=True,
)


class SkillEvalVersionPayload(FrozenModel):
    package: str = "artagon-eval-skills"
    version: str = __version__


@app.command()
def version() -> None:
    """Print the installed artagon-eval-skills version envelope."""
    vault = SecretVault()
    logger = configure_stderr_logger(vault)
    code = emit_cli_result("skill-eval-version", Ok(SkillEvalVersionPayload()), logger=logger)
    raise typer.Exit(code=code)


@app.command()
def lint(
    skills_dir: Annotated[
        Path,
        typer.Option("--skills-dir", help="Directory containing skill folders with SKILL.md."),
    ] = Path("skills"),
) -> None:
    """Run Tier-0 official agentskills.io specification lint across a skills directory."""
    vault = SecretVault()
    logger = configure_stderr_logger(vault)
    result = lint_skills_directory(skills_dir.resolve(), scrubber=vault)
    code = emit_cli_result("skill-eval-lint", result, logger=logger)
    raise typer.Exit(code=code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

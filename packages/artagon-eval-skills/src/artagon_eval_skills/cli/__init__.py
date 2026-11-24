"""Typer CLI entrypoints for `skill-eval` and `skill-lint`."""

from __future__ import annotations

from artagon_eval_skills.cli.app import app as skill_eval_app
from artagon_eval_skills.cli.lint import app as skill_lint_app

__all__ = ["skill_eval_app", "skill_lint_app"]

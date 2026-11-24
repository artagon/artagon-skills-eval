"""CLI entrypoint for `harness-eval-nix-check` (starter Phase 0/1 verification)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from expression import Error, Ok

from artagon_eval_core.cli.app import emit_cli_result
from artagon_eval_core.domain.errors import EvalResult, SchemaUsageError
from artagon_eval_core.domain.primitives import static_redacted_literal
from artagon_eval_core.domain.types import FrozenModel
from artagon_eval_core.runtime.logging import configure_stderr_logger
from artagon_eval_core.runtime.redact import SecretVault

app = typer.Typer(
    name="harness-eval-nix-check",
    help="Verify locked Nix versions and ADR-0006 offline flake readiness.",
    no_args_is_help=False,
)


class NixReceiptSummary(FrozenModel):
    locked_versions_path: str
    nixpkgs_rev: str
    python_version: str
    package_count: int
    tool_count: int


def _inspect_locked_receipt(repo_root: Path) -> EvalResult[NixReceiptSummary]:
    receipt_path = repo_root / "nix" / "locked-versions.json"
    if not receipt_path.is_file():
        return Error(
            SchemaUsageError(
                reason_code="locked_versions_missing",
                message=static_redacted_literal("nix/locked-versions.json not found"),
            )
        )
    try:
        raw: object = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Error(
            SchemaUsageError(
                reason_code="locked_versions_invalid",
                message=static_redacted_literal("Failed to parse nix/locked-versions.json"),
            )
        )
    if not isinstance(raw, dict):
        return Error(
            SchemaUsageError(
                reason_code="locked_versions_invalid",
                message=static_redacted_literal("nix/locked-versions.json root must be an object"),
            )
        )
    packages = raw.get("packages")
    tools = raw.get("tools")
    rev = raw.get("nixpkgs_rev")
    py_ver = raw.get("python")
    if (
        not isinstance(rev, str)
        or not isinstance(py_ver, str)
        or not isinstance(packages, dict)
        or not isinstance(tools, dict)
    ):
        return Error(
            SchemaUsageError(
                reason_code="locked_versions_invalid",
                message=static_redacted_literal("nix/locked-versions.json missing required keys"),
            )
        )
    return Ok(
        NixReceiptSummary(
            locked_versions_path="nix/locked-versions.json",
            nixpkgs_rev=rev,
            python_version=py_ver,
            package_count=len(packages),
            tool_count=len(tools),
        )
    )


@app.command()
def check(
    repo_root: Annotated[
        Path,
        typer.Option("--repo-root", help="Workspace root containing flake.nix and nix/."),
    ] = Path(),
) -> None:
    """Validate nix/locked-versions.json presence and structure."""
    vault = SecretVault()
    logger = configure_stderr_logger(vault)
    result = _inspect_locked_receipt(repo_root.resolve())
    code = emit_cli_result("nix-check", result, logger=logger)
    raise typer.Exit(code=code)


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(app())

"""Lazy Typer proxy for `skillopt-runner` failing closed with exit 69 when missing."""

from __future__ import annotations

import typer

from artagon_eval_core.cli.app import emit_cli_result
from artagon_eval_core.domain.types import FrozenModel
from artagon_eval_core.plugins.contracts import (
    EP_OPTIMIZERS,
    is_optimizer_adapter,
    load_adapter,
)
from artagon_eval_core.runtime.logging import configure_stderr_logger
from artagon_eval_core.runtime.redact import SecretVault

app = typer.Typer(
    name="skillopt-runner",
    help="Isolated subscription proxy for the optional artagon-eval-skillopt adapter.",
    no_args_is_help=True,
)


class SkillOptStatusPayload(FrozenModel):
    adapter: str
    install_extra: str
    available: bool


@app.command()
def status() -> None:
    """Check whether the optional artagon-eval-skillopt adapter is installed."""
    vault = SecretVault()
    logger = configure_stderr_logger(vault)
    loaded = load_adapter(
        EP_OPTIMIZERS,
        "skillopt",
        install_extra="skillopt",
        protocol_guard=is_optimizer_adapter,
    ).map(
        lambda adapter: SkillOptStatusPayload(
            adapter=adapter.name,
            install_extra=adapter.install_extra,
            available=True,
        )
    )
    code = emit_cli_result("skillopt-status", loaded, logger=logger)
    raise typer.Exit(code=code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

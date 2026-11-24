"""Root Typer CLI for `harness-eval` using ctx.obj injection (zero module globals)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Annotated, Literal, TextIO

import structlog
import typer
from expression import Error, Ok

from artagon_eval_core import __version__
from artagon_eval_core.domain.errors import (
    ErrEnvelope,
    EvalResult,
    NormativeExitCode,
    OkEnvelope,
    map_error_to_exit_code,
)
from artagon_eval_core.domain.primitives import SafeId
from artagon_eval_core.domain.types import FrozenModel
from artagon_eval_core.plugins.contracts import (
    EP_BENCHMARKS,
    EP_OPTIMIZERS,
    EP_SINKS,
    list_installed_adapters,
)
from artagon_eval_core.ports.effects import SecretScrubberPort
from artagon_eval_core.runtime.logging import configure_stderr_logger, log_eval_error
from artagon_eval_core.runtime.redact import SecretVault


@dataclass(frozen=True, slots=True)
class AppContext:
    """Per-invocation CLI context stored on typer.Context.obj."""

    output_format: Literal["json", "text"]
    scrubber: SecretScrubberPort
    logger: structlog.typing.FilteringBoundLogger


class VersionPayload(FrozenModel):
    package: str = "artagon-eval-core"
    version: str = __version__


class AdapterCatalogPayload(FrozenModel):
    optimizers: tuple[str, ...]
    benchmarks: tuple[str, ...]
    sinks: tuple[str, ...]


def emit_cli_result[T: FrozenModel](
    command: SafeId,
    result: EvalResult[T],
    *,
    logger: structlog.typing.FilteringBoundLogger,
    output_format: Literal["json", "text"] = "json",
    stdout: TextIO | None = None,
) -> int:
    """Emit canonical Envelope[T] on stdout and mandatory redacted structlog on stderr."""
    out = sys.stdout if stdout is None else stdout
    match result:
        case Ok(data):
            envelope = OkEnvelope(command=command, data=data)
            _ = out.write(envelope.model_dump_json(indent=2) + "\n")
            return int(NormativeExitCode.OK)
        case Error(err):
            log_eval_error(logger, command, err)
            if output_format == "json":
                err_env = ErrEnvelope.from_eval_error(command, err)
                _ = out.write(err_env.model_dump_json(indent=2) + "\n")
            return int(map_error_to_exit_code(err))


app = typer.Typer(
    name="harness-eval",
    help="Multi-CLI harness evaluation platform (functional core + lazy Pluggy adapters).",
    no_args_is_help=True,
)


def _get_ctx(ctx: typer.Context) -> AppContext:
    if isinstance(ctx.obj, AppContext):
        return ctx.obj
    vault = SecretVault()
    return AppContext(
        output_format="json",
        scrubber=vault,
        logger=configure_stderr_logger(vault),
    )


@app.callback()
def _init_context(
    ctx: typer.Context,
    output: Annotated[
        Literal["json", "text"],
        typer.Option("--output", help="Output format for command envelopes."),
    ] = "json",
) -> None:
    vault = SecretVault()
    ctx.obj = AppContext(
        output_format=output,
        scrubber=vault,
        logger=configure_stderr_logger(vault),
    )


@app.command()
def version(ctx: typer.Context) -> None:
    """Print the installed artagon-eval-core version envelope."""
    app_ctx = _get_ctx(ctx)
    code = emit_cli_result(
        "version",
        Ok(VersionPayload()),
        logger=app_ctx.logger,
        output_format=app_ctx.output_format,
    )
    raise typer.Exit(code=code)


@app.command()
def adapters(ctx: typer.Context) -> None:
    """List lazily discovered Pluggy adapters without importing them."""
    app_ctx = _get_ctx(ctx)
    payload = AdapterCatalogPayload(
        optimizers=list_installed_adapters(EP_OPTIMIZERS),
        benchmarks=list_installed_adapters(EP_BENCHMARKS),
        sinks=list_installed_adapters(EP_SINKS),
    )
    code = emit_cli_result(
        "adapters",
        Ok(payload),
        logger=app_ctx.logger,
        output_format=app_ctx.output_format,
    )
    raise typer.Exit(code=code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

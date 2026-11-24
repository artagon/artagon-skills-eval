"""Structured stderr logging backed by structlog with mandatory SecretScrubberPort redaction."""

from __future__ import annotations

import sys
from collections.abc import MutableMapping
from typing import TextIO

import structlog

from artagon_eval_core.domain.errors import EvalError, map_error_to_exit_code
from artagon_eval_core.ports.effects import SecretScrubberPort


def _scrub_event_value(scrubber: SecretScrubberPort, value: object) -> object:
    if isinstance(value, str):
        return str(scrubber.scrub(value))
    if isinstance(value, tuple):
        return [_scrub_event_value(scrubber, item) for item in value]
    if isinstance(value, list):
        return [_scrub_event_value(scrubber, item) for item in value]
    if isinstance(value, dict):
        return {
            str(scrubber.scrub(str(k))): _scrub_event_value(scrubber, v) for k, v in value.items()
        }
    return value


def _make_redact_processor(
    scrubber: SecretScrubberPort,
) -> structlog.types.Processor:
    def _processor(
        _logger: object,
        _method_name: str,
        event_dict: MutableMapping[str, object],
    ) -> MutableMapping[str, object]:
        for key in tuple(event_dict.keys()):
            event_dict[key] = _scrub_event_value(scrubber, event_dict[key])
        return event_dict

    return _processor


def configure_stderr_logger(
    scrubber: SecretScrubberPort,
    *,
    stream: TextIO | None = None,
) -> structlog.typing.FilteringBoundLogger:
    """Create a bound structlog logger writing redacted JSON records strictly to stderr."""
    target = sys.stderr if stream is None else stream
    logger: structlog.typing.FilteringBoundLogger = structlog.wrap_logger(
        structlog.PrintLogger(file=target),
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _make_redact_processor(scrubber),
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
    )
    return logger


def log_eval_error(
    logger: structlog.typing.FilteringBoundLogger,
    command: str,
    err: EvalError,
) -> None:
    """Emit a mandatory redacted diagnostic line to stderr for any EvalError."""
    logger.error(
        "eval_command_failed",
        command=command,
        error_kind=err.kind,
        exit_code=int(map_error_to_exit_code(err)),
        reason_code=err.reason_code,
        error=str(err.message),
        log_paths=[str(p) for p in err.log_paths],
        redacted=err.redacted,
    )

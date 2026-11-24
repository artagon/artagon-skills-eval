"""Shared control-plane runtime primitives (SecretVault redaction and structlog stderr)."""

from __future__ import annotations

from artagon_eval_core.runtime.logging import configure_stderr_logger, log_eval_error
from artagon_eval_core.runtime.redact import SecretVault

__all__ = [
    "SecretVault",
    "configure_stderr_logger",
    "log_eval_error",
]

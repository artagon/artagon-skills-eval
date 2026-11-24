"""ADR-0012 hot-path shims: stdlib and optional msgspec ONLY."""

from __future__ import annotations

from artagon_eval_core.shims.scrub import (
    REDACTED_PLACEHOLDER,
    SECRET_PATTERNS,
    StdlibSecretScrubber,
    is_sensitive_field_name,
)
from artagon_eval_core.shims.wire import (
    HAVE_MSGSPEC,
    HotPathShimDescriptor,
    decode_descriptor_bytes,
    encode_json_bytes,
)

__all__ = [
    "HAVE_MSGSPEC",
    "REDACTED_PLACEHOLDER",
    "SECRET_PATTERNS",
    "HotPathShimDescriptor",
    "StdlibSecretScrubber",
    "decode_descriptor_bytes",
    "encode_json_bytes",
    "is_sensitive_field_name",
]

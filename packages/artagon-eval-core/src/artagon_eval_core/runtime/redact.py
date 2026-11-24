"""Control-plane SecretVault implementing SecretScrubberPort and minting RedactedStr."""

from __future__ import annotations

import threading
from collections.abc import Iterable, Mapping
from typing import Final

from detect_secrets.core.scan import scan_line
from detect_secrets.settings import transient_settings
from rpds import HashTrieMap

from artagon_eval_core.domain.primitives import (
    NonNegInt,
    PositiveInt,
    RedactedJsonValue,
    RedactedStr,
    _mint_redacted_str,
)
from artagon_eval_core.domain.types import JsonValue
from artagon_eval_core.shims.scrub import (
    REDACTED_PLACEHOLDER,
    StdlibSecretScrubber,
    is_sensitive_field_name,
)

_DETECT_SECRETS_PLUGINS: Final[tuple[str, ...]] = (
    "AWSKeyDetector",
    "AzureStorageKeyDetector",
    "BasicAuthDetector",
    "DiscordBotTokenDetector",
    "GitHubTokenDetector",
    "GitLabTokenDetector",
    "JwtTokenDetector",
    "NpmDetector",
    "OpenAIDetector",
    "PrivateKeyDetector",
    "SendGridDetector",
    "SlackDetector",
    "StripeDetector",
    "TelegramBotTokenDetector",
    "TwilioKeyDetector",
)

_DETECT_SECRETS_LOCK: Final[threading.Lock] = threading.Lock()


def _detect_secrets_values(line: str) -> list[str]:
    if not line or len(line) < 12:
        return []
    config: dict[str, object] = {
        "plugins_used": [{"name": plugin_name} for plugin_name in _DETECT_SECRETS_PLUGINS]
    }
    found: list[str] = []
    with _DETECT_SECRETS_LOCK, transient_settings(config):
        for candidate in scan_line(line):
            secret_val = candidate.secret_value
            if (
                isinstance(secret_val, str)
                and len(secret_val) >= 12
                and secret_val != REDACTED_PLACEHOLDER
            ):
                found.append(secret_val)
    return sorted(set(found), key=len, reverse=True)


def _decode_stream_text(raw: str | bytes | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return raw


class SecretVault(StdlibSecretScrubber):
    """Control-plane redactor combining StdlibSecretScrubber and detect-secrets."""

    def __init__(
        self,
        exact_secrets: Iterable[str] = (),
        *,
        min_exact_len: int = 6,
        enable_detect_secrets: bool = True,
    ) -> None:
        super().__init__(exact_secrets, min_exact_len=min_exact_len)
        self._enable_detect_secrets = enable_detect_secrets

    @property
    def redacted_count(self) -> NonNegInt:
        return super().redacted_count

    def register_exact_secrets(self, secrets: tuple[str, ...]) -> None:
        for secret in secrets:
            self.register_secret(secret)

    def scrub_text(self, text: str) -> str:
        out = super().scrub_text(text)
        if not out or not self._enable_detect_secrets:
            return out
        for line in out.splitlines():
            for candidate in _detect_secrets_values(line):
                if candidate in out:
                    self._bump_count(out.count(candidate))
                    out = out.replace(candidate, REDACTED_PLACEHOLDER)
        return out

    def scrub(self, raw: str) -> RedactedStr:
        """Scrub raw text and mint a sealed RedactedStr."""
        return _mint_redacted_str(self.scrub_text(raw))

    def scrub_json(self, raw: JsonValue) -> RedactedJsonValue:
        """Recursively scrub a closed immutable JsonValue into a RedactedJsonValue."""
        if raw is None or isinstance(raw, (bool, int, float)):
            return raw
        if isinstance(raw, str):
            return self.scrub(raw)
        if isinstance(raw, tuple):
            return tuple(self.scrub_json(item) for item in raw)
        return self._scrub_persistent_map(raw)

    def _scrub_persistent_map(
        self, mapping: Mapping[str, JsonValue]
    ) -> HashTrieMap[str, RedactedJsonValue]:
        items: dict[str, RedactedJsonValue] = {}
        for key, value in mapping.items():
            clean_key = self.scrub_text(key)
            if is_sensitive_field_name(key):
                items[clean_key] = self._scrub_sensitive_json(value)
            else:
                items[clean_key] = self.scrub_json(value)
        return HashTrieMap(items)

    def _scrub_sensitive_json(self, value: JsonValue) -> RedactedJsonValue:
        if isinstance(value, str):
            if value and value != REDACTED_PLACEHOLDER:
                self._bump_count(1)
                return _mint_redacted_str(REDACTED_PLACEHOLDER)
            return _mint_redacted_str(value)
        if isinstance(value, tuple):
            return tuple(self._scrub_sensitive_json(item) for item in value)
        if isinstance(value, Mapping):
            return HashTrieMap(
                {self.scrub_text(k): self._scrub_sensitive_json(v) for k, v in value.items()}
            )
        return value

    def scrub_excerpt(
        self,
        *,
        stdout_text: str | bytes | None = None,
        stderr_text: str | bytes | None = None,
        max_chars: PositiveInt = 400,
    ) -> RedactedStr:
        """Produce a bounded, redacted diagnostic excerpt prioritizing stderr then stdout."""
        stderr_clean = _decode_stream_text(stderr_text).strip()
        stdout_clean = _decode_stream_text(stdout_text).strip()
        combined = stderr_clean if stderr_clean else stdout_clean
        if stderr_clean and stdout_clean:
            combined = f"stderr={stderr_clean} | stdout={stdout_clean}"
        scrubbed = self.scrub_text(combined)
        if len(scrubbed) > max_chars:
            scrubbed = scrubbed[: max_chars - 3] + "..." if max_chars >= 3 else scrubbed[:max_chars]
        return _mint_redacted_str(scrubbed)

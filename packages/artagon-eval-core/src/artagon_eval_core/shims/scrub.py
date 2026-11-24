"""Pure-stdlib exact-token and regex secret scrubber for ADR-0012 hot-path shims."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from functools import lru_cache
from typing import Final

REDACTED_PLACEHOLDER: Final[str] = "[REDACTED_SECRET]"

SECRET_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    ("anthropic_key", r"\bsk-ant-[A-Za-z0-9_-]{10,}\b"),
    ("openai_key", r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{16,}\b"),
    ("github_pat", r"\b(?:gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{16,})\b"),
    ("google_api_key", r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ("google_oauth_access", r"\bya29\.[A-Za-z0-9._-]{12,}\b"),
    ("google_oauth_refresh", r"(?<![A-Za-z0-9])1//[0-9A-Za-z_-]{16,}\b"),
    ("auth_header", r"(?i)(\b(?:Bearer|Basic)\s+)[A-Za-z0-9._~+/=-]{10,}"),
)

_SAFE_METADATA_KEYS: Final[frozenset[str]] = frozenset(
    {
        "secret_file_consumed",
        "secret_api_key_path",
        "secret_env_path",
        "api_key_env_name",
        "api_key_ref",
        "scrubbed_env_keys",
    }
)

_SENSITIVE_FAST_SUBSTRINGS: Final[tuple[str, ...]] = (
    "key",
    "token",
    "secret",
    "password",
    "cookie",
    "auth",
)


@lru_cache(maxsize=1)
def _compiled_patterns() -> tuple[re.Pattern[str], re.Pattern[str]]:
    direct_union = "|".join(f"(?:{pat})" for name, pat in SECRET_PATTERNS if name != "auth_header")
    direct_re = re.compile(direct_union)
    auth_re = re.compile(r"(?i)(\b(?:Bearer|Basic)\s+)[A-Za-z0-9._~+/=-]{10,}")
    return direct_re, auth_re


@lru_cache(maxsize=1)
def _sensitive_field_re() -> re.Pattern[str]:
    return re.compile(
        r"(?i:(?:^|_|-)(?:api_?key|auth_?token|api_?token|access_?token|refresh_?token|"
        r"oauth_?token|bearer_?token|session_?token|id_?token|client_?secret|private_?key|"
        r"password|secret|cookie|authorization)(?:$|_|-))"
        r"|(?:[a-z0-9](?:ApiKey|ClientSecret|PrivateKey|Password|Secret|Cookie)$)"
        r"|(?:(?<!first)(?<!input)(?<!output)(?<!prompt)(?<!completion)(?<!total)(?<!max)[a-z0-9]Token$)"
    )


def is_sensitive_field_name(key_str: str) -> bool:
    """Return True when a field or env name denotes a secret credential value."""
    if key_str in _SAFE_METADATA_KEYS:
        return False
    low = key_str.lower()
    if not any(sub in low for sub in _SENSITIVE_FAST_SUBSTRINGS):
        return False
    return bool(_sensitive_field_re().search(key_str))


def _clean_exact_secrets(exact_secrets: Iterable[str], min_len: int) -> list[str]:
    cleaned = {s.strip() for s in exact_secrets if len(s.strip()) >= min_len}
    return sorted(cleaned, key=len, reverse=True)


class StdlibSecretScrubber:
    """Pure-stdlib pre-write redactor scrubbing exact credentials and known token regexes."""

    def __init__(self, exact_secrets: Iterable[str] = (), *, min_exact_len: int = 6) -> None:
        self._min_exact_len = min_exact_len
        self._exact_secrets: list[str] = _clean_exact_secrets(exact_secrets, min_exact_len)
        self._redacted_count: int = 0

    @property
    def redacted_count(self) -> int:
        return self._redacted_count

    @property
    def exact_secrets(self) -> tuple[str, ...]:
        return tuple(self._exact_secrets)

    def _bump_count(self, delta: int) -> None:
        self._redacted_count += delta

    def register_secret(self, secret: str, *, min_len: int | None = None) -> None:
        threshold = self._min_exact_len if min_len is None else min_len
        val = secret.strip()
        if len(val) >= threshold and val not in self._exact_secrets:
            self._exact_secrets.append(val)
            self._exact_secrets.sort(key=len, reverse=True)

    def scrub_text(self, text: str) -> str:
        if not text:
            return text
        out = self._scrub_exact(text)
        return self._scrub_patterns(out)

    def _replace_outside_placeholders(self, text: str, secret: str) -> str:
        parts = text.split(REDACTED_PLACEHOLDER)
        hits = sum(part.count(secret) for part in parts)
        if hits == 0:
            return text
        self._bump_count(hits)
        return REDACTED_PLACEHOLDER.join(
            part.replace(secret, REDACTED_PLACEHOLDER) for part in parts
        )

    def _scrub_exact(self, text: str) -> str:
        out = text
        for secret in self._exact_secrets:
            if secret == REDACTED_PLACEHOLDER or secret not in out:
                continue
            if REDACTED_PLACEHOLDER in secret:
                self._bump_count(out.count(secret))
                out = out.replace(secret, REDACTED_PLACEHOLDER)
            else:
                out = self._replace_outside_placeholders(out, secret)
        return out

    def _scrub_patterns(self, text: str) -> str:
        direct_re, auth_re = _compiled_patterns()
        out, n_direct = direct_re.subn(REDACTED_PLACEHOLDER, text)
        self._bump_count(n_direct)
        out, n_auth = auth_re.subn(rf"\1{REDACTED_PLACEHOLDER}", out)
        self._bump_count(n_auth)
        return out

    def scrub_mapping_strings(self, mapping: Mapping[str, str]) -> dict[str, str]:
        """Scrub a flat string mapping, forcing full redaction on sensitive keys."""
        out: dict[str, str] = {}
        for key, val in mapping.items():
            clean_key = self.scrub_text(key)
            if is_sensitive_field_name(key):
                if val and val != REDACTED_PLACEHOLDER:
                    self._bump_count(1)
                    out[clean_key] = REDACTED_PLACEHOLDER
                else:
                    out[clean_key] = val
            else:
                out[clean_key] = self.scrub_text(val)
        return out

"""Reusable strictly typed Hypothesis strategies for artagon-eval-core and adapter contracts."""

from __future__ import annotations

import string
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Final

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy
from rpds import HashTrieMap, HashTrieSet

from artagon_eval_core.domain.errors import (
    AdapterUnavailableError,
    BillingGuardError,
    CliUsageError,
    CredentialUnavailableError,
    EvalError,
    GateRejectedError,
    IsolationTamperError,
    MultiplexerError,
    MutationScope,
    QuotaCensoredError,
    SchemaUsageError,
    SplitDataError,
    VerifierCassetteError,
)
from artagon_eval_core.domain.primitives import (
    SPLIT_ALIASES,
    CampaignId,
    RedactedJsonValue,
    RedactedStr,
    TaskSplit,
    parse_campaign_id,
)
from artagon_eval_core.domain.types import JsonScalar, JsonValue
from artagon_eval_core.runtime.redact import SecretVault

_ASCII_LOWER_DIGITS: Final[str] = string.ascii_lowercase + string.digits
_HEX_LOWER: Final[str] = "0123456789abcdef"
_HEX_UPPER: Final[str] = "ABCDEF"
_SAFE_ID_HEAD: Final[str] = string.ascii_letters + string.digits
_SAFE_ID_TAIL: Final[str] = string.ascii_letters + string.digits + "._-"
_PATH_SEG_CHARS: Final[str] = string.ascii_letters + string.digits + "._-"
_TOKEN_CHARS: Final[str] = string.ascii_letters + string.digits + "_-"
_YAML_TEXT_CHARS: Final[str] = string.ascii_letters + string.digits + " .,/_-+()!@#$%&*=[]{}<>?;"
_TOOL_NAME_CHARS: Final[str] = string.ascii_letters + string.digits + "_-:"
_META_KEY_TAIL: Final[str] = string.ascii_lowercase + string.digits + "_-"
_MUTATION_SCOPES: Final[tuple[MutationScope, ...]] = (
    "none",
    "frozen_manifest",
    "campaign_artifacts",
    "candidate_bundle",
    "promotion_patch",
    "state_ledger",
)


def _with_random_case(draw: st.DrawFn, base: str) -> str:
    chars: list[str] = []
    for ch in base:
        if ch.isalpha() and draw(st.booleans()):
            chars.append(ch.upper())
        else:
            chars.append(ch.lower())
    return "".join(chars)


def _pad_whitespace(draw: st.DrawFn, value: str) -> str:
    ws_alphabet = " \t\n\r"
    lead = draw(st.text(alphabet=ws_alphabet, max_size=4))
    trail = draw(st.text(alphabet=ws_alphabet, max_size=4))
    return f"{lead}{value}{trail}"


def non_empty_strs(max_size: int = 32) -> SearchStrategy[str]:
    """Generate strings guaranteed to satisfy NonEmptyStr (non-empty after strip)."""
    core = st.text(
        alphabet=string.ascii_letters + string.digits + " _-./:",
        min_size=1,
        max_size=max_size,
    ).filter(lambda s: bool(s.strip()))
    return core.map(str.strip)


def _concat2(head: str, tail: str) -> str:
    return f"{head}{tail}"


def _abs_path(seg_a: str, seg_b: str) -> str:
    return f"/{seg_a}/{seg_b}"


def _dotdot_mid(seg_a: str, seg_b: str) -> str:
    return f"{seg_a}/../{seg_b}"


def _dot_mid(seg_a: str, seg_b: str) -> str:
    return f"{seg_a}/./{seg_b}"


def _double_slash(seg_a: str, seg_b: str) -> str:
    return f"{seg_a}//{seg_b}"


def _backslash_path(seg_a: str, seg_b: str) -> str:
    return f"{seg_a}\\{seg_b}"


def _trailing_slash(seg_a: str, seg_b: str) -> str:
    return f"{seg_a}/{seg_b}/"


def _win_drive_path(drive: str, seg_a: str) -> str:
    return f"{drive}:{seg_a}"


def _ctrl_path(seg_a: str, ch: str, seg_b: str) -> str:
    return f"{seg_a}{ch}{seg_b}"


def safe_ids(max_size: int = 32) -> SearchStrategy[str]:
    """Generate strings guaranteed to satisfy SafeId."""
    head = st.sampled_from(_SAFE_ID_HEAD)
    tail = st.text(alphabet=_SAFE_ID_TAIL, min_size=0, max_size=max(0, max_size - 1))
    return st.builds(_concat2, head, tail)


def campaign_ids(max_size: int = 32) -> SearchStrategy[CampaignId]:
    """Generate validated nominal CampaignId values."""
    return safe_ids(max_size=max_size).map(parse_campaign_id)


@st.composite
def valid_skill_ids(draw: st.DrawFn) -> str:
    """Generate valid 1..64 char lowercase kebab-case SkillId values."""
    seg_count = draw(st.integers(min_value=1, max_value=5))
    segments: list[str] = []
    remaining = 64
    for idx in range(seg_count):
        slots_left = seg_count - idx - 1
        max_seg = min(16, remaining - 2 * slots_left)
        seg = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=1, max_size=max(1, max_seg)))
        segments.append(seg)
        remaining -= len(seg) + 1
    return "-".join(segments)


@st.composite
def invalid_skill_ids(draw: st.DrawFn) -> str:
    """Generate strings guaranteed to violate SkillId invariants."""
    kind = draw(
        st.sampled_from(
            (
                "empty",
                "uppercase",
                "underscore",
                "double_hyphen",
                "leading_hyphen",
                "trailing_hyphen",
                "too_long",
                "bad_char",
            )
        )
    )
    if kind == "empty":
        return ""
    if kind == "uppercase":
        prefix = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, max_size=8))
        upper = draw(st.sampled_from(string.ascii_uppercase))
        suffix = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, max_size=8))
        return f"{prefix}{upper}{suffix}"
    if kind == "underscore":
        left = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=1, max_size=8))
        right = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=1, max_size=8))
        return f"{left}_{right}"
    if kind == "double_hyphen":
        left = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=1, max_size=8))
        right = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=1, max_size=8))
        return f"{left}--{right}"
    if kind == "leading_hyphen":
        rest = draw(valid_skill_ids())
        return f"-{rest[:63]}"
    if kind == "trailing_hyphen":
        rest = draw(valid_skill_ids())
        return f"{rest[:63]}-"
    if kind == "too_long":
        extra = draw(st.integers(min_value=65, max_value=96))
        return draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=extra, max_size=extra))
    bad = draw(st.sampled_from(" /\\:@.!$"))
    left = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=1, max_size=6))
    right = draw(st.text(alphabet=_ASCII_LOWER_DIGITS, min_size=1, max_size=6))
    return f"{left}{bad}{right}"


def valid_sha256_hex() -> SearchStrategy[str]:
    """Generate exact 64-character lowercase hex SHA-256 digests."""
    return st.text(alphabet=_HEX_LOWER, min_size=64, max_size=64)


@st.composite
def invalid_sha256_hex(draw: st.DrawFn) -> str:
    """Generate strings guaranteed to fail Sha256Hex validation."""
    kind = draw(st.sampled_from(("short", "long", "uppercase", "non_hex")))
    if kind == "short":
        return draw(st.text(alphabet=_HEX_LOWER, min_size=0, max_size=63))
    if kind == "long":
        return draw(st.text(alphabet=_HEX_LOWER, min_size=65, max_size=96))
    base = list(draw(valid_sha256_hex()))
    idx = draw(st.integers(min_value=0, max_value=63))
    if kind == "uppercase":
        base[idx] = draw(st.sampled_from(_HEX_UPPER))
    else:
        base[idx] = draw(st.sampled_from("ghijklmnopqrstuvwxyz_- /!\n"))
    return "".join(base)


def _valid_posix_segment() -> SearchStrategy[str]:
    return st.text(alphabet=_PATH_SEG_CHARS, min_size=1, max_size=16).filter(
        lambda seg: seg not in {".", ".."}
    )


def valid_relative_repo_paths() -> SearchStrategy[str]:
    """Generate normalized POSIX relative paths guaranteed to pass RelativeRepoPath."""
    return st.lists(_valid_posix_segment(), min_size=1, max_size=5).map("/".join)


def invalid_relative_repo_paths() -> SearchStrategy[str]:
    """Generate adversarial paths guaranteed to fail RelativeRepoPath validation."""
    seg = _valid_posix_segment()
    ctrl_char = st.one_of(st.integers(min_value=0, max_value=31), st.just(127)).map(chr)
    return st.one_of(
        st.just(""),
        st.just("."),
        st.just(".."),
        st.builds(_abs_path, seg, seg),
        seg.map(lambda a: f"../{a}"),
        st.builds(_dotdot_mid, seg, seg),
        seg.map(lambda a: f"{a}/.."),
        st.builds(_dot_mid, seg, seg),
        st.builds(_double_slash, seg, seg),
        st.builds(_backslash_path, seg, seg),
        st.builds(_trailing_slash, seg, seg),
        st.builds(_win_drive_path, st.sampled_from(string.ascii_letters), seg),
        st.builds(_ctrl_path, seg, ctrl_char, seg),
    )


@st.composite
def sentinel_model_ids(draw: st.DrawFn) -> str:
    """Generate ModelId sentinel strings with arbitrary casing and whitespace."""
    base = draw(st.sampled_from(("", "default", "auto")))
    cased = _with_random_case(draw, base)
    return _pad_whitespace(draw, cased)


@st.composite
def valid_model_ids(draw: st.DrawFn) -> str:
    """Generate concrete non-sentinel ModelId inputs with optional outer whitespace."""
    core = draw(
        st.text(
            alphabet=string.ascii_letters + string.digits + "-._:/",
            min_size=1,
            max_size=40,
        ).filter(lambda s: s.strip().lower() not in {"", "default", "auto"})
    )
    return _pad_whitespace(draw, core)


@st.composite
def task_split_alias_inputs(draw: st.DrawFn) -> tuple[str, TaskSplit]:
    """Generate (raw_alias_input, expected_canonical_split) for all 6 split aliases."""
    alias = draw(st.sampled_from(sorted(SPLIT_ALIASES.keys())))
    expected = SPLIT_ALIASES[alias]
    cased = _with_random_case(draw, alias)
    return (_pad_whitespace(draw, cased), expected)


def invalid_task_split_strings() -> SearchStrategy[str]:
    """Generate strings that are never valid task split aliases."""
    return st.text(min_size=0, max_size=24).filter(lambda s: s.strip().lower() not in SPLIT_ALIASES)


def persistent_maps[K: Hashable, V](
    keys: SearchStrategy[K],
    values: SearchStrategy[V],
    *,
    min_size: int = 0,
    max_size: int = 6,
) -> SearchStrategy[HashTrieMap[K, V]]:
    """Generate immutable rpds.HashTrieMap[K, V] instances."""
    return st.dictionaries(keys, values, min_size=min_size, max_size=max_size).map(HashTrieMap)


def persistent_sets[T: Hashable](
    elements: SearchStrategy[T],
    *,
    min_size: int = 0,
    max_size: int = 8,
) -> SearchStrategy[HashTrieSet[T]]:
    """Generate immutable rpds.HashTrieSet[T] instances."""
    return st.frozensets(elements, min_size=min_size, max_size=max_size).map(HashTrieSet)


def json_scalars() -> SearchStrategy[JsonScalar]:
    """Generate finite JSON scalar primitives."""
    return st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1_000_000, max_value=1_000_000),
        st.floats(
            min_value=-1e6,
            max_value=1e6,
            allow_nan=False,
            allow_infinity=False,
        ),
        st.text(max_size=24),
    )


def json_values(max_leaves: int = 12) -> SearchStrategy[JsonValue]:
    """Generate recursive closed immutable JsonValue structures."""
    key_st = st.text(alphabet=string.ascii_letters + string.digits + "_-", min_size=1, max_size=12)

    def _extend(children: SearchStrategy[JsonValue]) -> SearchStrategy[JsonValue]:
        return st.one_of(
            st.lists(children, max_size=4).map(tuple),
            persistent_maps(key_st, children, max_size=4),
        )

    return st.recursive(json_scalars(), _extend, max_leaves=max_leaves)


@st.composite
def high_entropy_secrets(draw: st.DrawFn) -> str:
    """Generate realistic high-entropy secret tokens suitable for SecretVault registration."""
    kind = draw(
        st.sampled_from(
            (
                "anthropic",
                "openai",
                "github_pat",
                "google_api",
                "jwt",
                "bearer_body",
                "opaque_token",
            )
        )
    )
    alnum = string.ascii_letters + string.digits
    if kind == "anthropic":
        tail = draw(st.text(alphabet=_TOKEN_CHARS, min_size=14, max_size=28))
        return f"sk-ant-{tail}{draw(st.sampled_from(alnum))}"
    if kind == "openai":
        prefix = draw(st.sampled_from(("sk-", "sk-proj-", "sk-svcacct-")))
        tail = draw(st.text(alphabet=_TOKEN_CHARS, min_size=18, max_size=30))
        return f"{prefix}{tail}{draw(st.sampled_from(alnum))}"
    if kind == "github_pat":
        prefix = draw(st.sampled_from(("ghp_", "gho_", "ghu_", "ghs_", "github_pat_")))
        tail = draw(st.text(alphabet=alnum, min_size=18, max_size=32))
        return f"{prefix}{tail}"
    if kind == "google_api":
        tail = draw(st.text(alphabet=alnum, min_size=22, max_size=32))
        return f"AIza{tail}"
    if kind == "jwt":
        p1 = draw(st.text(alphabet=alnum, min_size=10, max_size=18))
        p2 = draw(st.text(alphabet=alnum, min_size=10, max_size=18))
        p3 = draw(st.text(alphabet=alnum, min_size=10, max_size=18))
        return f"eyJ{p1}.eyJ{p2}.{p3}"
    if kind == "bearer_body":
        token = draw(st.text(alphabet=alnum + "._~+/=-", min_size=14, max_size=28))
        return f"Bearer {token}"
    # Opaque secret distinct from REDACTED_PLACEHOLDER
    head = draw(st.text(alphabet=alnum, min_size=10, max_size=24))
    suffix = draw(st.text(alphabet=string.digits, min_size=4, max_size=8))
    return f"sec_{head}_{suffix}"


def redacted_strs(max_size: int = 40) -> SearchStrategy[RedactedStr]:
    """Generate capability-sealed RedactedStr instances via SecretVault.scrub()."""
    return st.text(max_size=max_size).map(
        lambda raw: SecretVault(enable_detect_secrets=False).scrub(raw)
    )


def redacted_json_values(max_leaves: int = 10) -> SearchStrategy[RedactedJsonValue]:
    """Generate scrubbed immutable RedactedJsonValue trees via SecretVault.scrub_json()."""
    return json_values(max_leaves=max_leaves).map(
        lambda val: SecretVault(enable_detect_secrets=False).scrub_json(val)
    )


def mutation_scopes() -> SearchStrategy[MutationScope]:
    """Generate all valid Envelope MutationScope literals."""
    return st.sampled_from(_MUTATION_SCOPES)


_SIMPLE_ERROR_CLASSES: Final[
    tuple[
        type[GateRejectedError]
        | type[SchemaUsageError]
        | type[CredentialUnavailableError]
        | type[IsolationTamperError]
        | type[VerifierCassetteError]
        | type[QuotaCensoredError]
        | type[MultiplexerError]
        | type[CliUsageError]
        | type[SplitDataError],
        ...,
    ]
] = (
    GateRejectedError,
    SchemaUsageError,
    CredentialUnavailableError,
    IsolationTamperError,
    VerifierCassetteError,
    QuotaCensoredError,
    MultiplexerError,
    CliUsageError,
    SplitDataError,
)


def redacted_details_maps(max_size: int = 3) -> SearchStrategy[HashTrieMap[str, RedactedJsonValue]]:
    """Generate vault-scrubbed details maps guaranteed idempotent under SecretVault."""
    key_st = st.text(alphabet=string.ascii_lowercase + "_", min_size=1, max_size=10)
    raw_maps = persistent_maps(key_st, json_values(max_leaves=6), max_size=max_size)

    def _scrub_map(raw_map: HashTrieMap[str, JsonValue]) -> HashTrieMap[str, RedactedJsonValue]:
        scrubbed = SecretVault(enable_detect_secrets=False).scrub_json(raw_map)
        assert isinstance(scrubbed, HashTrieMap)
        return scrubbed

    return raw_maps.map(_scrub_map)


@st.composite
def eval_errors(draw: st.DrawFn) -> EvalError:
    """Generate instances across all 11 closed EvalError ADT variants."""
    variant = draw(st.integers(min_value=0, max_value=10))
    reason = draw(non_empty_strs(max_size=24))
    message = draw(redacted_strs(max_size=40))
    details = draw(redacted_details_maps(max_size=3))
    log_paths = tuple(draw(st.lists(valid_relative_repo_paths(), max_size=3)))

    if variant < len(_SIMPLE_ERROR_CLASSES):
        err_cls = _SIMPLE_ERROR_CLASSES[variant]
        return err_cls(
            reason_code=reason,
            message=message,
            details=details,
            log_paths=log_paths,
        )
    if variant == 9:
        offending = tuple(draw(st.lists(safe_ids(max_size=16), max_size=3)))
        return BillingGuardError(
            reason_code=reason,
            message=message,
            details=details,
            log_paths=log_paths,
            offending_vars=offending,
        )
    return AdapterUnavailableError(
        reason_code=reason,
        message=message,
        details=details,
        log_paths=log_paths,
        adapter_name=draw(non_empty_strs(max_size=16)),
        install_extra=draw(non_empty_strs(max_size=16)),
    )


@dataclass(frozen=True, slots=True)
class SkillDocInput:
    """Typed generator payload for rendering valid Tier-0 SKILL.md documents."""

    name: str
    description: str
    license_text: str | None
    compatibility: str | None
    allowed_tools: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...]
    body: str
    with_bom: bool


def _yaml_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def render_skill_md(doc: SkillDocInput) -> str:
    """Render a SkillDocInput into a valid agentskills.io SKILL.md string."""
    lines: list[str] = [
        "---",
        f"name: {_yaml_single_quote(doc.name)}",
        f"description: {_yaml_single_quote(doc.description)}",
    ]
    if doc.license_text is not None:
        lines.append(f"license: {_yaml_single_quote(doc.license_text)}")
    if doc.compatibility is not None:
        lines.append(f"compatibility: {_yaml_single_quote(doc.compatibility)}")
    if doc.allowed_tools:
        lines.append(f"allowed-tools: {_yaml_single_quote(' '.join(doc.allowed_tools))}")
    if doc.metadata:
        lines.append("metadata:")
        for key, val in doc.metadata:
            lines.append(f"  {key}: {_yaml_single_quote(val)}")
    lines.append("---")
    if doc.body:
        lines.append("")
        lines.append(doc.body)
    rendered = "\n".join(lines) + "\n"
    return f"\ufeff{rendered}" if doc.with_bom else rendered


def _yaml_safe_non_empty(max_size: int) -> SearchStrategy[str]:
    return (
        st.text(alphabet=_YAML_TEXT_CHARS, min_size=1, max_size=max_size)
        .map(str.strip)
        .filter(lambda s: 1 <= len(s) <= max_size)
    )


@st.composite
def valid_skill_doc_inputs(draw: st.DrawFn) -> SkillDocInput:
    """Generate valid SkillFrontmatter inputs covering all optional fields and BOM."""
    name = draw(valid_skill_ids())
    description = draw(_yaml_safe_non_empty(max_size=120))
    license_text = draw(st.one_of(st.none(), _yaml_safe_non_empty(max_size=32)))
    compatibility = draw(st.one_of(st.none(), _yaml_safe_non_empty(max_size=120)))
    tool_st = st.text(alphabet=_TOOL_NAME_CHARS, min_size=1, max_size=16)
    allowed_tools = tuple(draw(st.lists(tool_st, max_size=5)))
    meta_key_st = st.builds(
        _concat2,
        st.sampled_from(string.ascii_lowercase),
        st.text(alphabet=_META_KEY_TAIL, max_size=12),
    )
    meta_dict = draw(st.dictionaries(meta_key_st, _yaml_safe_non_empty(max_size=32), max_size=4))
    body = draw(
        st.text(alphabet=string.ascii_letters + string.digits + " #*-_\n", max_size=80).map(
            str.strip
        )
    )
    with_bom = draw(st.booleans())
    return SkillDocInput(
        name=name,
        description=description,
        license_text=license_text,
        compatibility=compatibility,
        allowed_tools=allowed_tools,
        metadata=tuple(sorted(meta_dict.items())),
        body=body,
        with_bom=with_bom,
    )

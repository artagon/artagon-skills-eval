"""Constrained domain value objects, nominal NewTypes, ConfinedScratchPath, and RedactedStr."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Final, Literal, NewType, Self, final

from expression import Error, Ok, Result
from pydantic import AfterValidator, Field, GetCoreSchemaHandler, StringConstraints
from pydantic_core import CoreSchema, core_schema

from artagon_eval_core.domain.types import PersistentMap

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

SAFE_ID_PATTERN: Final[str] = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
SafeId = Annotated[str, StringConstraints(pattern=SAFE_ID_PATTERN)]

SKILL_ID_PATTERN: Final[str] = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def _validate_skill_id(raw: str) -> str:
    norm = unicodedata.normalize("NFKC", raw)
    if not (1 <= len(norm) <= 64) or not re.fullmatch(SKILL_ID_PATTERN, norm):
        msg = f"Invalid SkillId {raw!r}: expected 1..64 lowercase kebab-case chars"
        raise ValueError(msg)
    return norm


SkillId = Annotated[str, AfterValidator(_validate_skill_id)]

SHA256_PATTERN: Final[str] = r"^[0-9a-f]{64}$"
Sha256Hex = Annotated[str, StringConstraints(pattern=SHA256_PATTERN)]

_REL_PATH_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?!/)(?!.*(?:^|/)\.\.?(?:/|$))(?!.*//)(?!.*\\)(?!.*/$).+$"
)
_WIN_DRIVE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:")


def _validate_relative_repo_path(raw: str) -> str:
    if not raw or any(ord(ch) < 32 or ord(ch) == 127 for ch in raw):
        msg = f"RelativeRepoPath forbids empty string or control chars: {raw!r}"
        raise ValueError(msg)
    if _WIN_DRIVE_RE.match(raw) or not _REL_PATH_RE.fullmatch(raw):
        msg = f"Invalid RelativeRepoPath (normalized POSIX relative path required): {raw!r}"
        raise ValueError(msg)
    return raw


RelativeRepoPath = Annotated[str, AfterValidator(_validate_relative_repo_path)]

MODEL_SENTINELS: Final[frozenset[str]] = frozenset({"", "default", "auto"})


def _validate_non_sentinel_model(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.lower() in MODEL_SENTINELS:
        msg = f"Sentinel token {raw!r} is not a concrete ModelId; use Nothing"
        raise ValueError(msg)
    return cleaned


ModelId = Annotated[str, AfterValidator(_validate_non_sentinel_model)]
ModelAlias = Annotated[str, AfterValidator(_validate_non_sentinel_model)]

PositiveInt = Annotated[int, Field(gt=0)]
NonNegInt = Annotated[int, Field(ge=0)]
WallSeconds = Annotated[int, Field(ge=1, le=86_400)]
PositiveFloat = Annotated[float, Field(gt=0.0, allow_inf_nan=False)]
NonNegFloat = Annotated[float, Field(ge=0.0, allow_inf_nan=False)]
UnitFloat = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
SeedUint64 = Annotated[int, Field(ge=0, le=18_446_744_073_709_551_615)]

HarnessName = Literal["claude", "codex", "agy", "copilot"]
CatalogHarnessName = Literal["claude", "codex", "agy", "copilot", "grok"]
EffortLevel = Literal["low", "medium", "high", "xhigh", "max", "ultra"]
TaskSplit = Literal["train", "val", "test"]
EvalSurface = Literal["general", "skill_eval"]
PinMode = Literal["nix", "host"]
ExecutionMode = Literal["headless", "ntm", "herdr", "cao"]
BillingGuardMode = Literal["separated", "env_only", "api_key_explicit"]
ContractVersion = Literal["artagon/skill-evals/v1", "artagon/skill-evals/v2"]
VendorFamily = Literal[
    "anthropic",
    "openai",
    "google",
    "github_copilot",
    "moonshot",
    "xai",
    "microsoft",
    "deepseek",
    "alibaba",
    "zhipu",
    "mistral",
    "meta",
]

SPLIT_ALIASES: Final[Mapping[str, TaskSplit]] = MappingProxyType(
    {
        "train": "train",
        "development": "train",
        "val": "val",
        "selection": "val",
        "test": "test",
        "holdout": "test",
    }
)


def parse_task_split(raw: object) -> Result[TaskSplit, tuple[str, str]]:
    """Single canonical split normalizer returning Ok(TaskSplit) or Error((code, detail))."""
    if not isinstance(raw, str) or not raw.strip():
        return Error(("invalid_task_split", "Missing or non-string task split"))
    norm = SPLIT_ALIASES.get(raw.strip().lower())
    if norm is None:
        return Error(
            (
                "invalid_task_split",
                "Unknown task split; expected train|development|val|selection|test|holdout",
            )
        )
    return Ok(norm)


CampaignId = NewType("CampaignId", str)
TrialId = NewType("TrialId", str)
ArmId = NewType("ArmId", str)
TaskId = NewType("TaskId", str)
BlockId = NewType("BlockId", str)
TaskFamilyId = NewType("TaskFamilyId", str)
HmacKeyId = NewType("HmacKeyId", str)


def parse_safe_newtype[N: str](constructor: Callable[[str], N], raw: str) -> N:
    """Validated constructor for SafeId-backed nominal NewTypes."""
    if not re.fullmatch(SAFE_ID_PATTERN, raw):
        msg = f"Invalid SafeId value: {raw!r}"
        raise ValueError(msg)
    return constructor(raw)


def _validate_safe_id_str(raw: str) -> str:
    if not re.fullmatch(SAFE_ID_PATTERN, raw):
        msg = f"Invalid SafeId value: {raw!r}"
        raise ValueError(msg)
    return raw


def parse_campaign_id(raw: str) -> CampaignId:
    return CampaignId(_validate_safe_id_str(raw))


def parse_trial_id(raw: str) -> TrialId:
    return TrialId(_validate_safe_id_str(raw))


def parse_arm_id(raw: str) -> ArmId:
    return ArmId(_validate_safe_id_str(raw))


def parse_task_id(raw: str) -> TaskId:
    return TaskId(_validate_safe_id_str(raw))


def parse_block_id(raw: str) -> BlockId:
    return BlockId(_validate_safe_id_str(raw))


def parse_task_family_id(raw: str) -> TaskFamilyId:
    return TaskFamilyId(_validate_safe_id_str(raw))


def parse_hmac_key_id(raw: str) -> HmacKeyId:
    return HmacKeyId(_validate_safe_id_str(raw))


def _serialize_confined_path(value: ConfinedScratchPath) -> str:
    return str(value.path)


@final
class ConfinedScratchPath:
    """Opaque path proven confined to <repo_root>/scratch/skill-eval/<SafeId>."""

    __slots__ = ("_path", "_run_id")
    _MINT_TOKEN: Final[object] = object()

    def __init__(self, path: Path, run_id: CampaignId, *, _token: object) -> None:
        if _token is not self._MINT_TOKEN:
            msg = "Construct ConfinedScratchPath only via ConfinedScratchPath.from_validated()"
            raise TypeError(msg)
        self._path = path
        self._run_id = run_id

    @property
    def path(self) -> Path:
        return self._path

    @property
    def run_id(self) -> CampaignId:
        return self._run_id

    def child_rel(self, rel: RelativeRepoPath) -> Path:
        """Join a validated RelativeRepoPath strictly inside this confined scratch root."""
        return self._path / rel

    @classmethod
    def from_validated(cls, repo_real: Path, candidate_norm: Path, run_id: CampaignId) -> Self:
        """Pure structural verification called by FilesystemPort.confine_scratch_dir()."""
        allowed_parent = repo_real / "scratch" / "skill-eval"
        plugins_root = repo_real / "plugins"
        if candidate_norm == plugins_root or plugins_root in candidate_norm.parents:
            msg = f"out_dir_inside_plugins: {candidate_norm}"
            raise ValueError(msg)
        if candidate_norm.parent != allowed_parent or candidate_norm.name != str(run_id):
            msg = f"run_dir_outside_scratch: {candidate_norm}"
            raise ValueError(msg)
        return cls(candidate_norm, run_id, _token=cls._MINT_TOKEN)

    def __str__(self) -> str:
        return str(self._path)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ConfinedScratchPath) and self._path == other._path

    def __hash__(self) -> int:
        return hash(self._path)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: object,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.is_instance_schema(
            cls,
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_confined_path,
                return_schema=core_schema.str_schema(),
            ),
        )


_REDACTION_MINT_CAP: Final[object] = object()


@final
class RedactedStr(str):
    """Secret-scrubbed string minted exclusively by SecretScrubberPort or static literals."""

    __slots__ = ()

    def __new__(cls, value: str, *, _cap: object) -> Self:
        if _cap is not _REDACTION_MINT_CAP:
            msg = "RedactedStr cannot be constructed directly; call SecretScrubberPort.scrub()"
            raise TypeError(msg)
        return super().__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: object,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.is_instance_schema(
            cls,
            serialization=core_schema.str_schema(),
        )


def _mint_redacted_str(scrubbed_text: str) -> RedactedStr:
    """Package-internal minting primitive reserved for runtime.redact and test fakes."""
    return RedactedStr(scrubbed_text, _cap=_REDACTION_MINT_CAP)


def static_redacted_literal(literal_message: str) -> RedactedStr:
    """Mint a RedactedStr strictly for static compile-time constant messages.

    Enforced by ast-grep rule `static-redacted-literal-const-only`: argument must be a literal.
    """
    return RedactedStr(literal_message, _cap=_REDACTION_MINT_CAP)


type RedactedJsonScalar = RedactedStr | int | float | bool | None
type RedactedJsonValue = (
    RedactedJsonScalar | tuple[RedactedJsonValue, ...] | PersistentMap[str, RedactedJsonValue]
)

"""Seven typed Effect Protocol ports isolating pure domain logic from I/O boundaries."""

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

from expression import NOTHING

from artagon_eval_core.domain.errors import EvalResult
from artagon_eval_core.domain.fp import NullableOption
from artagon_eval_core.domain.primitives import (
    ArmId,
    CampaignId,
    ConfinedScratchPath,
    HarnessName,
    HmacKeyId,
    NonEmptyStr,
    NonNegFloat,
    NonNegInt,
    PositiveFloat,
    PositiveInt,
    RedactedJsonValue,
    RedactedStr,
    RelativeRepoPath,
    Sha256Hex,
    SkillId,
    TaskId,
    TaskSplit,
    TrialId,
)
from artagon_eval_core.domain.types import FrozenModel, JsonValue, PersistentMap


class SubprocessRequest(FrozenModel):
    argv: tuple[str, ...]
    cwd: Path
    env: PersistentMap[str, str]
    timeout_seconds: PositiveFloat
    stdin_text: NullableOption[str] = NOTHING
    new_process_group: bool = True


class SubprocessResult(FrozenModel):
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: NonNegFloat


class KeyringProjectionSpec(FrozenModel):
    auth_mode: Literal["subscription", "api_key"]
    harness: HarnessName
    require_dbus_proxy: bool
    api_key_ref: NullableOption[NonEmptyStr] = NOTHING


class KeyringProjectionLease(FrozenModel):
    projected_env: PersistentMap[str, str]
    dbus_proxy_pid: NullableOption[PositiveInt] = NOTHING


class ProvenanceTag(FrozenModel):
    task_id: TaskId
    split: TaskSplit
    payload_sha256: Sha256Hex
    hmac_tag: Sha256Hex
    header_line: NonEmptyStr


class HoldoutLedgerUpdate(FrozenModel):
    skill_id: SkillId
    test_digest: Sha256Hex
    new_eval_count: PositiveInt
    ledger_reset_by_operator: bool


class TrialTraceSummary(FrozenModel):
    """Frozen pre-redacted summary of a single 4-layer trial trace."""

    schema_version: Literal["harness-eval-trace/v1"] = "harness-eval-trace/v1"
    trial_id: TrialId
    campaign_id: CampaignId
    arm_id: ArmId
    task_id: TaskId
    harness: HarnessName
    status: Literal[
        "completed",
        "failed",
        "timeout",
        "quota_censored",
        "billing_violation",
        "isolation_failed",
        "cassette_miss_failed",
        "multiplexer_failed",
    ]
    final_output_text: NullableOption[RedactedStr] = NOTHING
    redaction_applied: Literal[True] = True
    duration_ms: NonNegFloat = 0.0


class CompactionReceipt(FrozenModel):
    tables_dir: Path
    row_counts: PersistentMap[str, NonNegInt]
    parquet_written: bool
    duckdb_written: bool
    sqlite_fallback_written: bool


class SqlQueryResult(FrozenModel):
    backend: Literal["duckdb", "sqlite_fallback"]
    columns: tuple[str, ...]
    rows: tuple[tuple[RedactedJsonValue, ...], ...]


class SecretScrubberPort(Protocol):
    """Sole authority permitted to mint RedactedStr and RedactedJsonValue."""

    @property
    def redacted_count(self) -> NonNegInt: ...

    def register_exact_secrets(self, secrets: tuple[str, ...]) -> None: ...

    def scrub(self, raw: str) -> RedactedStr: ...

    def scrub_json(self, raw: JsonValue) -> RedactedJsonValue: ...

    def scrub_excerpt(
        self,
        *,
        stdout_text: str | bytes | None = None,
        stderr_text: str | bytes | None = None,
        max_chars: PositiveInt = 400,
    ) -> RedactedStr: ...


class SubprocessPort(Protocol):
    """Bounded process-group subprocess execution."""

    def run(self, request: SubprocessRequest) -> EvalResult[SubprocessResult]: ...

    def which(
        self, executable: NonEmptyStr, *, path_env: str | None = None
    ) -> EvalResult[Path]: ...

    def terminate_active_groups(self) -> NonNegInt: ...


class FilesystemPort(Protocol):
    """Confined, symlink-hostile POSIX filesystem operations (O_NOFOLLOW, 0700/0600, atomic replace)."""

    def resolve_contained(
        self,
        root: Path,
        rel_path: RelativeRepoPath,
    ) -> EvalResult[Path]: ...

    def confine_scratch_dir(
        self,
        repo_root: Path,
        run_dir_arg: str | Path,
        *,
        create: bool = True,
    ) -> EvalResult[ConfinedScratchPath]: ...

    def read_regular_utf8(
        self, path: Path, *, max_bytes: PositiveInt = 1_048_576
    ) -> EvalResult[str]: ...

    def read_regular_bytes(
        self, path: Path, *, max_bytes: PositiveInt = 16_777_216
    ) -> EvalResult[bytes]: ...

    def atomic_write_0600(self, path: Path, data: bytes) -> EvalResult[None]: ...

    def create_private_dir_0700(self, path: Path) -> EvalResult[Path]: ...

    def remove_confined_tree(self, target: Path, *, boundary: Path) -> EvalResult[None]: ...

    def sha256_regular_file(self, path: Path) -> EvalResult[Sha256Hex]: ...

    def exclusive_lock(self, lock_path: Path) -> AbstractContextManager[EvalResult[None]]: ...


class KeyringPort(Protocol):
    """OS keychain / Secret Service credential resolution and ephemeral trial projection."""

    def check_subscription_store_separation(
        self,
        harness: HarnessName,
    ) -> EvalResult[Literal["separated", "env_only"]]: ...

    def resolve_api_key(self, api_key_ref: NonEmptyStr) -> EvalResult[str]: ...

    def project_trial_keyring(
        self,
        spec: KeyringProjectionSpec,
    ) -> AbstractContextManager[EvalResult[KeyringProjectionLease]]: ...


class HmacCustodyPort(Protocol):
    """Tamper-evident 0600 XDG HMAC keys, provenance headers, and flock holdout ledger."""

    def mint_campaign_key(self, campaign_id: CampaignId) -> EvalResult[HmacKeyId]: ...

    def sign_provenance(
        self,
        key_id: HmacKeyId,
        *,
        task_id: TaskId,
        split: TaskSplit,
        payload_sha256: Sha256Hex,
    ) -> EvalResult[ProvenanceTag]: ...

    def verify_provenance(
        self,
        key_id: HmacKeyId,
        *,
        header_line: str,
        task_id: TaskId,
        split: TaskSplit,
        payload_sha256: Sha256Hex,
        allow_test: bool = False,
    ) -> EvalResult[ProvenanceTag]: ...

    def sign_canonical_payload(
        self,
        key_id: HmacKeyId,
        canonical_bytes: bytes,
    ) -> EvalResult[Sha256Hex]: ...

    def verify_canonical_payload(
        self,
        key_id: HmacKeyId,
        canonical_bytes: bytes,
        expected_tag: Sha256Hex,
    ) -> EvalResult[None]: ...

    def increment_holdout_ledger(
        self,
        *,
        skill_id: SkillId,
        test_digest: Sha256Hex,
        allow_holdout_reuse: bool,
        max_calls_before_reuse: PositiveInt = 3,
    ) -> EvalResult[HoldoutLedgerUpdate]: ...


class ClockPort(Protocol):
    """Deterministic time source for ABBA timestamps, deadlines, and OTel span epochs."""

    def wall_ns(self) -> NonNegInt: ...

    def mono_ns(self) -> NonNegInt: ...

    def utc_now(self) -> datetime: ...


class TelemetrySinkPort(Protocol):
    """Local 4-layer trace persistence, Parquet/DuckDB compaction, and read-only SQL queries."""

    def write_trial_trace(
        self, campaign_dir: Path, trace: TrialTraceSummary
    ) -> EvalResult[Path]: ...

    def compact_campaign(
        self,
        campaign_dir: Path,
        traces: tuple[TrialTraceSummary, ...],
    ) -> EvalResult[CompactionReceipt]: ...

    def query_readonly_sql(
        self,
        campaign_dir: Path,
        sql: NonEmptyStr,
    ) -> EvalResult[SqlQueryResult]: ...

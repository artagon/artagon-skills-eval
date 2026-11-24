"""Typed Pluggy adapter hookspecs, frozen request/receipt contracts, and lazy loader."""

from __future__ import annotations

import importlib.metadata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Final, Literal, Protocol, TypeGuard, runtime_checkable

import pluggy
from expression import NOTHING, Error, Ok
from pydantic import Field

from artagon_eval_core.domain.errors import AdapterUnavailableError, EvalResult
from artagon_eval_core.domain.fp import NullableOption
from artagon_eval_core.domain.primitives import (
    CampaignId,
    ConfinedScratchPath,
    EffortLevel,
    EvalSurface,
    HarnessName,
    HmacKeyId,
    ModelId,
    NonEmptyStr,
    NonNegInt,
    PositiveInt,
    RedactedJsonValue,
    RedactedStr,
    RelativeRepoPath,
    SafeId,
    SeedUint64,
    Sha256Hex,
    SkillId,
    TaskSplit,
    UnitFloat,
    static_redacted_literal,
)
from artagon_eval_core.domain.types import (
    FrozenModel,
    PersistentMap,
    empty_persistent_map,
)
from artagon_eval_core.ports.effects import (
    ClockPort,
    FilesystemPort,
    HmacCustodyPort,
    KeyringPort,
    SecretScrubberPort,
    SubprocessPort,
    TrialTraceSummary,
)

EP_OPTIMIZERS: Final[str] = "artagon_eval.optimizers"
EP_BENCHMARKS: Final[str] = "artagon_eval.benchmarks"
EP_SINKS: Final[str] = "artagon_eval.sinks"

opt_hookspec: Final[pluggy.HookspecMarker] = pluggy.HookspecMarker(EP_OPTIMIZERS)
bench_hookspec: Final[pluggy.HookspecMarker] = pluggy.HookspecMarker(EP_BENCHMARKS)
sink_hookspec: Final[pluggy.HookspecMarker] = pluggy.HookspecMarker(EP_SINKS)

opt_hookimpl: Final[pluggy.HookimplMarker] = pluggy.HookimplMarker(EP_OPTIMIZERS)
bench_hookimpl: Final[pluggy.HookimplMarker] = pluggy.HookimplMarker(EP_BENCHMARKS)
sink_hookimpl: Final[pluggy.HookimplMarker] = pluggy.HookimplMarker(EP_SINKS)


@dataclass(frozen=True, slots=True)
class AdapterRuntimeDeps:
    """Frozen bundle of injected Effect ports passed to every adapter."""

    subprocess: SubprocessPort
    fs: FilesystemPort
    keyring: KeyringPort
    custody: HmacCustodyPort
    clock: ClockPort
    scrubber: SecretScrubberPort


class QuarantinedTaskItem(FrozenModel):
    task_id: SafeId
    split: Literal["train", "val"]
    prompt: NonEmptyStr
    expected_output: NonEmptyStr
    expectations: tuple[NonEmptyStr, ...] = Field(min_length=1)
    content_sha256: Sha256Hex


class QuarantinedOptimizerCorpus(FrozenModel):
    skill_id: SkillId
    train_tasks: tuple[QuarantinedTaskItem, ...] = Field(min_length=1)
    val_tasks: tuple[QuarantinedTaskItem, ...] = Field(min_length=1)
    test_quarantined_count: PositiveInt
    test_digest_sha256: Sha256Hex


class OptimizerRequest(FrozenModel):
    adapter_name: Literal[
        "dspy-gepa", "optimize-anything", "pydsp", "skillopt", "evoskill", "skillspec"
    ]
    campaign_id: CampaignId
    skill_rel_dir: RelativeRepoPath
    run_dir: ConfinedScratchPath
    corpus: QuarantinedOptimizerCorpus
    harness: HarnessName
    model: NullableOption[ModelId] = NOTHING
    effort: NullableOption[EffortLevel] = NOTHING
    surface: Literal["skill_eval"] = "skill_eval"
    os_sandbox_active: bool
    allow_unsandboxed_candidates: bool = False
    max_cli_launches: PositiveInt = 20
    max_concurrency: PositiveInt = 2
    seed: SeedUint64 = 0
    hmac_key_id: HmacKeyId


class OptimizerReceipt(FrozenModel):
    """Frozen receipt emitted by every optimizer adapter (never auto-promotes)."""

    schema_version: Literal["harness-eval-candidate-bundle/v1"] = "harness-eval-candidate-bundle/v1"
    adapter_name: NonEmptyStr
    promotion_status: Literal["unpromoted_candidate", "no_viable_candidate"]
    skill_id: SkillId
    harness: HarnessName
    seed_sha256: Sha256Hex
    candidate_sha256: NullableOption[Sha256Hex] = NOTHING
    candidate_patch_rel: NullableOption[RelativeRepoPath] = NOTHING
    launches_used: NonNegInt
    max_cli_launches: PositiveInt
    train_count: PositiveInt
    val_count: PositiveInt
    test_quarantined_count: PositiveInt
    test_executions: Literal[0] = 0
    os_sandbox_active: bool


@runtime_checkable
class OptimizerAdapter(Protocol):
    name: NonEmptyStr
    install_extra: NonEmptyStr

    @opt_hookspec(firstresult=True)
    def run_optimization(
        self,
        request: OptimizerRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[OptimizerReceipt]: ...


class WazaBenchmarkParams(FrozenModel):
    adapter_kind: Literal["waza"] = "waza"
    eval_yaml_rel: RelativeRepoPath
    waza_mode: Literal["mock", "copilot-sdk", "harness-eval"] = "mock"
    harnesses: tuple[HarnessName, ...] = ("copilot",)
    trust_suite_code: bool = False
    allow_unsplit_v1: bool = False
    max_cli_launches: PositiveInt = 20


class SkillSpecBenchmarkParams(FrozenModel):
    adapter_kind: Literal["skillspec"] = "skillspec"
    skill_rel_dir: RelativeRepoPath
    subcommand: Literal["validate", "boundary", "route"]
    pin_config_rel: RelativeRepoPath


BenchmarkParams = Annotated[
    WazaBenchmarkParams | SkillSpecBenchmarkParams,
    Field(discriminator="adapter_kind"),
]


class BenchmarkRequest(FrozenModel):
    campaign_id: CampaignId
    run_dir: ConfinedScratchPath
    surface: EvalSurface = "skill_eval"
    params: BenchmarkParams
    model: NullableOption[ModelId] = NOTHING
    effort: NullableOption[EffortLevel] = NOTHING


class BenchmarkReceipt(FrozenModel):
    schema_version: Literal["artagon-benchmark-receipt/v1"] = "artagon-benchmark-receipt/v1"
    adapter_name: Literal["waza", "skillspec"]
    plumbing_only: bool
    cli_launches_used: NonNegInt
    splits_executed: tuple[TaskSplit, ...] = ()
    summary_metrics: PersistentMap[str, RedactedJsonValue] = Field(
        default_factory=empty_persistent_map
    )


@runtime_checkable
class BenchmarkAdapter(Protocol):
    name: NonEmptyStr
    install_extra: NonEmptyStr

    @bench_hookspec(firstresult=True)
    def run_benchmark(
        self,
        request: BenchmarkRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[BenchmarkReceipt]: ...


class ExportEndpointPolicy(FrozenModel):
    endpoint_url: NonEmptyStr
    allow_remote_export: bool = False


class TelemetryExportRequest(FrozenModel):
    sink_name: Literal["phoenix", "mlflow", "langfuse-otlp", "otlp-json", "waza-outcome"]
    campaign_id: CampaignId
    traces: tuple[TrialTraceSummary, ...]
    endpoint: NullableOption[ExportEndpointPolicy] = NOTHING
    hash_holdout_payloads: bool = True
    hmac_key_id: NullableOption[HmacKeyId] = NOTHING
    out_path: NullableOption[ConfinedScratchPath] = NOTHING


class TelemetryExportReceipt(FrozenModel):
    schema_version: Literal["artagon-telemetry-export/v1"] = "artagon-telemetry-export/v1"
    sink_name: NonEmptyStr
    exported_trial_count: NonNegInt
    holdout_payloads_hashed: bool
    destination: RedactedStr


class OfflineScoringRequest(FrozenModel):
    """Offline verdict scoring (zero LLM calls; predict_fn is structurally absent)."""

    sink_name: Literal["phoenix", "mlflow", "pydantic-evals"]
    traces: tuple[TrialTraceSummary, ...]
    scorer_ids: tuple[SafeId, ...] = Field(min_length=1)
    hmac_key_id: HmacKeyId


class OfflineScoringReceipt(FrozenModel):
    sink_name: NonEmptyStr
    scored_count: NonNegInt
    predict_fn_used: Literal[False] = False
    mean_scores: PersistentMap[SafeId, UnitFloat]


@runtime_checkable
class TelemetrySinkAdapter(Protocol):
    name: NonEmptyStr
    install_extra: NonEmptyStr

    @sink_hookspec(firstresult=True)
    def export_traces(
        self,
        request: TelemetryExportRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[TelemetryExportReceipt]: ...

    @sink_hookspec(firstresult=True)
    def score_offline(
        self,
        request: OfflineScoringRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[OfflineScoringReceipt]: ...


def list_installed_adapters(group: str) -> tuple[str, ...]:
    """Inspect importlib.metadata without importing any heavy adapter package."""
    return tuple(sorted(ep.name for ep in importlib.metadata.entry_points(group=group)))


def is_optimizer_adapter(obj: object) -> TypeGuard[OptimizerAdapter]:
    return isinstance(obj, OptimizerAdapter)


def is_benchmark_adapter(obj: object) -> TypeGuard[BenchmarkAdapter]:
    return isinstance(obj, BenchmarkAdapter)


def is_telemetry_sink_adapter(obj: object) -> TypeGuard[TelemetrySinkAdapter]:
    return isinstance(obj, TelemetrySinkAdapter)


def load_adapter[A](
    group: str,
    name: NonEmptyStr,
    *,
    install_extra: NonEmptyStr,
    protocol_guard: Callable[[object], TypeGuard[A]],
) -> EvalResult[A]:
    """Lazily load a single requested Pluggy adapter, returning exit 69 if absent or invalid."""
    eps = [ep for ep in importlib.metadata.entry_points(group=group) if ep.name == name]
    if not eps:
        return Error(
            AdapterUnavailableError(
                reason_code="optional_dependency_missing",
                message=static_redacted_literal("Requested evaluation adapter is not installed"),
                adapter_name=name,
                install_extra=install_extra,
            )
        )
    try:
        plugin_factory: object = eps[0].load()
    except ImportError:
        return Error(
            AdapterUnavailableError(
                reason_code="optional_dependency_missing",
                message=static_redacted_literal("Adapter optional dependency import failed"),
                adapter_name=name,
                install_extra=install_extra,
            )
        )
    if not callable(plugin_factory):
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_factory_invalid",
                message=static_redacted_literal("Adapter entry point is not callable"),
                adapter_name=name,
                install_extra=install_extra,
            )
        )
    instance: object = plugin_factory()
    if not protocol_guard(instance):
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_contract_mismatch",
                message=static_redacted_literal("Loaded adapter does not match expected protocol"),
                adapter_name=name,
                install_extra=install_extra,
            )
        )
    return Ok(instance)

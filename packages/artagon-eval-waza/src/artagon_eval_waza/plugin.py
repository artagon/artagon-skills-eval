"""Pluggy plugin skeleton for artagon-eval-waza."""

from __future__ import annotations

from dataclasses import dataclass

from expression import Error

from artagon_eval_core.domain.errors import AdapterUnavailableError, EvalResult
from artagon_eval_core.domain.primitives import static_redacted_literal
from artagon_eval_core.plugins.contracts import (
    AdapterRuntimeDeps,
    BenchmarkReceipt,
    BenchmarkRequest,
    OfflineScoringReceipt,
    OfflineScoringRequest,
    TelemetryExportReceipt,
    TelemetryExportRequest,
    bench_hookimpl,
    sink_hookimpl,
)


@dataclass(frozen=True, slots=True)
class WazaBenchmarkAdapter:
    name: str = "waza"
    install_extra: str = "waza"

    @bench_hookimpl
    def run_benchmark(
        self,
        request: BenchmarkRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[BenchmarkReceipt]:
        _ = (request, deps)
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_not_implemented_phase4",
                message=static_redacted_literal("Waza benchmark adapter runtime ships in Phase 4"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )


@dataclass(frozen=True, slots=True)
class WazaOutcomeSinkAdapter:
    name: str = "waza-outcome"
    install_extra: str = "waza"

    @sink_hookimpl
    def export_traces(
        self,
        request: TelemetryExportRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[TelemetryExportReceipt]:
        _ = (request, deps)
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_not_implemented_phase4",
                message=static_redacted_literal("Waza outcome sink ships in Phase 4"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )

    @sink_hookimpl
    def score_offline(
        self,
        request: OfflineScoringRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[OfflineScoringReceipt]:
        _ = (request, deps)
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_not_implemented_phase4",
                message=static_redacted_literal("Waza offline scorer ships in Phase 4"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )


def create_benchmark_adapter() -> WazaBenchmarkAdapter:
    return WazaBenchmarkAdapter()


def create_sink_adapter() -> WazaOutcomeSinkAdapter:
    return WazaOutcomeSinkAdapter()

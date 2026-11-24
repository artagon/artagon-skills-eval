"""Pluggy plugin skeleton for artagon-eval-observability (Apache-2.0 Phoenix & MLflow 3)."""

from __future__ import annotations

from dataclasses import dataclass

from expression import Error

from artagon_eval_core.domain.errors import AdapterUnavailableError, EvalResult
from artagon_eval_core.domain.primitives import static_redacted_literal
from artagon_eval_core.plugins.contracts import (
    AdapterRuntimeDeps,
    OfflineScoringReceipt,
    OfflineScoringRequest,
    TelemetryExportReceipt,
    TelemetryExportRequest,
    sink_hookimpl,
)


@dataclass(frozen=True, slots=True)
class ObservabilitySinkAdapter:
    name: str
    install_extra: str

    @sink_hookimpl
    def export_traces(
        self,
        request: TelemetryExportRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[TelemetryExportReceipt]:
        _ = (request, deps)
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_not_implemented_phase5",
                message=static_redacted_literal("Observability telemetry sink ships in Phase 5"),
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
                reason_code="adapter_not_implemented_phase5",
                message=static_redacted_literal("Observability offline scorer ships in Phase 5"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )


def create_phoenix_sink_adapter() -> ObservabilitySinkAdapter:
    return ObservabilitySinkAdapter(name="phoenix", install_extra="phoenix")


def create_mlflow_sink_adapter() -> ObservabilitySinkAdapter:
    return ObservabilitySinkAdapter(name="mlflow", install_extra="mlflow")

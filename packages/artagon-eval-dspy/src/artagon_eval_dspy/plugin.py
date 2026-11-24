"""Pluggy plugin skeleton for artagon-eval-dspy (DSPy / GEPA / pyDSP)."""

from __future__ import annotations

from dataclasses import dataclass

from expression import Error

from artagon_eval_core.domain.errors import AdapterUnavailableError, EvalResult
from artagon_eval_core.domain.primitives import static_redacted_literal
from artagon_eval_core.plugins.contracts import (
    AdapterRuntimeDeps,
    OptimizerReceipt,
    OptimizerRequest,
    opt_hookimpl,
)


@dataclass(frozen=True, slots=True)
class DSPyOptimizerAdapter:
    name: str
    install_extra: str = "dspy"

    @opt_hookimpl
    def run_optimization(
        self,
        request: OptimizerRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[OptimizerReceipt]:
        _ = (request, deps)
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_not_implemented_phase5",
                message=static_redacted_literal("DSPy/GEPA optimizer adapter ships in Phase 5"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )


def create_dspy_gepa_adapter() -> DSPyOptimizerAdapter:
    return DSPyOptimizerAdapter(name="dspy-gepa")


def create_optimize_anything_adapter() -> DSPyOptimizerAdapter:
    return DSPyOptimizerAdapter(name="optimize-anything")


def create_pydsp_adapter() -> DSPyOptimizerAdapter:
    return DSPyOptimizerAdapter(name="pydsp")

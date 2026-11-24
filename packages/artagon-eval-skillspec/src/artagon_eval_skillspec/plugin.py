"""Pluggy plugin skeleton for artagon-eval-skillspec."""

from __future__ import annotations

from dataclasses import dataclass

from expression import Error

from artagon_eval_core.domain.errors import AdapterUnavailableError, EvalResult
from artagon_eval_core.domain.primitives import static_redacted_literal
from artagon_eval_core.plugins.contracts import (
    AdapterRuntimeDeps,
    BenchmarkReceipt,
    BenchmarkRequest,
    OptimizerReceipt,
    OptimizerRequest,
    bench_hookimpl,
    opt_hookimpl,
)


@dataclass(frozen=True, slots=True)
class SkillSpecBenchmarkAdapter:
    name: str = "skillspec"
    install_extra: str = "skillspec"

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
                message=static_redacted_literal("SkillSpec benchmark adapter ships in Phase 4"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )


@dataclass(frozen=True, slots=True)
class SkillSpecOptimizerAdapter:
    name: str = "skillspec"
    install_extra: str = "skillspec"

    @opt_hookimpl
    def run_optimization(
        self,
        request: OptimizerRequest,
        deps: AdapterRuntimeDeps,
    ) -> EvalResult[OptimizerReceipt]:
        _ = (request, deps)
        return Error(
            AdapterUnavailableError(
                reason_code="adapter_not_implemented_phase4",
                message=static_redacted_literal("SkillSpec optimizer adapter ships in Phase 4"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )


def create_benchmark_adapter() -> SkillSpecBenchmarkAdapter:
    return SkillSpecBenchmarkAdapter()


def create_optimizer_adapter() -> SkillSpecOptimizerAdapter:
    return SkillSpecOptimizerAdapter()

"""Pluggy plugin skeleton for artagon-eval-evoskill (zero import-time sys.meta_path mutation)."""

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
class EvoSkillOptimizerAdapter:
    name: str = "evoskill"
    install_extra: str = "evoskill"

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
                message=static_redacted_literal("EvoSkill optimizer adapter ships in Phase 5"),
                adapter_name=self.name,
                install_extra=self.install_extra,
            )
        )


def create_optimizer_adapter() -> EvoSkillOptimizerAdapter:
    return EvoSkillOptimizerAdapter()

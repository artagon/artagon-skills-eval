"""Smoke tests verifying artagon-eval-skillspec Pluggy entry-point discovery."""

from __future__ import annotations

from expression import Ok

from artagon_eval_core.plugins.contracts import (
    EP_BENCHMARKS,
    EP_OPTIMIZERS,
    is_benchmark_adapter,
    is_optimizer_adapter,
    list_installed_adapters,
    load_adapter,
)


def test_skillspec_entry_points_load_cleanly() -> None:
    assert "skillspec" in list_installed_adapters(EP_BENCHMARKS)
    assert "skillspec" in list_installed_adapters(EP_OPTIMIZERS)

    bench = load_adapter(
        EP_BENCHMARKS, "skillspec", install_extra="skillspec", protocol_guard=is_benchmark_adapter
    )
    opt = load_adapter(
        EP_OPTIMIZERS, "skillspec", install_extra="skillspec", protocol_guard=is_optimizer_adapter
    )
    assert isinstance(bench, Ok)
    assert isinstance(opt, Ok)

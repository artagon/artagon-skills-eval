"""Smoke tests verifying artagon-eval-waza Pluggy entry-point discovery and protocol compliance."""

from __future__ import annotations

from expression import Ok

from artagon_eval_core.plugins.contracts import (
    EP_BENCHMARKS,
    EP_SINKS,
    is_benchmark_adapter,
    is_telemetry_sink_adapter,
    list_installed_adapters,
    load_adapter,
)


def test_waza_entry_points_load_cleanly() -> None:
    assert "waza" in list_installed_adapters(EP_BENCHMARKS)
    assert "waza-outcome" in list_installed_adapters(EP_SINKS)

    bench = load_adapter(
        EP_BENCHMARKS, "waza", install_extra="waza", protocol_guard=is_benchmark_adapter
    )
    assert isinstance(bench, Ok)
    assert bench.ok.name == "waza"

    sink = load_adapter(
        EP_SINKS, "waza-outcome", install_extra="waza", protocol_guard=is_telemetry_sink_adapter
    )
    assert isinstance(sink, Ok)
    assert sink.ok.name == "waza-outcome"

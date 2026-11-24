"""Smoke tests verifying artagon-eval-observability Pluggy entry-point discovery."""

from __future__ import annotations

from expression import Ok

from artagon_eval_core.plugins.contracts import (
    EP_SINKS,
    is_telemetry_sink_adapter,
    list_installed_adapters,
    load_adapter,
)


def test_observability_entry_points_load_cleanly() -> None:
    installed = list_installed_adapters(EP_SINKS)
    for ep_name in ("phoenix", "mlflow"):
        assert ep_name in installed
        loaded = load_adapter(
            EP_SINKS, ep_name, install_extra=ep_name, protocol_guard=is_telemetry_sink_adapter
        )
        assert isinstance(loaded, Ok)
        assert loaded.ok.name == ep_name

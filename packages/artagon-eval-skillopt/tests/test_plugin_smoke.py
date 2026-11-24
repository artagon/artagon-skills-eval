"""Smoke tests verifying artagon-eval-skillopt Pluggy entry-point discovery."""

from __future__ import annotations

from expression import Ok

from artagon_eval_core.plugins.contracts import (
    EP_OPTIMIZERS,
    is_optimizer_adapter,
    list_installed_adapters,
    load_adapter,
)


def test_skillopt_entry_point_loads_cleanly() -> None:
    assert "skillopt" in list_installed_adapters(EP_OPTIMIZERS)
    loaded = load_adapter(
        EP_OPTIMIZERS, "skillopt", install_extra="skillopt", protocol_guard=is_optimizer_adapter
    )
    assert isinstance(loaded, Ok)
    assert loaded.ok.name == "skillopt"

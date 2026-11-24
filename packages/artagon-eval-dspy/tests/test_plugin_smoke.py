"""Smoke tests verifying artagon-eval-dspy Pluggy entry-point discovery and protocol compliance."""

from __future__ import annotations

from expression import Ok

from artagon_eval_core.plugins.contracts import (
    EP_OPTIMIZERS,
    is_optimizer_adapter,
    list_installed_adapters,
    load_adapter,
)


def test_dspy_entry_points_load_cleanly() -> None:
    installed = list_installed_adapters(EP_OPTIMIZERS)
    for ep_name in ("dspy-gepa", "optimize-anything", "pydsp"):
        assert ep_name in installed
        loaded = load_adapter(
            EP_OPTIMIZERS, ep_name, install_extra="dspy", protocol_guard=is_optimizer_adapter
        )
        assert isinstance(loaded, Ok)
        assert loaded.ok.name == ep_name

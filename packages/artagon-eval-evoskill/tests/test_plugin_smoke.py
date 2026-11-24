"""Smoke tests verifying artagon-eval-evoskill Pluggy entry-point discovery."""

from __future__ import annotations

import sys

from expression import Ok

from artagon_eval_core.plugins.contracts import (
    EP_OPTIMIZERS,
    is_optimizer_adapter,
    list_installed_adapters,
    load_adapter,
)


def test_evoskill_entry_point_loads_without_meta_path_mutation() -> None:
    meta_before = list(sys.meta_path)
    assert "evoskill" in list_installed_adapters(EP_OPTIMIZERS)
    loaded = load_adapter(
        EP_OPTIMIZERS, "evoskill", install_extra="evoskill", protocol_guard=is_optimizer_adapter
    )
    assert isinstance(loaded, Ok)
    assert loaded.ok.name == "evoskill"
    assert list(sys.meta_path) == meta_before

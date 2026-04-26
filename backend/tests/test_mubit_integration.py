from __future__ import annotations

import sys
import types

from app.agents import mubit_integration
from app.core.config import settings


def test_mubit_learning_skips_without_key(monkeypatch) -> None:
    mubit_integration._reset_mubit_for_tests()
    monkeypatch.setattr(settings, "mubit_enabled", True)
    monkeypatch.setattr(settings, "mubit_api_key", None)

    assert mubit_integration.initialize_mubit_learning() is False


def test_mubit_learning_initializes_sdk_once(monkeypatch) -> None:
    mubit_integration._reset_mubit_for_tests()
    calls: list[dict[str, str]] = []

    package = types.ModuleType("mubit")
    learn = types.ModuleType("mubit.learn")

    def init(**kwargs):
        calls.append(kwargs)

    learn.init = init
    package.learn = learn

    monkeypatch.setitem(sys.modules, "mubit", package)
    monkeypatch.setitem(sys.modules, "mubit.learn", learn)
    monkeypatch.setattr(settings, "mubit_enabled", True)
    monkeypatch.setattr(settings, "mubit_api_key", "mbt_test")
    monkeypatch.setattr(settings, "mubit_agent_id", "test-agent")

    assert mubit_integration.initialize_mubit_learning() is True
    assert mubit_integration.initialize_mubit_learning() is True
    assert calls == [{"api_key": "mbt_test", "agent_id": "test-agent"}]

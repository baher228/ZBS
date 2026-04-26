from __future__ import annotations

from app.agents.models import AgentCapability, OrchestratorDecision, OrchestratorStatus, TaskResponse
from app.agents.result_cache import cache_key, get_cached_model, set_cached_model


def test_agent_result_cache_round_trips_pydantic_models() -> None:
    key = cache_key("test.task", {"prompt": "Write launch copy", "context": {"b": "2", "a": "1"}})
    response = TaskResponse(
        selected_agent=AgentCapability.CONTENT_GENERATOR,
        agent_response=None,
        review=None,
        decision=OrchestratorDecision(
            status=OrchestratorStatus.COMPLETED,
            selected_agent=AgentCapability.CONTENT_GENERATOR,
            message="Done",
        ),
    )

    set_cached_model(key, response)

    cached = get_cached_model(key, TaskResponse)
    assert cached == response


def test_agent_result_cache_key_is_stable_for_dict_order() -> None:
    assert cache_key("test", {"a": 1, "b": 2}) == cache_key("test", {"b": 2, "a": 1})

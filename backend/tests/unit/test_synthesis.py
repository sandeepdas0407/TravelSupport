from datetime import date
from types import SimpleNamespace

import pytest

from app.services import synthesis
from app.utils.errors import SynthesisError


class _FakeMessages:
    def __init__(self, response: object) -> None:
        self._response = response

    async def create(self, **kwargs: object) -> object:
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response: object) -> None:
        self.messages = _FakeMessages(response)


def _tool_use_response(input_data: dict) -> object:
    block = SimpleNamespace(type="tool_use", input=input_data)
    return SimpleNamespace(content=[block])


async def test_synthesize_plan_parses_tool_use(settings, banff, monkeypatch) -> None:
    plan_input = {
        "summary": "A scenic drive.",
        "day_by_day": [{"day_number": 1, "date": "2026-10-05", "title": "Day 1", "description": "Drive."}],
        "recommended_stays": ["Banff Park Lodge"],
        "packing_suggestions": ["Jacket"],
    }
    fake_client = _FakeAnthropicClient(_tool_use_response(plan_input))
    monkeypatch.setattr(synthesis, "AsyncAnthropic", lambda api_key: fake_client)

    origin = banff.model_copy(update={"resolved_name": "Seattle, WA"})
    route = synthesis.RouteSummary(origin=origin, destination=banff, distance_km=970, duration_minutes=620)

    plan = await synthesis.synthesize_plan(
        settings, route, [], [], 1, date(2026, 10, 5), "traveling with a dog"
    )

    assert plan.summary == "A scenic drive."
    assert plan.day_by_day[0].day_number == 1


async def test_synthesize_plan_raises_when_no_tool_use(settings, banff, monkeypatch) -> None:
    fake_client = _FakeAnthropicClient(SimpleNamespace(content=[]))
    monkeypatch.setattr(synthesis, "AsyncAnthropic", lambda api_key: fake_client)

    route = synthesis.RouteSummary(origin=banff, destination=banff, distance_km=1, duration_minutes=1)

    with pytest.raises(SynthesisError):
        await synthesis.synthesize_plan(settings, route, [], [], 1, date(2026, 10, 5), None)

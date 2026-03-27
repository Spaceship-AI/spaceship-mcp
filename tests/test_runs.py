"""Tests for SpaceshipClient run_agent."""

from __future__ import annotations

import json
import pytest
import respx
import httpx

from spaceship_mcp.client import SpaceshipClient, SpaceshipError
from .conftest import BASE_URL, SAMPLE_RUN


def test_run_agent_returns_run_info(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/api/v1/agents/agent-uuid-1/run").mock(
            return_value=httpx.Response(202, json=SAMPLE_RUN)
        )

        result = client.run_agent("agent-uuid-1", prompt="Do the thing")

    assert result["execution_id"] == "exec-uuid-1"
    assert result["status"] == "queued"


def test_run_agent_sends_prompt_in_body(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/api/v1/agents/agent-uuid-1/run").mock(
            return_value=httpx.Response(202, json=SAMPLE_RUN)
        )

        client.run_agent("agent-uuid-1", prompt="Hello!")

    body = json.loads(route.calls[0].request.content)
    assert body["prompt"] == "Hello!"


def test_run_agent_sends_thread_id(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/api/v1/agents/agent-uuid-1/run").mock(
            return_value=httpx.Response(202, json=SAMPLE_RUN)
        )

        client.run_agent("agent-uuid-1", prompt="Hi", thread_id="thread-abc")

    body = json.loads(route.calls[0].request.content)
    assert body["thread_id"] == "thread-abc"


def test_run_agent_raises_on_429(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/api/v1/agents/agent-uuid-1/run").mock(
            return_value=httpx.Response(
                429, json={"error": "Concurrent run limit reached (3 runs)."}
            )
        )

        with pytest.raises(SpaceshipError) as exc_info:
            client.run_agent("agent-uuid-1", prompt="Run!")

    assert exc_info.value.status_code == 429


def test_run_agent_raises_on_422(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/api/v1/agents/agent-uuid-1/run").mock(
            return_value=httpx.Response(422, json={"error": "prompt is required"})
        )

        with pytest.raises(SpaceshipError) as exc_info:
            client.run_agent("agent-uuid-1", prompt="")

    assert exc_info.value.status_code == 422

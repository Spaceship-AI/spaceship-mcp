"""Tests for SpaceshipClient agent methods."""

from __future__ import annotations

import json
import pytest
import respx
import httpx

from spaceship_mcp.client import SpaceshipClient, SpaceshipError
from .conftest import BASE_URL, API_KEY, SAMPLE_AGENT


def test_list_agents_returns_agents(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/agents").mock(
            return_value=httpx.Response(200, json={"agents": [SAMPLE_AGENT]})
        )

        result = client.list_agents()

    assert result == [SAMPLE_AGENT]


def test_list_agents_sends_project_id_filter(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/agents").mock(
            return_value=httpx.Response(200, json={"agents": []})
        )

        client.list_agents(project_id=42)

    assert "project_id=42" in str(route.calls[0].request.url)


def test_get_agent_returns_agent(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/agents/agent-uuid-1").mock(
            return_value=httpx.Response(200, json={"agent": SAMPLE_AGENT})
        )

        result = client.get_agent("agent-uuid-1")

    assert result == SAMPLE_AGENT


def test_get_agent_raises_on_404(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/agents/bad-uuid").mock(
            return_value=httpx.Response(404, json={"error": "Agent not found"})
        )

        with pytest.raises(SpaceshipError) as exc_info:
            client.get_agent("bad-uuid")

    assert exc_info.value.status_code == 404


def test_create_agent_with_prompt(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/api/v1/agents").mock(
            return_value=httpx.Response(
                201,
                json={"agent": SAMPLE_AGENT, "scaffold_applied": False},
            )
        )

        result = client.create_agent(name="Bot", project_id=1, prompt="You are helpful.")

    assert result["agent"] == SAMPLE_AGENT
    assert result["scaffold_applied"] is False


def test_create_agent_with_description(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/api/v1/agents").mock(
            return_value=httpx.Response(
                201,
                json={"agent": SAMPLE_AGENT, "scaffold_applied": True},
            )
        )

        result = client.create_agent(name="Bot", project_id=1, description="A support agent")

    assert result["scaffold_applied"] is True
    body = json.loads(route.calls[0].request.content)
    assert body["description"] == "A support agent"
    assert "prompt" not in body


def test_create_agent_sends_tools(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/api/v1/agents").mock(
            return_value=httpx.Response(
                201,
                json={"agent": SAMPLE_AGENT, "scaffold_applied": False},
            )
        )

        client.create_agent(
            name="Bot", project_id=1, prompt="Prompt", tools=["tool-uuid-1"]
        )

    body = json.loads(route.calls[0].request.content)
    assert body["tools"] == ["tool-uuid-1"]


def test_update_agent_returns_updated_agent(client: SpaceshipClient) -> None:
    updated = {**SAMPLE_AGENT, "name": "Renamed Bot"}
    with respx.mock(base_url=BASE_URL) as mock:
        mock.patch("/api/v1/agents/agent-uuid-1").mock(
            return_value=httpx.Response(200, json={"agent": updated, "scaffold_applied": False})
        )

        result = client.update_agent("agent-uuid-1", name="Renamed Bot")

    assert result["agent"]["name"] == "Renamed Bot"


def test_delete_agent_returns_none(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.delete("/api/v1/agents/agent-uuid-1").mock(
            return_value=httpx.Response(204)
        )

        result = client.delete_agent("agent-uuid-1")

    assert result is None


def test_delete_agent_raises_on_404(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.delete("/api/v1/agents/bad-uuid").mock(
            return_value=httpx.Response(404, json={"error": "Agent not found"})
        )

        with pytest.raises(SpaceshipError) as exc_info:
            client.delete_agent("bad-uuid")

    assert exc_info.value.status_code == 404

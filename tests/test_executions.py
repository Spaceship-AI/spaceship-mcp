"""Tests for SpaceshipClient execution and log methods."""

from __future__ import annotations

import pytest
import respx
import httpx

from spaceship_mcp.client import SpaceshipClient, SpaceshipError
from .conftest import BASE_URL, SAMPLE_EXECUTION, SAMPLE_LOG


def test_get_executions_returns_list(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/agents/agent-uuid-1/executions").mock(
            return_value=httpx.Response(200, json={"executions": [SAMPLE_EXECUTION]})
        )

        result = client.get_executions("agent-uuid-1")

    assert result == [SAMPLE_EXECUTION]


def test_get_executions_sends_execution_id_filter(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/agents/agent-uuid-1/executions").mock(
            return_value=httpx.Response(200, json={"executions": [SAMPLE_EXECUTION]})
        )

        client.get_executions("agent-uuid-1", execution_id="exec-uuid-1")

    assert "execution_id=exec-uuid-1" in str(route.calls[0].request.url)


def test_get_executions_sends_limit(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/agents/agent-uuid-1/executions").mock(
            return_value=httpx.Response(200, json={"executions": []})
        )

        client.get_executions("agent-uuid-1", limit=5)

    assert "limit=5" in str(route.calls[0].request.url)


def test_get_logs_returns_logs_in_asc_order(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/agents/agent-uuid-1/logs").mock(
            return_value=httpx.Response(200, json={"logs": [SAMPLE_LOG]})
        )

        result = client.get_logs("agent-uuid-1", "exec-uuid-1")

    assert result == [SAMPLE_LOG]
    assert "order=asc" in str(route.calls[0].request.url)


def test_get_logs_sends_execution_id(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/agents/agent-uuid-1/logs").mock(
            return_value=httpx.Response(200, json={"logs": []})
        )

        client.get_logs("agent-uuid-1", "exec-uuid-1")

    assert "execution_id=exec-uuid-1" in str(route.calls[0].request.url)


def test_get_executions_raises_on_404(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/agents/bad-uuid/executions").mock(
            return_value=httpx.Response(404, json={"error": "Agent not found"})
        )

        with pytest.raises(SpaceshipError) as exc_info:
            client.get_executions("bad-uuid")

    assert exc_info.value.status_code == 404

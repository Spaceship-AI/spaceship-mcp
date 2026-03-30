"""Tests for orchestration-related SpaceshipClient methods."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from spaceship_mcp.client import SpaceshipClient, SpaceshipError
from .conftest import (
    BASE_URL,
    SAMPLE_ORCHESTRATION,
    SAMPLE_ORCH_RUN,
    SAMPLE_ORCH_EXECUTION,
)


# ---------------------------------------------------------------------------
# list_orchestrations
# ---------------------------------------------------------------------------


def test_list_orchestrations_returns_list(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/orchestrations").mock(
            return_value=httpx.Response(200, json={"orchestrations": [SAMPLE_ORCHESTRATION]})
        )
        result = client.list_orchestrations()
    assert result == [SAMPLE_ORCHESTRATION]


def test_list_orchestrations_sends_project_id_filter(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/orchestrations").mock(
            return_value=httpx.Response(200, json={"orchestrations": []})
        )
        client.list_orchestrations(project_id=42)
    assert "project_id=42" in str(route.calls[0].request.url)


def test_list_orchestrations_sends_limit(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/orchestrations").mock(
            return_value=httpx.Response(200, json={"orchestrations": []})
        )
        client.list_orchestrations(limit=5)
    assert "limit=5" in str(route.calls[0].request.url)


def test_list_orchestrations_raises_on_401(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/orchestrations").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )
        with pytest.raises(SpaceshipError) as exc_info:
            client.list_orchestrations()
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_orchestration
# ---------------------------------------------------------------------------


def test_get_orchestration_returns_orchestration(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/orchestrations/orch-uuid-1").mock(
            return_value=httpx.Response(200, json={"orchestration": SAMPLE_ORCHESTRATION})
        )
        result = client.get_orchestration("orch-uuid-1")
    assert result == SAMPLE_ORCHESTRATION


def test_get_orchestration_raises_on_404(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/orchestrations/bad-uuid").mock(
            return_value=httpx.Response(404, json={"error": "Orchestration not found"})
        )
        with pytest.raises(SpaceshipError) as exc_info:
            client.get_orchestration("bad-uuid")
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# run_orchestration
# ---------------------------------------------------------------------------


def test_run_orchestration_returns_execution_id(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/api/v1/orchestrations/orch-uuid-1/run").mock(
            return_value=httpx.Response(202, json=SAMPLE_ORCH_RUN)
        )
        result = client.run_orchestration("orch-uuid-1")
    assert result["execution_id"] == SAMPLE_ORCH_RUN["execution_id"]
    assert result["status"] == "queued"


def test_run_orchestration_sends_input_data(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/api/v1/orchestrations/orch-uuid-1/run").mock(
            return_value=httpx.Response(202, json=SAMPLE_ORCH_RUN)
        )
        client.run_orchestration("orch-uuid-1", input_data={"query": "hello"})
    body = json.loads(route.calls[0].request.content)
    assert body["input_data"] == {"query": "hello"}


def test_run_orchestration_sends_params(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/api/v1/orchestrations/orch-uuid-1/run").mock(
            return_value=httpx.Response(202, json=SAMPLE_ORCH_RUN)
        )
        client.run_orchestration("orch-uuid-1", params={"timeout": 30})
    body = json.loads(route.calls[0].request.content)
    assert body["params"] == {"timeout": 30}


def test_run_orchestration_omits_none_fields(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.post("/api/v1/orchestrations/orch-uuid-1/run").mock(
            return_value=httpx.Response(202, json=SAMPLE_ORCH_RUN)
        )
        client.run_orchestration("orch-uuid-1")
    body = json.loads(route.calls[0].request.content)
    assert "input_data" not in body
    assert "params" not in body


def test_run_orchestration_raises_on_422(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.post("/api/v1/orchestrations/orch-uuid-1/run").mock(
            return_value=httpx.Response(422, json={"error": "Orchestration must be active"})
        )
        with pytest.raises(SpaceshipError) as exc_info:
            client.run_orchestration("orch-uuid-1")
    assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# get_orchestration_executions
# ---------------------------------------------------------------------------


def test_get_orchestration_executions_returns_list(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/orchestrations/orch-uuid-1/executions").mock(
            return_value=httpx.Response(200, json={"executions": [SAMPLE_ORCH_EXECUTION]})
        )
        result = client.get_orchestration_executions("orch-uuid-1")
    assert result == [SAMPLE_ORCH_EXECUTION]


def test_get_orchestration_executions_sends_execution_id_filter(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/orchestrations/orch-uuid-1/executions").mock(
            return_value=httpx.Response(200, json={"executions": [SAMPLE_ORCH_EXECUTION]})
        )
        client.get_orchestration_executions("orch-uuid-1", execution_id="orch-exec-uuid-1")
    assert "execution_id=orch-exec-uuid-1" in str(route.calls[0].request.url)


def test_get_orchestration_executions_sends_limit(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/orchestrations/orch-uuid-1/executions").mock(
            return_value=httpx.Response(200, json={"executions": []})
        )
        client.get_orchestration_executions("orch-uuid-1", limit=3)
    assert "limit=3" in str(route.calls[0].request.url)


def test_get_orchestration_executions_raises_on_404(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/orchestrations/bad-uuid/executions").mock(
            return_value=httpx.Response(404, json={"error": "Orchestration not found"})
        )
        with pytest.raises(SpaceshipError) as exc_info:
            client.get_orchestration_executions("bad-uuid")
    assert exc_info.value.status_code == 404

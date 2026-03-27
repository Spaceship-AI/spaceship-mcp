"""Tests for SpaceshipClient.list_projects."""

from __future__ import annotations

import pytest
import respx
import httpx

from spaceship_mcp.client import SpaceshipClient, SpaceshipError
from .conftest import BASE_URL, API_KEY, SAMPLE_PROJECT


def test_list_projects_returns_projects(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/projects").mock(
            return_value=httpx.Response(200, json={"projects": [SAMPLE_PROJECT]})
        )

        result = client.list_projects()

    assert result == [SAMPLE_PROJECT]


def test_list_projects_sends_limit_param(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/projects").mock(
            return_value=httpx.Response(200, json={"projects": []})
        )

        client.list_projects(limit=10)

    assert route.called
    assert "limit=10" in str(route.calls[0].request.url)


def test_list_projects_raises_on_401(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/projects").mock(
            return_value=httpx.Response(401, json={"error": "Invalid or missing API key"})
        )

        with pytest.raises(SpaceshipError) as exc_info:
            client.list_projects()

    assert exc_info.value.status_code == 401


def test_list_projects_sends_api_key_header(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/projects").mock(
            return_value=httpx.Response(200, json={"projects": []})
        )

        client.list_projects()

    request = route.calls[0].request
    assert request.headers.get("authorization") == f"Bearer {API_KEY}"

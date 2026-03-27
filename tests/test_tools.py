"""Tests for SpaceshipClient.list_tools."""

from __future__ import annotations

import pytest
import respx
import httpx

from spaceship_mcp.client import SpaceshipClient, SpaceshipError
from .conftest import BASE_URL, API_KEY, SAMPLE_TOOL


def test_list_tools_returns_tools(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/tools").mock(
            return_value=httpx.Response(200, json={"tools": [SAMPLE_TOOL]})
        )

        result = client.list_tools()

    assert result == [SAMPLE_TOOL]


def test_list_tools_returns_empty_list_when_no_tools(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/tools").mock(
            return_value=httpx.Response(200, json={"tools": []})
        )

        result = client.list_tools()

    assert result == []


def test_list_tools_raises_on_401(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/api/v1/tools").mock(
            return_value=httpx.Response(401, json={"error": "Invalid or missing API key"})
        )

        with pytest.raises(SpaceshipError) as exc_info:
            client.list_tools()

    assert exc_info.value.status_code == 401


def test_list_tools_sends_api_key_header(client: SpaceshipClient) -> None:
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/api/v1/tools").mock(
            return_value=httpx.Response(200, json={"tools": []})
        )

        client.list_tools()

    request = route.calls[0].request
    assert request.headers.get("authorization") == f"Bearer {API_KEY}"

"""Shared fixtures for spaceship-mcp tests."""

from __future__ import annotations

import pytest
import respx
import httpx

from spaceship_mcp.client import SpaceshipClient

BASE_URL = "https://spaceshipai.io"
API_KEY = "sk_live_test_key"


@pytest.fixture
def client() -> SpaceshipClient:
    return SpaceshipClient(api_key=API_KEY, base_url=BASE_URL)


# ---------------------------------------------------------------------------
# Sample response payloads
# ---------------------------------------------------------------------------

SAMPLE_PROJECT = {"id": 1, "name": "Alpha Project", "slug": "alpha-project"}

SAMPLE_TOOL = {
    "uuid": "tool-uuid-1",
    "name": "web_search",
    "description": "Search the web",
    "tool_type": "builtin",
}

SAMPLE_AGENT = {
    "id": 10,
    "uuid": "agent-uuid-1",
    "name": "Support Bot",
    "prompt": "You are a helpful support agent.",
    "framework": "langchain",
    "project_id": 1,
    "tools": [],
}

SAMPLE_RUN = {
    "execution_id": "exec-uuid-1",
    "agent_id": "agent-uuid-1",
    "status": "queued",
    "thread_id": "thread-uuid-1",
}

SAMPLE_EXECUTION = {
    "execution_id": "exec-uuid-1",
    "status": "completed",
    "started_at": "2026-03-26T10:00:00Z",
    "duration_ms": 1500,
    "event_count": 5,
}

SAMPLE_LOG = {
    "id": 1,
    "event_type": "start",
    "execution_id": "exec-uuid-1",
    "payload": {},
    "duration_ms": None,
    "created_at": "2026-03-26T10:00:00Z",
}

SAMPLE_ORCHESTRATION = {
    "id": 1,
    "uuid": "orch-uuid-1",
    "name": "Test Orchestration",
    "framework": "crewai",
    "status": "active",
    "project_id": 1,
    "orchestration_members": [],
}

SAMPLE_ORCH_RUN = {
    "execution_id": "orch-exec-uuid-1",
    "status": "queued",
}

SAMPLE_ORCH_EXECUTION = {
    "execution_id": "orch-exec-uuid-1",
    "status": "completed",
    "duration_ms": 3000,
    "error_message": None,
    "created_at": "2026-03-26T10:00:00Z",
    "updated_at": "2026-03-26T10:00:05Z",
}

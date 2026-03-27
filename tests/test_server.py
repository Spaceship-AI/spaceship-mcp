"""Tests for the test_agent MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from spaceship_mcp.server import test_agent as mcp_test_agent
from .conftest import SAMPLE_RUN


class FakeCtx:
    """Minimal stand-in for FastMCP Context."""

    def __init__(self) -> None:
        self.report_progress = AsyncMock()


# ---------------------------------------------------------------------------
# test_agent — happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_agent_returns_completed_on_success() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_agent.return_value = SAMPLE_RUN
    mock_client.get_executions.return_value = [
        {**SAMPLE_RUN, "status": "completed", "started_at": "2026-03-26T10:00:00Z",
         "duration_ms": 500, "event_count": 3}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await mcp_test_agent(ctx, agent_id="agent-uuid-1", prompt="Hello!")

    assert result["status"] == "completed"
    assert result["execution_id"] == SAMPLE_RUN["execution_id"]
    assert result["agent_id"] == "agent-uuid-1"


@pytest.mark.asyncio
async def test_test_agent_returns_error_status() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_agent.return_value = SAMPLE_RUN
    mock_client.get_executions.return_value = [
        {**SAMPLE_RUN, "status": "error"}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await mcp_test_agent(ctx, agent_id="agent-uuid-1", prompt="Hello!")

    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_test_agent_reports_progress_while_polling() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_agent.return_value = SAMPLE_RUN
    # First poll: still running; second poll: completed
    mock_client.get_executions.side_effect = [
        [{**SAMPLE_RUN, "status": "running"}],
        [{**SAMPLE_RUN, "status": "completed"}],
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await mcp_test_agent(ctx, agent_id="agent-uuid-1", prompt="Poll me")

    assert result["status"] == "completed"
    ctx.report_progress.assert_called_once()
    call_kwargs = ctx.report_progress.call_args.kwargs
    assert "running" in call_kwargs["message"]


@pytest.mark.asyncio
async def test_test_agent_polls_with_execution_id_filter() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_agent.return_value = SAMPLE_RUN
    mock_client.get_executions.return_value = [
        {**SAMPLE_RUN, "status": "completed"}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        await mcp_test_agent(ctx, agent_id="agent-uuid-1", prompt="Check filter")

    mock_client.get_executions.assert_called_with(
        agent_id="agent-uuid-1",
        execution_id=SAMPLE_RUN["execution_id"],
        limit=1,
    )


# ---------------------------------------------------------------------------
# test_agent — timeout path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_agent_returns_timeout_when_deadline_exceeded() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_agent.return_value = SAMPLE_RUN
    # Always running — never completes
    mock_client.get_executions.return_value = [
        {**SAMPLE_RUN, "status": "running"}
    ]

    # Advance monotonic time past the 15s deadline after the first sleep
    import time as _time
    _calls = []

    async def fake_sleep(_: float) -> None:
        _calls.append(1)

    original_monotonic = _time.monotonic
    call_count = 0

    def fast_monotonic() -> float:
        nonlocal call_count
        call_count += 1
        # First call sets the deadline, subsequent calls jump past it
        if call_count <= 1:
            return original_monotonic()
        return original_monotonic() + 20  # 20s > 15s deadline

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", side_effect=fake_sleep), \
         patch("spaceship_mcp.server.time.monotonic", side_effect=fast_monotonic):
        result = await mcp_test_agent(ctx, agent_id="agent-uuid-1", prompt="Slow agent")

    assert result["status"] == "timeout"
    assert result["execution_id"] == SAMPLE_RUN["execution_id"]


@pytest.mark.asyncio
async def test_test_agent_returns_timeout_when_executions_empty() -> None:
    """Handles edge case where get_executions returns [] (race condition)."""
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_agent.return_value = SAMPLE_RUN
    mock_client.get_executions.return_value = []

    import time as _time
    original_monotonic = _time.monotonic
    call_count = 0

    def fast_monotonic() -> float:
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            return original_monotonic()
        return original_monotonic() + 20

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock), \
         patch("spaceship_mcp.server.time.monotonic", side_effect=fast_monotonic):
        result = await mcp_test_agent(ctx, agent_id="agent-uuid-1", prompt="Ghost run")

    assert result["status"] == "timeout"

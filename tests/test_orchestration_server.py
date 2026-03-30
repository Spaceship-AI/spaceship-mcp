"""Tests for the test_orchestration MCP tool."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from spaceship_mcp.server import test_orchestration as mcp_test_orchestration
from .conftest import SAMPLE_ORCH_RUN, SAMPLE_ORCH_EXECUTION


class FakeCtx:
    """Minimal stand-in for FastMCP Context."""

    def __init__(self) -> None:
        self.report_progress = AsyncMock()


# ---------------------------------------------------------------------------
# test_orchestration — happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_orchestration_returns_completed_on_success() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    mock_client.get_orchestration_executions.return_value = [
        {**SAMPLE_ORCH_EXECUTION, "status": "completed"}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await mcp_test_orchestration(
            ctx, orchestration_id="orch-uuid-1", input_data={"query": "test"}
        )

    assert result["status"] == "completed"
    assert result["execution_id"] == SAMPLE_ORCH_RUN["execution_id"]
    assert result["orchestration_id"] == "orch-uuid-1"


@pytest.mark.asyncio
async def test_test_orchestration_returns_failed_status() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    mock_client.get_orchestration_executions.return_value = [
        {**SAMPLE_ORCH_EXECUTION, "status": "failed"}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await mcp_test_orchestration(ctx, orchestration_id="orch-uuid-1")

    assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_test_orchestration_returns_cancelled_status() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    mock_client.get_orchestration_executions.return_value = [
        {**SAMPLE_ORCH_EXECUTION, "status": "cancelled"}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await mcp_test_orchestration(ctx, orchestration_id="orch-uuid-1")

    assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_test_orchestration_reports_progress_while_polling() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    # First poll: still running; second poll: completed
    mock_client.get_orchestration_executions.side_effect = [
        [{**SAMPLE_ORCH_EXECUTION, "status": "running"}],
        [{**SAMPLE_ORCH_EXECUTION, "status": "completed"}],
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        result = await mcp_test_orchestration(ctx, orchestration_id="orch-uuid-1")

    assert result["status"] == "completed"
    ctx.report_progress.assert_called_once()
    call_kwargs = ctx.report_progress.call_args.kwargs
    assert "running" in call_kwargs["message"]


@pytest.mark.asyncio
async def test_test_orchestration_polls_with_execution_id_filter() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    mock_client.get_orchestration_executions.return_value = [
        {**SAMPLE_ORCH_EXECUTION, "status": "completed"}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        await mcp_test_orchestration(ctx, orchestration_id="orch-uuid-1")

    mock_client.get_orchestration_executions.assert_called_with(
        orchestration_id="orch-uuid-1",
        execution_id=SAMPLE_ORCH_RUN["execution_id"],
        limit=1,
    )


@pytest.mark.asyncio
async def test_test_orchestration_passes_empty_dict_when_no_input_data() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    mock_client.get_orchestration_executions.return_value = [
        {**SAMPLE_ORCH_EXECUTION, "status": "completed"}
    ]

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        await mcp_test_orchestration(ctx, orchestration_id="orch-uuid-1")

    mock_client.run_orchestration.assert_called_with(
        orchestration_id="orch-uuid-1",
        input_data={},
    )


# ---------------------------------------------------------------------------
# test_orchestration — timeout path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_orchestration_returns_timeout_when_deadline_exceeded() -> None:
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    mock_client.get_orchestration_executions.return_value = [
        {**SAMPLE_ORCH_EXECUTION, "status": "running"}
    ]

    import time as _time
    original_monotonic = _time.monotonic
    call_count = 0

    async def fake_sleep(_: float) -> None:
        pass

    def fast_monotonic() -> float:
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            return original_monotonic()
        return original_monotonic() + 20  # 20s > 15s deadline

    with patch("spaceship_mcp.server._client", return_value=mock_client), \
         patch("asyncio.sleep", side_effect=fake_sleep), \
         patch("spaceship_mcp.server.time.monotonic", side_effect=fast_monotonic):
        result = await mcp_test_orchestration(ctx, orchestration_id="orch-uuid-1")

    assert result["status"] == "timeout"
    assert result["execution_id"] == SAMPLE_ORCH_RUN["execution_id"]


@pytest.mark.asyncio
async def test_test_orchestration_returns_timeout_when_executions_empty() -> None:
    """Handles edge case where get_orchestration_executions returns [] (race condition)."""
    ctx = FakeCtx()
    mock_client = MagicMock()
    mock_client.run_orchestration.return_value = SAMPLE_ORCH_RUN
    mock_client.get_orchestration_executions.return_value = []

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
        result = await mcp_test_orchestration(ctx, orchestration_id="orch-uuid-1")

    assert result["status"] == "timeout"

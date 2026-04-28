"""Spaceship AI MCP server — 16 tools for full agent and orchestration lifecycle management."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .client import SpaceshipClient

mcp = FastMCP("Spaceship AI")


def _client() -> SpaceshipClient:
    api_key = os.environ.get("SPACESHIP_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "SPACESHIP_API_KEY environment variable is not set. "
            "Add it to your MCP server config."
        )
    base_url = os.environ.get("SPACESHIP_API_URL", SpaceshipClient.DEFAULT_BASE_URL)
    return SpaceshipClient(api_key=api_key, base_url=base_url)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@mcp.tool()
def list_projects(limit: int = 50) -> list[dict]:
    """List all projects in the authenticated organization.

    Use this to discover which projects exist before listing or creating agents.
    Returns each project's id, name, and slug.
    """
    return _client().list_projects(limit=limit)


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@mcp.tool()
def list_agents(
    project_id: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """List agents in the organization, optionally filtered by project.

    Pass ``project_id`` (UUID from list_projects) to scope the results to a
    single project. Each agent record includes its tools and configuration.
    """
    return _client().list_agents(project_id=project_id, limit=limit)


@mcp.tool()
def get_agent(agent_id: str) -> dict:
    """Get full details of a single agent including its tools and system prompt.

    Args:
        agent_id: The agent's UUID (from list_agents or create_agent).
    """
    return _client().get_agent(agent_id=agent_id)


@mcp.tool()
def create_agent(
    name: str,
    project_id: str,
    description: Optional[str] = None,
    prompt: Optional[str] = None,
    framework: str = "langchain",
    tools: Optional[list[str]] = None,
) -> dict:
    """Create a new agent.

    Pass ``description`` to let the server auto-generate a detailed system prompt
    (``scaffold_applied: true`` in the response). Pass ``prompt`` to set the system
    prompt directly. At least one of description or prompt is recommended.

    Args:
        name: Display name for the agent.
        project_id: UUID of the project this agent belongs to (from list_projects).
        description: Natural-language description — triggers server-side prompt scaffolding.
        prompt: Raw system prompt to use as-is (skips scaffolding).
        framework: Execution framework. Defaults to ``langchain``.
        tools: List of tool UUIDs to attach (from list_tools).
    """
    return _client().create_agent(
        name=name,
        project_id=project_id,
        description=description,
        prompt=prompt,
        framework=framework,
        tools=tools,
    )


@mcp.tool()
def update_agent(
    agent_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    prompt: Optional[str] = None,
    tools: Optional[list[str]] = None,
) -> dict:
    """Update an agent's name, prompt, or tools.

    Providing ``description`` re-runs server-side prompt scaffolding and overwrites
    the current system prompt. Providing ``prompt`` sets it directly. Providing
    ``tools`` replaces the full tool list.

    Args:
        agent_id: The agent's UUID.
        name: New display name.
        description: New description — triggers re-scaffolding.
        prompt: New raw system prompt.
        tools: Replacement list of tool UUIDs.
    """
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if prompt is not None:
        kwargs["prompt"] = prompt
    if tools is not None:
        kwargs["tools"] = tools
    return _client().update_agent(agent_id=agent_id, **kwargs)


@mcp.tool()
def delete_agent(agent_id: str) -> dict:
    """PERMANENTLY delete an agent and all its logs, memories, and threads.

    This action is irreversible. Double-check the agent_id before calling.

    Args:
        agent_id: The agent's UUID.
    """
    _client().delete_agent(agent_id=agent_id)
    return {"deleted": True, "agent_id": agent_id}


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


@mcp.tool()
def run_agent(
    agent_id: str,
    prompt: str,
    thread_id: Optional[str] = None,
    params: Optional[dict] = None,
) -> dict:
    """Start an asynchronous agent run and return immediately.

    Returns an ``execution_id`` — use ``get_run_status`` to poll for completion
    or ``get_run_logs`` to fetch the full output once done.

    Args:
        agent_id: The agent's UUID.
        prompt: The user message / task for the agent to execute.
        thread_id: Conversation thread UUID for memory continuity across runs.
        params: Optional extra parameters passed to the agent.
    """
    return _client().run_agent(
        agent_id=agent_id,
        prompt=prompt,
        params=params,
        thread_id=thread_id,
    )


@mcp.tool()
def get_run_status(agent_id: str, execution_id: str) -> dict:
    """Poll the status of a specific run.

    Status values: ``queued`` → ``running`` → ``completed`` | ``error`` |
    ``cancelled`` | ``paused`` (waiting for approval).

    Poll every 3-5 seconds. Most agents complete within 30-60 seconds.

    Args:
        agent_id: The agent's UUID.
        execution_id: The execution UUID returned by ``run_agent``.
    """
    client = _client()
    executions = client.get_executions(agent_id=agent_id, execution_id=execution_id, limit=1)
    if not executions:
        return {"execution_id": execution_id, "status": "not_found"}
    return executions[0]


@mcp.tool()
def get_run_logs(agent_id: str, execution_id: str) -> list[dict]:
    """Fetch the full event log for a completed run in chronological order.

    Returns every event (start, tool_call, memory_access, completion, error, …)
    so you can see exactly what the agent did and what it returned.

    Args:
        agent_id: The agent's UUID.
        execution_id: The execution UUID returned by ``run_agent``.
    """
    return _client().get_logs(
        agent_id=agent_id,
        execution_id=execution_id,
        order="asc",
    )


@mcp.tool()
def list_executions(agent_id: str, limit: int = 10) -> list[dict]:
    """List recent runs for an agent with their status and duration.

    Useful for reviewing run history or checking whether a previous run
    succeeded before starting a new one.

    Args:
        agent_id: The agent's UUID.
        limit: Number of runs to return (default 10, max 50).
    """
    return _client().get_executions(agent_id=agent_id, limit=limit)


# ---------------------------------------------------------------------------
# Orchestrations
# ---------------------------------------------------------------------------


@mcp.tool()
def list_orchestrations(
    project_id: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """List orchestrations in the organization, optionally filtered by project.

    Pass ``project_id`` (UUID from list_projects) to scope results to a single
    project. Each orchestration includes its members and their attached tools.
    """
    return _client().list_orchestrations(project_id=project_id, limit=limit)


@mcp.tool()
def get_orchestration(orchestration_id: str) -> dict:
    """Get full details of a single orchestration including its members and tools.

    Args:
        orchestration_id: The orchestration's UUID (from list_orchestrations).
    """
    return _client().get_orchestration(orchestration_id=orchestration_id)


@mcp.tool()
def run_orchestration(
    orchestration_id: str,
    input_data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """Start an asynchronous orchestration run and return immediately.

    Returns an ``execution_id`` — use ``test_orchestration`` to block until
    completion or poll ``/executions`` for status updates.

    Args:
        orchestration_id: The orchestration's UUID.
        input_data: Input data passed to the orchestration (e.g. ``{"query": "…"}``).
        params: Optional extra execution parameters.
    """
    return _client().run_orchestration(
        orchestration_id=orchestration_id,
        input_data=input_data,
        params=params,
    )


# ---------------------------------------------------------------------------
# Quick test (synchronous short-poll)
# ---------------------------------------------------------------------------


@mcp.tool()
async def test_agent(ctx, agent_id: str, prompt: str) -> dict:
    """Quick synchronous test of an agent with a 90-second timeout.

    Starts a run and polls every 2 seconds until it completes (or times out).
    Reports progress via MCP notifications while waiting. Returns the final
    status and execution_id. Use ``get_run_logs`` afterwards to see the output.

    For production usage, prefer ``run_agent`` + ``get_run_status`` (non-blocking).

    Args:
        agent_id: The agent's UUID.
        prompt: The test prompt to send.
    """
    client = _client()
    run = client.run_agent(agent_id=agent_id, prompt=prompt)
    execution_id = run["execution_id"]
    deadline = time.monotonic() + 90

    while time.monotonic() < deadline:
        executions = client.get_executions(
            agent_id=agent_id, execution_id=execution_id, limit=1
        )
        status = executions[0]["status"] if executions else "queued"

        if status in ("completed", "error", "cancelled"):
            return {
                "status": status,
                "execution_id": execution_id,
                "agent_id": agent_id,
            }

        remaining = int(deadline - time.monotonic())
        await ctx.report_progress(
            progress=0,
            total=1,
            message=f"Run {status}... ({remaining}s remaining)",
        )
        await asyncio.sleep(2)

    return {"status": "timeout", "execution_id": execution_id, "agent_id": agent_id}


@mcp.tool()
async def test_orchestration(
    ctx,
    orchestration_id: str,
    input_data: Optional[dict] = None,
) -> dict:
    """Quick synchronous test of an orchestration with a 90-second timeout.

    Starts a run and polls every 2 seconds until it completes (or times out).
    Reports progress via MCP notifications while waiting. Returns the final
    status and execution_id.

    Args:
        orchestration_id: The orchestration's UUID.
        input_data: Optional input data for the orchestration run.
    """
    client = _client()
    run = client.run_orchestration(
        orchestration_id=orchestration_id,
        input_data=input_data or {},
    )
    execution_id = run["execution_id"]
    deadline = time.monotonic() + 90

    while time.monotonic() < deadline:
        executions = client.get_orchestration_executions(
            orchestration_id=orchestration_id, execution_id=execution_id, limit=1
        )
        status = executions[0]["status"] if executions else "pending"

        if status in ("completed", "failed", "cancelled"):
            return {
                "status": status,
                "execution_id": execution_id,
                "orchestration_id": orchestration_id,
            }

        remaining = int(deadline - time.monotonic())
        await ctx.report_progress(
            progress=0,
            total=1,
            message=f"Run {status}... ({remaining}s remaining)",
        )
        await asyncio.sleep(2)

    return {"status": "timeout", "execution_id": execution_id, "orchestration_id": orchestration_id}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_tools() -> list[dict]:
    """List all tools available to attach to agents.

    Returns both built-in tools (shared across all orgs) and custom tools
    belonging to your organization. Use the ``uuid`` field when creating or
    updating agents with the ``tools`` parameter.
    """
    return _client().list_tools()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

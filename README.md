# spaceship-mcp

MCP server for [Spaceship AI](https://spaceshipai.io) — manage agents from Claude Code, Cursor, and any other MCP client.

## Quick start

### Claude Code / Claude Desktop

Add to your `.mcp.json` (project-level) or `claude_desktop_config.json`:

```json
{
  "spaceship": {
    "command": "uvx",
    "args": ["spaceship-mcp"],
    "env": {
      "SPACESHIP_API_KEY": "sk_live_...",
      "SPACESHIP_API_URL": "https://spaceshipai.io"
    }
  }
}
```

Get your API key from the Spaceship AI dashboard under **Settings → API Keys**.

### Local development (pointing at localhost)

```json
{
  "spaceship": {
    "command": "uvx",
    "args": ["spaceship-mcp"],
    "env": {
      "SPACESHIP_API_KEY": "sk_live_...",
      "SPACESHIP_API_URL": "http://localhost:3000"
    }
  }
}
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPACESHIP_API_KEY` | Yes | — | Your Spaceship API key (`sk_live_...`) |
| `SPACESHIP_API_URL` | No | `https://spaceshipai.io` | Override for local dev or staging |

## Tools

| Tool | What it does |
|------|-------------|
| `list_projects` | List all projects in your org |
| `list_agents` | List agents, optionally filtered by project |
| `get_agent` | Get full details of a single agent |
| `create_agent` | Create an agent (pass `description` for auto-generated system prompt) |
| `update_agent` | Update name, prompt, or tools; re-scaffold with `description` |
| `delete_agent` | **Permanently** delete an agent (irreversible) |
| `run_agent` | Start an async run; returns `execution_id` for polling |
| `get_run_status` | Poll run status: queued → running → completed / error / cancelled / paused |
| `get_run_logs` | Fetch full chronological event log for a completed run |
| `list_executions` | List recent runs for an agent with status and duration |
| `test_agent` | Quick sync test (15s timeout) — start a run and wait for it to finish |
| `list_tools` | List tools available to attach to agents |

## Typical workflow in Claude Code

```
list_projects
  → list_agents project_id=1
    → create_agent name="Support Bot" project_id=1 description="Handles customer refund requests"
      → run_agent agent_id="..." prompt="Process refund for order #1234"
        → get_run_status agent_id="..." execution_id="..."
          → get_run_logs agent_id="..." execution_id="..."
```

Or use `test_agent` to run and wait in one step:

```
test_agent agent_id="..." prompt="Hello, can you help me?"
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

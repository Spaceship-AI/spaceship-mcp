```ansi
       ███████╗██████╗  █████╗  ██████╗███████╗███████╗██╗  ██╗██╗██████╗    █████╗ ██╗
       ██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔════╝██║  ██║██║██╔══██╗  ██╔══██╗██║
       ███████╗██████╔╝███████║██║     █████╗  ███████╗███████║██║██████╔╝  ███████║██║
       ╚════██║██╔═══╝ ██╔══██║██║     ██╔══╝  ╚════██║██╔══██║██║██╔═══╝   ██╔══██║██║
       ███████║██║     ██║  ██║╚██████╗███████╗███████║██║  ██║██║██║       ██║  ██║██║
       ╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝       ╚═╝  ╚═╝╚═╝
```


# Spaceship AI MCP Server

MCP server for [Spaceship AI](https://spaceshipai.io) — build, run, and manage AI agents directly from Claude Code, Cursor, VS Code, and Windsurf.

## Quick start

Don't want to manually configure your MCP server?

Run `spaceshipai@latest init` to set everything up automatically with one command:

```bash
npx spaceshipai@latest init
```

This works with Claude Code, Cursor, VS Code, and Windsurf. It will authenticate via your browser, create a Spaceship API key for you, and configure your editor automatically.

## Manual installation

If you prefer to configure manually, add the following to your IDE's MCP config file.

**Claude Code** — run in your terminal:

```bash
claude mcp add --scope user --transport stdio spaceship --env SPACESHIP_API_KEY=sk_live_... -- uvx spaceship-mcp
```

Or add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "spaceship": {
      "command": "uvx",
      "args": ["spaceship-mcp"],
      "env": {
        "SPACESHIP_API_KEY": "sk_live_..."
      }
    }
  }
}
```

**Cursor** — add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "spaceship": {
      "command": "uvx",
      "args": ["spaceship-mcp"],
      "env": {
        "SPACESHIP_API_KEY": "sk_live_..."
      }
    }
  }
}
```

**VS Code** — add to `~/.vscode/mcp.json`:

```json
{
  "servers": {
    "spaceship": {
      "command": "uvx",
      "args": ["spaceship-mcp"],
      "env": {
        "SPACESHIP_API_KEY": "sk_live_..."
      }
    }
  }
}
```

**Windsurf** — add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "spaceship": {
      "command": "uvx",
      "args": ["spaceship-mcp"],
      "env": {
        "SPACESHIP_API_KEY": "sk_live_..."
      }
    }
  }
}
```

Get your API key from [spaceshipai.io](https://spaceshipai.io) under **Settings → API Keys**.

## Tools

### Projects

| Tool | Description |
|------|-------------|
| `list_projects` | List all projects in your organization |

### Agents

| Tool | Description |
|------|-------------|
| `list_agents` | List agents, optionally filtered by project |
| `get_agent` | Get full details of a single agent including its system prompt and tools |
| `create_agent` | Create an agent — pass `description` for auto-generated system prompt |
| `update_agent` | Update name, prompt, or tools; re-scaffold by passing a new `description` |
| `delete_agent` | **Permanently** delete an agent and all its logs, memories, and threads |

### Running agents

| Tool | Description |
|------|-------------|
| `run_agent` | Start an async run; returns `execution_id` for polling |
| `get_run_status` | Poll status: `queued` → `running` → `completed` / `error` / `cancelled` |
| `get_run_logs` | Fetch the full chronological event log for a completed run |
| `list_executions` | List recent runs for an agent with status and duration |
| `test_agent` | Quick sync test — runs an agent and waits up to 15s for the result |

### Orchestrations

| Tool | Description |
|------|-------------|
| `list_orchestrations` | List orchestrations, optionally filtered by project |
| `get_orchestration` | Get full details of an orchestration including its members and tools |
| `run_orchestration` | Start an async orchestration run; returns `execution_id` |
| `test_orchestration` | Quick sync test — runs an orchestration and waits up to 15s for the result |

### Tools

| Tool | Description |
|------|-------------|
| `list_tools` | List built-in and custom tools available to attach to agents |

## Example prompts

Once installed, you can talk to your agents naturally in any supported IDE:

```
List my projects, then show me all agents in the "production" project.
```

```
Create an agent called "Support Bot" in project 12 that handles customer refund requests.
```

```
Run the "Data Processor" agent with the prompt "Summarize last week's sales data".
```

```
Check the status of execution abc-123 for agent xyz-456, then show me the logs.
```

```
Test the "Email Classifier" agent with "Is this email spam: win a free iPhone now!"
```

```
List my orchestrations in the "production" project, then run the "Data Pipeline" orchestration.
```

```
Test the "Research Team" orchestration with input {"topic": "AI safety"} and show me the result.
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SPACESHIP_API_KEY` | Yes | — | Your API key (`sk_live_...`) |
| `SPACESHIP_API_URL` | No | `https://spaceshipai.io` | Override for local dev or staging |

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT

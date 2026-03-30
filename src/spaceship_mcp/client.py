"""SpaceshipClient — thin httpx wrapper around the Spaceship AI V1 API."""

from __future__ import annotations

import httpx


class SpaceshipError(Exception):
    """Raised for non-2xx responses from the Spaceship API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class SpaceshipClient:
    """Synchronous HTTP client for the Spaceship AI V1 API.

    Args:
        api_key: Spaceship API key (``sk_live_...``).
        base_url: Base URL for the API. Defaults to the production server.
    """

    DEFAULT_BASE_URL = "https://spaceshipai.io"

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        resp = self._client.get(path, params=params)
        self._raise_for_status(resp)
        return resp.json()

    def _post(self, path: str, json: dict | None = None) -> dict | list:
        resp = self._client.post(path, json=json or {})
        self._raise_for_status(resp)
        return resp.json()

    def _patch(self, path: str, json: dict | None = None) -> dict | list:
        resp = self._client.patch(path, json=json or {})
        self._raise_for_status(resp)
        return resp.json()

    def _delete(self, path: str) -> None:
        resp = self._client.delete(path)
        self._raise_for_status(resp)

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.is_success:
            return
        try:
            detail = resp.json().get("error", resp.text)
        except Exception:
            detail = resp.text
        raise SpaceshipError(
            f"Spaceship API error {resp.status_code}: {detail}",
            status_code=resp.status_code,
        )

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def list_projects(self, limit: int = 50) -> list[dict]:
        """Return projects for the authenticated organization."""
        data = self._get("/api/v1/projects", params={"limit": limit})
        return data["projects"]

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    def list_agents(
        self,
        project_id: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Return agents, optionally filtered by project."""
        params: dict = {"limit": limit}
        if project_id is not None:
            params["project_id"] = project_id
        data = self._get("/api/v1/agents", params=params)
        return data["agents"]

    def get_agent(self, agent_id: str) -> dict:
        """Return full details of a single agent."""
        data = self._get(f"/api/v1/agents/{agent_id}")
        return data["agent"]

    def create_agent(
        self,
        name: str,
        project_id: int,
        framework: str = "langchain",
        description: str | None = None,
        prompt: str | None = None,
        tools: list[str] | None = None,
    ) -> dict:
        """Create a new agent.

        Pass ``description`` to trigger server-side prompt scaffolding.
        Pass ``prompt`` to set the system prompt directly (skips scaffolding).
        """
        payload: dict = {"name": name, "project_id": project_id, "framework": framework}
        if description is not None:
            payload["description"] = description
        if prompt is not None:
            payload["prompt"] = prompt
        if tools is not None:
            payload["tools"] = tools
        data = self._post("/api/v1/agents", json=payload)
        return data

    def update_agent(self, agent_id: str, **kwargs) -> dict:
        """Update agent fields. Providing ``description`` re-runs scaffolding."""
        data = self._patch(f"/api/v1/agents/{agent_id}", json=kwargs)
        return data

    def delete_agent(self, agent_id: str) -> None:
        """Permanently delete an agent."""
        self._delete(f"/api/v1/agents/{agent_id}")

    # ------------------------------------------------------------------
    # Orchestrations
    # ------------------------------------------------------------------

    def list_orchestrations(
        self,
        project_id: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Return orchestrations, optionally filtered by project."""
        params: dict = {"limit": limit}
        if project_id is not None:
            params["project_id"] = project_id
        data = self._get("/api/v1/orchestrations", params=params)
        return data["orchestrations"]

    def get_orchestration(self, orchestration_id: str) -> dict:
        """Return full details of a single orchestration including its members."""
        data = self._get(f"/api/v1/orchestrations/{orchestration_id}")
        return data["orchestration"]

    def run_orchestration(
        self,
        orchestration_id: str,
        input_data: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Enqueue an orchestration run. Returns ``{execution_id, status}``."""
        payload: dict = {}
        if input_data is not None:
            payload["input_data"] = input_data
        if params is not None:
            payload["params"] = params
        return self._post(f"/api/v1/orchestrations/{orchestration_id}/run", json=payload)

    def get_orchestration_executions(
        self,
        orchestration_id: str,
        execution_id: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Return execution summaries for an orchestration."""
        p: dict = {"limit": limit}
        if execution_id is not None:
            p["execution_id"] = execution_id
        data = self._get(f"/api/v1/orchestrations/{orchestration_id}/executions", params=p)
        return data["executions"]

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------

    def run_agent(
        self,
        agent_id: str,
        prompt: str,
        params: dict | None = None,
        thread_id: str | None = None,
    ) -> dict:
        """Enqueue an agent run. Returns ``{execution_id, agent_id, status, thread_id}``."""
        payload: dict = {"prompt": prompt}
        if params is not None:
            payload["params"] = params
        if thread_id is not None:
            payload["thread_id"] = thread_id
        data = self._post(f"/api/v1/agents/{agent_id}/run", json=payload)
        return data

    # ------------------------------------------------------------------
    # Executions
    # ------------------------------------------------------------------

    def get_executions(
        self,
        agent_id: str,
        limit: int = 10,
        execution_id: str | None = None,
    ) -> list[dict]:
        """Return execution summaries for an agent."""
        params: dict = {"limit": limit}
        if execution_id is not None:
            params["execution_id"] = execution_id
        data = self._get(f"/api/v1/agents/{agent_id}/executions", params=params)
        return data["executions"]

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def get_logs(
        self,
        agent_id: str,
        execution_id: str,
        order: str = "asc",
    ) -> list[dict]:
        """Return detailed logs for a specific run in chronological order."""
        data = self._get(
            f"/api/v1/agents/{agent_id}/logs",
            params={"execution_id": execution_id, "order": order},
        )
        return data["logs"]

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def list_tools(self) -> list[dict]:
        """Return tools available to the authenticated org (builtin + custom)."""
        data = self._get("/api/v1/tools")
        return data["tools"]

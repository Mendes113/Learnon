"""
Education workflow tools for Archon MCP Server.

These tools wrap the backend education API to start/advance/get/list
education processes that orchestrate pedagogical workflows.
"""

import json
import logging
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from mcp.server.fastmcp import Context, FastMCP

from src.mcp_server.utils.error_handling import MCPErrorFormatter
from src.mcp_server.utils.timeout_config import get_default_timeout
from src.server.config.service_discovery import get_api_url

logger = logging.getLogger(__name__)


def register_education_tools(mcp: FastMCP):
    """Register education tools with the MCP server."""

    @mcp.tool()
    async def start_education_process(ctx: Context, user_id: str, topic: str, process_type: str = "fundamental_explanation") -> str:
        """
        Start a new education process for a user and topic.

        Args:
            user_id: Identifier of the learner/user
            topic: Topic to learn (e.g., "funções em Python")
            process_type: One of [fundamental_explanation|guided_practice|assessment]

        Returns: JSON with process_id and initial step
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, "/api/education/processes"),
                    json={"user_id": user_id, "topic": topic, "process_type": process_type},
                )
                if response.status_code >= 200 and response.status_code < 300:
                    return json.dumps(response.json())
                else:
                    return MCPErrorFormatter.from_http_error(response, "start education process")
        except httpx.RequestError as e:
            return MCPErrorFormatter.from_exception(e, "start education process")
        except Exception as e:
            logger.error(f"Error starting education process: {e}", exc_info=True)
            return MCPErrorFormatter.from_exception(e, "start education process")

    @mcp.tool()
    async def advance_education_process(ctx: Context, process_id: str, user_input: Optional[str] = None) -> str:
        """
        Advance the current step for a process with optional user input.
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, f"/api/education/processes/{process_id}/advance"),
                    json={"user_input": user_input},
                )
                if response.status_code >= 200 and response.status_code < 300:
                    return json.dumps(response.json())
                else:
                    return MCPErrorFormatter.from_http_error(response, "advance education process")
        except httpx.RequestError as e:
            return MCPErrorFormatter.from_exception(e, "advance education process")
        except Exception as e:
            logger.error(f"Error advancing education process: {e}", exc_info=True)
            return MCPErrorFormatter.from_exception(e, "advance education process")

    @mcp.tool()
    async def get_education_process(ctx: Context, process_id: str) -> str:
        """Get the current state of an education process."""
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(urljoin(api_url, f"/api/education/processes/{process_id}"))
                if response.status_code >= 200 and response.status_code < 300:
                    return json.dumps(response.json())
                else:
                    return MCPErrorFormatter.from_http_error(response, "get education process")
        except httpx.RequestError as e:
            return MCPErrorFormatter.from_exception(e, "get education process")
        except Exception as e:
            logger.error(f"Error getting education process: {e}", exc_info=True)
            return MCPErrorFormatter.from_exception(e, "get education process")

    @mcp.tool()
    async def list_education_processes(ctx: Context, user_id: Optional[str] = None) -> str:
        """List active education processes, optionally filtered by user_id."""
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()
            params: dict[str, Any] = {}
            if user_id:
                params["user_id"] = user_id
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(urljoin(api_url, "/api/education/processes"), params=params)
                if response.status_code >= 200 and response.status_code < 300:
                    return json.dumps(response.json())
                else:
                    return MCPErrorFormatter.from_http_error(response, "list education processes")
        except httpx.RequestError as e:
            return MCPErrorFormatter.from_exception(e, "list education processes")
        except Exception as e:
            logger.error(f"Error listing education processes: {e}", exc_info=True)
            return MCPErrorFormatter.from_exception(e, "list education processes")

    @mcp.tool()
    async def suggest_education_next_step(
        ctx: Context,
        process_id: str,
        score: Optional[float] = None,
        apply: bool = False,
    ) -> str:
        """
        Suggest the next pedagogical step based on performance and optionally apply it.

        Args:
            process_id: Education process id
            score: Optional last evaluation score (0..1). If omitted, uses session history.
            apply: If true, inserts the suggested step into the plan.
        """
        try:
            api_url = get_api_url()
            timeout = get_default_timeout()
            payload: dict[str, Any] = {"apply": apply}
            if score is not None:
                payload["score"] = score
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    urljoin(api_url, f"/api/education/processes/{process_id}/suggest-next-step"),
                    json=payload,
                )
                if response.status_code >= 200 and response.status_code < 300:
                    return json.dumps(response.json())
                else:
                    return MCPErrorFormatter.from_http_error(response, "suggest next step")
        except httpx.RequestError as e:
            return MCPErrorFormatter.from_exception(e, "suggest next step")
        except Exception as e:
            logger.error(f"Error suggesting next step: {e}", exc_info=True)
            return MCPErrorFormatter.from_exception(e, "suggest next step")

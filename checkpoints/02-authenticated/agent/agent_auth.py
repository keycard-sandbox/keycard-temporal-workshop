"""Completed agent authentication wiring (Exercise 02)."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import httpx2
import keycard
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

from llm import build_model
from mcp_client import MCP_URL


def build_agent(http_client, system_prompt, tool_guard) -> Agent:
    return Agent(
        build_model(api_key="managed-by-keycard", http_client=http_client),
        system_prompt=system_prompt,
        toolsets=[
            MCPToolset(MCP_URL, auth=keycard.ZoneTokenAuth(),
                       process_tool_call=tool_guard).filtered(
                lambda ctx, tool: tool.name != "record_expense_review"
            )
        ],
    )


def model_http_client():
    return httpx2.AsyncClient(auth=keycard.LLMVaultAuth())


def request_identity(token):
    return keycard.identity(token)


def open_expense_session():
    return Client(StreamableHttpTransport(MCP_URL, auth=keycard.ZoneTokenAuth()))


def login_available():
    return True

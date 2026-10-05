"""Exercise 01: a raw model key and unauthenticated MCP access."""

import os
from contextlib import nullcontext
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import Client
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

load_dotenv(Path(__file__).resolve().parent / ".env")

from llm import build_model
from mcp_client import MCP_URL


def build_agent(http_client, system_prompt, tool_guard) -> Agent:
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "LLM_API_KEY is not set. Configure model access before starting Expense Desk."
        )
    return Agent(
        build_model(api_key=api_key, http_client=http_client),
        system_prompt=system_prompt,
        toolsets=[MCPToolset(MCP_URL, process_tool_call=tool_guard).filtered(
            lambda ctx, tool: tool.name != "record_expense_review"
        )],
    )


def request_identity(token):
    return nullcontext()


def open_expense_session():
    return Client(MCP_URL)


def login_available():
    return False


def model_http_client():
    return nullcontext(None)

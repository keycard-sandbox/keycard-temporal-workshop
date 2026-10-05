"""Per-request Keycard credentials, with an optional user delegation anchor."""

from contextvars import ContextVar
from collections.abc import AsyncGenerator, Iterator
from contextlib import contextmanager
import json
import os
from pathlib import Path

import httpx2
from dotenv import load_dotenv
from llm import credential_header
from keycardai.oauth import (
    AsyncClient,
    BasicAuth,
    ClientConfig,
    TokenType,
)

load_dotenv(Path(__file__).resolve().parent / ".env")

ISSUER = os.environ.get("KEYCARD_ISSUER", "").rstrip("/")
CLIENT_ID = os.environ.get("KEYCARD_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("KEYCARD_CLIENT_SECRET", "")
if not (ISSUER and CLIENT_ID and CLIENT_SECRET):
    raise SystemExit("Set KEYCARD_ISSUER, KEYCARD_CLIENT_ID, and KEYCARD_CLIENT_SECRET in agent/.env.")

MCP_RESOURCE = os.environ.get("MCP_URL", "http://localhost:8100/mcp")  # identifier = server URL, byte-for-byte
LLM_RESOURCE = os.environ.get("LLM_RESOURCE", "").strip()
AGENT_RESOURCE = os.environ.get("AGENT_RESOURCE", "")

# keycard.cloud's edge rejects default Python user-agents.
_CONFIG = ClientConfig(user_agent="expense-agent")
# SDK initialization is lazy and locked. Retain discovered metadata, never minted tokens.
_oauth_client = AsyncClient(ISSUER, auth=BasicAuth(CLIENT_ID, CLIENT_SECRET), config=_CONFIG)

# Browser sign-in token: the anchor every per-call exchange starts from.
_user_token: ContextVar[str | None] = ContextVar("expense_user_token", default=None)


@contextmanager
def identity(token: str | None) -> Iterator[None]:
    marker = _user_token.set(token)
    try:
        yield
    finally:
        _user_token.reset(marker)


async def mint(resource: str, scope: str | None = None) -> str:
    subject_token = _user_token.get()
    async with _oauth_client as client:
        if subject_token is None:
            response = await client.client_credentials_grant(resource=resource, scope=scope)
        else:
            response = await client.exchange_token(
                subject_token=subject_token,
                subject_token_type=TokenType.ACCESS_TOKEN,
                resource=resource,
                scope=scope,
            )
    return response.access_token


TOOL_SCOPES = {
    "get_keycard_identity": "expense:read",
    "submit_expense": "expense:write",
    "record_expense_review": "expense:approve",
    "list_expenses": "expense:read",
    "get_expense": "expense:read",
    "audit_expense": "expense:read",
    "approve_expense": "expense:approve",
    "reject_expense": "expense:approve",
    "settle_expense": "expense:settle",
}


def _tool_scope(request: "httpx2.Request") -> str | None:
    """The scope for a tools/call request; session traffic mints scope-less."""
    try:
        body = json.loads(request.content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(body, dict) or body.get("method") != "tools/call":
        return None
    return TOOL_SCOPES.get((body.get("params") or {}).get("name"))


class ZoneTokenAuth(httpx2.Auth):
    async def async_auth_flow(self, request: httpx2.Request) -> AsyncGenerator[httpx2.Request, httpx2.Response]:
        request.headers["Authorization"] = f"Bearer {await mint(MCP_RESOURCE, _tool_scope(request))}"
        yield request


class LLMVaultAuth(httpx2.Auth):
    async def async_auth_flow(self, request: httpx2.Request) -> AsyncGenerator[httpx2.Request, httpx2.Response]:
        if not LLM_RESOURCE:
            raise ValueError("Set LLM_RESOURCE to the model API resource registered in Keycard.")
        name, value = credential_header(await mint(LLM_RESOURCE))
        request.headers[name] = value
        yield request

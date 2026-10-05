"""Keycard wiring for the Expense MCP server (Exercise 02).

`auth` verifies that every inbound request carries a zone token issued for
this server. `ledger_token` exchanges that verified token, per call, for a
ledger credential holding the one scope the operation needs. Plain functions,
no Temporal: the interceptor seam can wrap these same calls later.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from keycardai.mcp.server.auth import AuthProvider, ClientSecret
from keycardai.oauth import BasicAuth, Client, ClientConfig, TokenType
from keycardai.oauth.exceptions import OAuthError
from mcp.server.mcpserver import Context

load_dotenv(Path(__file__).resolve().parent / ".env")

ISSUER = os.environ.get("KEYCARD_ISSUER", "").rstrip("/")
CLIENT_ID = os.environ.get("MCP_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("MCP_CLIENT_SECRET", "")
if not (ISSUER and CLIENT_ID and CLIENT_SECRET):
    raise SystemExit("Set KEYCARD_ISSUER, MCP_CLIENT_ID, and MCP_CLIENT_SECRET in mcp-server/.env (instructor-provided).")

MCP_RESOURCE = "http://localhost:8100/mcp"  # registered identifier, byte-for-byte: localhost, not 127.0.0.1
LEDGER_RESOURCE = "urn:ledger:api"

# keycard.cloud's edge rejects default Python user-agents.
_CONFIG = ClientConfig(user_agent="expense-mcp-server")
# SDK initialization is thread-safe; reuse discovery, exchange afresh for every call.
_oauth_client = Client(ISSUER, auth=BasicAuth(CLIENT_ID, CLIENT_SECRET), config=_CONFIG)

ExchangeError = OAuthError

auth = AuthProvider(
    zone_url=ISSUER,
    mcp_server_name="Expense MCP Server",
    mcp_server_url=MCP_RESOURCE,
    audience=MCP_RESOURCE,
    application_credential=ClientSecret((CLIENT_ID, CLIENT_SECRET)),
)


def scope_for(method: str, path: str) -> str:
    """One ledger scope per operation: least privilege, per call."""
    if method == "GET":
        return "ledger:read"
    if path.endswith(("/approve", "/reject", "/review")):
        return "ledger:approve"
    if path.endswith("/settle"):
        return "ledger:settle"
    return "ledger:write"


def ledger_token(ctx: Context, scope: str) -> str:
    """Exchange the verified caller's token (RFC 8693) for a ledger credential."""
    subject = ctx.request_context.request.user.access_token
    with _oauth_client as client:
        response = client.exchange_token(
            subject_token=subject,
            subject_token_type=TokenType.ACCESS_TOKEN,
            resource=LEDGER_RESOURCE,
            scope=scope + " openid email",
        )
    return response.access_token

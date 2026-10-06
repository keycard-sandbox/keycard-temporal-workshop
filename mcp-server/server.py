"""Expense MCP tools backed by the ledger API."""

import os
import atexit
from typing import Literal
from urllib.parse import urlencode

import httpx
import mcp_auth
import uvicorn
from mcp.server.mcpserver import Context, MCPServer

LEDGER_URL = os.environ.get("LEDGER_URL", "http://localhost:8300").rstrip("/")
ledger_http = httpx.Client(timeout=10.0, limits=httpx.Limits(max_connections=30, max_keepalive_connections=10))
atexit.register(ledger_http.close)

mcp = MCPServer("Expense MCP Server")


def _call(method: str, path: str, headers: dict, json: dict | None = None) -> dict | list:
    """Parsed body on success, {"error", "status", "detail"} on any failure."""
    try:
        resp = ledger_http.request(method, f"{LEDGER_URL}{path}", headers=headers, json=json)
    except httpx.HTTPError as exc:
        return {"error": "ledger_unreachable", "detail": str(exc)}
    if resp.is_success:
        return resp.json()
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    return {"error": "ledger_error", "status": resp.status_code, "detail": detail}


def _ledger(method: str, path: str, user: str, ctx: Context, json: dict | None = None) -> dict | list:
    return mcp_auth.ledger(method, path, user, ctx, json, call=_call)


@mcp.tool()
def submit_expense(ctx: Context, user: str, amount_cents: int, memo: str = "") -> dict:
    """Submit a new expense request. Amounts are in USD cents."""
    return _ledger("POST", "/requests", user, ctx, {"amount_cents": amount_cents, "memo": memo})


@mcp.tool()
def get_keycard_identity(ctx: Context, user: str = "") -> dict:
    """Read the current identity and approval limit. Only verified=true establishes expense ownership."""
    return _ledger("GET", "/me", user, ctx)


@mcp.tool()
def list_expenses(ctx: Context, user: str, status: str = "", mine: bool = False) -> list | dict:
    """List expenses by status. Use mine=false unless the user explicitly asks for their own expenses. mine=true requires verified identity."""
    query = urlencode({"status": status, "mine": str(mine).lower()})
    return _ledger("GET", f"/requests?{query}", user, ctx)


def _decision(action: str, ctx: Context, user: str, request_id: str,
              reason: str, expected_updated_at: str | None) -> dict:
    result = _ledger("POST", f"/requests/{request_id}/{action}", user, ctx,
                     {"reason": reason, "expected_updated_at": expected_updated_at})
    if result.get("status") == 409:
        # A conflict is not this caller's success. Read again; never repeat the write.
        current = _ledger("GET", f"/requests/{request_id}", user, ctx)
        if isinstance(current, dict) and current.get("id") == request_id and not current.get("error"):
            result["current_expense"] = current
    return result


@mcp.tool()
def get_expense(ctx: Context, user: str, request_id: str) -> dict:
    """Look up one expense request by id, e.g. EXP007."""
    return _ledger("GET", f"/requests/{request_id}", user, ctx)


@mcp.tool()
def approve_expense(ctx: Context, user: str, request_id: str, expected_updated_at: str, reason: str = "") -> dict:
    """Approve an expense. First read it with get_expense; copy its exact updated_at into expected_updated_at."""
    return _decision("approve", ctx, user, request_id, reason, expected_updated_at)


@mcp.tool()
def reject_expense(ctx: Context, user: str, request_id: str, expected_updated_at: str, reason: str = "") -> dict:
    """Reject an expense. First read it with get_expense; copy its exact updated_at into expected_updated_at."""
    return _decision("reject", ctx, user, request_id, reason, expected_updated_at)


@mcp.tool()
def settle_expense(ctx: Context, user: str, request_id: str) -> dict:
    """Settle (pay) an approved expense request. Records a payment on the ledger."""
    return _ledger("POST", f"/requests/{request_id}/settle", user, ctx)


@mcp.tool()
def audit_expense(ctx: Context, user: str, request_id: str) -> list | dict:
    """Read the append-only audit trail for one expense request."""
    return _ledger("GET", f"/requests/{request_id}/audit", user, ctx)


@mcp.tool()
def record_expense_review(ctx: Context, user: str, request_id: str, outcome: Literal["human_review"],
                          message: str, expected_updated_at: str) -> dict:
    """Autonomous reviewer only: record a human referral."""
    return _ledger("POST", f"/requests/{request_id}/review", user, ctx, {
        "outcome": outcome, "message": message, "expected_updated_at": expected_updated_at,
    })


def build_app():
    return mcp_auth.build_app(mcp)


if __name__ == "__main__":
    uvicorn.run(build_app(), host="127.0.0.1", port=8100, log_level="warning")

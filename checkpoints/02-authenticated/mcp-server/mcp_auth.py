"""Completed MCP authentication wiring (Exercise 02)."""

import keycard
from mcp.server.mcpserver import Context


def ledger(method: str, path: str, user: str, ctx: Context, json: dict | None = None, *, call) -> dict | list:
    """Identity comes from the verified token; the supplied `user` is ignored."""
    try:
        token = keycard.ledger_token(ctx, keycard.scope_for(method, path))
    except keycard.ExchangeError as exc:
        return {"error": "exchange_denied", "detail": str(exc)}
    return call(method, path, {"Authorization": f"Bearer {token}"}, json)


def build_app(mcp):
    return keycard.auth.app(mcp)

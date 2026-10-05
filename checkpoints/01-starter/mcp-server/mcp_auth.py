"""Exercise 01: trust a supplied name and forward the shared Ledger key."""

import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.mcpserver import Context

load_dotenv(Path(__file__).resolve().parent / ".env")


def ledger(method: str, path: str, user: str, ctx: Context, json: dict | None = None, *, call) -> dict | list:
    # Deliberately trusts the caller-supplied name.
    return call(method, path, {"X-API-Key": os.environ.get("LEDGER_API_KEY", "").strip(), "X-User": user}, json)


def build_app(mcp):
    if not os.environ.get("LEDGER_API_KEY", "").strip():
        raise SystemExit(f"Set LEDGER_API_KEY in {Path(__file__).resolve().parent / '.env'}.")
    return mcp.streamable_http_app()

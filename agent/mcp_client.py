"""Tiny MCP client over streamable-http.

Direct callers use this client; chat uses Pydantic AI tools at the same MCP_URL.
"""

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from temporalio.exceptions import ApplicationError

from mcp import Client

MCP_URL = os.environ.get("MCP_URL", "http://localhost:8100/mcp")


def open_session():
    """Async context manager yielding a connected MCP client."""
    return Client(MCP_URL)


async def call(session, name: str, **args):
    """Call a tool and return its parsed result (dict or list).

    Both branches fire: tools returning plain `dict` arrive as text-only JSON,
    while `list | dict` tools arrive wrapped as structured {"result": [...]}.
    """
    result = await session.call_tool(name, args or None)
    if result.structured_content is not None:
        sc = result.structured_content
        if isinstance(sc, dict) and set(sc) == {"result"}:
            return sc["result"]
        return sc
    text = "".join(c.text for c in result.content if getattr(c, "type", "") == "text")
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return text


def activity_failure(error: Exception, operation: str) -> "ApplicationError":
    """Allowlist diagnostics: exception bodies, URLs and chained causes may contain credentials."""
    from temporalio.exceptions import ApplicationError
    from keycardai.oauth.exceptions import OAuthError, PERMANENT_ERROR_CODES

    status = getattr(error, "status_code", None)
    response = getattr(error, "response", None)
    if status is None and response is not None:
        status = getattr(response, "status_code", None)
    code = getattr(error, "error", None)
    permanent_codes = PERMANENT_ERROR_CODES
    known_codes = permanent_codes | {"server_error", "temporarily_unavailable",
        "invalid_grant", "invalid_scope", "invalid_target", "unauthorized_client",
        "interaction_required", "consent_required"}
    details = {}
    if isinstance(status, int) and 100 <= status <= 599:
        details["http_status"] = status
    if isinstance(code, str) and code in known_codes:
        details["oauth_code"] = code
    non_retryable = isinstance(error, (ValueError, TypeError, KeyError))
    kind = "ReviewDependencyFailure"
    if non_retryable:
        kind = "ReviewConfigurationFailure"
    if isinstance(status, int) and 400 <= status < 500 and status not in {408, 409, 429}:
        non_retryable = True
        kind = "ReviewRequestRejected"
    if isinstance(error, (TimeoutError, ConnectionError)):
        kind = "ReviewTransportFailure"
    if isinstance(error, OAuthError):
        non_retryable = not error.retryable
        kind = "ReviewAuthorizationFailure" if non_retryable else "ReviewDependencyFailure"
    if isinstance(error, ApplicationError):
        non_retryable = error.non_retryable
        if error.type in {"ReviewRequestRejected", "ReviewDependencyFailure"}:
            kind = error.type
    return ApplicationError(f"{operation} failed ({kind}).", details,
                            type=kind, non_retryable=non_retryable)


def require_result(result, operation: str) -> None:
    from temporalio.exceptions import ApplicationError

    if isinstance(result, dict) and result.get("error"):
        status = result.get("status")
        permanent = isinstance(status, int) and 400 <= status < 500 and status not in {408, 409, 429}
        error = ApplicationError(operation, type="ReviewRequestRejected" if permanent else "ReviewDependencyFailure",
                                 non_retryable=permanent)
        error.status_code = status
        raise error

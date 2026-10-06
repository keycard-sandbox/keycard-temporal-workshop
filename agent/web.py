"""Expense Desk's local, single-worker browser server. No durable execution here."""

import asyncio
import json
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic_ai.usage import UsageLimits
from pydantic_ai.messages import ModelResponse, TextPart

import chat
from mcp_client import call

ORIGIN = os.environ.get("EXPENSE_DESK_ORIGIN", "http://localhost:8400").rstrip("/")
CALLBACK = ORIGIN + "/callback"
COOKIE = "expense_desk"
TTL = 3600
STATUSES = {
    "",
    "pending",
    "approved",
    "rejected",
    "cancelled",
    "paid",
}
LABELS = {
    "get_keycard_identity": "Checking your account",
    "submit_expense": "Filing expense",
    "list_expenses": "Reading expenses",
    "get_expense": "Reading expense",
    "audit_expense": "Reading Activity",
    "record_expense_review": "Recording review",
    "approve_expense": "Approving expense",
    "reject_expense": "Rejecting expense",
    "settle_expense": "Settling expense",
}


@dataclass
class Session:
    expires: float = field(default_factory=lambda: time.time() + TTL)
    # Retain the sign-in anchor, never downstream tokens or model credentials.
    token: str | None = None
    identity: str = ""
    subject: str = ""
    mode: str = "signed_out"
    history: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    flow: object = None
    flow_expires: float = 0
    busy: bool = False


sessions: dict[str, Session] = {}


def set_session(response: Response, session: Session) -> None:
    for sid, item in list(sessions.items()):
        if item.expires <= time.time():
            sessions.pop(sid, None)
    if len(sessions) >= 200:
        raise RuntimeError("Session capacity reached")
    sid = secrets.token_urlsafe(32)
    sessions[sid] = session
    response.set_cookie(
        COOKIE,
        sid,
        httponly=True,
        secure=ORIGIN.startswith("https://"),
        samesite="lax",
        max_age=TTL,
        path="/",
    )


def session_for(request: Request) -> Session | None:
    session = sessions.get(request.cookies.get(COOKIE, ""))
    if session and session.expires > time.time():
        return session
    sessions.pop(request.cookies.get(COOKIE, ""), None)
    return None


def error(message, status=400):
    return JSONResponse({"error": message}, status_code=status)


def active_session(request: Request) -> Session | None:
    session = session_for(request)
    return session if session and session.mode != "signed_out" else None


async def me(request):
    existing = session_for(request)
    session = existing or (
        Session() if chat.login_available() else Session(mode="starter", identity="")
    )
    response = JSONResponse(
        {
            "mode": session.mode,
            "identity": session.identity,
            "login": chat.login_available(),
            "messages": session.messages,
        }
    )
    if not existing:
        set_session(response, session)
    return response


async def session_action(request):
    old = session_for(request)
    if not old:
        return error("Your session ended. Reload Expense Desk to continue.", 401)
    if old.busy:
        return error("Wait for the agent to finish before signing out or signing in.", 409)
    action = request.path_params["action"]
    if action not in {"signout", "login", "agent"}:
        return error("Unknown session action.")
    if action in {"login", "agent"} and not chat.login_available():
        return error("Sign-in is not available.")
    response = JSONResponse({"ok": True})
    fresh = Session(mode="application" if action == "agent" else "signed_out",
                    identity="Expense Desk Agent" if action == "agent" else "")
    if action == "login":
        import keycard
        from keycardai.oauth.pkce import begin_authorization

        try:
            if not keycard.AGENT_RESOURCE:
                return error("Sign-in is not configured. Contact your administrator.")
            async with keycard.AsyncClient(keycard.ISSUER, config=keycard._CONFIG) as client:
                metadata = await client.discover_server_metadata()
            fresh.flow = await begin_authorization(
                client_id=keycard.CLIENT_ID,
                redirect_uri=CALLBACK,
                metadata=metadata,
                resources=[keycard.AGENT_RESOURCE, keycard.MCP_RESOURCE],
                scopes=["openid", "email", "profile"],
            )
            fresh.flow_expires = time.time() + 600
            response = JSONResponse({"url": fresh.flow.url})
        except Exception:
            return error(
                "Sign-in could not start. Try again or contact your administrator.",
                502,
            )
    sessions.pop(request.cookies.get(COOKIE, ""), None)
    set_session(response, fresh)
    return response


async def callback(request):
    session = session_for(request)
    if not session or not session.flow or session.flow_expires < time.time():
        return RedirectResponse("/?signin=expired", status_code=303)
    flow = session.flow
    session.flow = None  # A failed callback must not leave a reusable login attempt.
    import keycard
    from keycardai.oauth.pkce import complete_authorization
    from keycardai.oauth.utils.jwt import get_claims

    try:
        response = await complete_authorization(
            callback_params=request.query_params,
            state=flow.state,
            code_verifier=flow.code_verifier,
            client_id=keycard.CLIENT_ID,
            client_secret=keycard.CLIENT_SECRET,
            redirect_uri=CALLBACK,
            issuer=keycard.ISSUER,
        )
        # Claims from the trusted token endpoint are used only to check the exchange anchor.
        claims = get_claims(response.access_token)
        audience = claims.get("aud")
        first_audience = audience[0] if isinstance(audience, list) and audience else audience
        if first_audience != keycard.AGENT_RESOURCE:
            raise ValueError("Login token is not addressed to this agent")
        async with keycard.AsyncClient(keycard.ISSUER, config=keycard._CONFIG) as client:
            user = await client.userinfo(response.access_token)
        email = user.claims.get("email")
        if user.sub != claims.get("sub") or not isinstance(email, str) or "@" not in email:
            raise ValueError("UserInfo must return the signed-in subject and email")
        fresh = Session(
            token=response.access_token,
            identity=email,
            subject=user.sub,
            mode="user",
            expires=min(
                time.time() + TTL,
                claims.get("exp", time.time() + (response.expires_in or TTL)),
            ),
        )
    except Exception:
        return RedirectResponse("/?signin=failed", status_code=303)
    sessions.pop(request.cookies.get(COOKIE, ""), None)
    redirect = RedirectResponse("/", status_code=303)
    set_session(redirect, fresh)
    return redirect


def expense_labels(row, session):
    if session.mode == "starter":
        return {**row, "submitter_label": row.get("submitter"),
                "approver_label": row.get("approver"), "unverified_submitter": False}
    return {**row, "unverified_submitter": not row.get("submitter_verified", False)}


async def expenses(request):
    request.state.timings = {}
    async def invoke(mcp, name, **args):
        started = time.perf_counter()
        try:
            return await call(mcp, name, user="", **args)
        finally:
            request.state.timings[name] = (time.perf_counter() - started) * 1000

    session = active_session(request)
    if not session:
        return error("Your session ended. Sign in to continue.", 401)
    status = request.query_params.get("status", "")
    ownership = request.query_params.get("ownership", "mine" if session.mode == "user" else "all")
    rid = request.path_params.get("rid")
    if ownership not in {"mine", "all"} or status not in STATUSES or (rid and not re.fullmatch(r"(?:EXP[0-9]{3,19}|exp-[a-zA-Z0-9-]{1,80})", rid)):
        return error("Choose a valid expense or status.")
    if ownership == "mine" and session.mode != "user":
        return error("Sign in to view My expenses.", 403)
    try:
        with chat.request_identity(session.token):
            started = time.perf_counter()
            async with asyncio.timeout(20), chat.open_expense_session() as mcp:
                request.state.timings["mcp_connect"] = (time.perf_counter() - started) * 1000
                if rid:
                    async with asyncio.TaskGroup() as reads:
                        row_task = reads.create_task(invoke(mcp, "get_expense", request_id=rid))
                        trail_task = reads.create_task(invoke(mcp, "audit_expense", request_id=rid))
                    row, trail = row_task.result(), trail_task.result()
                    if not isinstance(row, dict) or row.get("error") or not isinstance(trail, list):
                        return error(
                            "Could not read this expense and its Activity. Access may be denied; try Refresh.",
                            502,
                        )
                    activity = [
                        {**event,
                         "actor_label": event.get("actor") if session.mode == "starter" else event.get("actor_label", "Identity unavailable")}
                        for event in trail
                    ]
                    return JSONResponse({"expense": expense_labels(row, session), "activity": activity})
                rows = await invoke(mcp, "list_expenses", status=status,
                                  mine=ownership == "mine")
                if not isinstance(rows, list):
                    return error(
                        "Could not read expenses. Access may be denied; try Refresh.",
                        502,
                    )
                return JSONResponse([expense_labels(row, session) for row in rows])
    except Exception:
        return error(
            "Could not reach expenses. Try Refresh, or contact your administrator if the problem continues.",
            502,
        )


async def conversation(request):
    session = active_session(request)
    if not session:
        return error("Your session ended. Sign in to continue.", 401)
    try:
        body = await request.json()
        prompt = body.get("message", "").strip()
        selected_id = body.get("selected_id")
        if selected_id is not None and not re.fullmatch(
            r"(?:EXP[0-9]{3,19}|exp-[a-zA-Z0-9-]{1,80})", str(selected_id)
        ):
            return error("Choose a valid expense.")
        if not prompt or len(prompt) > 4000:
            return error("Write a message of 1 to 4,000 characters.")
    except (ValueError, AttributeError):
        return error("That message could not be read.")
    if session.busy:
        return error("The agent is still working on your last message.", 409)
    if len(session.messages) >= 80:
        return error("This conversation is full. Start a new session to continue.", 409)
    session.busy = True
    return StreamingResponse(
        chat_events(session, prompt, selected_id), media_type="application/x-ndjson"
    )


def event_line(kind, **data):
    return json.dumps({"type": kind, **data}) + "\n"


def refusal_text(tool_name, detail):
    """Explain confirmed business refusals without exposing service diagnostics."""
    detail = detail if isinstance(detail, str) else ""
    if "own expense" in detail.lower() or "self-approval" in detail.lower():
        return "You cannot approve or reject your own expense. Ask another reviewer."
    if detail.startswith("Amount exceeds your approval limit"):
        amounts = re.findall(r"\$[\d,]+\.\d{2}", detail)
        if len(amounts) == 2:
            return f"The expense amount ({amounts[0]}) exceeds your approval limit ({amounts[1]})."
        return "This expense exceeds your approval limit."
    action = {"approve_expense": "approve this expense", "reject_expense": "reject this expense",
              "submit_expense": "submit this expense", "settle_expense": "pay this expense"}.get(
                  tool_name, "complete this request")
    return f"You do not have permission to {action}."


async def chat_events(session, prompt, selected_id):
    tool_failed = False
    conflicts: list[str] = []
    refusals: list[str] = []
    session.messages.append({"role": "user", "text": prompt})
    try:
        yield event_line("progress", text="Thinking")
        with chat.request_identity(session.token):
            async with chat.model_http_client() as http_client, asyncio.timeout(180):
                agent = chat.build_agent(http_client)
                async with (
                    agent,
                    chat.run_events(
                        agent, prompt,
                        message_history=session.history,
                        instructions=(
                            f"Selected expense: {selected_id or 'none'}. "
                            "Read the selected expense before answering questions about it."
                        ),
                        usage_limits=UsageLimits(request_limit=12, tool_calls_limit=20),
                    ) as events,
                ):
                    async for event in events:
                        if event.event_kind == "function_tool_call":
                            label = LABELS.get(event.part.tool_name, "Working on your request")
                            yield event_line("progress", text=label)
                        elif event.event_kind == "function_tool_result":
                            part = event.part
                            failed = False
                            if part.part_kind == "retry-prompt":
                                failed = True
                            elif part.outcome != "success":
                                failed = True
                            elif isinstance(part.content, dict):
                                failed = bool(part.content.get("error"))
                                if part.content.get("status") == 403:
                                    failed = True
                                    refusals.append(refusal_text(part.tool_name, part.content.get("detail")))
                                elif part.content.get("error") == "name_required":
                                    # Missing input is a clarification, not an uncertain expense write.
                                    failed = False
                            tool_failed |= failed
                            if (
                                part.tool_name in {"approve_expense", "reject_expense"}
                                and isinstance(part.content, dict)
                                and part.content.get("status") == 409
                            ):
                                current = part.content.get("current_expense")
                                if isinstance(current, dict) and current.get("id") and current.get("status"):
                                    status = current["status"]
                                    explanation = (
                                        f"Your decision conflicted with another action. "
                                        f"{current['id']} is currently {status}."
                                    )
                                    if current.get("approver"):
                                        explanation += f" Decided by: {current.get('approver_label') or 'Identity unavailable'}."
                                    conflicts.append(explanation)
                                else:
                                    conflicts.append(
                                        "Your decision conflicted with another action. "
                                        "The current state is unknown. "
                                        "Refresh the expense and its Activity."
                                    )
                            if failed:
                                yield event_line(
                                    "progress",
                                    text="Checking the result",
                                )
                            request_id = None
                            if (
                                part.tool_name == "submit_expense"
                                and not failed
                                and isinstance(part.content, dict)
                            ):
                                request_id = part.content.get("id")
                            yield event_line("refresh", request_id=request_id)
                        elif event.event_kind == "agent_run_result":
                            session.history = event.result.all_messages()
                            text = chat.response_text(event.result)
                            if conflicts or refusals:
                                text = " ".join(dict.fromkeys(conflicts + refusals))
                            elif tool_failed:
                                text = (
                                    "I could not confirm that all requested actions succeeded. "
                                    "Check the expense and its Activity before trying again."
                                )
                            if text != event.result.output:
                                # Replace only the final answer; preserve tool calls/results for the next turn.
                                for message in reversed(session.history):
                                    if isinstance(message, ModelResponse):
                                        message.parts = [TextPart(text)]
                                        break
                            session.messages.append({"role": "assistant", "text": text})
                            yield event_line("result", text=text)
        yield event_line("refresh")
    except Exception:
        # A transport failure may follow a successful write; do not retry it here.
        text = "The request stopped before I could confirm the result. Check the expense and its Activity before trying again."
        session.messages.append({"role": "assistant", "text": text})
        yield event_line("error", text=text)
        yield event_line("refresh")
    finally:
        session.busy = False


app = Starlette(
    routes=[
        Route("/api/session", me),
        Route("/api/session/{action}", session_action, methods=["POST"]),
        Route("/callback", callback),
        Route("/api/expenses", expenses),
        Route("/api/expenses/{rid}", expenses, methods=["GET"]),
        Route("/api/chat", conversation, methods=["POST"]),
        Mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True)),
    ]
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[urlparse(ORIGIN).hostname])


async def browser_boundary(request: Request, call_next):
    started = time.perf_counter()
    origin = urlparse(ORIGIN)
    if (request.method in {"GET", "HEAD"} and origin.hostname in {"localhost", "127.0.0.1"}
            and request.url.hostname in {"localhost", "127.0.0.1"}
            and request.url.hostname != origin.hostname
            and request.url.port == (origin.port or 8400)):
        return RedirectResponse(ORIGIN + request.url.path +
                                ("?" + request.url.query if request.url.query else ""), status_code=307)
    if request.method in {"POST", "PATCH"} and request.headers.get("origin") != ORIGIN:
        return error("This request must come from Expense Desk.", 403)
    try:
        if int(request.headers.get("content-length", "0")) > 16384:
            return error("That message is too long.", 413)
    except ValueError:
        return error("That request could not be read.")
    response = await call_next(request)
    timings = getattr(request.state, "timings", {})
    timings["app"] = (time.perf_counter() - started) * 1000
    response.headers["Server-Timing"] = ", ".join(f"{name};dur={duration:.1f}" for name, duration in timings.items())
    response.headers.update(
        {
            "Cache-Control": "public, max-age=0, must-revalidate" if request.url.path in {
                "/app.js", "/styles.css", "/vendor/markdown-it.min.js"
            } else "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        }
    )
    return response


app.add_middleware(BaseHTTPMiddleware, dispatch=browser_boundary)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=urlparse(ORIGIN).port or 8400, access_log=False)

"""Expense chat over MCP tools."""

import asyncio
from pathlib import Path
from contextlib import asynccontextmanager, suppress

import agent_auth
from agent_auth import login_available, model_http_client, open_expense_session, request_identity
from pydantic_ai import Agent, AgentRunResultEvent
from pydantic_ai.messages import ModelResponse, TextPart

from mcp_client import call as mcp_call

def system_prompt() -> str:
    """Load only the behavioral contract for the installed authentication wiring."""
    directory = Path(__file__).parent
    if login_available():
        return (directory / "chat-authenticated.md").read_text() + "\n" + (directory / "expense-policy.md").read_text()
    return (directory / "chat-starter.md").read_text()


SYSTEM = system_prompt()


def response_text(result) -> str:
    """Keep completed response parts separated when the provider returns several."""
    for message in reversed(result.new_messages()):
        if isinstance(message, ModelResponse):
            parts = [part.content.strip() for part in message.parts
                     if isinstance(part, TextPart) and part.content.strip()]
            final_parts = [part.content.strip() for part in message.parts
                           if isinstance(part, TextPart) and part.content.strip()
                           and (part.provider_details or {}).get("phase") == "final_answer"]
            if final_parts or parts:
                return "\n\n".join(dict.fromkeys(final_parts or parts))
    return result.output


async def approve_as_application(arguments):
    """Approve a newly submitted expense autonomously with application credentials."""
    with request_identity(None):
        async with open_expense_session() as mcp:
            return await mcp_call(mcp, "approve_expense", **arguments)


def decision_guard():
    conflicts = {}
    amounts = {}
    submitted = set()
    lock = asyncio.Lock()

    async def process(ctx, call_tool, name, arguments):
        if name == "submit_expense" and not login_available() and not arguments.get("user", "").strip():
            return {"error": "name_required", "detail": "Ask for a name and optional email before submitting; email may be skipped."}
        if name == "get_keycard_identity":
            result = await call_tool(name, arguments)
            if isinstance(result, dict) and result.get("verified") is False:
                return {"verified": False}
            return result
        if name not in {"approve_expense", "reject_expense"}:
            result = await call_tool(name, arguments)
            if isinstance(result, dict) and not result.get("error") and result.get("id"):
                if name == "get_expense":
                    amounts[(ctx.run_id, result["id"])] = result.get("amount_cents")
                elif name == "submit_expense":
                    submitted.add((ctx.run_id, result["id"]))
            return result
        async with lock:
            key = (ctx.run_id, arguments.get("request_id"))
            if key in conflicts:
                return conflicts[key]
            amount = amounts.get(key)
            automatic = (name == "approve_expense" and login_available()
                         and key in submitted and amount is not None and amount < 5000)
            result = await (approve_as_application(arguments) if automatic else call_tool(name, arguments))
            if isinstance(result, dict) and result.get("status") == 409:
                conflicts[key] = result
            return result

    return process


def build_agent(http_client) -> Agent:
    return agent_auth.build_agent(http_client, SYSTEM, decision_guard())


@asynccontextmanager
async def run_events(agent, prompt, **kwargs):
    """Complete model text intact; keep tool progress live and cancellable."""
    queue = asyncio.Queue()

    async def produce():
        try:
            async with agent.iter(prompt, **kwargs) as run:
                async for node in run:
                    if Agent.is_call_tools_node(node):
                        async with node.stream(run.ctx) as events:
                            async for event in events:
                                await queue.put(event)
                await queue.put(AgentRunResultEvent(run.result))
        finally:
            await queue.put(None)

    async def consume():
        while (event := await queue.get()) is not None:
            yield event
        await task  # Propagate model/tool failures, not just the end of events.

    task = asyncio.create_task(produce())
    try:
        yield consume()
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

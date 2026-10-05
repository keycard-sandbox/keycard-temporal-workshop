"""One autonomous review step. Every external call runs inside a Temporal activity."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits
from temporalio import activity
from temporalio.exceptions import ApplicationError

import chat
from llm import build_model
from mcp_client import call, activity_failure, require_result

POLICY = (Path(__file__).parent / "expense-policy.md").read_text()


class Assessment(BaseModel):
    outcome: Literal["approve", "human_review"]
    message: str = Field(min_length=1, max_length=500)


async def assess(row: dict) -> Assessment:
    async with chat.model_http_client() as http_client:
        reviewer = Agent(
            build_model(api_key="managed-by-keycard", http_client=http_client),
            output_type=Assessment,
            instructions=POLICY
            + "\nReturn a concise reason, or a human referral. "
            "Input amount_cents is the Amount in USD cents. Assess only the Memo's business purpose; "
            "identity and amount authorization are enforced by code. Do not ask for the Submitter, "
            "Activity, receipts, or extra fields. Travel to a client office is a clear business purpose. "
            "If the business purpose is unclear, refer to a human. Give one plain sentence. "
            "Do not claim an action already happened.",
        )
        result = await reviewer.run(
            json.dumps({"amount_cents": row["amount_cents"], "memo": row["memo"]}),
            usage_limits=UsageLimits(request_limit=3),
        )
        return result.output


async def review_once(request_id: str) -> str:
    with chat.request_identity(None):
        async with chat.open_expense_session() as mcp:
            row = await call(mcp, "get_expense", user="autonomous-review", request_id=request_id)
            require_result(row, "Read expense")
            if not isinstance(row, dict):
                raise RuntimeError("Could not read expense")
            if row["status"] != "pending":
                return "done"
            # A pending expense with a referral waits for a human decision.
            if row.get("review"):
                return "waiting"
            if row["amount_cents"] >= 5000:
                result = Assessment(
                    outcome="human_review",
                    message=(
                        "This expense needs another person's approval."
                        if row["amount_cents"] <= 10000
                        else "This expense exceeds the $100 employee limit and needs a finance administrator's review."
                    ),
                )
            else:
                result = await assess(row)
            if result.outcome == "approve":
                outcome = await call(
                    mcp,
                    "approve_expense",
                    user="autonomous-review",
                    request_id=request_id,
                    reason=result.message,
                    expected_updated_at=row["updated_at"],
                )
                if (
                    isinstance(outcome, dict)
                    and outcome.get("status") == "approved"
                    and not outcome.get("error")
                ):
                    return "done"
            else:
                outcome = await call(
                    mcp,
                    "record_expense_review",
                    user="autonomous-review",
                    request_id=request_id,
                    outcome=result.outcome,
                    message=result.message,
                    expected_updated_at=row["updated_at"],
                )
                if isinstance(outcome, dict) and outcome.get("review") and not outcome.get("error"):
                    return "waiting"
            if isinstance(outcome, dict) and outcome.get("status") == 409:
                current = outcome.get("current_expense")
                if current is None:
                    current = await call(mcp, "get_expense", user="autonomous-review", request_id=request_id)
                if not isinstance(current, dict) or current.get("error"):
                    raise RuntimeError("Could not reread the conflicting expense")
                return "waiting" if current["status"] == "pending" else "done"
            if isinstance(outcome, dict) and outcome.get("status") == 403:
                note = await call(
                    mcp,
                    "record_expense_review",
                    user="autonomous-review",
                    request_id=request_id,
                    outcome="human_review",
                    message="The agent could not approve this expense. It needs a human reviewer.",
                    expected_updated_at=row["updated_at"],
                )
                if isinstance(note, dict) and note.get("review") and not note.get("error"):
                    return "waiting"
                require_result(note, "Record human referral")
            require_result(outcome, "Review action")
            raise RuntimeError("Review action did not succeed")


@activity.defn
async def review_expense(request_id: str) -> str:
    try:
        return await review_once(request_id)
    except Exception as error:
        failure = activity_failure(error, "Expense review")
    # Raise outside except so SDK exception context cannot enter workflow history.
    raise failure

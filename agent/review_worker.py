"""Run one shared review worker for the workshop after user delegation is introduced."""

import asyncio
import os
from datetime import datetime, timezone

from temporalio import activity
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import ApplicationError, WorkflowAlreadyStartedError
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

import chat
from mcp_client import call, activity_failure, require_result
from review import review_expense
from review_workflows import ExpenseReview, ReviewMonitor

ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")
QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "expense-desk-review")
ACTIVITY_CONCURRENCY = 2
# httpx2's runtime type checker installs import hooks. Reuse that package in the
# sandbox; workflow code itself stays sandboxed and performs no external I/O.
WORKFLOW_RUNNER = SandboxedWorkflowRunner(
    restrictions=SandboxRestrictions.default.with_passthrough_modules("beartype")
)


@activity.defn
async def discover_expenses(since: str) -> None:
    try:
        with chat.request_identity(None):
            async with chat.open_expense_session() as mcp:
                rows = await call(mcp, "list_expenses", user="autonomous-review", status="pending")
        require_result(rows, "Discover expenses")
        if not isinstance(rows, list):
            raise RuntimeError("Could not read expenses")
        client = activity.client()
        cutoff = datetime.fromisoformat(since)
        for row in rows:
            if datetime.fromisoformat(row["created_at"]) < cutoff:
                continue
            try:
                await client.start_workflow(
                    ExpenseReview.run,
                    row["id"],
                    id=f"expense-review-{row['id']}",
                    task_queue=activity.info().task_queue,
                    id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                )
            except WorkflowAlreadyStartedError:
                pass
        return
    except Exception as error:
        failure = activity_failure(error, "Review discovery")
    # Raise outside except so SDK exception context cannot enter workflow history.
    raise failure


def build_worker(client):
    return Worker(
        client,
        task_queue=QUEUE,
        workflows=[ExpenseReview, ReviewMonitor],
        activities=[review_expense, discover_expenses],
        max_concurrent_activities=ACTIVITY_CONCURRENCY,
        workflow_runner=WORKFLOW_RUNNER,
    )


async def main():
    if not chat.login_available():
        raise SystemExit(
            "Automatic review is not available in this configuration."
        )
    client = await Client.connect(ADDRESS, namespace=NAMESPACE)
    async with build_worker(client):
        try:
            await client.start_workflow(
                ReviewMonitor.run,
                datetime.now(timezone.utc).isoformat(),
                id="expense-desk-review-monitor",
                task_queue=QUEUE,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        except WorkflowAlreadyStartedError:
            pass
        print(
            "Automatic review is running. Enrollment starts at the monitor workflow's original activation time."
        )
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

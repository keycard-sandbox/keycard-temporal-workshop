"""Durable automatic review; workflow inputs and results contain no credentials."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

OPTIONS = {
    "start_to_close_timeout": timedelta(minutes=3),
    "retry_policy": RetryPolicy(
        initial_interval=timedelta(seconds=5), maximum_interval=timedelta(minutes=1)
    ),
}


@workflow.defn
class ExpenseReview:
    @workflow.run
    async def run(self, request_id: str) -> None:
        for _ in range(100):
            state = await workflow.execute_activity("review_expense", request_id, **OPTIONS)
            if state == "done":
                return
            await workflow.sleep(60)
        # Bound workflow history while preserving the expense being reviewed.
        workflow.continue_as_new(request_id)


@workflow.defn
class ReviewMonitor:
    @workflow.run
    async def run(self, since: str) -> None:
        for _ in range(100):
            await workflow.execute_activity("discover_expenses", since, **OPTIONS)
            await workflow.sleep(30)
        workflow.continue_as_new(since)

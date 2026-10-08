"""Simulated payment: credentials stay inside activity execution."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from typing import TypedDict
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

from keycardai.temporal import KeycardInterceptor, access, grant

# get_claims is demo-only inspection; the package needs no passthrough from consumers.
with workflow.unsafe.imports_passed_through():
    from keycardai.oauth.utils.jwt import get_claims
    from keycardai.oauth.server import ClientSecret

RESOURCE = os.environ["LEDGER_RESOURCE"]
TASK_QUEUE = os.environ.get("TEMPORAL_TASK_QUEUE", "keycard-temporal-demo")
ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")


class DebitResult(TypedDict):
    debited: int


class SettledResult(TypedDict):
    settled: int


class SettlementResult(TypedDict):
    debit: DebitResult
    settle: SettledResult


def _assert_aud(token: str) -> None:
    aud = get_claims(token).get("aud")
    if isinstance(aud, str):
        aud = [aud]
    if not isinstance(aud, list) or RESOURCE not in aud:
        # Non-retryable: retrying can't fix a misconfigured resource, and the retry policy has no attempt limit.
        raise ApplicationError("Minted credential has the wrong audience", non_retryable=True)


@grant(RESOURCE)
@activity.defn
async def debit_ledger(amount: int) -> DebitResult:
    _assert_aud(access().access_token)
    activity.logger.info("debited %s with a token minted for this call", amount)
    return {"debited": amount}


@grant(RESOURCE)
@activity.defn
async def mark_settled(amount: int) -> SettledResult:
    _assert_aud(access().access_token)
    activity.logger.info("settled %s with a token minted for this call", amount)
    return {"settled": amount}


@workflow.defn
class SettlementWorkflow:
    @workflow.run
    async def run(self, amount: int) -> SettlementResult:
        opts = dict(
            start_to_close_timeout=timedelta(minutes=2),
            # Unlimited attempts: a transient failure never ends the demo. Permanent
            # Keycard errors still fail fast because the SDK marks them non-retryable.
            retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=2),
                                     non_retryable_error_types=["GrantConfigurationError"]),
        )
        debit = await workflow.execute_activity(debit_ledger, amount, **opts)
        # A durable timer gives the room a restart window after debit completion is recorded.
        await workflow.sleep(timedelta(seconds=60))
        settle = await workflow.execute_activity(mark_settled, amount, **opts)
        return {"debit": debit, "settle": settle}


async def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "worker"
    client = await Client.connect(ADDRESS, namespace=NAMESPACE)
    if cmd == "worker":
        client_id = os.environ.get("WORKER_KEYCARD_CLIENT_ID", "")
        client_secret = os.environ.get("WORKER_KEYCARD_CLIENT_SECRET", "")
        if not (client_id and client_secret):
            raise SystemExit("Set WORKER_KEYCARD_CLIENT_ID and WORKER_KEYCARD_CLIENT_SECRET in temporal/.env (instructor-provided).")
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[SettlementWorkflow],
            activities=[debit_ledger, mark_settled],
            interceptors=[
                # Use the Temporal worker identity explicitly, separate from agent credentials.
                KeycardInterceptor(
                    zone_url=os.environ["KEYCARD_ISSUER"],
                    credential=ClientSecret((client_id, client_secret)),
                )
            ],
        )
        print(f"worker PID {os.getpid()} on {TASK_QUEUE}", flush=True)
        await worker.run()
    elif cmd == "run":
        wf_id = f"settlement-{uuid.uuid4().hex[:8]}"
        handle = await client.start_workflow(
            SettlementWorkflow.run, 4200, id=wf_id, task_queue=TASK_QUEUE
        )
        print(f"workflow id: {wf_id}", flush=True)
        print(await handle.result())
        print(f"now: uv run --locked --env-file .env check_history.py {wf_id}")
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

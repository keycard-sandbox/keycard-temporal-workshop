<!-- Generated from docs/attendee/ex04.md. Edit the source, then rebuild. -->
# Exercise 04: durable execution (37–52 minutes)

You'll stop a worker after Temporal records a completed activity, then restart it to finish the same workflow. The activities obtain real Keycard credentials but simulate payment; they don't move money.

## Before you start

This exercise is part of the full workshop. If your instructor has not supplied a running Temporal service and you are rehearsing locally, follow [local Temporal setup](06-temporal-local.md) before this exercise.

For local use, use `TEMPORAL_ADDRESS=localhost:7233`, `TEMPORAL_NAMESPACE=default`, and [Temporal UI](http://localhost:8233). Each isolated server uses `TEMPORAL_TASK_QUEUE=keycard-temporal-demo`. In Instruqt, preserve the supplied `.env`: address `127.0.0.1:7233`, namespace `default`, and queue `keycard-temporal-demo`; open the Temporal UI tab. Keep the same configuration when you restart the worker so it resumes the original workflow. The Temporal worker is the Python process you start in this exercise. It polls that queue for work and runs the workflow and its activities, while Temporal records progress independently.

The worker uses the instructor-supplied **Temporal Worker** application, which has access to the Ledger API resource. Its credentials are in `temporal/.env` as `WORKER_KEYCARD_CLIENT_ID` and `WORKER_KEYCARD_CLIENT_SECRET`. The worker acts as itself and doesn't need your browser sign-in.

For individual restart rehearsals on a shared Temporal service, set `TEMPORAL_TASK_QUEUE=keycard-temporal-<githubhandle>` using your own GitHub handle and confirm that only your worker polls it. Another worker on the same queue can finish the workflow while yours is stopped. If the session uses one shared queue, follow the instructor’s single-worker demonstration instead.

During the interruption, stop only the worker. Leave the Temporal service running.

## Start one workflow

1. In the worker terminal:

   ```sh
   cd "<package-path>/temporal"
   uv run --locked --env-file .env demo.py worker
   ```

   Replace `<package-path>` with the absolute package folder. Leave this worker running so it can run activities.
2. In a second terminal:

   ```sh
   cd "<package-path>/temporal"
   uv run --locked --env-file .env demo.py run
   ```
3. Copy the workflow ID and find it in [Temporal UI](http://localhost:8233), in the `default` namespace.

## Stop and restart the worker

1. Wait for the debit activity's **ActivityTaskCompleted** event and **TimerStarted**.
2. During the 60-second timer, press Control-C in the worker terminal. Leave the workflow's second terminal open.
3. Keep the worker stopped until the timer expires.
4. Restart the same worker command on the same namespace and task queue. Don't run `demo.py run` again.
5. Confirm that the original workflow completes. The debit should have one completed execution, followed by payment after the restart.

With the instructor, read the workflow class, `debit_ledger`, `mark_settled`, and the worker's `KeycardInterceptor` configuration in `demo.py`. Temporal reuses the recorded debit result; the next activity obtains credentials when it runs.

## Inspect credentials and history

1. In Keycard, open the **Temporal Worker** application and select **Activity**.
2. Find the Ledger API credential issuance before the interruption and after the restart. Use your run times and worker identity; ask the instructor for help if several attendees share that identity. A Temporal workflow ID doesn't necessarily match a Keycard request ID.
3. In a third terminal, inspect history using your saved workflow ID:

   ```sh
   cd "<package-path>/temporal"
   uv run --locked --env-file .env check_history.py <workflow-id>
   ```
4. Inspect activity inputs, results, headers, and failures in Temporal UI without displaying token values. The scanner checks JWT shapes; manual inspection also covers other credential formats.

History should contain amounts and results without credentials. Keycard Activity records credential issuance; Temporal history records workflow progress. This simulated workflow creates no Expense Desk payment entries.

## If you get stuck

From your resolved package path, restore the checkpoint:

```sh
cd "<package-path>"
uv run --locked --project agent python checkpoints/restore.py 04
```

Then restart the worker on the same namespace and queue. You don't need to install dependencies. If you missed the timer window, start a new workflow to repeat the demonstration. See [Troubleshooting](07-troubleshooting.md#services-and-workflow-recovery) if recovery stalls.

Temporal can retry an activity when it hasn't recorded completion. If an external payment succeeds before that record exists, the payment API still needs an idempotency key or a way to check the payment before retrying it.

At minute 52, stop new exercises. Use the remaining eight minutes to compare histories, ask questions, and recover unfinished work.

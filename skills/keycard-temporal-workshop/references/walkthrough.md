# Guide the current exercise

Read the full exercise in the detected layout before giving commands. Follow its order and adapt to the attendee's current progress. Keep optional investigations for take-home. Use only the current stage's row below unless the attendee asks about progression. Follow the instructor's session timing.

| Stage | Teaching point | Evidence |
| --- | --- | --- |
| 01 | A shared key authenticates access without verifying caller-supplied names. | Compare Created by (supplied name) with Identity details → Actor ID (masked shared API key). |
| 02 | The application authenticates as itself. | A new expense records the registered application despite a supplied username. Keycard Activity shows its credential request. |
| 03 | A signed-in human remains the subject through the agent and MCP exchanges. | Partner approval succeeds; self-approval fails. Inspect Expense Desk actors and both hops in Keycard Activity. |
| 04 | Temporal resumes recorded progress; credentials belong inside activity executions. | The original workflow completes after worker restart; recorded debit is reused and the subsequent activity obtains a credential. |

## Runtime boundaries

Click an expense ID or its small copy icon in Expense Desk chat, the expense list, or expense details to copy the ID. Clicking the ID in the list copies it without selecting the expense; click the expense description to open its details.

In a source checkout, starter commands from the root are `uv run --locked --project agent python starter/run.py web` and `uv run --locked --project mcp-server python starter/run.py mcp`. They read `starter/agent/.env` and `starter/mcp-server/.env`. Secure commands use `agent/web.py` and `mcp-server/server.py`, and read the corresponding component `.env` files. Both states share ports; stop the prior processes when switching.

In an attendee package, use the provided commands and `uv run --locked --project agent python checkpoints/restore.py NN` from the package root. Checkpoint 02 installs secure authentication; 03 uses the same secure wiring with user sign-in. A checkpoint number therefore does not establish the runtime's identity. Inspect the identity shown by Expense Desk.

In Exercise 01 the expense agent asks for a name and optional email when submitting; neither verifies a person. Never supply dummy emails. A requested approval or rejection should call the service and report its result, even above $100. It must not refuse merely because a person is unverified. If it does, stop and report the runtime mismatch; do not coach the attendee to bypass it.

For Exercise 02, choose **Continue as Expense Desk Agent** in the browser to demonstrate application identity. In Exercise 03, console sign-in alone does not authorize Expense Desk: start its browser sign-in. Use the exact pending expense ID exchanged with the partner.

## Recover the same Temporal workflow

Use the settlement directory resolved for this layout. Run the supplied `uv run --locked --env-file .env demo.py worker` and, separately, `uv run --locked --env-file .env demo.py run`. Record the workflow ID, namespace, and queue without printing credentials.

On a shared Temporal service, confirm that the attendee has a unique settlement task queue with only their worker polling it; otherwise use the instructor’s single-worker demonstration. Another worker on the same queue can invalidate the interruption exercise.

Wait for `ActivityTaskCompleted` for debit and `TimerStarted`, then stop only the worker during the 60-second timer. Leave it stopped until the timer expires and restart the same worker on the same namespace and queue. Don't start a new workflow to recover the old one. If the attendee missed the window, explain that repeating the demonstration requires a new run.

Run `uv run --locked --env-file .env check_history.py <workflow-id>`. The scanner detects JWT shapes; its success does not prove the absence of every secret format. Inspect inputs, results, headers, and failures without copying raw history into chat. Correlate Keycard issuance using time and worker identity; a Temporal workflow ID is not necessarily a Keycard request ID.

The demo acquires real credentials but simulates debit and settlement. It creates no real payments or Expense Desk payment entries. Temporal reuses a recorded activity result; an external payment that commits before its activity result is recorded still needs an API-side idempotency key or reconciliation.

## Trace without mixing attendees

Follow the exact filter sequence in Exercise 03: attendee application's Activity, Actor = attendee email, Resource = Expense MCP Resource, then copy Session from a matching Credential Issued event and apply it. On Expense MCP Actor's Activity, reapply Actor and Session and change Resource to Ledger API. Confirm the expected delegation chain and destination at each hop. Request narrows one request's events, not both hops. Session can include multiple tool calls; don't claim a unique expense correlation from it.

Exercise 02 starts with client credentials, not a user session. Inspect the attendee's own application feed; use the instructor-led shared MCP hop demonstration. Don't invent an email filter for an application subject or assume shared actor filtering isolates attendees. If UI labels or matching behavior differ, capture a redacted instructor handoff instead of guessing.

The authenticated Expense Desk agent uses its account identity and never asks for a submission name or email. It reports identity lookup failures instead of substituting a supplied name. It keeps credentials and identity-verification explanations out of its conversation. Use the exercise guide and Activity inspection to teach those concepts.

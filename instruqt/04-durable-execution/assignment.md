---
slug: durable-execution
id: siix7i1gdajk
type: challenge
title: 'Exercise 04: Durable execution'
teaser: Kill a settlement worker mid-workflow, restart it, and confirm no credentials
  landed in history.
notes:
- type: text
  contents: |-
    # What happens when the worker dies after the debit?

    A settlement debits the ledger, waits, then marks the expense settled. Kill the worker between those steps. Does the debit run twice?
- type: text
  contents: |-
    # Where do the credentials go?

    Each activity gets a fresh Keycard credential when it runs. Temporal records every input and result forever. You'll check that none of those credentials ended up in the record.
tabs:
- id: dqqrryj6gtus
  title: Temporal UI
  type: service
  hostname: workshop
  path: /namespaces/workshop-local/workflows
  port: 8233
- id: rfixxa9ynqi9
  title: Worker
  type: terminal
  hostname: workshop
  workdir: /root/workshop/temporal
- id: mpxk6zkw7eck
  title: Client
  type: terminal
  hostname: workshop
  workdir: /root/workshop/temporal
- id: hfxjdoyg94zn
  title: Editor
  type: code
  hostname: workshop
  path: /root/workshop
- id: bzpex6hvzn6g
  title: Keycard
  type: website
  url: https://console.keycard.ai
  new_window: true
difficulty: intermediate
timelimit: 1200
enhanced_loading: null
---

# Read the code

In the [button label="Editor" background="#444CE7"](tab-3), open `temporal/demo.py`. Find `SettlementWorkflow`, the `debit_ledger` and `mark_settled` activities, and the `KeycardInterceptor` the worker registers.

Each activity declares the resource it needs with `@grant`. The interceptor fetches a token for each activity execution and hands it over through `access()`. Nothing about the token goes into the activity's arguments or return value.

The activities fetch real Keycard credentials but only simulate the payment. No money moves.

# Start the worker

Click [button label="Worker" background="#444CE7"](tab-1):

```bash,run
uv run --locked --env-file .env demo.py worker
```

Leave it running.

# Start one workflow

Click [button label="Client" background="#444CE7"](tab-2):

```bash,run
uv run --locked --env-file .env demo.py run
```

Copy the workflow ID it prints. Open [button label="Temporal UI" background="#444CE7"](tab-0) and find that workflow.

# Kill the worker

Watch the event history. When you see **ActivityTaskCompleted** for the debit followed by **TimerStarted**, go back to [button label="Worker" background="#444CE7"](tab-1) and press **Ctrl+C**.

The workflow is now in the middle of a 30-second timer with no worker. Leave the Client terminal alone and wait for the timer to expire.

# Bring it back

Restart the same worker command in the Worker tab:

```bash,run
uv run --locked --env-file .env demo.py worker
```

Don't run `demo.py run` again. The original workflow picks up where it stopped. In Temporal UI, the debit shows one completed execution and `mark_settled` runs after the restart. Temporal reused the recorded debit result instead of running it again.

# Check history for credentials

In the Client tab, scan the workflow history:

```bash,run
uv run --locked --env-file .env check_history.py WORKFLOW-ID
```

The scanner looks for JWT-shaped values. Also open an activity's inputs and results in Temporal UI. You should see amounts and results, never a token.

In [button label="Keycard" background="#444CE7"](tab-4), open **Applications > Temporal Worker > Activity**. You'll find a Ledger API credential issued before the interruption and another after the restart. Keycard records the issuance. Temporal records the progress. Neither holds the other's data.

# If something breaks

Missed the timer window? Run `demo.py run` again for a fresh workflow. To restore the original code:

```bash,run
cd /root/workshop && uv run --locked --project agent python checkpoints/restore.py 04
```

Then restart the worker.

Click **Check** when your workflow has completed.

# Key takeaways

- Temporal resumes a workflow from its recorded history, so a completed activity isn't run again after a worker restart.
- If a payment API call succeeds but the worker dies before Temporal records it, Temporal retries it. Real payment calls still need an idempotency key.
- Credentials fetched inside an activity stay out of workflow history.

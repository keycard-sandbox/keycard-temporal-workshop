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

    Each activity gets a fresh Keycard credential when it runs. Temporal stores every input and result in the Workflow's history. You'll check that none of those credentials ended up in the record.
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

Once someone approves an expense, the company still has to pay it.
Settlement takes two steps: debit the ledger, then mark the expense settled.
Now picture the program that runs those steps crashing right after the debit.
When it comes back, does it debit again, skip the settlement, or pick up where it left off?
With a plain script, the answer depends on whoever wrote the recovery code.

Temporal answers that question for you.
Temporal records each step's result in a Workflow's *Event History*.
When a Worker restarts, it replays that history and reuses the results it already has.
Then it continues from the step that hadn't finished.

Identity doesn't go away, though.
Every step still needs a Keycard credential.
Temporal stores Event History durably, and anyone who can read the Workflow can see it.
So the credential can't end up in it.

In this exercise, you'll run a settlement Workflow, stop its Worker partway through, and restart it to finish the same Workflow.
Then you'll check that no credentials landed in the Event History.
The Activities get real Keycard credentials, but they only simulate the payment, so no money moves.

## Step 1: Reading the settlement code

The settlement code lives in one file.
Open `temporal/demo.py` in the [button label="Editor" background="#444CE7"](tab-3) tab.

Start with the Workflow, which defines the order of the steps:

```python
@workflow.defn
class SettlementWorkflow:
    @workflow.run
    async def run(self, amount: int) -> SettlementResult:
        opts = dict(
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=2), maximum_attempts=3,
                                     non_retryable_error_types=["GrantConfigurationError"]),
        )
        debit = await workflow.execute_activity(debit_ledger, amount, **opts)
        # A durable timer gives the room a restart window after debit completion is recorded.
        await workflow.sleep(30)
        settle = await workflow.execute_activity(mark_settled, amount, **opts)
        return {"debit": debit, "settle": settle}
```

The Workflow runs the `debit_ledger` Activity, waits 30 seconds, and then runs the `mark_settled` Activity.
An *Activity* is a step that does real work, like calling another service.
Temporal can retry an Activity if it fails.
The retry policy allows up to three attempts.
It doesn't retry a `GrantConfigurationError`, because a misconfigured grant won't fix itself.

The `workflow.sleep(30)` call starts a durable *Timer*.
Temporal tracks the Timer itself, so it keeps counting even when no Worker is running.
That 30-second window is when you'll stop the Worker.

Next, look at one of the Activities:

```python
@grant(RESOURCE)
@activity.defn
async def debit_ledger(amount: int) -> DebitResult:
    _assert_aud(access().access_token)
    activity.logger.info("debited %s with a token minted for this call", amount)
    return {"debited": amount}
```

The `@grant(RESOURCE)` decorator, from Keycard's Temporal integration, declares that this Activity needs a credential for the Ledger API.
Inside the Activity, `access().access_token` returns a token issued for this one run of the Activity.
The token never appears in the Activity's input or its result, so it never reaches Event History.
The `_assert_aud` call checks that the token is addressed to the Ledger API.

Finally, find where the Worker is created:

```python
interceptors=[
    # Use the settlement identity explicitly, separate from agent credentials.
    KeycardInterceptor(
        zone_url=os.environ["KEYCARD_ISSUER"],
        credential=ClientSecret((client_id, client_secret)),
    )
],
```

A *Worker* is the process that runs your Workflow and Activity code.
The `KeycardInterceptor` runs before each Activity.
It uses the Worker's own Keycard application, **Temporal Worker**.
With it, the interceptor gets a fresh token for every Activity that has a `@grant`.
This Worker acts as itself, so it doesn't need your browser sign-in.

Now that you've seen the code, you'll start the Worker.

## Step 2: Starting the Worker

The Worker needs its own Keycard credentials before it can start.
The instructors will share the client ID and secret for the **Temporal Worker** application.

Open `temporal/.env` in the [button label="Editor" background="#444CE7"](tab-3) tab and set these two lines:

```dotenv,nocopy
WORKER_KEYCARD_CLIENT_ID=WORKER-CLIENT-ID
WORKER_KEYCARD_CLIENT_SECRET=WORKER-CLIENT-SECRET
```

Leave the other lines alone; your sandbox already filled them in.
Save the file.

**Note:** Keep the secret in `.env`. Don't paste it into chat, a screenshot, or a commit.

With the credentials in place, click on the [button label="Worker" background="#444CE7"](tab-1) tab and type the following command:

```bash,run
uv run --locked --env-file .env demo.py worker
```

The `--locked` flag runs the code with the exact package versions from the lockfile.
The `--env-file .env` flag loads the Worker's settings from `temporal/.env`, including the credentials you just added.
The `worker` argument tells `demo.py` to start a Worker.

You should see a line like this one:

```bash,nocopy
worker PID 1234 on settlement-local
```

The Worker is now polling the `settlement-local` *Task Queue* for work.
Leave it running.

Now that a Worker is ready, you'll give it a settlement to run.

## Step 3: Starting a settlement

Click on the [button label="Client" background="#444CE7"](tab-2) tab and type the following command:

```bash,run
uv run --locked --env-file .env demo.py run
```

The `run` argument starts one `SettlementWorkflow` with an amount of `4200` and waits for its result.
It prints the Workflow ID right away:

```bash,nocopy
workflow id: settlement-1a2b3c4d
```

Copy your Workflow ID.
Leave this terminal alone; it's waiting for the Workflow to finish.

Click on the [button label="Temporal UI" background="#444CE7"](tab-0) tab and open your Workflow.
Its Event History fills in as the Workflow runs.

Now that the settlement is running, it's time to interrupt it.

## Step 4: Stopping the Worker mid-settlement

Watch the Event History in the Temporal UI.
Wait until you see **ActivityTaskCompleted** for the debit, followed by **TimerStarted**.
The debit is done, and Temporal has recorded its result.

Now click on the [button label="Worker" background="#444CE7"](tab-1) tab and press `CTRL+C` to stop the Worker.

Go back to the Temporal UI.
Your Workflow still shows **Running**, even though no Worker is running it.
The Workflow's state lives in Temporal, not in the Worker.

Leave the Worker stopped until the 30-second Timer expires.

Now that the Timer has fired with no Worker around, you'll bring the Worker back.

## Step 5: Restarting the Worker

In the [button label="Worker" background="#444CE7"](tab-1) tab, type the same command again:

```bash,run
uv run --locked --env-file .env demo.py worker
```

**Warning:** Don't run `demo.py run` again. You're resuming the original Workflow, not starting a new one.

Watch your Workflow in the Temporal UI.
It finishes, and the Client tab prints the result.
Count the Activity Executions in the Event History: one `debit_ledger` and one `mark_settled`.

The new Worker didn't run the debit a second time.
It replayed the Event History, found the debit's recorded result, and reused it.
Then it ran `mark_settled`, the step that hadn't happened yet.
That Activity got its own fresh credential when it ran.

Now that the settlement has finished, you'll check where the credentials ended up.

## Step 6: Checking history for credentials

The Client tab printed a command to check the Event History.
Click on the [button label="Client" background="#444CE7"](tab-2) tab and type it, using your Workflow ID:

```bash,run
uv run --locked --env-file .env check_history.py WORKFLOW-ID
```

Keycard's access tokens use a format called JSON Web Token (JWT).
The script scans every event in your Workflow's history for values shaped like a JWT.
You should see a result like this:

```bash,nocopy
OK: no JWT-shaped token material across 22 events in settlement-1a2b3c4d
```

The script only looks for JWT-shaped values, so check by hand too.
In the Temporal UI, open the debit Activity's input and result.
You'll see amounts and results, but never a token.

Finally, look at the same run from Keycard's side.
In the [button label="Keycard" background="#444CE7"](tab-4) tab, open **Applications > Temporal Worker > Activity**.
Find the Ledger API credential issued before you stopped the Worker, and the one issued after you restarted it.
Use your run times to tell them apart, and ask an instructor if several attendees' events look alike.

Keycard records who got a credential and when.
Temporal records what the Workflow did.
Neither one holds the other's data.

## Conclusion

You ran a settlement Workflow, stopped its Worker after the debit, and restarted it to finish the same Workflow.
Temporal reused the recorded debit instead of running it again, and the next Activity got a fresh credential when it ran.
The Event History holds amounts and results, but no credentials.

There's one thing this demo doesn't prove.
Temporal reuses a result after it records it.
If a real payment succeeds and the Worker crashes before Temporal records the completion, Temporal retries the Activity.
So a real payment call still needs an idempotency key.
That key, or a check for an earlier payment, stops the retry from paying twice.

Now that you've seen identity and durability working together, head back to the room for the recap and questions.

## If you fall behind

If you missed the Timer window, start a new Workflow with `demo.py run` and stop the Worker sooner.

To restore the original settlement code, click on the [button label="Client" background="#444CE7"](tab-2) tab.
Move to the workshop folder, where the checkpoints live:

```bash,run
cd /root/workshop
```

Then restore the Exercise 04 code:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 04
```

Restart the Worker with the same command from Step 2, in the Worker tab.

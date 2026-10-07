---
slug: durable-execution
id: siix7i1gdajk
type: challenge
title: 'Exercise 04: Making your agent durable'
teaser: See how Temporal keeps an agent's work alive through a crash, then stop a
  Worker mid-run and watch it pick up where it left off.
notes:
- type: text
  contents: |-
    # What happens to your agent when its process dies?

    An agent is a loop of model calls and tool calls. If the process crashes halfway through, does it start over, repeat work it already did, or pick up where it left off?
- type: text
  contents: |-
    # Where do the credentials go?

    Each step gets a fresh Keycard credential when it runs. Temporal records every step's inputs and results. You'll check that none of those credentials ended up in the record.
tabs:
- id: dqqrryj6gtus
  title: Temporal UI
  type: service
  hostname: workshop
  path: /namespaces/default/workflows
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
  url: https://id.keycard.ai/openid/connect/login?tenant=v6f1suvmlhp7k4a21bzyqp80w3&iss=https%3A%2F%2Fkeycard-temporal-workshop.us.auth0.com%2F&target_link_uri=https%3A%2F%2Fconsole.keycard.ai
  new_window: true
difficulty: intermediate
timelimit: 1800
enhanced_loading: null
---

You now know who your agent is and who it acts for.
There's one more thing it needs: it has to survive failure.

An agent is a loop.
It reads some data, calls a model, calls a tool, waits, and does it again.
Any step can fail partway through: a deploy, a crash, a dropped connection.
A plain loop loses its place when its process dies, and when it starts again it can repeat work it already finished.
If that work was a payment, someone gets paid twice.

Temporal makes your agent durable.
Temporal records each step's result in a Workflow's *Event History*.
When a process restarts, it replays that history, reuses the results it already has, and continues from the step that hadn't finished.

In this exercise, you'll see that the Expense Desk agent already runs this way.
Then you'll run a smaller Workflow with the same shape, stop its Worker partway through, and watch it finish without repeating a step.
Finally, you'll check that no credentials ended up in the Event History.

## Step 1: Reading your agent as a Workflow

Expense Desk has an autonomous reviewer that checks new expenses and approves the small ones.
That reviewer is a Temporal *Workflow*, a function whose progress Temporal records.

Open `agent/review_workflows.py` in the [button label="Editor" background="#444CE7"](tab-3) tab:

```python
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
```

This is the agent loop.
Each pass runs the `review_expense` *Activity*, a step that does real work and that Temporal can retry if it fails.
Then the Workflow sleeps for 60 seconds and checks again.
After 100 passes, `continue_as_new` starts a fresh run for the same expense, so the history never grows without limit.

Now open `agent/review.py` to see the model call inside that Activity:

```python
async def assess(row: dict) -> Assessment:
    async with chat.model_http_client() as http_client:
        reviewer = Agent(
            build_model(api_key="managed-by-keycard", http_client=http_client),
            output_type=Assessment,
            instructions=POLICY
            ...
        )
        result = await reviewer.run(
            json.dumps({"amount_cents": row["amount_cents"], "memo": row["memo"]}),
            usage_limits=UsageLimits(request_limit=3),
        )
        return result.output
```

The Activity reads the expense through the MCP server.
Then a Pydantic AI agent asks the model whether the expense meets the policy.
Finally, the Activity records the decision through the MCP tools.
Every model call and tool call happens inside an Activity, so Temporal records each result.
If the process running the agent dies, another one picks up the same review where it stopped.

The instructors keep this reviewer turned off during the workshop.
It reviews every new expense in the shared Ledger API, including yours.

Now that you've seen the agent's shape, you'll run a smaller Workflow with the same shape, one you can interrupt on purpose.

## Step 2: Reading the settlement code

Once an expense is approved, it has to be paid.
The settlement Workflow does that in two steps, and it's small enough to stop at the exact moment you choose.
Open `temporal/demo.py`:

```python
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
```

The Workflow runs the `debit_ledger` Activity, waits 60 seconds, and then runs the `mark_settled` Activity.
The retry policy has no attempt limit, so a short outage only delays an Activity instead of failing the Workflow.

The `workflow.sleep` call starts a durable *Timer*.
Temporal tracks the Timer itself, so it keeps counting even when nothing is running your code.
Those 60 seconds are your window to stop the Worker.

Next, look at one of the Activities:

```python
@grant(RESOURCE)
@activity.defn
async def debit_ledger(amount: int) -> DebitResult:
    _assert_aud(access().access_token)
    activity.logger.info("debited %s with a token minted for this call", amount)
    return {"debited": amount}
```

The `@grant(RESOURCE)` decorator, from Keycard's Temporal integration, says this Activity needs a credential for the Ledger API.
Inside the Activity, `access().access_token` returns a token issued for this one run of the Activity.
The `_assert_aud` call checks that the token is addressed to the Ledger API.
The log line is the one you'll watch for in a moment.

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
*Interceptors* are Temporal's way to run your own code around every Workflow and Activity call.
The `KeycardInterceptor` runs before each Activity and gets a fresh token for every Activity that has a `@grant`.
The token never goes into the Activity's input or result, so it never reaches the Event History.

Now that you've seen the code, you'll give the Worker its credentials.

## Step 3: Adding the Worker's credentials

The Worker uses its own Keycard application, **Temporal Worker**, so it needs its own client ID and secret.
The instructors will share them with the room.

Open `temporal/.env` in the [button label="Editor" background="#444CE7"](tab-3) tab and set these two lines:

```dotenv,nocopy
WORKER_KEYCARD_CLIENT_ID=WORKER-CLIENT-ID
WORKER_KEYCARD_CLIENT_SECRET=WORKER-CLIENT-SECRET
```

Leave the other lines alone; your sandbox already filled them in.
Save the file.

Notice what just happened.
Everyone in the room now holds the same Worker secret, which is the shared-key problem from Exercise 01 all over again.
We did it here to keep setup fast.
In production, each deployment gets its own workload identity through Workload Identity Federation (WIF for short), and Keycard issues credentials to that identity, so there's no secret to pass around.

Now that the Worker has credentials, you'll start it.

## Step 4: Starting the Worker

Click on the [button label="Worker" background="#444CE7"](tab-1) tab and type the following command:

```bash,run
uv run --locked --env-file .env demo.py worker
```

The `--locked` flag runs the code with the exact package versions from the lockfile.
The `--env-file .env` flag loads the Worker's settings from `temporal/.env`, including the credentials you just added.
The `worker` argument tells `demo.py` to start a Worker.

You should see a line like this one:

```bash,nocopy
worker PID 1234 on keycard-temporal-demo
```

The Worker is now polling the `keycard-temporal-demo` *Task Queue* for work.
Leave it running.

Now that a Worker is ready, you'll give it a settlement to run.

## Step 5: Starting a settlement

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

Go back to the [button label="Worker" background="#444CE7"](tab-1) tab.
You'll see a log line containing `debited 4200 with a token minted for this call`.
That's the debit Activity running once.

Now that the debit has run, it's time to interrupt the Workflow.

## Step 6: Stopping the Worker mid-settlement

Click on the [button label="Temporal UI" background="#444CE7"](tab-0) tab and open your Workflow.
In its Event History, find **ActivityTaskCompleted** for the debit, followed by **TimerStarted**.
The debit is done, and Temporal has recorded its result.

Now click on the [button label="Worker" background="#444CE7"](tab-1) tab and press `CTRL+C` to stop the Worker.

Go back to the Temporal UI.
Your Workflow still shows **Running**, even though no Worker is running it.
The Workflow's state lives in Temporal, not in the Worker.

Leave the Worker stopped.
About a minute after the debit, **TimerFired** appears in the Event History.
Temporal fired the Timer on its own, with no Worker running.

Now that the Timer has fired with no Worker around, you'll bring the Worker back.

## Step 7: Restarting the Worker

In the [button label="Worker" background="#444CE7"](tab-1) tab, type the same command again:

```bash,run
uv run --locked --env-file .env demo.py worker
```

**Warning:** Don't run `demo.py run` again. You're resuming the original Workflow, not starting a new one.

Watch the Worker's log.
This time you'll see `settled 4200 with a token minted for this call`, but no new `debited` line.
The restarted Worker replayed the Event History, found the debit's recorded result, and reused it.
Then it ran `mark_settled`, the step that hadn't happened yet.

Your Workflow finishes, and the Client tab prints the result.
In the Event History, you'll find one `debit_ledger` and one `mark_settled` Activity Execution.

This is what makes your agent durable.
If the process running your agent dies, a new one replays the history and continues, instead of starting over or paying twice.

Now that the settlement has finished, you'll check where the credentials ended up.

## Step 8: Keeping secrets out of history

Temporal keeps a Workflow's Event History for the namespace's retention period, and anyone who can read the Workflow can see what's in it.
So anything sensitive should stay out of it.

The Client tab printed a command to check your Workflow's history.
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

Check by hand, too.
In the Temporal UI, open the debit Activity's input and result.
You'll see amounts and results, but never a token.

Temporal gives you two ways to keep sensitive data out of Event History:

- **Interceptors**, like the `KeycardInterceptor` you saw, keep data like credentials out of history entirely by fetching them inside each Activity.
- A **Payload Codec** encrypts the data that does go into history. Your Workers encrypt each input and result before it leaves the process, so the Temporal Service only stores ciphertext. A *Codec Server* that you run decrypts the data for the Temporal UI and CLI, and Temporal never holds your keys.

Finally, look at the same run from Keycard's side.
In the [button label="Keycard" background="#444CE7"](tab-4) tab, open **Applications > Temporal Worker > Activity**.
This **Activity** tab is Keycard's log of credential requests, not a Temporal Activity.
Find the Ledger API credential issued before you stopped the Worker, and the one issued after you restarted it.
Keycard records who got a credential and when, and Temporal records what the Workflow did.

## Conclusion

You saw that the Expense Desk agent runs as a Temporal Workflow, with every model call and tool call recorded as a step.
Then you stopped a Worker in the middle of a settlement, restarted it, and watched it finish without running the debit again.
The Event History held the amounts and results, but no credentials.

There's one thing this demo doesn't prove.
Temporal reuses a result after it records it.
If a real payment succeeds and the Worker crashes before Temporal records the completion, Temporal retries the Activity.
So a real payment call still needs an idempotency key.
That key, or a check for an earlier payment, stops the retry from paying twice.

Now that your agent has an identity and survives failure, head back to the room for the recap and questions.

## If you fall behind

If the Timer fired before you stopped the Worker, start a new Workflow with `demo.py run` and stop the Worker sooner.

To restore the original settlement code, click on the [button label="Client" background="#444CE7"](tab-2) tab.
Move to the workshop folder, where the checkpoints live:

```bash,run
cd /root/workshop
```

Then restore the Exercise 04 code:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 04
```

Restart the Worker with the same command from Step 4, in the Worker tab.

## Use Keycard for your own projects

Open [Keycard Workshop Registration](https://keycard-workshop-registration.fly.dev/) and enter the five-character access code supplied privately by your instructor. Sign in with GitHub, then choose **Continue to Keycard** to finish personal signup with the same verified primary email.

This is separate from the workshop organization's SSO link in Exercise 02. Personal signup does not join that organization or copy its applications, resources, credentials, or shared services into your own environment. Keep using the workshop SSO link for the exercises.

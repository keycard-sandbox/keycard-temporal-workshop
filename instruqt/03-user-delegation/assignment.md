---
slug: user-delegation
id: 9vxqvyeiktom
type: challenge
title: 'Exercise 03: User delegation'
teaser: Sign in, approve a partner's expense, and watch Expense Desk refuse your own.
notes:
- type: text
  contents: |-
    # Can the agent act for you without acting as you?

    Application identity says which software made the call. It doesn't say which person asked. Sign in and your agent carries your identity through two token exchanges to the ledger.
tabs:
- id: zusp4am3j8rt
  title: Expense Desk
  type: service
  hostname: workshop
  path: /
  port: 8400
  new_window: true
- id: fbw0yniaimnv
  title: Keycard
  type: website
  url: https://console.keycard.ai
  new_window: true
- id: tsnylbthituq
  title: Editor
  type: code
  hostname: workshop
  path: /root/workshop
- id: dgnlpmrbofqw
  title: Terminal
  type: terminal
  hostname: workshop
  workdir: /root/workshop
difficulty: intermediate
timelimit: 1200
enhanced_loading: null
---

In Exercise 02, your agent got its own identity.
The Ledger API now knows which application made each request, but it still doesn't know which person asked for it.

In this exercise, you'll sign in to Expense Desk so your agent can act on your behalf.
You'll approve a partner's expense and watch Expense Desk refuse to let you approve your own.
Then you'll follow your identity through each credential request in Keycard.

Keep the MCP server and Expense Desk running from Exercise 02.
Your sandbox kept your `agent/.env` and the authenticated code, so there's nothing to restart.

## Step 1: Signing in

Click on the [button label="Expense Desk" background="#444CE7"](tab-0) tab.
This time, Expense Desk opens in its own browser window.
Signing in sends you to Keycard and then GitHub, and GitHub's sign-in page can't load inside the lab.

Click on **Sign in** and sign in with your GitHub account.
When you return to Expense Desk, ask the agent:

```text
Which account am I using, and what is my approval limit?
```

You should see your signed-in email this time instead of the application from Exercise 02.

Choose **All expenses**, then select the expense ID you saved in Exercise 02 and open its **Activity**.
That expense still belongs to the application that created it.
Signing in doesn't change who created earlier expenses.

**My expenses** only shows expenses you create while signed in, so it can be empty even when **All expenses** isn't.
Expenses created without a verified identity, like the ones from Exercise 01, stay labeled **Unverified submitter**.
They never become verified later.

**Note:** If sign-in works but the agent's tools fail, open `docs/07-troubleshooting.md` in the [button label="Editor" background="#444CE7"](tab-2) tab and follow **Consent errors after sign-in** before you sign in again.

Now that you're signed in, you'll test what your agent is allowed to approve for you.

## Step 2: Testing what the agent can approve

File a new $75 expense with any memo, for example:

```text
Submit a $75 expense for printer paper and toner for the workshop.
```

Then file a second expense under $50:

```text
Submit $30 for office supplies for our team.
```

The agent approves the $30 expense in the same conversation.
Read its confirmation.
**Created by** is you, and **Decided by** is your agent.
Small expenses fall under the agent's own approval limit, so it can approve them by itself.

Now ask the agent to approve your own $75 expense by its ID:

```text
Approve expense EXPENSE-ID
```

Expense Desk refuses and explains that you can't approve your own expense.
It checks who owns the expense and enforces that rule, no matter what the agent asks for.

Now that you've seen the refusal, you'll approve an expense that isn't yours.

## Step 3: Approving a partner's expense

Swap expense IDs with the person next to you.

Choose **All expenses**, select your partner's pending expense, and click on **Approve**.
The button sends `Approve expense EXPENSE-ID` through the same agent conversation, so you could also type the request yourself.

After your partner decides your expense, click on **Refresh** to see their decision.
Your own chat refreshes your view after each turn, but it won't show your partner's changes until you refresh.

Open the expense's **Activity** and compare **Created by** with the actor who decided it.
Expand **Identity details** to see the full actor ID.
Partner approval should succeed, and self-approval should fail with a reason.

Ask the agent for your approval limit one more time.
The expected limit for attendees is $100.

Now that you've approved an expense as yourself, you'll trace how your identity traveled through the system.

## Step 4: Following the credential requests

Your request went through two hops: from your agent to the MCP server, and from the MCP server to the Ledger API.
Each hop has its own credential request in Keycard, and you can follow both.

Start with the first hop.
In the [button label="Keycard" background="#444CE7"](tab-1) tab, open **Applications > Expense Desk Agent - YOUR-GITHUB-HANDLE > Activity**.

1. Open **Filters > Clear** to remove earlier filters, and choose a time range that includes your run.
2. Open **Filters > Actor**, search for your GitHub email, and select the matching person.
   Actor includes applications acting on that person's behalf.
3. Set **Filters > Resource > Expense MCP Resource**.
4. Open a **Credential Issued** event labeled `urn:ietf:params:oauth:grant-type:token-exchange`.
5. Check that **Delegation Chain** shows your agent application on behalf of your email, and that **Resource** is **Expense MCP Resource**.
6. In the event's **Overview**, copy **Session**. Close the panel, open **Filters > Session**, paste the ID under **Or enter an ID**, and click on **Apply**.

The session ID narrows the feed to your signed-in run.
A session can contain several tool calls.

Next, follow the second hop.
Open **Applications > Expense MCP Actor > Activity**.
Switching applications clears the filters, so set **Actor** to your email and **Session** to the same ID again.
Then set **Resource** to **Ledger API**.

Open the **Credential Issued** event, again labeled `urn:ietf:params:oauth:grant-type:token-exchange`.
Check that **Delegation Chain** shows **Expense MCP Actor on behalf of** your email, that **Resource** is **Ledger API**, and that **Overview** shows the same **Session**.

Here's what happened across those two hops.
In the first exchange, your agent traded your sign-in token for a token addressed to Expense MCP.
In the second, Expense MCP Actor traded that token for one addressed to the Ledger API.
Your identity carried through both hops, while the application making each request changed.

**Note:** Each hop has its own **Request ID**, so use Actor and Session to follow a request across hops. If you can't find the chain, ask an instructor to help trace a known event.

## Conclusion

You signed in to Expense Desk, approved a partner's expense, and watched Expense Desk refuse to let you approve your own.
In Keycard, you followed your identity across two token exchanges, from your agent to the MCP server and on to the Ledger API.

You can now tell who asked for access and which application acted on their behalf.
There's one more problem: the work itself has to survive when something fails partway through.
Now that you know who's acting, you'll see in Exercise 04 how Temporal keeps that work going when a Worker stops.

## If you fall behind

To restore the authenticated code, click on the [button label="Terminal" background="#444CE7"](tab-3) tab and type the following commands:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 03
```

```bash,run
workshop-services restart
```

Then open Expense Desk and sign in again.
If someone already decided your earlier expenses, create new ones.
If sign-in stays blocked, follow along with the instructor's demonstration.

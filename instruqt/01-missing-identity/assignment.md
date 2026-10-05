---
slug: missing-identity
id: 22yh8kzjko1y
type: challenge
title: 'Exercise 01: Missing identity'
teaser: Submit and review expenses through one shared API key, then try to work out
  who did what.
notes:
- type: text
  contents: |-
    # Who approved that expense?

    Expense Desk files and approves expenses through an MCP server. The MCP server reaches the Ledger API with one shared API key.

    Every attendee uses that same key. Watch what that does to the audit trail.
- type: text
  contents: |-
    # What's already running

    Expense Desk, the Expense MCP server, and a Temporal dev server started with your sandbox. The Ledger API is shared, so you'll see other attendees' expenses as they work.
tabs:
- id: ks2jllyurxbk
  title: Expense Desk
  type: service
  hostname: workshop
  path: /
  port: 8400
- id: iaq4mnq7qnnq
  title: Editor
  type: code
  hostname: workshop
  path: /root/workshop
- id: ksptesayvfan
  title: Terminal
  type: terminal
  hostname: workshop
  workdir: /root/workshop
difficulty: basic
timelimit: 900
enhanced_loading: null
---

# Open Expense Desk

Click [button label="Expense Desk" background="#444CE7"](tab-0).

The full exercise lives in `docs/01-missing-identity.md`. Open it in the [button label="Editor" background="#444CE7"](tab-1) if you want the long version.

# Submit an expense

Ask the agent to file one. Pick your own amount and description:

```text
Submit a $75 expense for snacks for the workshop.
```

Give it a name when it asks. An email is optional. Neither one proves who you are. Save the expense ID it returns.

# Review someone else's

Choose **All expenses**, click **Refresh**, and pick a pending expense you didn't submit. Then decide it:

```text
Approve expense EXPENSE-ID
```

Working alone? Submit a second expense under a different name and review that one.

# Read the Activity

Select the expense you reviewed and open **Activity**. Compare **Created by** with **Activity > Identity details > Actor ID**.

Created by is whatever name someone typed. Actor ID is `API key: ********`, the shared credential. A valid key proves someone holds it. It doesn't say which application or person sent the request.

# If something breaks

Click [button label="Terminal" background="#444CE7"](tab-2) and restore the starter code:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 01 && workshop-services restart
```

Logs live in `/tmp/workshop/mcp.log` and `/tmp/workshop/web.log`.

Click **Check** when you can say why the audit trail can't name the approver.

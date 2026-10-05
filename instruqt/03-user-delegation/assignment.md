---
slug: user-delegation
id: ""
type: challenge
title: "Exercise 03: User delegation"
teaser: Sign in, approve a partner's expense, and watch Expense Desk refuse your own.
notes:
- type: text
  contents: |-
    # Can the agent act for you without acting as you?

    Application identity says which software made the call. It doesn't say which person asked. Sign in and your agent carries your identity through two token exchanges to the ledger.
tabs:
- title: Expense Desk
  type: service
  hostname: workshop
  port: 8400
  path: /
  new_window: true
- title: Keycard
  type: website
  url: https://console.keycard.ai
  new_window: true
- title: Editor
  type: service
  hostname: workshop
  port: 8080
  path: /?folder=/root/workshop
- title: Terminal
  type: terminal
  hostname: workshop
  workdir: /root/workshop
difficulty: intermediate
timelimit: 1200
---

# Sign in

Open [button label="Expense Desk" background="#444CE7"](tab-0) and sign in with GitHub. Then ask:

```text
Which account am I using, and what is my approval limit?
```

You should see your signed-in email and a $100 limit. The full exercise is `docs/03-user-delegation.md` in the [button label="Editor" background="#444CE7"](tab-2).

# Try to approve your own expense

1. File a new $75 expense with any memo.
2. File one under $50, for example `Submit $30 for office supplies for our team.` Your agent approves it in the same conversation.
3. Ask it to approve your own $75 expense by ID. Read the refusal.

# Approve a partner's

Swap expense IDs with a partner. Choose **All expenses**, select their pending expense, and click **Approve**. After they decide yours, click **Refresh**.

Working alone? Sign in from a private window with a second GitHub account to play the partner.

# Follow the credential requests

In [button label="Keycard" background="#444CE7"](tab-1), follow **Follow the credential requests** in the guide. You're looking for two token exchanges in one session:

- Your agent application, on behalf of your email, to Expense MCP Resource.
- Expense MCP Actor, on behalf of your email, to Ledger API.

The application making each request changes. Your identity carries through both.

# If something breaks

```bash,run
uv run --locked --project agent python checkpoints/restore.py 03 && workshop-services restart
```

Sign in again afterward. If sign-in fails but tools work, see **Consent errors after sign-in** in `docs/07-troubleshooting.md`.

Click **Check** when the partner approval succeeded and self-approval was refused.

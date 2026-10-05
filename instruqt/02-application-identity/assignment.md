---
slug: application-identity
id: ""
type: challenge
title: "Exercise 02: Application identity"
teaser: Register your agent in Keycard and make it authenticate as itself.
notes:
- type: text
  contents: |-
    # What if the agent had its own identity?

    A shared key can't tell one caller from another. In this exercise your Expense Desk agent gets its own Keycard application, so the ledger records which software made each request.
- type: text
  contents: |-
    # You'll need GitHub

    You join the workshop's Keycard organization with your GitHub account. Have your GitHub handle ready. You use it in every identifier you create.
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
timelimit: 1800
---

# Join Keycard

Follow **Join Keycard** and **Look around Keycard** in `docs/02-application-identity.md`. Open it in the [button label="Editor" background="#444CE7"](tab-2).

The join link in the guide signs you in with GitHub. Click [button label="Keycard" background="#444CE7"](tab-1) to get back to the console later.

# Find your callback URL

Your sandbox has its own HTTPS preview URL. Click [button label="Terminal" background="#444CE7"](tab-3) and print the callback:

```bash,run
cat CALLBACK_URL.txt
```

Use that exact value as the application's **Redirect URI**. Setup already wrote the matching origin into `agent/.env` as `EXPENSE_DESK_ORIGIN`. Leave that line alone.

# Register your agent

Work through these sections of the guide in the Keycard console:

1. **Create your application**, with Implicit consent and the Redirect URI above.
2. **Create the resource your application provides**.
3. **Add dependencies before signing in to Expense Desk**.
4. **Create your application credentials**.

# Fill in agent/.env

In the [button label="Editor" background="#444CE7"](tab-2), open `agent/.env` and set these three lines:

```dotenv,nocopy
KEYCARD_CLIENT_ID=YOUR-CLIENT-ID
KEYCARD_CLIENT_SECRET=YOUR-CLIENT-SECRET
AGENT_RESOURCE=urn:agent:resource:YOUR-GITHUB-HANDLE
```

The editor saves as you type. Run through **Check your registration** in the guide before moving on.

# Switch to application authentication

Compare `agent/agent_auth.py` with `checkpoints/02-authenticated/agent/agent_auth.py`. Then apply the checkpoint and restart both processes:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 02 && workshop-services restart
```

Open [button label="Expense Desk" background="#444CE7"](tab-0) again and choose **Continue as Expense Desk Agent**.

# Check what gets recorded

Ask the agent which account it's using, then have it file a $75 expense under someone else's name. **Created by** should show your registered application, whatever name you typed.

In Keycard, open **Applications > Expense Desk Agent - YOUR-GITHUB-HANDLE > Activity** and find the **Credential Issued** event for Expense MCP Resource.

Click **Check** when Created by shows your application.

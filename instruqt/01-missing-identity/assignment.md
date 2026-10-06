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

Expense Desk is an AI agent that files and approves expenses.
It doesn't work with the expense records directly.
It calls a Model Context Protocol (MCP) server, a service that gives an agent tools to use.
The MCP server then calls the *Ledger API*, which stores the expenses.
Right now, every one of those calls uses the same shared API key.
Everyone in this room holds that key.

In this exercise, you'll submit an expense, review someone else's, and then try to work out who did what.

## Step 1: Opening Expense Desk

Your sandbox has already started Expense Desk and the MCP server for you.
Click on the [button label="Expense Desk" background="#444CE7"](tab-0) tab to open it.

Everyone in the workshop shares one Ledger API.
You'll see other people's expenses appear as they work.
A fresh environment starts empty, so don't worry if the list is blank when you first open it.

Now that Expense Desk is open, you'll submit your first expense.

## Step 2: Submitting an expense

Ask the Expense Desk agent to submit an expense in the chat.
Choose your own amount and description.
For example:

```text
Submit a $75 expense for snacks for the workshop.
```

The agent will ask for your name if you didn't include one.
An email address is optional, so you can skip it.
Keep in mind that neither value verifies who you are.
The agent records whatever you type.

After the agent confirms the submission, save the expense ID it returns.
You'll use it later to find your expense.

Now that you've filed an expense, you'll review one that belongs to someone else.

## Step 3: Reviewing another attendee's expense

Choose **All expenses** and click on **Refresh** to see what other attendees have submitted.
If everyone is still typing, wait a moment and refresh again.

Pick a pending expense that you didn't submit, and copy its ID.
Then tell the agent what you decided:

```text
Approve expense EXPENSE-ID
```

You can approve or reject it; the choice is yours.
If the agent asks for a reviewer name, give it one.
If someone else has already reviewed that expense, refresh and choose another pending one.

Now that you've reviewed an expense, it's time to see what the system recorded about it.

## Step 4: Reading the expense history

In Expense Desk, select the expense you reviewed.
Its details panel has an **Activity** section, which records every action taken on that expense.
Then find your original submission and click on **Refresh** to see whether someone has reviewed it yet.

Look at both records and ask yourself two questions.
Can you tell who submitted each expense, or who approved or rejected it?
What connects the recorded names to the people in this room?

In that panel, compare **Created by** with **Activity > Identity details > Actor ID**.
**Created by** shows the name someone supplied with the expense.
**Actor ID** shows `API key: ********`, the shared credential that granted access.

A valid shared key proves that the caller holds the key.
That's enough to get access to the service.
It doesn't say which application or which person sent the request.
Expense Desk can record the name someone supplied, but a name isn't proof of identity.

## Conclusion

You submitted and reviewed expenses through a single shared API key, and you saw that the audit trail can't name who did what.
Anyone holding the key can claim any name.

Now that you've seen the problem, you'll start fixing it.
In Exercise 02, you'll register your agent with Keycard and give it an identity of its own.

## If you fall behind

If your Expense Desk stops working, you can restore this exercise's code.
Click on the [button label="Terminal" background="#444CE7"](tab-2) tab and type the following command:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 01
```

This restores the Exercise 01 versions of the authentication files.
It leaves your `.env` files alone.

Next, restart the MCP server and Expense Desk so they load the restored code:

```bash,run
workshop-services restart
```

The `workshop-services` command manages both processes in your sandbox.
It replaces the two terminals you'd use to start them on your own machine.

Checkpoints restore code, but they don't undo expenses.
If the problem continues, ask an instructor for help.

<!-- Generated from docs/attendee/ex01.md. Edit the source, then rebuild. -->
# Exercise 01: missing identity

Submit an expense, review someone else's, then see whether Activity can tell you who did what.

A fresh environment starts empty. Everyone using the same Ledger API shares its data, so you will see submissions and decisions as people work. Existing submissions remain when authentication changes. For this exercise, create your own expense and review another attendee's new submission.

## Submit an expense

1. Open Expense Desk at http://localhost:8400 locally, or use your supplied preview URL.
2. Ask the Expense Desk agent to submit an expense. Choose your own amount and description, for example: "Submit a $75 expense for snacks for the workshop."
3. If you haven’t supplied a name, answer the agent’s name question. An email address is optional; you can skip it. Neither value verifies your identity.
4. After the agent confirms the submission, click the returned expense ID or its copy icon to copy it, then save it so you can find it later. IDs are copyable in chat, the expense list, and expense details.

## Review another attendee's expense

1. Choose All expenses and click Refresh to see what other attendees have submitted. If everyone is still typing, wait a moment and refresh again.
2. Select a pending expense from this round that you didn't submit. Copy its ID.
3. Tell the Expense Desk agent: "Approve expense <id>" or "Reject expense <id>". You decide whether to approve or deny it. If the Expense Desk agent asks for a reviewer name, give it one.
4. If someone else has already reviewed that expense, refresh and choose another pending expense.

## Inspect Activity

Select the expense you reviewed and inspect Activity. Then find your original submission and click Refresh to see whether someone has reviewed it.

Can you tell who submitted each expense or who approved or denied it? What connects the recorded names to the people in the room?

Compare **Created by** with **Activity → Identity details → Actor ID**. Created by shows the name someone supplied with the expense. Actor ID shows `API key: ********`, the shared credential that granted access. A valid shared key proves possession of that credential and authenticates service access. It does not uniquely identify which application or person sent the request. Expense Desk can record the supplied name, but the name is not identity proof.

## If you get stuck

From your resolved package path, restore the checkpoint:

```sh
cd "<package-path>"
uv run --locked --project agent python checkpoints/restore.py 01
```

Then restart the supplied MCP and browser processes. Checkpoints restore code; they don't undo expenses. If your service is unavailable, follow the instructor's prepared Activity records. For startup errors, see [Troubleshooting](07-troubleshooting.md#services-and-workflow-recovery).

<!-- Generated from docs/attendee/ex03.md. Edit the source, then rebuild. -->
# Exercise 03: user delegation

Your Expense Desk agent can now act for a signed-in user. You'll approve or reject someone else's expense and see why Expense Desk refuses approval of your own expenses.

## Sign in to Expense Desk

1. Keep the MCP and Expense Desk browser processes from Exercise 02 running. Open your configured Expense Desk URL.
2. Click the **Sign in** button in the upper right corner of Expense Desk and sign in with your GitHub account. Signing in to the Keycard console in Exercise 02 did not sign you in to Expense Desk.
3. In the **Expense Desk browser chat**, ask “Which account am I using, and what is my approval limit?” and compare the result with Exercise 02. You should see your signed-in email. Choose **All expenses**, then select the expense ID you saved to inspect its Activity.

Your earlier submission belongs to the application that created it. **My expenses** shows submissions you create under your signed-in identity, so that view can be empty even while **All expenses** contains earlier submissions. Signing in does not change who created them. Submissions made without a verified identity remain labeled **Unverified submitter**; they are never retroactively verified.

If sign-in succeeds but tools fail, check [consent errors](07-troubleshooting.md#consent-errors-after-sign-in) before signing in again.

## Approve (or reject) someone else's expense

1. In Expense Desk chat, file a new $75 expense with a memo of your choosing, for example, `Printer paper and toner for the workshop`.
2. File a second expense under $50, for example, “Submit $30 for office supplies for our team.” Wait for your agent to approve it in the same conversation turn. Stay signed in; don't click Approve or send an approval request. Read the confirmation and inspect the expense: Created by is you, Decided by is your agent acting under its own application identity. If the expense remains pending, report the result to your instructor; a manual approval wouldn't demonstrate autonomous approval.
3. Ask to approve your own pending $75 expense by its ID, for example "Approve expense <your id>". Read the explanation that approving your own expense is not allowed. Expense Desk checks expense ownership and enforces this restriction.
4. In Expense Desk, choose **All expenses** and click **Refresh**. Select someone else's expense with **Pending** status and an amount within your $100 approval limit. If none are available, watch the instructor's demo or wait for another attendee to submit one and refresh again.
5. Decide whether to approve or reject the selected expense, then click **Approve** or **Reject**. The button sends `Approve expense <id>` or `Reject expense <id>` through the same agent conversation; you can also type your chosen request.
6. If another attendee decides your expense, click **Refresh** to see their decision. Your own chat refreshes your view after each turn.
7. Compare Created by with the deciding actor in Activity. Expand **Identity details** to inspect the full actor ID.

Your approval or rejection of someone else's eligible expense should succeed, while self-approval should fail with a reason. Ask the Expense Desk agent for your approval limit. The expected attendee limit is $100.

## Follow the credential requests

1. In the **Keycard console**, open **Applications → Agent App - \<your-github-handle> → Activity**. Open **Filters → Clear** to remove earlier filters.
2. Open **Filters → Actor**, search for your signed-in GitHub email, and select the matching person. Actor includes applications acting on that person's behalf.
3. Set **Filters → Resource → Expense MCP Resource**. Open a **Credential Issued** entry labeled `urn:ietf:params:oauth:grant-type:token-exchange`. Check **Delegation Chain** for your agent application **on behalf of your email**, and **Resource** for **Expense MCP Resource**. Use the time of your action as a secondary check.
4. Open **Applications → Expense MCP Actor → Activity**. Switching applications clears the filters, so set **Actor** to the same email again. Set **Resource** to **Ledger API**.
5. Open **Credential Issued**, again labeled `urn:ietf:params:oauth:grant-type:token-exchange`. Check that **Delegation Chain** shows **Expense MCP Actor on behalf of** your email and **Resource** is **Ledger API**.

The first exchange trades the signed-in access token addressed to your agent resource for a token addressed to Expense MCP. The second exchange is made by Expense MCP Actor: it trades the incoming MCP token for a token addressed to Ledger API. Your user identity continues through both, while the application making each credential request changes.

**Optional:** To narrow the events to one signed-in session, copy **Session** from an event’s **Overview** and apply it under **Filters → Session** in both applications’ Activity tabs.

To inspect the action on a specific expense, return to Expense Desk, select that expense, and open its **Activity** section. If you can't find the expected delegation chain, ask the instructor for help.

If your session ends after this exercise, share unclear steps or errors with your instructor.

## If you get stuck

From your resolved package path, restore the checkpoint:

```sh
cd "<package-path>"
uv run --locked --project agent python checkpoints/restore.py 03
```

Then restart MCP and the Expense Desk browser server, return to Expense Desk, and sign in again. Create fresh expenses if someone already decided the previous ones. If sign-in remains blocked, follow the instructor's paired demonstration.

The supplied browser already uses Keycard's SDK. For ambiguous searches and more policy examples, see the [take-home exercises](05-take-home.md).

When you explicitly ask to approve an existing expense by ID, Expense Desk acts on your behalf, including for amounts under $50. The separate automatic approval uses the agent’s application identity only for an eligible expense submitted in that same turn.

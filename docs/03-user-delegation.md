<!-- Generated from docs/attendee/ex03.md. Edit the source, then rebuild. -->
# Exercise 03: user delegation

Your Expense Desk agent can now act for a signed-in user. You'll approve a partner's expense and see why Expense Desk refuses approval of your own expenses.

## Sign in to Expense Desk

1. Keep the MCP and Expense Desk browser processes from Exercise 02 running. Open your configured Expense Desk URL.
2. Sign in with your GitHub account.
3. In the **Expense Desk browser chat**, ask “Which account am I using, and what is my approval limit?” and compare the result with Exercise 02. You should see your signed-in email. Choose **All expenses**, then select the expense ID you saved to inspect its Activity.

Your earlier submission belongs to the application that created it. **My expenses** shows submissions you create under your signed-in identity, so that view can be empty even while **All expenses** contains earlier submissions. Signing in does not change who created them. Submissions made without a verified identity remain labeled **Unverified submitter**; they are never retroactively verified.

If sign-in succeeds but tools fail, check [consent errors](07-troubleshooting.md#consent-errors-after-sign-in) before signing in again.

## Approve your partner's expense

1. File a new $75 expense with a memo of your choosing, for example, `Printer paper and toner for the workshop`.
2. File a second expense under $50, for example, “Submit $30 for office supplies for our team.” Wait for your agent to approve it in the same conversation turn. Stay signed in; don't click Approve or send an approval request. Read the confirmation and inspect the expense: Created by is you, Decided by is your agent acting under its own application identity. If the expense remains pending, report the result to your instructor; a manual approval wouldn't demonstrate autonomous approval.
3. Ask to approve your own pending $75 expense by its ID, for example "Approve expense <your id>". Read the explanation that approving your own expense is not allowed. Expense Desk checks expense ownership and enforces this restriction.
4. Exchange expense IDs with a partner.
5. Choose **All expenses**, select your partner's pending expense, and click **Approve**. This sends “Approve expense <id>” through the same agent conversation; you can also type that request.
6. After your partner decides your expense, click **Refresh** to see their decision. Your own chat refreshes your view after each turn.
7. Compare Created by with the deciding actor in Activity. Expand **Identity details** to inspect the full actor ID.

Partner approval should succeed, while self-approval should fail with a reason. Ask the Expense Desk agent for your approval limit. The expected attendee limit is $100.

## Follow the credential requests

1. In the **Keycard console**, open **Applications → Agent App - <your GitHub username> → Activity**. Open **Filters → Clear** to remove earlier filters. Choose a time range containing your run.
2. Open **Filters → Actor**, search for your signed-in GitHub email, and select the matching person. Actor includes applications acting on that person's behalf.
3. Set **Filters → Resource → Expense MCP Resource**. Open a **Credential Issued** entry labeled `urn:ietf:params:oauth:grant-type:token-exchange`. Check **Delegation Chain** for your agent application **on behalf of your email**, and **Resource** for **Expense MCP Resource**. Use the time of your action as a secondary check.
4. In that event's **Overview**, copy **Session**. Close the detail panel, then open **Filters → Session**, paste that ID under **Or enter an ID**, and click **Apply**. This narrows your authenticated run; a session can contain several tool calls.
5. Open **Applications → Expense MCP Actor → Activity**. Switching applications clears the filters, so set **Actor** to the same email and **Session** to the copied ID again. Set **Resource** to **Ledger API**.
6. Open **Credential Issued**, again labeled `urn:ietf:params:oauth:grant-type:token-exchange`. Verify **Delegation Chain: Expense MCP Actor on behalf of <your GitHub email>**, **Resource: Ledger API**, and the same **Session** in Overview.

The first exchange trades the signed-in access token addressed to your agent resource for a token addressed to Expense MCP. The second exchange is made by Expense MCP Actor: it trades the incoming MCP token for a token addressed to Ledger API. Your user identity continues through both, while the application making each credential request changes.

**Request** is useful inside one hop: copy an event's **Request ID**, then use **Filters → Request → Apply** to see events emitted under that request, such as issuance and its authorization decision. Use Actor and Session to trace across hops; each hop can have a different Request ID. Remove the Request filter using its chip's remove button before tracing another hop. Use **Filters → Clear** when starting a different exercise.

Actor + Session narrows the feed to your signed-in session, which can contain several tool calls. Use Expense Desk Activity to inspect the action on a specific expense. If you can't find the expected chain or session, ask the instructor to help trace a known event.

If your session ends after this exercise, share unclear steps or errors with your instructor.

## If you get stuck

From your resolved package path, restore the checkpoint:

```sh
cd "<package-path>"
uv run --locked --project agent python checkpoints/restore.py 03
```

Then restart MCP and the browser, and sign in again. Create fresh expenses if someone already decided the previous ones. If sign-in remains blocked, follow the instructor's paired demonstration.

The supplied browser already uses Keycard's SDK. For ambiguous searches and more policy examples, see the [take-home exercises](05-take-home.md).

When you explicitly ask to approve an existing expense by ID, Expense Desk acts on your behalf, including for amounts under $50. The separate automatic approval uses the agent’s application identity only for an eligible expense submitted in that same turn.

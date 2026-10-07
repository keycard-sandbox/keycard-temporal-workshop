<!-- Generated from docs/attendee/troubleshooting.md. Edit the source, then rebuild. -->
# Troubleshooting the workshop

Start with the process that reported the error. A browser sign-in can succeed while an MCP exchange fails; a server can answer HTTP requests while refusing authorization. Keep the exact error and the time you saw it.

## Find the matching Keycard activity

Open your application in Keycard and select **Activity**. Resources and providers have Activity tabs too. Use Outcome and Time range to narrow the feed, then open a matching row. Inspect its outcome, actor, related entity, and reason. Copy its event or request ID when asking an instructor for help, without copying credentials.

Use the zone Audit Log when you need events beyond one entity's feed. The same activity can appear under several entities; compare event IDs to recognize it across views. See Keycard's [Activity guide](https://docs.keycard.ai/admin/activities/) for the detail-panel fields.

## Use the right history

| View | What to inspect |
| --- | --- |
| Keycard Activity | Sign-in, credential issuance, and authorization outcomes for applications, resources, and providers. |
| Expense Desk Activity | Expense submissions, decisions, payment entries, and the actors Expense Desk recorded. |
| Temporal workflow history | Completed activities, timers, retries, and workflow recovery. |

A Keycard credential doesn't guarantee that Expense Desk will approve an expense. Expense Desk also checks ownership, approval limits, and whether another action changed the expense. Read the refusal in Expense Desk.

## Registration and configuration errors

| Symptom | What to check | Who fixes it |
| --- | --- | --- |
| GitHub sign-in doesn't open the workshop zone | Use [Exercise 02’s workshop SSO link](02-application-identity.md#join-or-sign-back-into-keycard) and your intended GitHub account for both joining and signing back in after logout. Direct sign-in at `console.keycard.ai` does not work for workshop accounts. Don't create another zone. | Instructor checks zone access and registration permissions. |
| `invalid_target` | Compare `AGENT_RESOURCE`, `MCP_URL`, or `LLM_RESOURCE` with the named resource's identifier, including port and path. | You fix your values; the instructor fixes shared resources. |
| `invalid_client` | Use the client ID and secret from the same credential on your own application. | You update `agent/.env` and restart the Expense Desk agent. |
| Lost client secret | Replace the credential under Application Credentials and copy both new values. | You update your file; don't replace another app's credentials. |
| Sign-in works, but exchange reports that the client can't exchange the token | Your app must provide the resource named by `AGENT_RESOURCE`. | You repair your Provides relationship. |
| Application-only calls fail at the Ledger API exchange | Check your app's `urn:agent:app:` prefix, then ask the instructor to inspect the shared policy and MCP configuration. | You fix your identifier; the instructor checks the second hop. |
| Model credential request fails | Confirm the model dependency matches the supplied `LLM_RESOURCE`. | You fix the dependency; the instructor checks the vault credential. |

Restart the affected process after changing `.env`; a running process still has its old configuration. If you change an app identifier, keep its prescribed prefix and update any corresponding local values.

## Browser sign-in errors

For a redirect mismatch, compare your application's Redirect URI with `EXPENSE_DESK_ORIGIN` plus `/callback`. Locally, use `EXPENSE_DESK_ORIGIN=http://localhost:8400` and register `http://localhost:8400/callback`. In Instruqt, preserve the supplied HTTPS origin, register the exact URL in `CALLBACK_URL.txt`, and open Expense Desk in its own window for sign-in.


If the callback reports a state mismatch, return to Expense Desk and start sign-in again. A stale callback tab or a process restart during sign-in can invalidate the original attempt.

Signing into the Keycard console with GitHub lets you configure your Expense Desk agent. Exercise 03's Expense Desk sign-in authorizes that Expense Desk agent to act for you. Your existing GitHub session might skip the password prompt; check the identity Expense Desk displays before exchanging expense IDs.

## Consent errors after sign-in

1. Open your application and confirm **Implicit** consent and all three dependencies from [Exercise 02](02-application-identity.md#add-dependencies-before-signing-in-to-expense-desk).
2. Correct any differences, then return to Expense Desk and try **Refresh**.
3. If an exchange still reports "User consent is required" or `insufficient_authorization`, ask an instructor to inspect the shared configuration. Bring the failing resource identifier and Keycard event ID.

## Application is not allowed to access OpenID Connect UserInfo

OpenID Connect UserInfo can appear in Resources without being selectable as an application dependency. Keep the three dependencies above. The instructor must configure shared UserInfo access before Exercise 02: the MCP requests `openid email` on every onward Ledger API exchange, including application-only calls. If Activity says your application is not allowed to access OpenID Connect UserInfo, give the instructor the event ID and timestamp. Do not create a replacement resource or reset your checkpoint.

After the instructor repairs shared access, retry the original tool call or click **Refresh**. A dependency added only to Expense MCP Actor does not address missing access for the attendee application named in the denial. Keep `openid email` in the onward exchange; signed-in Ledger API calls need verified email.

## Policy denials and expense refusals

For `access_denied`, inspect the Keycard event's reason. Correct your own registration if it names a mismatch; ask an instructor about shared policies. Re-authenticating doesn't change a policy decision.

A self-approval refusal or an expense above your $100 limit is an expected Expense Desk decision in Exercise 03. Use your partner's exact pending expense ID for the successful approval. If someone already decided the expense, create a fresh one rather than retrying the old decision.

## Expense Desk looks out of date

Your own chat refreshes the view after each turn, including a failed response. Click **Refresh** after shared activity or a partner's decision to update the list, selected expense, and Activity. An idle tab doesn't refresh, and switching tabs doesn't request an update. If a refresh fails, check the displayed error and click **Refresh** to retry.

## Services and workflow recovery

| Symptom | Next step |
| --- | --- |
| Connection refused or Expense Desk unavailable | Check the supplied MCP and browser processes. Open `http://localhost:8400`; ask an instructor if the local processes or shared service remain unavailable. A connection error isn't evidence of an authorization refusal. |
| Port already in use | Stop your previous copy of the process and restart the supplied command. Changing the MCP port also changes its registered audience. |
| Workflow stays open after worker restart | Use the original namespace and queue. Start the worker, not a new workflow. |
| You missed the workflow timer | Run a new workflow and wait for ActivityTaskCompleted and TimerStarted before stopping its worker. |
| Expected issuance doesn't appear in Activity | Check the worker application, time range, and zone Audit Log. Ask the instructor to correlate the run; the shared feed also contains other attendees' requests. |

Replace `<package-path>` with your actual absolute extracted folder and `NN` with the stage number:

```sh
cd "<package-path>"
uv run --locked --project agent python checkpoints/restore.py NN
```

The command finishes after restoring code. Restart the affected foreground processes in separate terminals and leave them running. Checkpoints preserve `.env` and don't undo expenses, create Keycard objects, or repair shared services.

## Activity or creation controls unavailable

In this workshop, missing Activity access or application/resource creation controls can mean you still have the Viewer role. Ask the instructor to grant Admin access, then refresh the console. Don't modify another attendee's registration to work around missing permissions.

## Email cannot be resolved

Expense Desk requires an email returned by Keycard OpenID Connect UserInfo for a signed-in person. A GitHub login or an email typed in chat is not a substitute. Ask the instructor to check that the zone identity provider supplies email, UserInfo requests succeed, and the delegated Ledger API exchange allows `openid email`. Do not change your subject identifier or paste tokens into chat. Missing email must be repaired at the provider; sign-in never verifies earlier submissions.

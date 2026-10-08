# Guide registration without duplicating it

Read Exercise 02 (`02-application-identity.md` in a package, `ex02.md` in source) in the documentation directory identified by `SKILL.md`. Follow its registration steps for console fields, dependencies, callbacks, and the current consent setting. Ask for the GitHub username before registration and reuse it in every applicable name and identifier. Reuse it if already given. Name the Keycard application `Agent App - <githubhandle>` so the handle remains readable in the console. Locally, use `EXPENSE_DESK_ORIGIN=http://localhost:8400` and redirect URI `http://localhost:8400/callback`. In Instruqt, keep the supplied HTTPS origin and register the exact URL in `CALLBACK_URL.txt`; sign in with Expense Desk in its own window. Preserve the hosted Temporal namespace `default` and queue `keycard-temporal-demo`. Use the fixed settings in Setup; do not ask attendees to obtain these values from an instructor.

Workshop console access uses only the SSO link provided in Exercise 02, both for first-time joining and for signing back in after logout. Direct sign-in at `console.keycard.ai` does not work for workshop accounts. Keep Expense Desk’s own Sign in flow separate from workshop console access.

Guide attendees to add these four resources in this order: their own agent resource, Expense MCP, LLM API, and OpenID Connect UserInfo. **OpenID Connect UserInfo** lets Expense Desk retrieve the signed-in user’s email from Keycard. Select the UserInfo resource.

Have the attendee enter credentials directly into `agent/.env`. Update known non-secret values while preserving supplied settings and unrelated edits. If the file is absent, start with `.env.example` and obtain missing private shared-service credentials from the instructor; never replace an existing file with the example.

After creating the application, follow Exercise 02 to create its credential under **Application Credentials → Add credential → Client ID & Secret**.

Run preflight with the agent runtime, then walk through Exercise 02's registration checklist. Local checks can't verify the credential pair, Provides, dependencies, consent, or registered callback. Restart the affected process after edits and verify the current exercise's operation.

Treat any consent workaround in Exercise 02 as workshop-specific. For a persistent failure, follow the attendee troubleshooting guide rather than repeating sign-in or changing shared configuration. The workshop uses `.env`; CLI-managed credentials and workload identity remain optional discussion topics.

For personal access outside the workshop, use [Keycard Workshop Registration](https://keycard-workshop-registration.fly.dev/) with an instructor-supplied access code. It adds the verified primary GitHub email to the personal signup allowlist; the attendee then continues to the Keycard console. This does not enroll them in the workshop organization or provision their own services. Keep Exercise 02's workshop SSO link for workshop access, and never ask the attendee to paste an access code or credentials into chat.

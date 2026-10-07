# Guide registration without duplicating it

Read Exercise 02 (`02-application-identity.md` in a package, `ex02.md` in source) in the documentation directory identified by `SKILL.md`. Follow its registration steps for console fields, dependencies, callbacks, and the current consent setting. Ask for the GitHub username before registration and reuse it in every applicable name and identifier. Reuse it if already given. Locally, use `EXPENSE_DESK_ORIGIN=http://localhost:8400` and redirect URI `http://localhost:8400/callback`. In Instruqt, keep the supplied HTTPS origin and register the exact URL in `CALLBACK_URL.txt`; sign in with Expense Desk in its own window. Preserve the hosted Temporal namespace `default` and queue `keycard-temporal-demo`. Use the fixed settings in Setup; do not ask attendees to obtain these values from an instructor.

The attendee dependency list contains their own agent resource, Expense MCP, and the LLM API resource. Do not ask them to find or add OpenID Connect UserInfo in the dependency picker. If sign-in or email resolution fails, follow the troubleshooting guide and route shared UserInfo access checks to the instructor.

Have the attendee enter credentials directly into `agent/.env`. Update known non-secret values while preserving supplied settings and unrelated edits. If the file is absent, start with `.env.example` and obtain missing private shared-service credentials from the instructor; never replace an existing file with the example.

After creating the application, follow Exercise 02 to create its credential under **Application Credentials → Add credential → Client ID & Secret**.

Run preflight with the agent runtime, then walk through Exercise 02's registration checklist. Local checks can't verify the credential pair, Provides, dependencies, consent, or registered callback. Restart the affected process after edits and verify the current exercise's operation.

Treat any consent workaround in Exercise 02 as workshop-specific. For a persistent failure, follow the attendee troubleshooting guide rather than repeating sign-in or changing shared configuration. The workshop uses `.env`; CLI-managed credentials and workload identity remain optional discussion topics.

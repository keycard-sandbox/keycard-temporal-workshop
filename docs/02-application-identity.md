<!-- Generated from docs/attendee/ex02.md. Edit the source, then rebuild. -->
# Exercise 02: application identity

In Exercise 01, anyone could supply a name when submitting an expense. Now you'll give your Expense Desk agent its own identity so it can record which application made the request.

Stop the browser and starter MCP processes.

## Join or sign back into Keycard

1. Visit [the workshop SSO link](https://id.keycard.ai/openid/connect/login?tenant=v6f1suvmlhp7k4a21bzyqp80w3&iss=https%3A%2F%2Fkeycard-temporal-workshop.us.auth0.com%2F&target_link_uri=https%3A%2F%2Fconsole.keycard.ai).
2. Sign in with your GitHub account. On your first join, complete both consent prompts: authorize access through GitHub, then authorize Keycard. New workshop members start with Viewer access.
3. In the Keycard console, you should see "Workshop AIE NYC" in the upper left corner after signing in.
4. Tell Kim when you've joined. Kim will grant Admin access to create your agent registration and inspect Activity. After Kim confirms, refresh Keycard and check that you can see buttons to create applications and resources. Contact Kim if the controls are missing.

Use this same workshop SSO link to join for the first time and to sign back in whenever you are logged out. Bookmark it. Workshop accounts cannot sign in through `console.keycard.ai` directly; the SSO link takes you to the console after authentication. If you have trouble accessing Keycard, ask an instructor.

You can see other attendees' registrations because everyone uses the same Keycard organization and shared services.

## Tour the Keycard console

In the Keycard console, browse **Applications**, **Resources**, and **Providers**. Your instructors have configured the shared Expense MCP Actor application and the Expense MCP Resource, Ledger API, and LLM API resources. The Expense Desk backend appears as **Ledger API**.

In the Keycard console, open Applications → **Agent App - Example** and Resources → **Agent Resource - Example** to preview what you're about to create. Each application, resource, and provider opens on its **Activity** tab, where you can see credential requests. (Note: this is separate from the **Activity** section on each expense in Expense Desk, which records what happened to that expense.) The gear icon in the upper right shows settings such as name, identifier, etc.

In the Keycard console, open Resources → **Expense MCP Resource**. Its configured scopes are `expense:read`, `expense:write`, `expense:approve`, and `expense:settle`. Your agent requests the scope for the expense tool it calls. The instructors configured this shared resource; leave its settings unchanged.

### Applications and resources

When you send a letter, you identify both the sender and the destination. Keycard registrations describe similar roles: an **application** identifies the software requesting access, and a **resource** identifies what it needs to access. An access token's **audience** (`aud`) names the resource that should receive it.

Your Expense Desk agent has both roles. When you sign in, it receives a token addressed to its resource. When it calls Expense MCP, it authenticates as its application and asks Keycard to exchange that token for one addressed to Expense MCP. Connecting the agent's application and resource lets it make this exchange on your behalf.

Now follow the request one step further. The MCP server receives the token addressed to **Expense MCP Resource**, then authenticates as **Expense MCP Actor** to exchange it for a Ledger API token. These registrations describe the same running server: it receives requests from your agent and makes requests to Ledger API. Your instructors have configured both registrations.

The **Temporal Worker** application identifies the background program that runs jobs assigned by Temporal. Temporal tracks the job’s progress, and the worker uses Keycard to obtain credentials for Ledger API when it needs access. The instructors manage this registration, so leave it unchanged.

## Create your application in Keycard

Start with your agent's application registration. Then you'll create its resource and connect the two so the agent can act on your behalf after you sign in with GitHub.

Use your GitHub handle wherever you see `<your-github-handle>`, without the angle brackets or `@`. Keep the same spelling throughout. Each attendee needs unique identifiers since you're working in a shared space.

1. In the Keycard console, open **Applications** and click **Add Application**.
2. Enter the following values, using your own handle.

   | Field | Value |
   | --- | --- |
   | Name | `Agent App - <your-github-handle>` |
   | Identifier | `urn:agent:app:<your-github-handle>` |
   | Consent | Implicit |
   | Redirect URL | Local: `http://localhost:8400/callback`. Instruqt: the exact URL from `CALLBACK_URL.txt`. |


   Leave **Proxy MCP tools** off. That option creates a gateway that exposes tools from upstream MCP servers through one generated endpoint. Here Expense Desk calls the supplied Expense MCP endpoint directly; its SDK authentication and onward Ledger API exchange are the behavior you are learning. See [Proxy MCP Tools](https://docs.keycard.ai/admin/unified-access-gateway/).

3. Create the application.

For local use, register `http://localhost:8400/callback`, matching `EXPENSE_DESK_ORIGIN=http://localhost:8400`. In Instruqt, run `cat CALLBACK_URL.txt` from the package root and register that exact HTTPS URL; keep the matching `EXPENSE_DESK_ORIGIN` supplied in `agent/.env`. The callback returns your browser to Expense Desk after sign-in.

Use the short application name `Agent App - <your-github-handle>` so GitHub handles remain readable in the Keycard UI. Keep the literal identifier prefix unchanged.

## Create your resource in Keycard

Your agent also needs a resource of its own. This resource is the destination for your sign-in token. The sign-in token is a *subject* token because it represents the person the agent acts on behalf of. The agent sends the subject token to Keycard to exchange it for an MCP server access token.

1. In the Keycard console, open **Resources** and click on **Add Resource** → **Add Manually**.
2. Enter the following values.

   | Field | Value |
   | --- | --- |
   | Name | `Agent Resource - <your-github-handle>` |
   | Identifier | `urn:agent:resource:<your-github-handle>` |
   | Credential provider | Zone Provider |
   | Provided by Application | `Agent App - <your-github-handle>` |

3. Save the resource.
4. In the Keycard console, return to Applications → **Agent App - \<your-github-handle>** and click on the **Provides** tab. Your agent resource should already appear there because you selected **Provided by Application** when you created it.

This relationship tells Keycard that your application can exchange sign-in tokens addressed to your agent resource. Your agent uses that exchange to request an MCP server access token on your behalf. Without this relationship, Keycard refuses the exchange.

You chose **Zone Provider** because the workshop's services check tokens that Keycard issues. Zone Provider means Keycard itself issues the credential for this resource.

## Add dependencies to your Keycard application

**Provides** means "my application serves this resource." **Depends** means "my application requests credentials for this resource."

In the Keycard console, open **Applications → Agent App - \<your-github-handle> → Dependencies**, click **Add dependency**, and add these four resources:

| Resource | Identifier | Why your Expense Desk agent needs it |
| --- | --- | --- |
| `Agent Resource - <your-github-handle>` | `urn:agent:resource:<your-github-handle>` | Sign-in requests a subject token for this audience. |
| Expense MCP Resource (already configured by instructor) | `http://localhost:8100/mcp` | Your Expense Desk agent calls the expense tools. |
| LLM API resource (already configured by instructor) | `https://api.openai.com` | Your Expense Desk agent requests the LLM credential from Keycard's vault. |
| OpenID Connect UserInfo | Select the UserInfo resource. | Retrieves the signed-in user’s email from Keycard. |

**OpenID Connect UserInfo** lets Expense Desk retrieve the signed-in user’s email from Keycard. Select the UserInfo resource.

Your Expense Desk agent application needs two connections to its own resource:

The Dependencies connection lets the agent request a subject token when you sign in. The Provides connection lets it exchange that token for credentials to call Expense MCP on your behalf.

Each attendee creates a separate agent resource. Everyone uses the same Expense MCP, LLM API, and UserInfo resources.

Your agent's dependencies are now set. The MCP application handles Ledger API access, and the instructor manages its shared configuration. Leave that configuration unchanged.

## Create your application credentials

1. Open your application, select the **Application Credentials** tab, and click **Add credential**. Choose **Client ID & Secret**.
2. The console shows the secret only once, so copy both to `agent/.env` in your editor (the **Editor** tab in Instruqt), as shown below, before you click **Done**.

```ini
KEYCARD_CLIENT_ID=YOUR-CLIENT-ID
KEYCARD_CLIENT_SECRET=YOUR-CLIENT-SECRET
AGENT_RESOURCE=urn:agent:resource:<your-github-handle>
```

If you lose the secret, replace the credential and update both values.

`KEYCARD_CLIENT_ID` and `KEYCARD_CLIENT_SECRET` verify your agent application's identity. `AGENT_RESOURCE` is the identifier of the resource you created in [Create your resource in Keycard](#create-your-resource-in-keycard). Leave the other lines alone, including `KEYCARD_ISSUER`, `MCP_URL`, and the LLM settings, which the instructors supplied. Confirm changes were auto-saved.

### Choose credentials for other environments

A client ID and secret are acceptable for local development and this workshop's supplied runtime. The secret lets your Expense Desk agent prove its identity without configuring a deployment platform first. Keep it in `.env`. Don't paste it into chat, a screenshot, or a commit.

For production, use **Workload Identity Federation (WIF)** where your hosting platform supports it. The platform attests to your application's identity, and Keycard verifies that proof, so your app doesn't need a long-lived client secret on disk. See [application credential options](https://docs.keycard.ai/concepts/applications/#workload-identity).

The **Keycard CLI** provides another path for agents and processes you run through it: it brokers credentials into the process rather than requiring you to save them in `.env`. You can use this approach locally too. Choose WIF for a hosted workload or a supported CLI-managed runtime for your Expense Desk agent. Configure the runtime's authentication before running it unattended. See the [Keycard CLI guide](https://docs.keycard.ai/cli/).

We'll keep Client ID & Secret for the required exercises so you can use the supplied configuration. WIF and CLI setup are outside this session.

## Update the Expense Desk agent `.env`

Confirm you saved your application credentials and resource identifier in `agent/.env` as shown in [Create your application credentials](#create-your-application-credentials).

Locally, keep `EXPENSE_DESK_ORIGIN=http://localhost:8400`. In Instruqt, preserve the supplied HTTPS origin and use Expense Desk in its own window for sign-in.

Keep the fixed `KEYCARD_ISSUER`, `MCP_URL`, and LLM settings from [Setup](00-setup.md#fixed-workshop-configuration). These values refer to different parts of the system:

| Value | Meaning |
| --- | --- |
| `KEYCARD_ISSUER` | `https://ho0llbxj2o7enn7l48tuzic25t.keycard.cloud` — the shared workshop issuer. |
| `AGENT_RESOURCE` | Your personal resource identifier, matching the console. |
| `MCP_URL` | `http://localhost:8100/mcp` — the endpoint and registered resource identifier. |
| `EXPENSE_DESK_ORIGIN` | `http://localhost:8400` — the browser app origin. |
| Application Redirect URL | `http://localhost:8400/callback`. |

Identifiers and redirect URLs must match exactly. A changed port, trailing slash, or `127.0.0.1` in place of `localhost` changes the value.

Zone Provider means Keycard issues credentials for your agent resource. Select the built-in Zone Provider, not the external Auth0 or GitHub provider used for human sign-in.

## Check your registration

Before switching to application authentication, confirm:

- Your app identifier starts with `urn:agent:app:` and uses your GitHub handle.
- Your app depends on your resource, Expense MCP, LLM API, and OpenID Connect UserInfo.
- Your app has Implicit consent and the exact callback URL.
- Your resource configuration uses Zone Provider, and your application provides it.
- `agent/.env` has values for your Keycard application's client ID, client secret, and your resource identifier.

Now that Keycard knows about your agent, you'll switch the agent's code over to use its own identity. The checkpoint preserves `.env`; it changes local code, so it can't create or repair your Keycard registration.

## Switch to application authentication

Use the absolute package path you resolved during setup in place of `<package-path>` below. Stop the two starter processes with Control-C first.

1. In your editor, compare `agent/agent_auth.py` with `checkpoints/02-authenticated/agent/agent_auth.py`. Read `mint`, `ZoneTokenAuth`, and `LLMVaultAuth` in `agent/keycard.py` to see where credentials are requested.
2. In a terminal, apply the checkpoint:

   ```sh
   cd "<package-path>"
   uv run --locked --project agent python checkpoints/restore.py 02
   ```

   This command finishes after replacing `agent/agent_auth.py` and `mcp-server/mcp_auth.py`. Save any exercise edits you want to keep first. It preserves `.env` and does not change service data or console settings.
3. Start the MCP server in that terminal:

   ```sh
   cd "<package-path>"
   uv run --locked --project mcp-server python mcp-server/server.py
   ```

   The MCP server runs the expense tools in its Python environment. Keep this terminal open so your agent can call them.
4. Open another terminal and start Expense Desk:

   ```sh
   cd "<package-path>"
   uv run --locked --project agent python agent/web.py
   ```

   Open your configured Expense Desk URL, refresh the page, and choose **Continue as Expense Desk Agent**. Keep this browser server running. Your agent acts as its registered application until you sign in.

## Check which identity Expense Desk records

1. In **Expense Desk browser chat**, enter "Which account am I using, and what is my approval limit?"
2. Ask it to file a new $75 workshop expense under someone else's name. Save the expense ID and read Created by in the agent’s confirmation. The Expense Desk agent should record your registered application regardless of the provided name.
3. In the **Keycard console**, open **Applications → Agent App - \<your-github-handle> → Activity**. Click the Filter icon. If any filters are active, clear them, then set Resource → Expense MCP Resource. Open a **Credential Issued** event for your application. This credential came from a client credentials grant, and it identifies your application as the Actor accessing the Expense MCP Resource.
4. With the instructor, stay in the Keycard console and open **Applications → Expense MCP Actor → Activity**, clear old filters, and set **Resource → Ledger API**. The onward event is **Credential Issued**, labeled `urn:ietf:params:oauth:grant-type:token-exchange`. Inspect its delegation details to confirm the application subject from this demonstration.

Expense MCP Actor authenticates as the MCP server and exchanges the token it received for a token addressed to the Ledger API on behalf of your Agent App (the agent acting as itself). This feed contains credential requests from the whole workshop. Follow the instructor's selected example and confirm its application subject in the delegation details.

Your Expense Desk agent requests MCP and LLM credentials when it needs them. This run has no signed-in user. Return to Expense Desk, select the expense you just created, and inspect its **Activity** section. In Exercise 03, you'll sign in to Expense Desk without restarting its server.

## If you get stuck

Follow [Switch to application authentication](#switch-to-application-authentication) to restore the authentication files and restart both processes. For registration errors, use [Check your registration](#check-your-registration) and [Troubleshooting](07-troubleshooting.md) to find the failing step.

Confirm a successful authenticated tool call before moving on.

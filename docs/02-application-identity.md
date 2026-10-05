<!-- Generated from docs/attendee/ex02.md. Edit the source, then rebuild. -->
# Exercise 02: application identity

In Exercise 01, anyone could supply a name when submitting an expense. Now you'll give your Expense Desk agent its own identity so it can record which application made the request.

Stop the browser and starter MCP processes.

## Join Keycard

1. Visit [the workshop join link](https://id.keycard.ai/openid/connect/login?tenant=v6f1suvmlhp7k4a21bzyqp80w3&iss=https%3A%2F%2Fkeycard-temporal-workshop.us.auth0.com%2F&target_link_uri=https%3A%2F%2Fconsole.keycard.ai).
2. Sign in with your GitHub account. On your first join, complete both consent prompts: authorize access through GitHub, then authorize Keycard. New workshop members start with Viewer access.
3. You should see "Workshop AIE NYC" in the upper left corner after signing in.
4. Tell Kim when you've joined. Kim will grant Admin access to create your agent registration and inspect Activity. After Kim confirms, refresh Keycard and check that you can see buttons to create applications and resources. Contact Kim if the controls are missing.

If you have trouble accessing Keycard, ask an instructor.

You can see other attendees' registrations because everyone uses the same Keycard organization and shared services.

## Look around Keycard

Open Applications, Resources, and Providers. Your instructors have configured the shared Expense MCP Actor application and the Expense MCP Resource, Ledger API, and LLM API resources. Look at `Agent App - Example` and `Agent Resource - Example` for a preview of the registrations you'll create for your agent. In Keycard, the Expense Desk backend appears as **Ledger API**.

Applications, Resources, and Providers open on **Activity**, where you can inspect credential requests. Open the `Agent App - Example` application's Activity and look at the existing logs. Use the gear icon in the upper right to view settings such as name and identifier. You'll inspect your own Expense Desk agent's credential requests later.

### Applications and resources

When you send a letter, you identify both the sender and the destination. Keycard registrations describe similar roles: an **application** identifies the software requesting access, and a **resource** identifies what it needs to access. An access token's **audience** (`aud`) names the resource that should receive it.

Your Expense Desk agent has both roles. When you sign in, it receives a token addressed to its resource. When it calls Expense MCP, it authenticates as its application and asks Keycard to exchange that token for one addressed to Expense MCP. Connecting the agent's application and resource lets it make this exchange on your behalf.

Now follow the request one step further. The MCP server receives the token addressed to **Expense MCP Resource**, then authenticates as **Expense MCP Actor** to exchange it for a Ledger API token. These registrations describe the same running server: it receives requests from your agent and makes requests to Ledger API. Your instructors have configured both registrations.

You'll also see **Temporal Worker** (`urn:keycard:temporal:worker`). The instructor manages it; leave that registration unchanged.

## Create your application

Start with your agent's application registration. Then you'll create its resource and connect the two so the agent can act on your behalf after you sign in with GitHub.

Use your GitHub handle wherever you see `<githubhandle>`, without the angle brackets or `@`. Keep the same spelling throughout. Each attendee needs unique identifiers since you're working in a shared space.

1. Open **Applications** and click **Add Application**.
2. Enter the following values, using your own handle.

   | Field | Value |
   | --- | --- |
   | Name | `Expense Desk Agent - <githubhandle>` |
   | Identifier | `urn:agent:app:<githubhandle>` |
   | Consent | Implicit |
   | Redirect URI | Your instructor-supplied Expense Desk preview origin followed by `/callback` |


   Leave **Proxy MCP tools** off. That option creates a gateway that exposes tools from upstream MCP servers through one generated endpoint. Here Expense Desk calls the supplied Expense MCP endpoint directly; its SDK authentication and onward Ledger API exchange are the behavior you are learning. See [Proxy MCP Tools](https://docs.keycard.ai/admin/unified-access-gateway/).

3. Create the application.

Keep the `urn:agent:app:` prefix exactly. The workshop's shared Ledger API policy matches this prefix.

For local use, the redirect URI is `http://localhost:8400/callback`. For Instruqt, use your supplied HTTPS preview origin followed by `/callback`, matching `EXPENSE_DESK_ORIGIN`. The callback returns your browser to Expense Desk after sign-in.

The application name distinguishes software from people in Activity. Keep the literal identifier prefix unchanged.

## Create the resource your application provides

Create the resource that identifies your agent as the destination for your sign-in token. When the agent presents this token to Keycard for exchange, we call it the **subject token**: it represents the user the agent acts for.

1. Open **Resources**, click **Add Resource**, and choose **Add Manually** if the console offers the catalog.
2. Enter these values.

   | Field | Value |
   | --- | --- |
   | Name | `Agent Resource - <githubhandle>` |
   | Identifier | `urn:agent:resource:<githubhandle>` |
   | Credential provider | Zone Provider |
   | Provided by Application | `Expense Desk Agent - <githubhandle>` |

3. Save the resource. Open its **Scopes** tab and leave the scope list empty. This resource supplies the audience for sign-in and onward exchange. Expense MCP and Ledger API use their own operation scopes on later hops.
4. Return to your application and inspect **Provides**. Your resource should already appear because you selected **Provided by Application** during creation. This links the destination to the application that serves it and can exchange tokens addressed to it.

Choose **Zone Provider** because the workshop services validate Keycard-issued tokens. Credential providers determine what Keycard returns for a resource:

| Provider | Credential Keycard returns |
| --- | --- |
| Zone Provider | A Keycard-issued token for your service, as used by the agent, Expense MCP, and Ledger API. |
| External OAuth provider | A connected user's provider-issued credential for that provider's API. |
| Vault provider | A stored secret, such as the model API credential used here. |

GitHub participates in sign-in; that is distinct from choosing who issues a resource's access credential. See [credential provider concepts](https://docs.keycard.ai/concepts/resources/).

## Add dependencies before signing in to Expense Desk

**Provides** means "my application serves this resource." **Depends** means "my application requests credentials for this resource." These point in different directions: receiving a token does not by itself authorize every downstream call.

On your application, open **Dependencies**, click **Add dependency**, and connect all four resources:

| Resource | Identifier | Why your Expense Desk agent needs it |
| --- | --- | --- |
| Your Expense Desk agent resource | `urn:agent:resource:<githubhandle>` | Sign-in requests a subject token for this audience. |
| Expense MCP Resource (already configured by instructor) | `http://localhost:8100/mcp` | Your Expense Desk agent calls the expense tools. |
| OpenID Connect UserInfo (built in) | Select the zone’s built-in resource | Resolves the signed-in person’s email. |
| LLM API resource (already configured by instructor) | The supplied `LLM_RESOURCE` (`https://api.openai.com`) | Your Expense Desk agent requests the LLM credential from Keycard's vault. |

Your Expense Desk agent application needs two connections to its own resource:

The Dependencies connection lets the agent request a subject token when you sign in. The Provides connection lets it exchange that token for credentials to call Expense MCP on your behalf.

Each attendee creates a separate agent resource. Everyone uses the same Expense MCP and LLM API resources.

Your agent's dependencies are now set. The MCP application handles Ledger API access, and the instructor manages its shared configuration. Leave that configuration unchanged.

## Create your application credentials

1. Open your application, select **Application Credentials**, and click **Add credential**.
2. Choose **Client ID & Secret**.
3. Copy both values into `agent/.env` before clicking **Done**. The console shows the secret once. If you lose it, replace that credential and update both values in your file.

### Choose credentials for other environments

A client ID and secret are acceptable for local development and this workshop's supplied runtime. The secret lets your Expense Desk agent prove its identity without configuring a deployment platform first. Keep it in `.env`. Don't paste it into chat, a screenshot, or a commit.

For production, use **Workload Identity Federation (WIF)** where your hosting platform supports it. The platform attests to your application's identity, and Keycard verifies that proof, so your app doesn't need a long-lived client secret on disk. See [application credential options](https://docs.keycard.ai/concepts/applications/#workload-identity).

The **Keycard CLI** provides another path for agents and processes you run through it: it brokers credentials into the process rather than requiring you to save them in `.env`. You can use this approach locally too. Choose WIF for a hosted workload or a supported CLI-managed runtime for your Expense Desk agent. Configure the runtime's authentication before running it unattended. See the [Keycard CLI guide](https://docs.keycard.ai/cli/).

We'll keep Client ID & Secret for the required exercises so you can use the supplied configuration. WIF and CLI setup are outside this session.

## Update the Expense Desk agent `.env`

Edit these fields in `agent/.env`:

```dotenv
KEYCARD_CLIENT_ID=<client ID from your application credential>
KEYCARD_CLIENT_SECRET=<client secret from application credential>
AGENT_RESOURCE=urn:agent:resource:<githubhandle>
EXPENSE_DESK_ORIGIN=http://localhost:8400
```

For a hosted workshop, replace `http://localhost:8400` with your supplied Expense Desk preview origin.

Keep the supplied `KEYCARD_ISSUER`, `MCP_URL`, and LLM settings. These values refer to different parts of the system:

| Value | Meaning |
| --- | --- |
| `KEYCARD_ISSUER` | The shared workshop's Keycard issuer URL. Keep the instructor's exact value. |
| `AGENT_RESOURCE` | Your personal resource identifier, matching the console. |
| `MCP_URL` | The MCP endpoint and registered resource identifier, including `/mcp`. |
| `EXPENSE_DESK_ORIGIN` | The browser app's origin (where the agent displays). |
| Application Redirect URI | The agent's origin followed by `/callback`. |

Identifiers and redirect URIs must match exactly. A changed port, trailing slash, or `127.0.0.1` in place of `localhost` changes the value.

Zone Provider means Keycard issues credentials for your agent resource. Select the built-in Zone Provider, not the external Auth0 or GitHub provider used for human sign-in.

The built-in **OpenID Connect UserInfo** dependency supplies the signed-in email; the agent and MCP resources still use Zone Provider.

## Check your registration

Before switching to application authentication, confirm:

- Your app identifier starts with `urn:agent:app:` and uses your GitHub handle.
- Your resource uses Zone Provider, has no scopes, and your app provides it.
- Your app depends on your resource, Expense MCP, OpenID Connect UserInfo, and the supplied LLM resource.
- Your app has Implicit consent and the exact callback URL.
- Your `.env` contains your own credential pair and resource identifier.

Next, you'll apply the checkpoint and restart the processes with your new configuration. The checkpoint preserves `.env`; it changes local code, so it can't create or repair your Keycard registration.

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

   Open your configured Expense Desk URL and choose **Continue as Expense Desk Agent**. Keep this browser server running. Your agent acts as its registered application until you sign in.

## Check which identity Expense Desk records

1. In **Expense Desk browser chat**, enter "Which account am I using, and what is my approval limit?"
2. Ask it to file a new $75 workshop expense under someone else's name. Save the expense ID and read Created by in the agent’s confirmation. The Expense Desk agent should record your registered application regardless of the provided name.
3. In the **Keycard console**, open **Applications → Expense Desk Agent - <your GitHub username> → Activity**. Clear earlier filters with **Filters → Clear** and set **Resource → Expense MCP Resource**. Inspect **Credential Issued** for your application. This initial credential uses client credentials and identifies your application.
4. With the instructor, open **Applications → Expense MCP Actor → Activity**, clear old filters, and set **Resource → Ledger API**. The onward event is **Credential Issued**, labeled `urn:ietf:params:oauth:grant-type:token-exchange`. Inspect its delegation details to confirm the application subject from this demonstration.

Expense MCP Actor authenticates as the MCP server and exchanges the token it received for a token addressed to the Ledger API. This feed contains credential requests from the whole workshop. Follow the instructor's selected example and confirm its application subject in the delegation details.

Your Expense Desk agent requests MCP and LLM credentials when it needs them. This run has no signed-in user. Inspect the expense's Activity in the same browser. In Exercise 03, you'll sign in without restarting it.

## If you get stuck

Follow [Switch to application authentication](#switch-to-application-authentication) to restore the authentication files and restart both processes. For registration errors, use [Check your registration](#check-your-registration) and [Troubleshooting](07-troubleshooting.md) to find the failing step.

Confirm a successful authenticated tool call before moving on.

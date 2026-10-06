---
slug: application-identity
id: ncnmglwnp6hs
type: challenge
title: 'Exercise 02: Application identity'
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
- id: xjpko1x3xzth
  title: Expense Desk
  type: service
  hostname: workshop
  path: /
  port: 8400
- id: fnpf0bzyz9yg
  title: Keycard
  type: website
  url: https://console.keycard.ai
  new_window: true
- id: nn2xtezak31z
  title: Editor
  type: code
  hostname: workshop
  path: /root/workshop
- id: v62nx1undplb
  title: Terminal
  type: terminal
  hostname: workshop
  workdir: /root/workshop
difficulty: intermediate
timelimit: 1800
enhanced_loading: null
---

In Exercise 01, anyone could type any name when they submitted an expense.
The shared key let the request in, and the Ledger API recorded whatever name it got.

In this exercise, you'll give your Expense Desk agent its own identity in Keycard.
You'll register an application for it and connect it to the resources it needs.
Then you'll switch the agent from the shared key to Keycard credentials.
When you're done, the Ledger API records which application made each request.
The name someone types won't matter.

You'll need a GitHub account to sign in to Keycard.
Use your GitHub handle wherever you see `YOUR-GITHUB-HANDLE`, without the `@`.
Keep the same spelling everywhere.
Everyone in the room shares one Keycard organization, so each identifier has to be unique.

## Step 1: Joining Keycard

Everyone in the workshop joins the same Keycard organization.
You'll sign in with GitHub, so there's no new account to create.

Open the [workshop join link](https://id.keycard.ai/openid/connect/login?tenant=v6f1suvmlhp7k4a21bzyqp80w3&iss=https%3A%2F%2Fkeycard-temporal-workshop.us.auth0.com%2F&target_link_uri=https%3A%2F%2Fconsole.keycard.ai) and sign in with your GitHub account.
The first time you join, you'll see two consent prompts.
Approve both: the first authorizes access through GitHub, and the second authorizes Keycard.

Once you've signed in, you should see **Workshop AIE NYC** in the upper left corner.

New members start with Viewer access, which can look but can't create anything.
Tell an instructor that you've joined, and they'll grant you Admin access.
After they confirm, refresh the page and check that you can see the buttons to create applications and resources.

You can reach the console again later from the [button label="Keycard" background="#444CE7"](tab-1) tab.

Now that you're in the workshop organization, take a quick tour before you build anything.

## Step 2: Touring the Keycard console

Open **Applications**, **Resources**, and **Providers**.
The instructors already set up the shared **Expense MCP Actor** application.
They also set up three resources: **Expense MCP Resource**, **Ledger API**, and **LLM API**.
In Keycard, the expense service that stores everything appears as **Ledger API**.

Keycard uses two kinds of registrations, and it helps to think of them like a letter.
When you send a letter, you write down who it's from and where it's going.
An *application* is the sender: the software asking for access.
A *resource* is the destination: the thing it wants to reach.
An access token's *audience* names the resource that should receive it.

Your Expense Desk agent plays both roles.
When you sign in, it receives a token addressed to its own resource.
When it calls the MCP server, it signs in as its application.
Then it asks Keycard to trade that token for one addressed to Expense MCP.

The MCP server works the same way one step further down.
It receives the token addressed to **Expense MCP Resource**.
Then it signs in as **Expense MCP Actor** and trades that token for a Ledger API token.
Those two registrations describe one running server.

Open **Agent App - Example** and **Agent Resource - Example** to preview what you're about to create.
Each application, resource, and provider opens on its **Activity** tab, where you can see credential requests.
The gear icon in the upper right shows settings such as name and identifier.

You'll also see **Temporal Worker** with the identifier `urn:keycard:temporal:worker`.
The instructors manage it for Exercise 04, so leave it unchanged.

Now that you know your way around, you'll find the one value that's specific to your sandbox.

## Step 3: Finding your callback URL

In Exercise 03, you'll sign in to Expense Desk.
After sign-in, Keycard sends your browser back to a *callback URL* on your Expense Desk.
Keycard only sends people back to a URL that matches one you registered.
You need yours before you create the application.

Each sandbox has its own HTTPS address.
Your sandbox wrote the callback for that address to a file when it started.
Click on the [button label="Terminal" background="#444CE7"](tab-3) tab and type the following command to print it:

```bash,run
cat CALLBACK_URL.txt
```

You'll see a URL like this one, with your sandbox's ID in place of `SANDBOX-ID`:

```bash,nocopy
https://workshop-8400-SANDBOX-ID.env.play.instruqt.com/callback
```

Copy the whole URL.
A changed character, an extra slash, or a missing `/callback` makes Keycard treat it as a different address.

Your sandbox also wrote the matching address to `agent/.env` as `EXPENSE_DESK_ORIGIN`, so you won't need to change that line.

Now that you have your callback URL, you can register your agent.

## Step 4: Creating your application

Start with the application, the registration that identifies your agent as the software making requests.

In the Keycard console, open **Applications** and click on **Add Application**.
Enter the following values, using your own GitHub handle:

| Field | Value |
| --- | --- |
| Name | `Expense Desk Agent - YOUR-GITHUB-HANDLE` |
| Identifier | `urn:agent:app:YOUR-GITHUB-HANDLE` |
| Consent | Implicit |
| Redirect URI | The callback URL from Step 3 |

Leave **Proxy MCP tools** off.
That option creates a gateway that exposes tools from other MCP servers through one generated endpoint.
Here, Expense Desk calls the Expense MCP server directly, and that direct connection is what you're learning.

Create the application.

Keep the `urn:agent:app:` prefix exactly as shown.
The workshop's shared Ledger API policy matches on that prefix.
The application name also keeps software apart from people in Activity.

Now that the application exists, you'll create the resource it provides.

## Step 5: Creating your resource

Your agent also needs a resource of its own.
This resource is the destination for your sign-in token.
The agent hands that token to Keycard to exchange it.
At that point it's called the *subject token*, because it stands for the person the agent acts for.

Open **Resources**, click on **Add Resource**, and choose **Add Manually** if the console offers a catalog.
Enter the following values:

| Field | Value |
| --- | --- |
| Name | `Agent Resource - YOUR-GITHUB-HANDLE` |
| Identifier | `urn:agent:resource:YOUR-GITHUB-HANDLE` |
| Credential provider | Zone Provider |
| Provided by Application | `Expense Desk Agent - YOUR-GITHUB-HANDLE` |

Save the resource.
Open its **Scopes** tab and leave the scope list empty.
This resource only supplies the audience for sign-in and the exchanges that follow.
Expense MCP and the Ledger API use their own scopes on later hops.

Return to your application and look at **Provides**.
Your resource should already appear there, because you picked **Provided by Application** when you created it.

You chose **Zone Provider** because the workshop's services check tokens that Keycard issues.
Zone Provider means Keycard itself issues the credential for this resource.
Other providers return other things.
One returns a credential from an outside service, and another returns a stored secret like the model's API key.
GitHub takes part in signing you in, but that's separate from deciding who issues a resource's credential.

Now that your application provides a resource, you'll tell Keycard which resources it needs to call.

## Step 6: Adding dependencies

**Provides** means "my application serves this resource."
**Depends** means "my application asks for credentials to this resource."
They point in opposite directions.
Receiving a token doesn't, by itself, allow every call that comes after it.

On your application, open **Dependencies**, click on **Add dependency**, and connect all four of these resources:

| Resource | Identifier | Why your agent needs it |
| --- | --- | --- |
| Your agent resource | `urn:agent:resource:YOUR-GITHUB-HANDLE` | Sign-in requests a subject token for this audience. |
| Expense MCP Resource | `http://localhost:8100/mcp` | Your agent calls the expense tools. |
| OpenID Connect UserInfo | The zone's built-in resource | Looks up the signed-in person's email. |
| LLM API | `https://api.openai.com` | Your agent gets the model credential from Keycard's vault. |

Your agent now connects to its own resource twice.
The **Depends** connection lets it request a subject token when you sign in.
The **Provides** connection lets it exchange that token for credentials to call Expense MCP for you.

Everyone creates their own agent resource, but the whole room shares the Expense MCP and LLM API resources.
The MCP application handles Ledger API access, and the instructors manage that shared setup, so leave it unchanged.

Now that your registrations are connected, you'll create the credentials your agent uses to prove who it is.

## Step 7: Creating credentials and updating agent/.env

Open your application, select **Application Credentials**, and click on **Add credential**.
Choose **Client ID & Secret**.

The console shows the secret only once, so copy both values before you click on **Done**.
If you lose the secret, replace the credential and update both values.

Next, open `agent/.env` in the [button label="Editor" background="#444CE7"](tab-2) tab.
This file holds the settings Expense Desk reads when it starts.
Set these three lines:

```dotenv,nocopy
KEYCARD_CLIENT_ID=YOUR-CLIENT-ID
KEYCARD_CLIENT_SECRET=YOUR-CLIENT-SECRET
AGENT_RESOURCE=urn:agent:resource:YOUR-GITHUB-HANDLE
```

`KEYCARD_CLIENT_ID` and `KEYCARD_CLIENT_SECRET` are the credential you copied.
`AGENT_RESOURCE` is the identifier of the resource you created in Step 5.
Leave the other lines alone, including `KEYCARD_ISSUER`, `MCP_URL`, and the LLM settings, which the instructors supplied.
Save the file.

**Note:** Keep the secret in `.env`. Don't paste it into chat, a screenshot, or a commit.

A client ID and secret work well for this workshop.
In production, you'd use *Workload Identity Federation* (WIF for short) where your platform supports it.
With WIF, the platform vouches for your application, so no long-lived secret sits on disk.
The [Keycard CLI](https://docs.keycard.ai/cli/) is another option that hands credentials to a process instead of saving them to a file.

Before you continue, check your registration against this list:

- Your application identifier starts with `urn:agent:app:` and uses your GitHub handle.
- Your resource uses Zone Provider, has no scopes, and your application provides it.
- Your application depends on your resource, Expense MCP, OpenID Connect UserInfo, and the LLM API resource.
- Your application has Implicit consent and the exact callback URL from Step 3.
- `agent/.env` holds your own credential and resource identifier.

Now that Keycard knows about your agent, you'll switch the agent's code over to use it.

## Step 8: Switching to application authentication

So far, Expense Desk has run its Exercise 01 wiring.
That wiring uses a raw model key and calls the MCP server with no credentials at all.
You'll replace it with wiring that asks Keycard for a credential on every call.

Open `agent/agent_auth.py` in the Editor, and then open `checkpoints/02-authenticated/agent/agent_auth.py` next to it.
The authenticated version builds its MCP connection like this:

```python
MCPToolset(MCP_URL, auth=keycard.ZoneTokenAuth(),
           process_tool_call=tool_guard).filtered(
    ...
)
```

The difference from the starter is `auth=keycard.ZoneTokenAuth()`.
Every request the agent sends to the MCP server now passes through `ZoneTokenAuth` first.

Open `agent/keycard.py` to see what `ZoneTokenAuth` does:

```python
class ZoneTokenAuth(httpx2.Auth):
    async def async_auth_flow(self, request: httpx2.Request) -> AsyncGenerator[httpx2.Request, httpx2.Response]:
        request.headers["Authorization"] = f"Bearer {await mint(MCP_RESOURCE, _tool_scope(request))}"
        yield request
```

Before each MCP request goes out, `ZoneTokenAuth` calls `mint` for the MCP resource and the tool's scope.
It puts the result in the `Authorization` header.
The agent never stores a token; it gets a fresh one for each call.

The `mint` function in the same file decides how to get that token:

```python
async def mint(resource: str, scope: str | None = None) -> str:
    subject_token = _user_token.get()
    async with _oauth_client as client:
        if subject_token is None:
            response = await client.client_credentials_grant(resource=resource, scope=scope)
        else:
            response = await client.exchange_token(
                subject_token=subject_token,
                subject_token_type=TokenType.ACCESS_TOKEN,
                resource=resource,
                scope=scope,
            )
    return response.access_token
```

When nobody has signed in, `subject_token` is `None`, so the agent uses a *client credentials grant*.
It proves who it is with the client ID and secret from `agent/.env` and acts as itself.
That's what you'll see in this exercise.
After someone signs in, the agent exchanges their sign-in token instead, so it acts on that person's behalf.
That's Exercise 03.

`LLMVaultAuth`, in the same file, uses the same `mint` function to get the model credential from Keycard's vault.
That's why the authenticated version no longer needs `LLM_API_KEY`.

Now apply the checkpoint.
Click on the [button label="Terminal" background="#444CE7"](tab-3) tab and type the following command:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 02
```

This replaces `agent/agent_auth.py` and `mcp-server/mcp_auth.py` with their authenticated versions.
It doesn't change `.env`, your expenses, or anything in the Keycard console.

Then restart both processes so they load the new code and your new settings:

```bash,run
workshop-services restart
```

Once the restart finishes, click on the [button label="Expense Desk" background="#444CE7"](tab-0) tab and choose **Continue as Expense Desk Agent**.
Your agent now acts as its registered application.

Now that the agent has its own identity, you'll check what the Ledger API records.

## Step 9: Checking what gets recorded

In the Expense Desk chat, ask:

```text
Which account am I using, and what is my approval limit?
```

Next, ask the agent to file a new $75 workshop expense under someone else's name.
Save the expense ID and read **Created by** in the agent's confirmation.
It should show your registered application, whatever name you typed.

Now look at the same request from Keycard's side.
In the [button label="Keycard" background="#444CE7"](tab-1) tab, open **Applications > Expense Desk Agent - YOUR-GITHUB-HANDLE > Activity**.
Clear any earlier filters with **Filters > Clear**, then set **Resource > Expense MCP Resource**.
Open a **Credential Issued** event for your application.
This credential came from a client credentials grant, and it identifies your application.

With the instructor, open **Applications > Expense MCP Actor > Activity**, clear old filters, and set **Resource > Ledger API**.
The next hop is another **Credential Issued** event, labeled `urn:ietf:params:oauth:grant-type:token-exchange`.
Here, Expense MCP Actor exchanged the token it received for one addressed to the Ledger API.
This feed shows requests from the whole room, so follow the instructor's example and check the application in its delegation details.

## Conclusion

You registered an application and a resource for your agent in Keycard, and connected them.
Then you switched Expense Desk to request a credential for every call.
The Ledger API now records your application as the creator, no matter what name someone types.

There's still no person behind those requests, though.
Your agent acts as itself, not as you.
Now that your agent has an identity, you'll sign in as yourself in Exercise 03 and let the agent act on your behalf.

## If you fall behind

If Expense Desk won't start after the checkpoint, check your registration against the list in Step 7 first.
The checkpoint changes local code, so it can't create or repair anything in the Keycard console.

To restore the authenticated code, click on the [button label="Terminal" background="#444CE7"](tab-3) tab and type the following commands:

```bash,run
uv run --locked --project agent python checkpoints/restore.py 02
```

```bash,run
workshop-services restart
```

If Expense Desk still won't start, run `workshop-services status` and ask an instructor for help.
The logs are in `/tmp/workshop/web.log` and `/tmp/workshop/mcp.log`.

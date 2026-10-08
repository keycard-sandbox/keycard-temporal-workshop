# Explain the pre-provisioned architecture

Use only the section relevant to the question. Begin with a direct explanation, then trace a workshop request or show the relevant configuration. Invite the attendee to inspect evidence instead of giving a glossary lecture. Confirm shared-zone settings with the instructor when diagnosing a configuration failure.

## Shared access does not identify the caller

In Exercise 01, a valid shared key proves possession of that credential and authenticates service access. It does not uniquely identify which application or person sent the request: another holder could use the same key from different software. A supplied name or email does not establish either identity.

Use the visible evidence: Created by records the supplied name; Activity → Identity details → Actor ID records `API key: ********`. For example: “Your name is the label supplied with the expense. The shared key granted access, but cannot tell us which application or person used it.” This explains the current observation without needing a comparison with another exercise.

## Applications identify callers; resources identify destinations

The agent application authenticates to Keycard when it asks for credentials. Its resource gives the user's sign-in token a destination, called its audience. The agent provides that resource so it can exchange a token addressed to itself for a credential addressed to MCP. This resource is a registration; it needs no extra server listening at its URN.

MCP also has both registrations because it receives agent requests and calls Ledger API. Its resource names the incoming destination, `http://localhost:8100/mcp`. Its application authenticates the onward request to Keycard for a Ledger API credential. One running service can need two registrations because these registrations describe different roles.

| Component | Application role | Resource role | Who configures it |
| --- | --- | --- | --- |
| Expense agent | Requests MCP and model credentials | `urn:agent:resource:<your-github-handle>` receives the sign-in audience | Attendee |
| Expense MCP | Exchanges the incoming token for Ledger API access | `http://localhost:8100/mcp` receives agent calls | Instructor |
| Ledger API | No onward exchange is required in this workshop | `urn:ledger:api` identifies the final API | Instructor |
| Model API | The agent requests its credential | Supplied `LLM_RESOURCE` identifies a vault-backed credential target | Instructor |
| Temporal worker | Requests Ledger API credentials inside activities | The required app-only demo does not need a user-session anchor | Instructor |

Avoid teaching that every API or application always needs both. The pairing matters here because the agent and MCP continue a delegation chain. Ledger API ends the chain.

Provides means the application may continue a chain from access tokens addressed to that resource. Depends declares destinations the application requests credentials for. Providing a resource does not grant access to every downstream service, and depending on it does not let an app exchange its incoming tokens. Each attendee provides their own agent resource; all attendees can depend on the shared MCP resource.

**Expense MCP Actor** is the application registration of the MCP server, named for its role as the caller in the onward exchange. **Expense MCP Resource** is the destination for the agent's incoming token. The same running MCP server receives one token and authenticates as its application to exchange it for a Ledger API token.

The **Temporal Worker** application identifies the background program that runs jobs assigned by Temporal. Temporal tracks the job’s progress, and the worker uses Keycard to obtain credentials for Ledger API when it needs access. The instructors manage this registration, so leave it unchanged.

Leave **Proxy MCP tools** off. That option creates a gateway that exposes tools from upstream MCP servers through one generated endpoint. Here Expense Desk calls the supplied Expense MCP endpoint directly; its SDK authentication and onward Ledger API exchange are the behavior you are learning. See [Proxy MCP Tools](https://docs.keycard.ai/admin/unified-access-gateway/).

## Follow one user-delegated request

```text
GitHub sign-in → Keycard → user session addressed to Agent Resource
                              │
Agent App authenticates + exchanges session → token for Expense MCP
                              │
MCP App authenticates + exchanges incoming token → token for the Ledger API
                              │
Ledger API verifies the token and applies expense rules
```

For Exercise 03:

| Step | Application requesting credentials | Subject | Destination |
| --- | --- | --- | --- |
| Sign-in code redemption | Attendee agent | Signed-in user | Agent resource |
| Agent's MCP request | Attendee agent | Same user | Expense MCP resource |
| MCP's Ledger API request | Shared MCP application | Same user | Ledger API resource |

At each exchange, the calling application proves its own identity and presents the subject token. Keycard checks the request before issuing the next credential. The agent provides the audience of its incoming session; MCP provides the audience of its incoming token. Each service receives a credential addressed to its own resource, with the user's identity established through sign-in and token exchange.

The agent requests model credentials on a separate branch through `LLMVaultAuth`; MCP does not proxy the model call. Read `agent/keycard.py` (`mint`, `ZoneTokenAuth`, `LLMVaultAuth`) and `mcp-server/keycard.py` (`ledger_token`) to connect the picture to code.

In Exercise 02 there is no signed-in user session. The agent starts with client credentials, and the subject represents the application. MCP still exchanges the incoming token for Ledger API. The agent requests its initial credential directly for Expense MCP; it does not first obtain a user-session token addressed to its own resource. That session anchor belongs to the user sign-in flow. Signing into the Keycard console to configure an app is distinct from signing in to Expense Desk to delegate as a user.

Use Keycard Activity to explain which application requested which resource. Don't promise that every JWT embeds the full delegation chain or an `act` claim. Identity continuity does not mean scope strings carry unchanged across hops: this code requests `expense:*` scopes toward MCP and `ledger:*` scopes toward Ledger API.

## Providers have different jobs

GitHub helps establish who signs in. Keycard's Zone Provider issues the credentials addressed to the workshop agent, MCP, and Ledger API resources. A GitHub sign-in therefore does not mean the MCP server should accept a GitHub API token.

An external OAuth credential provider serves another purpose: Keycard can broker a connected user's credential for that provider's API. For example, an API requiring a vendor's OAuth token would use that vendor's credential provider. The Ledger API resource uses Zone Provider; attendees don't configure an external OAuth connection for it.

The model resource uses a vault-backed credential. The resource identifier names what the agent requests; the credential can be an API key rather than a Keycard JWT. Keep the instructor's model-resource setting and let the supplied SDK integration obtain it.

Two callbacks can exist in a federated sign-in: the upstream provider returns to Keycard; Keycard returns to Expense Desk at its registered `/callback`. The agent's environment-specific callback belongs in its application registration: `http://localhost:8400/callback` locally, or the exact HTTPS URL in `CALLBACK_URL.txt` in Instruqt. It does not replace the upstream provider's redirect URL. See [Keycard providers](https://docs.keycard.ai/concepts/providers/) for identity and access federation.

## Policies decide access; Expense Desk decides expense actions

Keycard policies use Cedar to evaluate whether a credential request is permitted. Explain principal, action, resource, and context through the actual request: the requesting application and, for delegation, the user; the requested access; its destination; and relevant request facts. Cedar uses default deny and a matching forbid overrides a permit. See [Keycard policies](https://docs.keycard.ai/concepts/policies/).

Dependencies describe requested relationships; consent records the user's authorization where applicable; policy evaluates access. None should be described as permission to do anything reachable through an unlimited dependency graph. Providing a resource is a separate structural requirement for these access-token exchanges.

The recorded workshop policy `allow-agent-apps-ledger-access` matches `urn:agent:app:*` and supports the application-subject exchange from MCP to the Ledger API. Keep the prescribed identifier prefix. This permit also allows matching agents to request Ledger API credentials directly; it does not prove that all Ledger API access must pass through MCP. Shared policies and their active set belong to the instructor.

Verify live access decisions by inspecting credential issuance or failure alongside the authorization event. Ask the instructor to investigate any mismatch with the configured policy. Don't edit policies or propose CLI-local policy schemas as zone policy fixes.

Expense Desk then checks the business action: ownership, approval limits, and the current expense state. A user receiving a credential does not imply that Expense Desk must let them approve their own expense.

For a self-approval refusal, compare the expense submitter with the current verified identity and read the refusal. A refused write does not establish a successful Decided by actor or a new decision in Activity. Inspect the current status instead of inventing a decision record. Different identities still require the amount, state, and other business checks to pass.

Trace an allowed approval or rejection of another attendee's expense: credential requests succeed, Expense Desk sees the verified user, and its expense checks allow the selected pending expense. Trace a self-approval refusal: credentials can succeed while Expense Desk refuses the business action. For `access_denied` during minting, inspect Keycard Activity before blaming Expense Desk. Re-authentication can't change a policy decision.

## Temporal records progress; activities acquire credentials

A workflow describes durable orchestration. Activities perform external work; workers poll the chosen task queue and execute that work. The namespace groups Temporal executions, while the task queue routes work to compatible workers. A durable timer keeps its deadline when a worker stops.

On replay, Temporal uses recorded results to reconstruct workflow progress. In Exercise 04, wait until debit completion is recorded before stopping the worker. The next activity obtains a credential when it executes. An unrecorded activity can execute again, so Temporal alone does not make an external payment exactly once.

Read the actual workflow class, activities, and `KeycardInterceptor` wiring in `demo.py`. The supplied demo uses application credentials and simulates payment. Don't describe it as a live user-delegated payment flow. As an advanced extension, the integration supports resolving a user identity reference inside an activity to obtain a current session token; that needs session lookup and appropriate worker registration. Don't persist the user's token as the workflow argument or present that extension as already configured.

Keycard Activity records credential events; Expense Desk records business actions; Temporal history records execution. These views answer different questions and their IDs are not interchangeable. For broader details, use [Temporal's Python guide](https://docs.temporal.io/develop/python) and the versions in the local lockfile.

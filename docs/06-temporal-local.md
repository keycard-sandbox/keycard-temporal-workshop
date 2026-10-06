<!-- Generated from docs/attendee/temporal-local-dry-run.md. Edit the source, then rebuild. -->
# Local Temporal setup

For Exercise 04, you'll run a local Temporal server alongside the workshop app. You control this server and its worker, so you can stop the worker and watch it recover. Skip this setup if your session ends after Exercise 03.


## Prepare your package and tools

Get the attendee package and private configuration from Kim. The package root contains `agent/`, `mcp-server/`, `temporal/`, and `checkpoints/`. Keep credentials in local `.env` files and out of chat and source control.

Install the Temporal CLI if `temporal --version` isn't available. On macOS with Homebrew:

```bash
cd "<package-path>"
brew install temporal
```

For Linux or Windows, use the platform instructions in the [Temporal CLI installation guide](https://docs.temporal.io/cli/setup-cli). On Windows, run the workshop in the instructor-approved shell environment; ask Kim before proceeding if the package's shell commands don't apply to your environment.

Confirm `uv --version` is available; if it isn't, follow the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/). From the package root, install the settlement dependencies before class:

```bash
cd "<package-path>"
uv sync --locked --project settlement
```

Complete the Expense Desk setup using the agent and MCP configuration supplied by Kim, including model access and the shared Ledger API. Ask Kim for any missing configuration before Exercise 01.

## Start your Temporal server

Open a dedicated terminal at the package root and run:

```bash
cd "<package-path>"
temporal server start-dev --ip 127.0.0.1 --port 7233 --ui-ip 127.0.0.1 --ui-port 8233 --namespace workshop-local --ui-disable-news-fetch --disable-config-env --disable-config-file
```

Keep this terminal open through Exercise 04. This temporary server keeps history in memory; stopping it discards that history. During the exercise, stop only the worker, which runs in a different terminal.

If startup reports an occupied port, ask Kim before changing ports or stopping an existing server. A preexisting Temporal server might belong to another project.

Open [your Temporal UI](http://localhost:8233) and select the `workshop-local` namespace. Before you start a workflow, an empty workflow list is expected. In another terminal, verify the namespace:

```bash
cd "<package-path>"
temporal operator namespace describe --namespace workshop-local --address 127.0.0.1:7233 --disable-config-env --disable-config-file
```

Expect the namespace name `workshop-local` and state `Registered`. Stop and ask Kim if the UI doesn't open or the namespace check fails.

## Configure the settlement worker

If `temporal/.env` doesn't exist, copy `temporal/.env.example` to `temporal/.env` with your editor. Preserve an existing file. Enter these connection settings:

```dotenv
TEMPORAL_ADDRESS=127.0.0.1:7233
TEMPORAL_NAMESPACE=workshop-local
TEMPORAL_TASK_QUEUE=settlement-local
```

Everyone can use this queue name because each computer has a separate Temporal server. Run only one settlement worker on your server so the restart demonstration is under your control.

Enter the instructor-supplied Keycard settings in the same file:

```dotenv
KEYCARD_ISSUER=https://ho0llbxj2o7enn7l48tuzic25t.keycard.cloud
WORKER_KEYCARD_CLIENT_ID=<supplied Temporal Worker client ID>
WORKER_KEYCARD_CLIENT_SECRET=<supplied Temporal Worker client secret>
LEDGER_RESOURCE=urn:ledger:api
```

Replace the angle-bracket placeholders privately. Kim supplies credentials for the `Temporal Worker` application, which must depend on the existing Ledger API resource. Your attendee Expense Desk agent's credentials belong in `agent/.env`; they aren't the settlement worker credentials.

## Continue with the workshop

Complete Exercises 01–03 before starting a settlement workflow. In Exercise 04, use this terminal arrangement:

| Terminal | Process | During the interruption |
| --- | --- | --- |
| Temporal server | The `temporal server start-dev` command | Leave running |
| Temporal worker, in `temporal/` | `uv run --locked --env-file .env demo.py worker` | Stop and restart as Exercise 04 directs |
| Workflow client, in `temporal/` | `uv run --locked --env-file .env demo.py run` | Leave running; don't start another workflow |

Follow Exercise 04 in `docs/04-durable-execution.md` from the package root. Use your local UI and `workshop-local` namespace wherever it asks for the supplied Temporal UI and namespace. The worker obtains real Keycard credentials, but the settlement activities simulate payment and don't change expense balances.

After inspecting history and recording results, press Control-C in the worker terminal, then the server terminal. Stopping the server discards its in-memory history. Remove only your local credential copies when the instructor confirms the workshop is complete; don't revoke shared application credentials yourself.

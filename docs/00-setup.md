<!-- Generated from docs/attendee/setup.md. Edit the source, then rebuild. -->
# Set up Expense Desk

The full workshop is an instructor-led demonstration. You may watch or follow along; use the supplied Instruqt track for take-home practice once its access and retention are confirmed.

For local follow-along, you will run Expense Desk locally and connect it to the workshop's shared services. Follow this guide before starting Exercise 01.

For sessions covering Exercises 01–03, follow the instructions below. You don't need Temporal, Docker, a local database, or your own model API key.

If dependencies are already installed in your current package folder, skip their installation. If Expense Desk is already running in a hosted environment, open its supplied preview URL; otherwise use the startup commands below.

## Set up the attendee package

Kim supplies the attendee package and configuration privately. If the package already contains the two `.env` files, keep them. Otherwise, place the supplied files as described below. The attendee package starts with Exercise 01's shared-key app.

1. Extract the package into a new local folder.
2. Open the folder in your editor. Confirm it contains `agent/`, `mcp-server/`, and `checkpoints/`.
3. Place the supplied configuration files at these locations:

   ```text
   agent/.env
   mcp-server/.env
   ```

Keep the leading dot in `.env` and make sure your editor doesn't append `.txt`. These files contain workshop credentials, so keep their contents out of chat, screenshots, and commits. If you're still waiting on the files, you can install the dependencies first.

The configuration supplies model access and the shared Ledger API service. If `KEYCARD_CLIENT_ID`, `KEYCARD_CLIENT_SECRET`, and `AGENT_RESOURCE` in `agent/.env` are blank, leave them blank until Exercise 02. Preserve existing configuration; in Exercise 02, confirm those fields identify your own registration. Keep all other supplied values.

## Install uv

1. Open a terminal and check whether uv is installed:

   ```sh
   uv --version
   ```

2. If the command isn't available, install uv. On macOS with Homebrew, run:

   ```sh
   brew install uv
   ```

   For other installation methods and platforms, follow the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

3. If you installed uv, open a new terminal and run `uv --version` to confirm the installation.

## Command locations

Resolve the full path of the extracted folder containing `agent/`, `mcp-server/`, `docs/`, and `checkpoints/`. The command blocks use `<package-path>` for that absolute path. Replace it before running commands. If you use the companion assistant, ask it to fill in your actual quoted path. For example, if you extracted into Downloads, the path may be `/Users/yourname/Downloads/expense-desk-keycard-temporal`.

Read the numbered files in `docs/` in order. `checkpoints/01-starter/` and `checkpoints/02-authenticated/` hold code snapshots for restoring an exercise. Use `checkpoints/restore.py` only when directed; it overwrites those code files while preserving credentials and service data.

## Install the dependencies

1. Open a terminal in the package folder that contains `agent/`, `mcp-server/`, and `checkpoints/`.
2. Run these commands in order, waiting for each command to finish:

   ```sh
   cd "<package-path>"
   uv python install 3.13
   uv sync --locked --python 3.13 --project agent
   uv sync --locked --python 3.13 --project mcp-server
   ```

Each extracted package has its own Python environments. The startup commands use `uv run --locked` to install missing dependencies from the lockfiles, so you don't need to activate an environment yourself.

If you're using Windows, contact Kim before the session. Some later exercises use macOS and Linux commands that need adjustment for Windows.

## Install the skill (optional)

The package includes `skills/keycard-temporal-workshop/`, a companion that helps your local coding agent explain the workshop and troubleshoot exercises. Your coding agent is separate from the expense agent in Expense Desk.

Install the skill for the coding agent you use. Run the commands from the package folder that contains `agent/`, `mcp-server/`, and `skills/`. Copy the whole skill folder so its references and configuration checker stay together.

### Codex

Install into the workshop folder:

```sh
cd "<package-path>"
mkdir -p .agents/skills/keycard-temporal-workshop
cp -R skills/keycard-temporal-workshop/. .agents/skills/keycard-temporal-workshop/
```

Open the package folder in Codex. If the skill doesn't appear, restart Codex, then start a new task and enter:

```text
Use the keycard-temporal-workshop skill to help me with setup. Explain each step and let me perform the exercises myself.
```

Codex discovers project skills in `.agents/skills/`. See [Codex skill documentation](https://developers.openai.com/codex/skills).

### Claude Code

Install into the workshop folder:

```sh
cd "<package-path>"
mkdir -p .claude/skills/keycard-temporal-workshop
cp -R skills/keycard-temporal-workshop/. .claude/skills/keycard-temporal-workshop/
```

Start Claude Code in the package folder, then enter:

```text
/keycard-temporal-workshop Help me with setup. Explain each step and let me perform the exercises myself.
```

If the command doesn't appear, restart Claude Code in that folder. See [Claude Code skill documentation](https://code.claude.com/docs/en/skills).

### Other local coding agents

Copy `skills/keycard-temporal-workshop/` into your agent's documented project skill directory. If your agent can read local files but doesn't support skill installation, enter:

```text
Read skills/keycard-temporal-workshop/SKILL.md and follow its instructions to help me with this workshop. Read the referenced files as needed. Explain each step and let me perform the exercises myself.
```

On Windows, you can copy the folder in your file manager instead of using the shell commands. Confirm that `SKILL.md` is directly inside the destination's `keycard-temporal-workshop/` folder, alongside `references/`, `scripts/`, and `agents/`.

To check that your coding agent has loaded the companion, ask it to identify the workshop skill and the setup guide it will follow. If your package has no `skills/` folder, ask Kim for an updated package.

## Start Expense Desk

The MCP server connects to the shared Ledger API service. Expense Desk runs separately and provides the browser app. Keep both processes running while you use the app.

1. Open two terminal tabs in the package folder.
2. In the first tab, start the MCP server:

   ```sh
   cd "<package-path>"
   uv run --locked --project mcp-server python mcp-server/server.py
   ```

3. In the second tab, start Expense Desk:

   ```sh
   cd "<package-path>"
   uv run --locked --project agent python agent/web.py
   ```

4. Open [Expense Desk](http://localhost:8400) locally, or use the preview URL your instructor supplied.

Once you can open Expense Desk, let Kim know you're ready and wait for the session to begin Exercise 01. You'll join Keycard and register your agent in Exercise 02.

To stop the app after checking setup, press Control-C in each terminal tab. Run the same two startup commands before the session.

Continue with [Exercise 01](01-missing-identity.md) when the session starts.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| uv can't find `pyproject.toml`, or Python can't find the script | Run the commands from the package folder that contains `agent/` and `mcp-server/`. |
| Missing configuration or API key | Confirm both supplied `.env` files are in their component folders. Restart both processes after changing configuration. |
| Port 8100 or 8400 is already in use | Stop a previous workshop process you started. If another application owns the port, contact Kim before changing the workshop ports. |
| Expense Desk opens but can't load expenses | Check the MCP terminal for an error and confirm it's still running. Contact Kim if the error persists. |
| Expense Desk asks you to sign in | Contact Kim; you might have a source checkout or a package that already advanced past Exercise 01. |

If you need help, send Kim the command you ran and the error message. Remove credentials before sharing either.

For sign-in and exercise errors, see [Troubleshooting](07-troubleshooting.md).

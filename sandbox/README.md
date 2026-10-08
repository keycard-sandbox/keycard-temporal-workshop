# Instruqt sandbox and track

This repository's root is the generated attendee package. It's mirrored from the internal workshop repository with `just sync-public` from the private repository, so don't edit `agent/`, `mcp-server/`, `temporal/`, `checkpoints/`, `docs/` or `skills/` here. The Instruqt track (`instruqt/`), this sandbox image (`sandbox/`), the image build workflow (`.github/`) and the `justfile` are edited here directly.

## What the sandbox runs

One container, hostname `workshop`. The image bakes the attendee package at `/root/workshop` with synced uv environments and a warmed Temporal dev-server database for the `default` namespace. Track setup writes the `.env` files from Instruqt secrets, then starts:

| Process | Address | Reached through |
| --- | --- | --- |
| Expense MCP server | `127.0.0.1:8100` | Expense Desk only |
| Expense Desk (`agent/web.py`) | `127.0.0.1:8400` | Caddy on the container address, port 8400 |
| Temporal dev server and UI | `0.0.0.0:7233`, `:8233` | Temporal UI tab |

`workshop-services start|stop|restart|status` manages the MCP server, Expense Desk and Caddy. Logs are in `/tmp/workshop/`.

Expense Desk listens on `127.0.0.1` only, and its `TrustedHostMiddleware` accepts only the `EXPENSE_DESK_ORIGIN` hostname. Caddy listens on the container's own address, which is what Instruqt's proxy reaches, and rewrites `Host` to the preview hostname. Expense Desk sends `frame-ancestors 'none'`. Caddy narrows that to `https://*.instruqt.com` so Exercises 01 and 02 can embed it. Exercise 03 opens it in its own window, because GitHub sign-in can't complete inside a frame.

## Preview origin and callback

Track setup sets `EXPENSE_DESK_ORIGIN=https://workshop-8400-$INSTRUQT_PARTICIPANT_ID.env.play.instruqt.com` and writes the matching `/callback` URL to `/root/workshop/CALLBACK_URL.txt`. Exercise 02 has attendees paste that value as their application's Redirect URI.

## Secrets

Set these in the Instruqt web UI. They reach lifecycle scripts only, and setup writes them into the `.env` files.

| Secret | Written to |
| --- | --- |
| `KEYCARD_WORKSHOP_LLM_API_KEY` | `agent/.env` `LLM_API_KEY` |
| `KEYCARD_WORKSHOP_LEDGER_API_KEY` | `mcp-server/.env` `LEDGER_API_KEY` |
| `KEYCARD_WORKSHOP_MCP_CLIENT_ID`, `KEYCARD_WORKSHOP_MCP_CLIENT_SECRET` | `mcp-server/.env` |
| `KEYCARD_WORKSHOP_WORKER_CLIENT_ID`, `KEYCARD_WORKSHOP_WORKER_CLIENT_SECRET` | `temporal/.env` `WORKER_KEYCARD_CLIENT_ID`, `WORKER_KEYCARD_CLIENT_SECRET` |

Attendees don't enter the Worker credentials during Exercise 04.

Blank secrets don't stop the sandbox. Setup writes empty values, warns that Expense Desk isn't running, and leaves Temporal, the editor and the terminals up. Fill in the values and run `workshop-services start`.

## Build and publish

Pushes to `main` build `ghcr.io/keycardai/keycard-temporal-workshop-sandbox:latest`, and every build is also tagged with its commit SHA. `instruqt/config.yml` pins the track to one of those commit-SHA tags, a build that has been tested on a lab, so a new push to `main` never changes the live track by itself. Other branches publish a branch-named tag. Pull requests and Dependabot pushes build without publishing. The workflow uses this repository’s `GITHUB_TOKEN` with `packages: write` to publish within the `keycardai` organization.

To ship a new image: wait for the Sandbox image workflow on `main`, test that build on a lab, set the `image:` tag in `instruqt/config.yml` to its commit SHA, and verify an anonymous pull of that tag before running `just push`. Instruqt needs public access to pull it.

```sh
just sandbox-build dev   # local linux/amd64 build from this checkout
just sandbox-run dev     # local shell with the track setup applied
just validate
just create              # once: register the slug (maintenance mode)
just push --force        # first push, then:
just pull                # commit the server-assigned ids
```

## Challenges

| Challenge | Check | Solve |
| --- | --- | --- |
| 01 Missing identity | follow-along | none |
| 02 Application identity | follow-along | applies checkpoint 02; registration is manual |
| 03 User delegation | follow-along | applies checkpoint 03; sign-in is manual |
| 04 Durable execution | follow-along | runs one settlement without interruption |

`instruqt track test` can't get past Exercise 02, because registration and sign-in need a real person and a GitHub account.

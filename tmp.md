# Temporary test setup to revert

The live Instruqt track runs on stand-ins so it can be tested before the real image and secrets exist. Each spot is marked `TEMP(tmp.md)`; `grep -rn "TEMP(tmp.md)" .` finds them all. Delete this file once everything below is done.

## Prerequisites

- [ ] Kim makes the `keycard-sandbox/keycard-temporal-workshop-sandbox` GHCR package public, and `:latest` exists. That needs one merge to `main`, because CI publishes `:latest` from `main` only.
- [ ] The six workshop secrets exist in the Instruqt `temporal` team settings (`instruqt secrets create NAME VALUE`), with values from Kim's `.env` files:
  - `KEYCARD_WORKSHOP_LLM_API_KEY`
  - `KEYCARD_WORKSHOP_LEDGER_API_KEY`
  - `KEYCARD_WORKSHOP_MCP_CLIENT_ID`
  - `KEYCARD_WORKSHOP_MCP_CLIENT_SECRET`
  - `KEYCARD_WORKSHOP_WORKER_CLIENT_ID`
  - `KEYCARD_WORKSHOP_WORKER_CLIENT_SECRET`

## Reverts

1. `instruqt/config.yml`: set `image:` back to `ghcr.io/keycard-sandbox/keycard-temporal-workshop-sandbox:latest`.
2. `instruqt/config.yml`: uncomment the `secrets:` block.
3. `instruqt/track_scripts/setup-workshop`: change the three `:-test-placeholder}` defaults for `LEDGER_API_KEY`, `MCP_CLIENT_ID` and `MCP_CLIENT_SECRET` back to `:-}`.
4. Remove the `TEMP(tmp.md)` comments, then run `just push` and `just pull`, and commit.
5. Optional: delete the `temporal-sa/keycard-temporal-workshop-sandbox` GHCR package once nothing points at it.

## Why each stand-in exists

- **Test image:** Instruqt pulls images anonymously, and the `keycard-sandbox` package is still private. A copy built from this repo lives at `ghcr.io/temporal-sa/keycard-temporal-workshop-sandbox:test` and is public.
- **Commented-out secrets:** `instruqt track push` refuses a `config.yml` that names a secret the team doesn't have.
- **Placeholder defaults:** with blank values the MCP server refuses to start, so Expense Desk can't render. The placeholders let the lab boot and show the UI. Data and chat calls fail until real values are in place.

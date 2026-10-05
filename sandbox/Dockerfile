# ABOUTME: Instruqt sandbox for the Keycard + Temporal workshop.
#
# Build from the repo root: `just sandbox-build`, or
# `docker build -f sandbox/Dockerfile .`. Only the attendee package
# (not instruqt/, sandbox/ or CI files) is baked at /root/workshop, and its
# uv environments are synced in place so `uv run --locked` starts offline.

FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git vim nano less unzip ca-certificates jq procps \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv

ARG TEMPORAL_CLI_VERSION=1.9.1
RUN curl -fsSL \
      "https://github.com/temporalio/cli/releases/download/v${TEMPORAL_CLI_VERSION}/temporal_cli_${TEMPORAL_CLI_VERSION}_linux_amd64.tar.gz" \
    | tar -xz -C /usr/local/bin temporal \
    && chmod +x /usr/local/bin/temporal

# Caddy forwards the Instruqt preview to Expense Desk, which listens on
# 127.0.0.1 only and accepts one Host. See workshop-services.
ARG CADDY_VERSION=2.10.2
RUN curl -fsSL \
      "https://github.com/caddyserver/caddy/releases/download/v${CADDY_VERSION}/caddy_${CADDY_VERSION}_linux_amd64.tar.gz" \
    | tar -xz -C /usr/local/bin caddy \
    && chmod +x /usr/local/bin/caddy

ARG CODE_SERVER_VERSION=4.96.4
RUN curl -fsSL https://code-server.dev/install.sh | sh -s -- --version ${CODE_SERVER_VERSION}

# Workspace trust must be off or code-server shows a blank page. Dotfiles stay
# visible so attendees can edit agent/.env in Exercise 02.
RUN mkdir -p /root/.cs-workshop/User && printf '%s\n' \
      '{' \
      '    "security.workspace.trust.enabled": false,' \
      '    "workbench.colorTheme": "Default Dark+",' \
      '    "workbench.startupEditor": "none",' \
      '    "workbench.editor.enablePreview": false,' \
      '    "editor.fontSize": 14,' \
      '    "editor.minimap.enabled": false,' \
      '    "files.autoSave": "afterDelay",' \
      '    "files.autoSaveDelay": 300,' \
      '    "telemetry.telemetryLevel": "off",' \
      '    "explorer.compactFolders": false,' \
      '    "files.exclude": { "**/.venv": true, "**/__pycache__": true, "**/uv.lock": true }' \
      '}' > /root/.cs-workshop/User/settings.json

RUN code-server --user-data-dir /root/.cs-workshop --install-extension detachhead.basedpyright \
    || echo "==> WARNING: basedpyright did not install; the editor still works without it."

COPY README.md .gitignore /root/workshop/
COPY agent/ /root/workshop/agent/
COPY mcp-server/ /root/workshop/mcp-server/
COPY temporal/ /root/workshop/temporal/
COPY checkpoints/ /root/workshop/checkpoints/
COPY docs/ /root/workshop/docs/
COPY skills/ /root/workshop/skills/
COPY sandbox/workshop-services /usr/local/bin/workshop-services
RUN chmod +x /usr/local/bin/workshop-services

WORKDIR /root/workshop
RUN uv sync --locked --python /usr/local/bin/python3.13 --project agent \
    && uv sync --locked --python /usr/local/bin/python3.13 --project mcp-server \
    && uv sync --locked --python /usr/local/bin/python3.13 --project temporal

# Bake the dev server DB with the workshop namespace so lab start only
# launches the server. Pattern from temporal-sa/instruqt-tracks.
RUN temporal server start-dev --headless \
      --db-filename /root/temporal.db \
      --namespace workshop-local \
      --log-level error > /tmp/build-server.log 2>&1 & \
    for i in $(seq 1 120); do \
      temporal operator namespace describe -n workshop-local --address 127.0.0.1:7233 >/dev/null 2>&1 && break; \
      sleep 0.5; \
    done \
    && temporal operator namespace describe -n workshop-local --address 127.0.0.1:7233 >/dev/null \
    && pkill -INT -x temporal \
    && for i in $(seq 1 40); do pgrep -x temporal >/dev/null || break; sleep 0.25; done

RUN echo 'export TEMPORAL_ADDRESS="${TEMPORAL_ADDRESS:-127.0.0.1:7233}"' >> /root/.bashrc \
    && echo 'export TEMPORAL_NAMESPACE=workshop-local' >> /root/.bashrc \
    && echo 'cd /root/workshop 2>/dev/null || true' >> /root/.bashrc

WORKDIR /root
CMD ["/bin/bash"]

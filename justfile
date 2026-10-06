# ABOUTME: Instruqt track and sandbox image helpers. Run from anywhere in the repo.
# Requires the Instruqt CLI; authenticate once with `instruqt auth login`.

IMAGE := "ghcr.io/keycardai/keycard-temporal-workshop-sandbox"

default:
    @just --list

# Build the sandbox image for Instruqt (linux/amd64) from this checkout.
sandbox-build tag="dev":
    docker buildx build --platform linux/amd64 --load -f sandbox/Dockerfile -t {{IMAGE}}:{{tag}} .

# Push a built image. Instruqt pulls config.yml's tag; CI publishes :latest from main.
sandbox-push tag="dev":
    docker push {{IMAGE}}:{{tag}}

# Run the image locally and execute the track setup (no Instruqt secrets).
sandbox-run tag="dev":
    docker run --rm -it --platform linux/amd64 \
        -p 8233:8233 -p 8080:8080 \
        -v "$PWD/instruqt:/opt/track:ro" \
        {{IMAGE}}:{{tag}} \
        bash -c 'mkdir -p /opt/instruqt/bootstrap && touch /opt/instruqt/bootstrap/host-bootstrap-completed && /opt/track/track_scripts/setup-workshop && exec bash'

# Register the slug server-side. Run once, before the first push.
create:
    #!/usr/bin/env bash
    set -euo pipefail
    slug=$(grep -E '^slug:' instruqt/track.yml | head -1 | awk '{print $2}' | tr -d '"')
    title=$(grep -E '^title:' instruqt/track.yml | head -1 | sed -E 's/^title:[[:space:]]*//' | sed -E 's/^"(.*)"$/\1/')
    tmp=$(mktemp -d)
    (cd "$tmp" && instruqt track create "$slug" --title "$title")
    rm -rf "$tmp"
    echo "Registered '$slug' in maintenance mode. Next: 'just push --force' once, then 'just pull'."

push *flags:
    cd instruqt && instruqt track push {{flags}}

pull:
    cd instruqt && instruqt track pull

validate:
    cd instruqt && instruqt track validate

test:
    cd instruqt && instruqt track test

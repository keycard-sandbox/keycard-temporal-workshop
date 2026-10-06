"""History hygiene check: no token material in durable workflow history.

    uv run check_history.py <workflow-id>

Walks the exported event history, base64-decoding every payload field, and
scans all bytes for JWT-shaped strings (header.payload base64url).
Exit 0 = clean, exit 1 = leak.
"""

import asyncio
import base64
import json
import os
import re
import sys

from temporalio.client import Client

JWT_SHAPE = re.compile(rb"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}")


def _scan(node, leaks: list) -> None:
    if isinstance(node, dict):
        for v in node.values():
            _scan(v, leaks)
    elif isinstance(node, list):
        for v in node:
            _scan(v, leaks)
    elif isinstance(node, str):
        leaks.extend(JWT_SHAPE.findall(node.encode()))
        try:  # payload fields are base64; decode and scan the raw bytes too
            leaks.extend(JWT_SHAPE.findall(base64.b64decode(node, validate=True)))
        except ValueError:
            pass


async def main() -> None:
    wf_id = sys.argv[1]
    client = await Client.connect(os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
                                  namespace=os.environ.get("TEMPORAL_NAMESPACE", "default"))
    history = await client.get_workflow_handle(wf_id).fetch_history()
    doc = json.loads(history.to_json())
    leaks: list = []
    _scan(doc, leaks)
    n_events = len(doc.get("events", []))
    if leaks:
        sys.exit(f"FAIL: {len(leaks)} JWT-shaped string(s) in history for {wf_id}")
    print(f"OK: no JWT-shaped token material across {n_events} events in {wf_id}")


if __name__ == "__main__":
    asyncio.run(main())

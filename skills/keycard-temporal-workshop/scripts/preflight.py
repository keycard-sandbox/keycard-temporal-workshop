"""Read-only workshop checks. Never emit configuration values or file contents."""

import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from dotenv.parser import parse_stream


def read_env(path):
    """Use the runtime's dotenv parser without expanding environment variables."""
    values, issues = {}, []
    try:
        with path.open() as stream:
            for binding in parse_stream(stream):
                if binding.error:
                    issues.append("invalid_assignment")
                elif binding.key is not None:
                    values[binding.key] = binding.value or ""
    except FileNotFoundError:
        return {}, ["file_missing"]
    except (OSError, UnicodeError):
        return {}, ["file_unreadable"]
    if any("${" in value for value in values.values()):
        issues.append("interpolation_requires_runtime_check")
    return values, sorted(set(issues))


def present(value):
    return bool(value and not re.search(r"<[^>]+>|YOUR[_ -]|CHANGEME", value, re.I))


def url_valid(value, origin=False):
    try:
        parsed = urlsplit(value)
        port = parsed.port
        return bool(
            parsed.scheme in {"http", "https"}
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
            and not any(c.isspace() for c in value)
            and (port is None or port > 0)
            and (not origin or parsed.path == "")
        )
    except ValueError:
        return False


def inspect(root, stage, starter=False):
    source = (root / "docs/attendee/ex01.md").is_file()
    packaged = (root / "docs/01-missing-identity.md").is_file()
    layout = "source" if source else "attendee" if packaged else "unknown"
    result = {"layout": layout, "stage": stage, "checks": [], "limitations": [
        "Local files only; no network calls or writes.",
        "No credential validity, live registration, process, or environment-override verification.",
        "Environment interpolation requires a separate runtime check.",
    ]}

    def check(name, ok):
        result["checks"].append({"check": name, "status": "ok" if ok else "needs_attention"})

    check("recognized_workshop_root", layout != "unknown")
    if layout == "unknown":
        return result
    check("starter_option_matches_layout_and_stage", not starter or (source and stage == "01"))
    if starter and (not source or stage != "01"):
        return result
    if source and stage == "01" and not starter:
        check("source_exercise_01_requires_starter_option", False)
        return result
    if stage == "04":
        component = root / "temporal"
        required = ("KEYCARD_ISSUER", "WORKER_KEYCARD_CLIENT_ID", "WORKER_KEYCARD_CLIENT_SECRET",
                    "LEDGER_RESOURCE")
    else:
        component = root / ("starter/agent" if starter else "agent")
        required = ("MCP_URL", "LLM_PROVIDER", "LLM_MODEL")
        required += ("LLM_API_KEY",) if stage == "01" else (
            "KEYCARD_ISSUER", "KEYCARD_CLIENT_ID", "KEYCARD_CLIENT_SECRET",
            "AGENT_RESOURCE", "EXPENSE_DESK_ORIGIN", "LLM_RESOURCE")
    values, issues = read_env(component / ".env")
    check("dotenv_readable_and_supported", not issues)
    result["dotenv_issues"] = issues
    for key in required:
        check(key + "_present", present(values.get(key, "")))
    for key in ("KEYCARD_ISSUER", "MCP_URL", "EXPENSE_DESK_ORIGIN"):
        if values.get(key):
            check(key + "_url_shape", url_valid(values[key], origin=key == "EXPENSE_DESK_ORIGIN"))
    if stage in {"02", "03"}:
        check("AGENT_RESOURCE_workshop_shape", bool(re.fullmatch(
            r"urn:agent:resource:[A-Za-z0-9][A-Za-z0-9-]*", values.get("AGENT_RESOURCE", ""))))
        check("MCP_URL_matches_workshop_identifier", values.get("MCP_URL") == "http://localhost:8100/mcp")
    if stage == "04":
        result["temporal_settings"] = {
            key: "configured" if key in values else "runtime_default"
            for key in ("TEMPORAL_ADDRESS", "TEMPORAL_NAMESPACE", "TEMPORAL_TASK_QUEUE")
        }
        result["limitations"].append(
            "Confirm Temporal address, namespace, and queue against the instructor's settings; defaults may target a different room."
        )
        for key in result["temporal_settings"]:
            if key in values:
                check(key + "_nonempty", present(values[key]))
        check("settlement_demo_present", (component / "demo.py").is_file())
        check("LEDGER_RESOURCE_matches_workshop_identifier", values.get("LEDGER_RESOURCE") == "urn:ledger:api")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("01", "02", "03", "04"), required=True)
    parser.add_argument("--starter", action="store_true")
    args = parser.parse_args()
    result = inspect(args.root, args.stage, args.starter)
    print(json.dumps(result, indent=2))
    return int(any(c["status"] != "ok" for c in result["checks"]))


if __name__ == "__main__":
    raise SystemExit(main())

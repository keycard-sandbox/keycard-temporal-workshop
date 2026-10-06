"""Restore exercise source without changing credentials or service data."""

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
stage = sys.argv[1] if len(sys.argv) == 2 else ""
if stage not in {"01", "02", "03", "04"}:
    raise SystemExit("Usage: python checkpoints/restore.py 01|02|03|04")
for source in (ROOT / "checkpoints" / ("01-starter" if stage == "01" else "02-authenticated")).rglob("*.py"):
    relative = source.relative_to(source.parents[1])
    shutil.copy2(source, ROOT / relative)
if stage == "04":
    for source in (ROOT / "checkpoints/04-temporal/temporal").glob("*.py"):
        shutil.copy2(source, ROOT / "temporal" / source.name)
print(f"Checkpoint {stage} restored. Restart the affected processes; keep your existing .env files.")

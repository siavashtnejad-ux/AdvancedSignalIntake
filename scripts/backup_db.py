from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "data" / "ethical_horizon.db"
backup_dir = ROOT / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)

if not src.exists():
    raise SystemExit(f"Database not found: {src}")

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
dst = backup_dir / f"ethical_horizon_{stamp}.db"

with sqlite3.connect(src) as source, sqlite3.connect(dst) as target:
    source.backup(target)

print(dst)

#!/usr/bin/env python3
"""Standalone reseeding helper.

Drops the existing SQLite database and recreates it with the demo pipelines,
alert rules and sample events.  Useful for resetting a development database
to a known-good state.

Usage (from the repository root)::

    python scripts/seed.py               # use configured DB path
    python scripts/seed.py --path data/demo.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "app"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", help="Path to the SQLite DB file to seed")
    args = parser.parse_args()

    from app.config import settings
    from app.database import Database, get_db
    from app.seed import seed

    db_path = Path(args.path) if args.path else settings.database_path
    print(f"Resetting database at: {db_path}")

    if db_path.exists():
        db_path.unlink()
    db = Database(db_path)

    # Point the process-global DB at our chosen file so all services agree.
    import app.database as dbmod
    dbmod._db = db

    seeded = seed(db)
    print("Seeded demo data." if seeded else "Database was not empty; nothing seeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
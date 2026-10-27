#!/usr/bin/env python3
"""Database cleanup script for US Backend.

Safely deletes all records across all database tables in reverse topological
dependency order (child tables first, parent tables last).

Usage:
    python scripts/clear_db.py                # Prompts for confirmation before clearing
    python scripts/clear_db.py -y             # Clear without confirmation prompt
    python scripts/clear_db.py --keep-questions # Clear everything except seeded questions
    python scripts/clear_db.py --reseed       # Clear everything, then re-seed questions
    python scripts/clear_db.py --dry-run      # Preview row counts without deleting
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select
from api.db.base import Base
from api.db.session import SessionLocal, database_url
import api.v1.models  # Registers all models in Base.metadata
from scripts.seed_questions import QUESTIONS, seed_questions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clear records from the US database in correct foreign key order.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt and immediately clear the database.",
    )
    parser.add_argument(
        "--keep-questions",
        action="store_true",
        help="Do not delete rows from the 'questions' table.",
    )
    parser.add_argument(
        "--reseed",
        action="store_true",
        help="Re-seed the 'questions' table immediately after clearing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview row counts for each table without deleting any data.",
    )
    return parser.parse_args()


def get_table_counts(db) -> list[tuple[str, int]]:
    """Return a list of (table_name, count) in reverse dependency order."""
    counts = []
    for table in reversed(Base.metadata.sorted_tables):
        cnt = db.scalar(select(func.count()).select_from(table)) or 0
        counts.append((table.name, cnt))
    return counts


def main() -> int:
    args = parse_args()

    # Mask database credentials for safe logging
    safe_db_url = database_url
    if "@" in safe_db_url and "://" in safe_db_url:
        proto, rest = safe_db_url.split("://", 1)
        creds, host_part = rest.split("@", 1)
        user = creds.split(":", 1)[0]
        safe_db_url = f"{proto}://{user}:***@{host_part}"

    print("=" * 60)
    print(" US DATABASE CLEANUP SCRIPT")
    print(f" Target Database: {safe_db_url}")
    print("=" * 60)

    db = SessionLocal()
    try:
        counts = get_table_counts(db)
        total_rows = sum(cnt for _, cnt in counts)

        print("\nCurrent table statistics:")
        for name, cnt in counts:
            skip_note = " (will keep)" if args.keep_questions and name == "questions" else ""
            print(f"  • {name:<22}: {cnt:>5} rows{skip_note}")
        print(f"  Total records: {total_rows}")
        print("-" * 60)

        if args.dry_run:
            print("[DRY RUN] No changes were made to the database.")
            return 0

        if total_rows == 0:
            print("Database is already empty. Nothing to clear.")
            if args.reseed:
                print("\nRe-seeding questions as requested...")
                inserted, reactivated = seed_questions()
                print(f"Seeded {len(QUESTIONS)} questions ({inserted} inserted, {reactivated} reactivated).")
            return 0

        # Confirmation prompt if not bypassed
        if not args.yes:
            prompt = "\nWARNING: This will permanently delete data! Type 'yes' to proceed: "
            try:
                response = input(prompt).strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                return 1
            if response != "yes":
                print("Aborted. Database was not modified.")
                return 1

        print("\nClearing tables...")
        deleted_summary: list[tuple[str, int]] = []

        with db.begin():
            for table in reversed(Base.metadata.sorted_tables):
                if args.keep_questions and table.name == "questions":
                    continue
                result = db.execute(delete(table))
                deleted_rows = result.rowcount if result.rowcount is not None and result.rowcount >= 0 else 0
                deleted_summary.append((table.name, deleted_rows))
                print(f"  ✓ Cleared {table.name:<20} ({deleted_rows} rows removed)")

        print("-" * 60)
        total_deleted = sum(cnt for _, cnt in deleted_summary)
        print(f"Successfully cleared {len(deleted_summary)} tables ({total_deleted} total rows deleted).")

        if args.reseed:
            print("\nRe-seeding questions...")
            inserted, reactivated = seed_questions()
            print(f"Seeded {len(QUESTIONS)} questions ({inserted} inserted, {reactivated} reactivated).")

        print("Done!")
        return 0

    except Exception as exc:
        print(f"\n[ERROR] Database cleanup failed: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

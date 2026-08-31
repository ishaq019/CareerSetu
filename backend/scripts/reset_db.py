"""Destructive schema reset for development / staging.

The database schema had drifted from the ORM models (columns added over time
without being applied to an existing database). This script DROPS every app
table and recreates them from the current models, then stamps Alembic at
``head`` so future migrations line up.

⚠️  THIS DELETES ALL DATA in the app tables (users, analyses, interviews,
roadmaps). Only run it against a development / disposable database.

Usage (from the ``backend`` directory, venv active):

    python -m scripts.reset_db            # prompts for confirmation
    python -m scripts.reset_db --yes      # skip the prompt
"""
from __future__ import annotations

import sys

from app import models  # noqa: F401  (register ORM models on Base.metadata)
from app.core.config import settings
from app.db import Base, engine


def main() -> int:
    # Refuse against a production database — a stray `python -m scripts.reset_db`
    # on a real host would wipe every user account.
    if settings.is_production:
        if "--i-know-what-im-doing" not in sys.argv:
            print(
                "ERROR: reset_db is disabled in production. Refusing to drop tables.\n"
                "       Pass --i-know-what-im-doing to override."
            )
            return 2
        print(
            "WARNING: running reset_db against a production database. "
            "All data will be destroyed."
        )

    assume_yes = "--yes" in sys.argv or "-y" in sys.argv
    target = "sqlite" if settings.is_sqlite else "postgresql"
    print(f"Target database: {target}")
    print("This will DROP and RECREATE all CareerSetu tables. All data is lost.")

    if not assume_yes:
        reply = input("Type 'reset' to continue: ").strip().lower()
        if reply != "reset":
            print("Aborted.")
            return 1

    print("Dropping tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables from current models...")
    Base.metadata.create_all(bind=engine)
    print("Schema rebuilt.")

    # Stamp Alembic at head so `alembic upgrade head` is a no-op going forward.
    try:
        from alembic import command
        from alembic.config import Config

        cfg = Config("alembic.ini")
        command.stamp(cfg, "head")
        print("Alembic stamped at head.")
    except Exception as exc:  # alembic optional in some environments
        print(f"(Skipped Alembic stamp: {exc})")

    print("Done. Restart uvicorn and retry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

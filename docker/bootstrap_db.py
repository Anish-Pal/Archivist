"""Bring the target database up to the current schema.

The Alembic history starts *after* the initial tables were created by
``database/init_db.py``, so ``alembic upgrade head`` alone fails against an
empty database (the first revision alters tables that do not exist yet).

Fresh database  -> create every table from the models, then stamp head.
Existing database -> hand off to a normal ``alembic upgrade head``.

Prints the chosen strategy so the caller knows which command to run next.
"""

import sys

from sqlalchemy import inspect

from database.database import Base, engine
from database import models  # noqa: F401  (registers every table on Base)


def main() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "alembic_version" in tables:
        print("bootstrap: alembic_version present, running incremental upgrade")
        print("STRATEGY=upgrade")
        return

    if tables & {"users", "conversations", "messages", "session", "documents"}:
        # Schema was created before Alembic was introduced (or by init_db.py).
        # Create anything missing, then adopt the current head without
        # replaying migrations that would fail on already-current tables.
        print("bootstrap: existing schema without alembic_version, stamping head")
    else:
        print("bootstrap: empty database, creating schema from models")

    Base.metadata.create_all(bind=engine)
    print("STRATEGY=stamp")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - surface the cause and fail the boot
        print(f"bootstrap: database setup failed: {exc}", file=sys.stderr)
        sys.exit(1)

"""Copy SQLite history into an empty PostgreSQL database, preserving IDs.

Run from backend: python migrate_sqlite.py --source zaradera.db
Target is DATABASE_URL in the environment/.env. Stop uploads during migration.
"""
import argparse
from pathlib import Path

from sqlalchemy import create_engine, func, select, text

from app.config import get_settings
from app.db_url import database_url
from app.models import Upload, Snapshot, User
from app.database import Base


TABLES = [User.__table__, Upload.__table__, Snapshot.__table__]


def migrate(source_engine, target_engine):
    Base.metadata.create_all(target_engine)
    counts = {}
    with source_engine.connect() as source, target_engine.begin() as target:
        # Lock out writes while checking emptiness and copying all tables.
        if target_engine.dialect.name == "postgresql":
            target.execute(text("LOCK TABLE users, uploads, snapshots IN ACCESS EXCLUSIVE MODE"))
        for table in TABLES:
            if target.scalar(select(func.count()).select_from(table)):
                raise ValueError("Target database must be empty; nothing was copied.")
        for table in TABLES:
            count = 0
            result = source.execute(select(table)).mappings()
            while batch := result.fetchmany(500):
                target.execute(table.insert(), [dict(row) for row in batch])
                count += len(batch)
            counts[table.name] = count
            if target.scalar(select(func.count()).select_from(table)) != count:
                raise ValueError("Row count verification failed; migration rolled back.")
        if target_engine.dialect.name == "postgresql":
            for table in TABLES:
                # Table names come only from the fixed model list above.
                target.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                    f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table.name}"
                ))
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error("Source database does not exist.")
    target_url = database_url(get_settings().database_url)
    if target_url.get_backend_name() != "postgresql":
        parser.error("Set DATABASE_URL to your PostgreSQL target first.")
    # Read-only URI prevents accidentally creating or modifying the source.
    source = create_engine("sqlite:///file:" + args.source.resolve().as_posix() + "?mode=ro&uri=true")
    target = create_engine(target_url, pool_pre_ping=True)
    try:
        counts = migrate(source, target)
        print("Migration verified: " + ", ".join(f"{name}={count}" for name, count in counts.items()))
    finally:
        source.dispose()
        target.dispose()


if __name__ == "__main__":
    main()

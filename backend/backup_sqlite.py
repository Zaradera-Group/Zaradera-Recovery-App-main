"""Create a consistent SQLite backup, including when the app is running.

Run from backend: .venv/Scripts/python backup_sqlite.py /path/to/backup.db
"""
import sqlite3
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

from app.config import get_settings


def main():
    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        raise SystemExit("This utility requires a file-based SQLite database.")
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python backup_sqlite.py DESTINATION.db")
    source = Path(url.database).resolve()
    destination = Path(sys.argv[1]).resolve()
    if not source.is_file():
        raise SystemExit("Source database does not exist.")
    if destination.exists() or source == destination:
        raise SystemExit("Choose a new destination; existing files are never overwritten.")
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as original:
        with sqlite3.connect(destination) as backup:
            original.backup(backup)
    print(f"Backup created: {destination}")


if __name__ == "__main__":
    main()

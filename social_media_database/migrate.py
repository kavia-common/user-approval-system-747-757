#!/usr/bin/env python3
"""
Simple migration runner for SQLite.

- Reads DB path from SQLITE_DB or defaults to local myapp.db
- Executes Python migration scripts in migrations/ in lexical order
- Tracks applied migrations in schema_migrations table

Usage:
  python migrate.py
"""
import os
import sqlite3
from typing import List

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")
DB_ENV = "SQLITE_DB"
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "myapp.db")

def get_db_path() -> str:
    return os.environ.get(DB_ENV) or DEFAULT_DB

def list_migrations() -> List[str]:
    if not os.path.isdir(MIGRATIONS_DIR):
        return []
    files = [f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".py") and f[0].isdigit()]
    return sorted(files)

def ensure_tracking(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

def applied_set(conn: sqlite3.Connection) -> set:
    rows = conn.execute("SELECT filename FROM schema_migrations").fetchall()
    return {r[0] for r in rows}

def main():
    db_path = get_db_path()
    print(f"Using DB: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    ensure_tracking(conn)

    pending = []
    already = applied_set(conn)
    for fname in list_migrations():
        if fname not in already:
            pending.append(fname)

    if not pending:
        print("No pending migrations.")
        return

    print("Pending migrations:")
    for f in pending:
        print(f" - {f}")

    for f in pending:
        print(f"Applying {f} ...")
        module_path = os.path.join(MIGRATIONS_DIR, f)
        scope = {}
        with open(module_path, "r") as fh:
            code = compile(fh.read(), module_path, "exec")
            exec(code, scope)
        if "run" not in scope or not callable(scope["run"]):
            raise RuntimeError(f"Migration {f} missing run(conn) function")
        try:
            scope["run"](conn)
            conn.execute("INSERT INTO schema_migrations (filename) VALUES (?)", (f,))
            conn.commit()
            print(f"✓ {f} applied")
        except Exception as e:
            conn.rollback()
            print(f"✗ Failed {f}: {e}")
            raise
    conn.close()
    print("All migrations applied.")

if __name__ == "__main__":
    main()

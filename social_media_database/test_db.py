#!/usr/bin/env python3
"""Test SQLite database connection and schema presence"""

import sqlite3
import sys
import os

DB_ENV = "SQLITE_DB"
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "myapp.db")

def get_db_path():
    return os.environ.get(DB_ENV) or DEFAULT_DB

try:
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Database file '{db_path}' not found")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("SELECT sqlite_version()")
    version = cur.fetchone()[0]

    # Verify core tables exist
    required = ["users", "profiles", "posts", "followers", "reactions", "analytics_daily_user", "analytics_platform_daily"]
    missing = []
    for t in required:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,))
        if not cur.fetchone():
            missing.append(t)
    conn.close()

    if missing:
        print(f"SQLite version: {version}. Missing tables: {', '.join(missing)}")
        sys.exit(2)

    print(f"SQLite version: {version}. All required tables present.")
    sys.exit(0)

except sqlite3.Error as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

#!/usr/bin/env python3
"""Initialize SQLite database for social_media_database

This script:
- Detects DB path from SQLITE_DB environment variable (fallback to local myapp.db)
- Creates full schema (users, profiles, posts, followers, reactions, analytics)
- Seeds initial data
- Writes db_connection.txt and db_visualizer/sqlite.env
- Prints useful info and stats

Note on execution rules:
- We create statements via sqlite3 execute() sequentially (no external .sql files).
"""

import os
import sqlite3
from datetime import datetime
from typing import List

DB_ENV = "SQLITE_DB"
DEFAULT_DB_NAME = "myapp.db"

def get_db_path() -> str:
    path = os.environ.get(DB_ENV)
    if path and path.strip():
        return path
    # default to local file in this folder
    return os.path.join(os.path.dirname(__file__), DEFAULT_DB_NAME)

def exec_many(conn: sqlite3.Connection, stmts: List[str]):
    cur = conn.cursor()
    for s in stmts:
        if not s:
            continue
        cur.execute(s)

def main():
    print("Starting SQLite setup...")

    db_path = get_db_path()
    db_dir = os.path.dirname(db_path) or "."
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    db_exists = os.path.exists(db_path)
    if db_exists:
        print(f"SQLite database already exists at {db_path}")
    else:
        print(f"Creating new SQLite database at {db_path} ...")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        # Import schema module
        from schema.sql import CREATE_USERS  # type: ignore
    except Exception:
        # fallback to relative import of schema.sql.py in this directory
        pass

    # Import local schema defs
    from schema import sql as _schema  # type: ignore

    # Build schema
    print("Applying schema DDL...")
    for ddl in _schema.ALL_DDL:
        conn.execute(ddl)
    for idx_stmt in _schema.CREATE_INDICES:
        conn.execute(idx_stmt)

    # Seed basic data only if empty
    print("Seeding initial data (idempotent)...")
    cur = conn.execute("SELECT COUNT(*) FROM users;")
    user_count = cur.fetchone()[0]
    if user_count == 0:
        # users
        conn.executemany(
            "INSERT INTO users (username, email, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?)",
            _schema.SEED_USERS,
        )
        # profiles
        conn.executemany(
            "INSERT INTO profiles (user_id, display_name, bio, location, website, avatar_url) VALUES (?, ?, ?, ?, ?, ?)",
            _schema.SEED_PROFILES,
        )
        # posts
        conn.executemany(
            "INSERT INTO posts (user_id, content, media_url, visibility) VALUES (?, ?, ?, ?)",
            _schema.SEED_POSTS,
        )
        # followers
        conn.executemany(
            "INSERT OR IGNORE INTO followers (follower_id, followee_id) VALUES (?, ?)",
            _schema.SEED_FOLLOWERS,
        )
        # reactions
        # Need post IDs: assume autoincrement start at 1 and insertion order preserved for this seed
        # We'll map: posts inserted above in order and just use their implied IDs
        reactions_params = []
        for (uid, post_id, rtype) in _schema.SEED_REACTIONS:
            reactions_params.append((uid, post_id, rtype))
        conn.executemany(
            "INSERT OR IGNORE INTO reactions (user_id, post_id, reaction_type) VALUES (?, ?, ?)",
            reactions_params,
        )

        # Basic analytics snapshot for 'today'
        # Compute aggregates lightweight
        conn.execute(_schema.UPSERT_ANALYTICS_PLATFORM_DAILY, (len(_schema.SEED_POSTS), len(_schema.SEED_REACTIONS), len(_schema.SEED_USERS)))
        # per-user simple counts
        # posts per user
        rows = conn.execute("SELECT user_id, COUNT(*) FROM posts GROUP BY user_id").fetchall()
        for user_id, pc in rows:
            # reactions received per user (on their posts)
            rc = conn.execute("""
                SELECT COUNT(*)
                FROM reactions r
                JOIN posts p ON p.id = r.post_id
                WHERE p.user_id = ?
            """, (user_id,)).fetchone()[0]
            # followers gained naive snapshot (total followers)
            fg = conn.execute("SELECT COUNT(*) FROM followers WHERE followee_id = ?", (user_id,)).fetchone()[0]
            conn.execute(_schema.UPSERT_ANALYTICS_DAILY_USER, (user_id, pc, rc, fg, 0))

    conn.commit()

    # Stats
    def table_count():
        return conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]

    # Save connection info
    connection_string = f"sqlite:///{db_path}"
    try:
        with open(os.path.join(os.path.dirname(__file__), "db_connection.txt"), "w") as f:
            f.write("# SQLite connection methods:\n")
            f.write(f"# Python: sqlite3.connect('{db_path}')\n")
            f.write(f"# Connection string: {connection_string}\n")
            f.write(f"# File path: {db_path}\n")
        print("Connection information saved to db_connection.txt")
    except Exception as e:
        print(f"Warning: Could not save connection info: {e}")

    # db_visualizer env file
    viz_dir = os.path.join(os.path.dirname(__file__), "db_visualizer")
    os.makedirs(viz_dir, exist_ok=True)
    try:
        with open(os.path.join(viz_dir, "sqlite.env"), "w") as f:
            f.write(f'export SQLITE_DB="{db_path}"\n')
        print("Environment variables saved to db_visualizer/sqlite.env")
    except Exception as e:
        print(f"Warning: Could not save environment variables: {e}")

    # Print stats
    print("\nSQLite setup complete!")
    print(f"Database: {os.path.basename(db_path)}")
    print(f"Location: {db_path}")
    print("")
    print("To use with Node.js viewer, run: source db_visualizer/sqlite.env")
    print("\nTo connect to the database, use one of the following methods:")
    print(f"1. Python: sqlite3.connect('{db_path}')")
    print(f"2. Connection string: {connection_string}")
    print(f"3. Direct file access: {db_path}")
    print("")
    print("Database statistics:")
    print(f"  Tables: {table_count()}")

    print("\nScript completed successfully.")
    conn.close()

if __name__ == "__main__":
    main()

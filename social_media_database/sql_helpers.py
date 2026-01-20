#!/usr/bin/env python3
"""
Lightweight SQL helper utilities for the SQLite database.

- Reads DB path from environment variable SQLITE_DB (falls back to local myapp.db)
- Provides context-managed connection with foreign_keys pragma enabled
- Convenience functions for executing statements safely
- Minimal "ORM-like" helpers for common entities

ENV:
  SQLITE_DB: Absolute or relative path to SQLite database file

Usage:
  from sql_helpers import get_db_path, get_connection, fetch_all, fetch_one, execute

Note: Keep dependencies minimal; use sqlite3 from stdlib.
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple

DEFAULT_DB = "myapp.db"

def get_db_path() -> str:
    """
    Determine the database path from env (SQLITE_DB) or default.

    Returns:
        str: Path to the SQLite database file.
    """
    return os.environ.get("SQLITE_DB") or os.path.join(os.path.dirname(__file__), DEFAULT_DB)

@contextmanager
def get_connection(db_path: Optional[str] = None):
    """
    Context manager returning a connection with foreign keys enabled.

    Args:
        db_path (Optional[str]): Specific DB path; if None uses get_db_path().

    Yields:
        sqlite3.Connection
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute(sql: str, params: Iterable[Any] = ()) -> int:
    """
    Execute a single write statement.

    Returns:
        int: lastrowid if available, else -1
    """
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params))
        try:
            return cur.lastrowid or -1
        except Exception:
            return -1

def executemany(sql: str, seq_params: Iterable[Iterable[Any]]) -> int:
    """
    Execute repeated statements.

    Returns:
        int: number of rows affected (best effort)
    """
    with get_connection() as conn:
        cur = conn.executemany(sql, list(seq_params))
        return cur.rowcount if cur.rowcount is not None else 0

def fetch_all(sql: str, params: Iterable[Any] = ()) -> List[Tuple]:
    """
    Fetch all rows for a SELECT.
    """
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.fetchall()

def fetch_one(sql: str, params: Iterable[Any] = ()) -> Optional[Tuple]:
    """
    Fetch one row for a SELECT.
    """
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params))
        return cur.fetchone()

# PUBLIC_INTERFACE
def get_user_with_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Return a joined user + profile record."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            """
            SELECT u.id, u.username, u.email, u.role, u.is_active, u.created_at,
                   p.display_name, p.bio, p.location, p.website, p.avatar_url, p.updated_at as profile_updated_at
            FROM users u
            LEFT JOIN profiles p ON p.user_id = u.id
            WHERE u.id = ?
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)

# PUBLIC_INTERFACE
def create_post(user_id: int, content: str, media_url: Optional[str] = None, visibility: str = "public") -> int:
    """Create a post for a user and return the post ID."""
    return execute(
        "INSERT INTO posts (user_id, content, media_url, visibility) VALUES (?, ?, ?, ?)",
        (user_id, content, media_url, visibility),
    )

# PUBLIC_INTERFACE
def react_to_post(user_id: int, post_id: int, reaction_type: str) -> bool:
    """Add or ignore duplicate reaction; returns True if inserted."""
    try:
        execute(
            "INSERT OR IGNORE INTO reactions (user_id, post_id, reaction_type) VALUES (?, ?, ?)",
            (user_id, post_id, reaction_type),
        )
        return True
    except sqlite3.Error:
        return False

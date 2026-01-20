# Social Media Database (SQLite)

This container provides the persistent storage for the social media dashboard.

Contents:
- SQLite schema for users, profiles, posts, followers, reactions
- Analytics aggregate tables (daily per-user and platform-wide)
- Seed data for quick development
- Simple migration runner
- Lightweight SQL helper utilities

## Environment

- SQLITE_DB: Absolute or relative path to the SQLite database file.
  - If not provided, defaults to myapp.db in this folder.
- See .env.example for a sample configuration.

## Initialize

Initialize the database (creates schema and seeds data):

  python3 init_db.py

This will:
- Create the database file at SQLITE_DB (or ./myapp.db)
- Build the schema
- Insert seed data (only if users table is empty)
- Create db_visualizer/sqlite.env for the viewer utility
- Write db_connection.txt with connection info

## Migrations

Add migration scripts under migrations/ as Python files with a run(conn) function.

Example:

def run(conn):
    conn.execute("ALTER TABLE posts ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")

Run pending migrations:

  python3 migrate.py

## Helpers

Use sql_helpers.py for simple operations:

from sql_helpers import get_user_with_profile, create_post, react_to_post

## Development utilities

- db_shell.py: interactive shell to explore and query the database
- db_visualizer/: small Node.js server to view tables (source env first)

## Schema overview

- users(id, username, email, password_hash, role, is_active, created_at)
- profiles(id, user_id [unique], display_name, bio, location, website, avatar_url, updated_at)
- posts(id, user_id, content, media_url, created_at, updated_at, visibility, is_deleted)
- followers(follower_id, followee_id, created_at) [composite PK]
- reactions(id, user_id, post_id, reaction_type, created_at) [unique (user_id, post_id, reaction_type)]
- analytics_daily_user(id, user_id, date, posts_count, reactions_received, followers_gained, followers_lost, created_at)
- analytics_platform_daily(id, date, total_posts, total_reactions, total_new_users, created_at)

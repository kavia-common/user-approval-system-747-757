#!/usr/bin/env python3
"""
Schema module for social_media_database.

Defines the SQL DDL statements for the application schema, to be used by init_db.py
and migration utilities. This file is imported (not executed) to provide the SQL strings.

Tables:
- users
- profiles
- posts
- followers
- reactions
- analytics_daily_user (aggregates per day per user)
- analytics_platform_daily (platform-wide aggregates per day)

Indices and constraints are included for performance and integrity.

Note: We keep DDL here as Python strings as per project rule to avoid raw .sql files.
"""

# Core tables

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', -- 'user' | 'admin'
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PROFILES = """
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    display_name TEXT,
    bio TEXT,
    location TEXT,
    website TEXT,
    avatar_url TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""

CREATE_POSTS = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    media_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    visibility TEXT NOT NULL DEFAULT 'public', -- 'public' | 'private' | 'followers'
    is_deleted INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""

CREATE_FOLLOWERS = """
CREATE TABLE IF NOT EXISTS followers (
    follower_id INTEGER NOT NULL,
    followee_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followee_id),
    FOREIGN KEY (follower_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (followee_id) REFERENCES users (id) ON DELETE CASCADE,
    CHECK (follower_id != followee_id)
);
"""

CREATE_REACTIONS = """
CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    reaction_type TEXT NOT NULL, -- 'like' | 'love' | 'haha' | 'wow' | 'sad' | 'angry'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, post_id, reaction_type),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
);
"""

# Analytics tables

CREATE_ANALYTICS_DAILY_USER = """
CREATE TABLE IF NOT EXISTS analytics_daily_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL, -- YYYY-MM-DD
    posts_count INTEGER NOT NULL DEFAULT 0,
    reactions_received INTEGER NOT NULL DEFAULT 0,
    followers_gained INTEGER NOT NULL DEFAULT 0,
    followers_lost INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
"""

CREATE_ANALYTICS_PLATFORM_DAILY = """
CREATE TABLE IF NOT EXISTS analytics_platform_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL, -- YYYY-MM-DD
    total_posts INTEGER NOT NULL DEFAULT 0,
    total_reactions INTEGER NOT NULL DEFAULT 0,
    total_new_users INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (date)
);
"""

# Helpful indices

CREATE_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_reactions_post_id ON reactions(post_id);",
    "CREATE INDEX IF NOT EXISTS idx_reactions_user_id ON reactions(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_followers_followee ON followers(followee_id);",
    "CREATE INDEX IF NOT EXISTS idx_followers_follower ON followers(follower_id);",
    "CREATE INDEX IF NOT EXISTS idx_analytics_daily_user_date ON analytics_daily_user(date);",
    "CREATE INDEX IF NOT EXISTS idx_analytics_platform_daily_date ON analytics_platform_daily(date);",
]

# Seed data statements (executed one by one by init script)

SEED_USERS = [
    ("alice", "alice@example.com", "hash_alice", "user", 1),
    ("bob", "bob@example.com", "hash_bob", "user", 1),
    ("carol", "carol@example.com", "hash_carol", "admin", 1),
]

SEED_PROFILES = [
    (1, "Alice A.", "Coffee lover and photographer.", "NYC", "https://alice.example.com", None),
    (2, "Bobby B.", "Tech enthusiast and gamer.", "SF", "https://bob.example.com", None),
    (3, "Carol C.", "Platform admin and data nerd.", "Remote", "https://carol.example.com", None),
]

SEED_POSTS = [
    (1, "Hello world! This is my first post.", None, "public"),
    (1, "Another day, another coffee shot.", None, "public"),
    (2, "Just reached level 20!", None, "followers"),
    (3, "System maintenance tonight at 11 PM UTC.", None, "public"),
]

SEED_FOLLOWERS = [
    (2, 1),  # bob follows alice
    (1, 2),  # alice follows bob
    (1, 3),  # alice follows carol
]

SEED_REACTIONS = [
    (2, 1, "like"),   # bob likes alice post #1
    (3, 1, "wow"),    # carol wow alice post #1
    (1, 3, "like"),   # alice likes bob post #3
    (2, 4, "love"),   # bob loves carol post #4
]

# Utility queries

UPSERT_ANALYTICS_DAILY_USER = """
INSERT INTO analytics_daily_user (user_id, date, posts_count, reactions_received, followers_gained, followers_lost)
VALUES (?, date('now'), ?, ?, ?, ?)
ON CONFLICT(user_id, date) DO UPDATE SET
    posts_count = posts_count + excluded.posts_count,
    reactions_received = reactions_received + excluded.reactions_received,
    followers_gained = followers_gained + excluded.followers_gained,
    followers_lost = followers_lost + excluded.followers_lost;
"""

UPSERT_ANALYTICS_PLATFORM_DAILY = """
INSERT INTO analytics_platform_daily (date, total_posts, total_reactions, total_new_users)
VALUES (date('now'), ?, ?, ?)
ON CONFLICT(date) DO UPDATE SET
    total_posts = total_posts + excluded.total_posts,
    total_reactions = total_reactions + excluded.total_reactions,
    total_new_users = total_new_users + excluded.total_new_users;
"""

ALL_DDL = [
    CREATE_USERS,
    CREATE_PROFILES,
    CREATE_POSTS,
    CREATE_FOLLOWERS,
    CREATE_REACTIONS,
    CREATE_ANALYTICS_DAILY_USER,
    CREATE_ANALYTICS_PLATFORM_DAILY,
]

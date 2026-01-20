# Migrations

Place migration scripts as Python files named with an incrementing prefix, e.g.:

- 0001_initial.py
- 0002_add_indexes.py

Each migration script must define a function:

def run(conn):
    conn.execute("...")  # execute statements one-by-one

Run all pending migrations:
  python migrate.py

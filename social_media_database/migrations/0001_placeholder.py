def run(conn):
    # Base schema is created by init_db.py; this placeholder ensures migration tracking starts.
    conn.execute("SELECT 1;")

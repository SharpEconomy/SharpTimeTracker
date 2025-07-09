import os
import csv
from datetime import datetime
import psycopg2

DB_URL = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")
if not DB_URL:
    raise SystemExit("Missing SUPABASE_DB_URL or DATABASE_URL")

TABLE = "time_entries"

with psycopg2.connect(DB_URL) as conn:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                id SERIAL PRIMARY KEY,
                name TEXT,
                date DATE,
                from_time TEXT,
                to_time TEXT,
                task TEXT,
                description TEXT,
                file TEXT,
                created_at TIMESTAMPTZ
            )
            """
        )
        conn.commit()



def parse_date(s: str) -> str:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s).date().isoformat()
    except ValueError:
        return datetime.now().date().isoformat()


with psycopg2.connect(DB_URL) as conn:
    with conn.cursor() as cur:
        with open("time_log.csv", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                created = row.get("Created At") or datetime.now().isoformat()
                cur.execute(
                    f"INSERT INTO {TABLE} (name, date, from_time, to_time, task, description, file, created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row.get("Name"),
                        parse_date(row.get("Date", "")),
                        row.get("From Time"),
                        row.get("To Time"),
                        row.get("Task"),
                        row.get("Description"),
                        row.get("File"),
                        created,
                    ),
                )
        conn.commit()

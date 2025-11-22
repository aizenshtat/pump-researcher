import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "research.db"

def init_db():
    """Initialize the database with schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    schema_path = Path(__file__).parent / "schema.sql"

    with sqlite3.connect(DB_PATH) as conn:
        with open(schema_path) as f:
            conn.executescript(f.read())

        # Run migrations for existing databases
        run_migrations(conn)

    print(f"Database initialized at {DB_PATH}")

def run_migrations(conn):
    """Run database migrations for schema updates."""
    cursor = conn.cursor()

    # Check if logs column exists in agent_runs
    cursor.execute("PRAGMA table_info(agent_runs)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'logs' not in columns:
        print("Migration: Adding logs column to agent_runs")
        cursor.execute("ALTER TABLE agent_runs ADD COLUMN logs TEXT")
        conn.commit()

def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    init_db()

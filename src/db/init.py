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

    print(f"Database initialized at {DB_PATH}")

def get_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH)

if __name__ == "__main__":
    init_db()

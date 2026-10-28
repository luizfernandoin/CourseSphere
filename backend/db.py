import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def get_db_path():
    """Dynamically resolves the path to the SQLite database file."""
    p1 = BASE_DIR / "cornell-course-sphere-data" / "roster_reviews.sqlite.db"
    p2 = BASE_DIR / "cournell-course-sphere-data" / "roster_reviews.sqlite.db"
    if p1.exists():
        return str(p1)
    if p2.exists():
        return str(p2)
    return str(p1)

def create_connection():
    """Creates a connection to the SQLite database."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query: str, params=()):
    """
    Executes a parameterized SQL query safely against SQLite.
    Parameters are bound using placeholders to prevent SQL injection.
    """
    conn = create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.commit()
        return rows
    finally:
        conn.close()

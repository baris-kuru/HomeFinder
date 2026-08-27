"""SQLite state: which listings we've seen and what we did about them."""
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "homefinder.db"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS seen (
            id INTEGER PRIMARY KEY,
            first_seen REAL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            company TEXT,
            status TEXT,
            address TEXT,
            ts REAL
        )"""
    )
    conn.commit()
    return conn


def is_seen(conn: sqlite3.Connection, listing_id: int) -> bool:
    cur = conn.execute("SELECT 1 FROM seen WHERE id = ?", (listing_id,))
    return cur.fetchone() is not None


def mark_seen(conn: sqlite3.Connection, listing_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO seen (id, first_seen) VALUES (?, ?)",
        (listing_id, time.time()),
    )
    conn.commit()


def record_application(conn, listing_id, company, status, address) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO applications (id, company, status, address, ts) VALUES (?, ?, ?, ?, ?)",
        (listing_id, company, status, address, time.time()),
    )
    conn.commit()


def count_seen(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM seen").fetchone()[0]

import os
import sqlite3
from contextlib import closing
from typing import Tuple, List

DB_PATH = os.environ.get("DB_PATH", "skate.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS weeks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  iso_year INTEGER NOT NULL,
  iso_week INTEGER NOT NULL,
  quota INTEGER NOT NULL,
  goalie_notified INTEGER NOT NULL DEFAULT 0,
  UNIQUE(iso_year, iso_week)
);

CREATE TABLE IF NOT EXISTS signups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  week_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(week_id) REFERENCES weeks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS broadcasts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goalie_info (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phone TEXT NOT NULL UNIQUE,
  venmo_username TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Initialize the database with schema and default settings"""
    with closing(db()) as conn:
        conn.executescript(SCHEMA)
        # ensure keys exist
        cur = conn.execute("SELECT value FROM settings WHERE key='goalie_phone'")
        if cur.fetchone() is None:
            conn.execute("INSERT INTO settings(key, value) VALUES('goalie_phone','')")
        conn.commit()

def get_week_info(week_id: int):
    """Get week information and signups"""
    with closing(db()) as conn:
        week = conn.execute(
            "SELECT iso_year, iso_week, quota, goalie_notified FROM weeks WHERE id=?",
            (week_id,)
        ).fetchone()
        signups = conn.execute(
            "SELECT name, phone, created_at FROM signups WHERE week_id=? ORDER BY created_at ASC",
            (week_id,)
        ).fetchall()
        return week, signups

def set_quota(week_id: int, quota: int):
    """Set quota for a specific week"""
    with closing(db()) as conn:
        conn.execute("UPDATE weeks SET quota=? WHERE id=?", (quota, week_id))
        conn.commit()

def mark_goalie_notified(week_id: int):
    """Mark that goalie has been notified for this week"""
    with closing(db()) as conn:
        conn.execute("UPDATE weeks SET goalie_notified=1 WHERE id=?", (week_id,))
        conn.commit()

def get_broadcast_numbers() -> List[str]:
    """Get all broadcast phone numbers"""
    with closing(db()) as conn:
        return [r[0] for r in conn.execute("SELECT phone FROM broadcasts ORDER BY id").fetchall()]

def add_broadcast_number(phone: str):
    """Add a phone number to broadcast list"""
    with closing(db()) as conn:
        conn.execute("INSERT INTO broadcasts(phone) VALUES(?)", (phone,))
        conn.commit()

def remove_broadcast_number(phone: str):
    """Remove a phone number from broadcast list"""
    with closing(db()) as conn:
        conn.execute("DELETE FROM broadcasts WHERE phone=?", (phone,))
        conn.commit()

def get_goalie_phone() -> str:
    """Get the goalie phone number from settings"""
    with closing(db()) as conn:
        return conn.execute("SELECT value FROM settings WHERE key='goalie_phone'").fetchone()[0]

def set_goalie_phone(phone: str):
    """Set the goalie phone number in settings"""
    with closing(db()) as conn:
        conn.execute("UPDATE settings SET value=? WHERE key='goalie_phone'", (phone,))
        conn.commit()

def get_goalie_venmo_username(phone: str) -> str | None:
    """Get Venmo username for a goalie by phone number"""
    with closing(db()) as conn:
        row = conn.execute(
            "SELECT venmo_username FROM goalie_info WHERE phone=?",
            (phone,)
        ).fetchone()
        return row[0] if row else None

def store_goalie_venmo_username(phone: str, venmo_username: str):
    """Store or update Venmo username for a goalie"""
    from datetime import datetime
    with closing(db()) as conn:
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO goalie_info(phone, venmo_username, created_at, updated_at) VALUES(?,?,?,?)",
            (phone, venmo_username, now, now)
        )
        conn.commit()
        print(f"[GOALIE INFO] Stored Venmo username @{venmo_username} for {phone}")

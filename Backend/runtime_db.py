from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from config import RUNTIME_DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cgpa REAL NOT NULL DEFAULT 0.0,
    year_standing INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    program_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    start_year INTEGER,
    end_year INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS completed_courses (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_code TEXT NOT NULL,
    semester TEXT,
    year INTEGER,
    grade TEXT,
    numeric_grade REAL,
    status TEXT NOT NULL DEFAULT 'COMPLETED',
    credits_earned REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS saved_recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_code TEXT NOT NULL,
    program_code TEXT,
    reason TEXT,
    saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""


def init_runtime_db() -> str:
    RUNTIME_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(RUNTIME_DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    return str(RUNTIME_DB_PATH)


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    init_runtime_db()
    conn = sqlite3.connect(RUNTIME_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

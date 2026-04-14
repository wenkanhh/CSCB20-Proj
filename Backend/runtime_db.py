import sqlite3
from config import RUNTIME_DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cgpa REAL NOT NULL DEFAULT 0.0,
    year_standing INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS user_programs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    program_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    start_year INTEGER,
    end_year INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS completed_courses (
    record_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    course_code TEXT NOT NULL,
    semester TEXT,
    year INTEGER,
    grade TEXT,
    numeric_grade REAL,
    status TEXT NOT NULL DEFAULT 'COMPLETED',
    credits_earned REAL NOT NULL DEFAULT 0.5,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

def init_runtime_db():
    RUNTIME_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(RUNTIME_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)

    conn.commit()
    conn.close()


def get_conn():
    init_runtime_db()

    conn = sqlite3.connect(RUNTIME_DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON;")

    return conn
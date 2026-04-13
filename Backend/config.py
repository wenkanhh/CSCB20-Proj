from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Prefer the user's real project structure. Fallback to the local sandbox layout for testing.
DATA_DIR_CANDIDATES = [
    PROJECT_ROOT / 'data' / 'data_cleaned',
    PROJECT_ROOT / 'data_cleaned',
    PROJECT_ROOT,
]
SQL_DIR_CANDIDATES = [
    PROJECT_ROOT / 'sql',
    PROJECT_ROOT,
]


def _first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


DATA_DIR = _first_existing(DATA_DIR_CANDIDATES)
SQL_DIR = _first_existing(SQL_DIR_CANDIDATES)

RUNTIME_DB_PATH = SQL_DIR / 'backend_runtime.db'
EXISTING_PROJECT_DB_PATH = SQL_DIR / 'database.db'

SECRET_KEY = os.environ.get('COURSE_PLANNER_SECRET_KEY', 'dev-secret-change-me')
DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'

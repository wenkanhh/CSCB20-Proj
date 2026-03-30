from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

import pandas as pd

from config import DATA_DIR, EXISTING_PROJECT_DB_PATH


@dataclass
class DataRepository:
    courses: list[dict[str, Any]]
    programs: list[dict[str, Any]]
    requirements_groups: list[dict[str, Any]]
    requirement_items: list[dict[str, Any]]
    program_requirement: list[dict[str, Any]]
    program_requirement_courses: list[dict[str, Any]]
    course_exclusions: list[dict[str, Any]]
    departments: list[dict[str, Any]]
    department_prefixes: list[dict[str, Any]]

    @classmethod
    def load(cls) -> 'DataRepository':
        def load_csv(filename: str) -> list[dict[str, Any]]:
            path = DATA_DIR / filename
            if not path.exists():
                return []
            df = pd.read_csv(path)
            df = df.where(pd.notna(df), None)
            return df.to_dict(orient='records')

        return cls(
            courses=load_csv('courses.csv'),
            programs=load_csv('programs.csv'),
            requirements_groups=load_csv('requirements_groups.csv'),
            requirement_items=load_csv('requirement_items.csv'),
            program_requirement=load_csv('program_requirement.csv'),
            program_requirement_courses=load_csv('program_requirement_courses.csv'),
            course_exclusions=load_csv('course_exclusions.csv'),
            departments=load_csv('departments.csv'),
            department_prefixes=load_csv('department_prefixes.csv'),
        )

    def list_courses(self, search: str = '', prefix: str = '', limit: int = 200) -> list[dict[str, Any]]:
        rows = self.courses
        if search:
            s = search.lower()
            rows = [
                row for row in rows
                if s in str(row.get('course_code', '')).lower()
                or s in str(row.get('course_name', '')).lower()
            ]
        if prefix:
            p = prefix.upper().strip()
            rows = [row for row in rows if str(row.get('course_code_prefix', '')).upper() == p]
        return rows[:limit]

    def get_course(self, course_code: str) -> dict[str, Any] | None:
        target = course_code.upper().strip()
        for row in self.courses:
            if str(row.get('course_code', '')).upper() == target:
                return row
        return None

    def list_programs(self, search: str = '', program_type: str = '') -> list[dict[str, Any]]:
        rows = self.programs
        if search:
            s = search.lower()
            rows = [
                row for row in rows
                if s in str(row.get('program_code', '')).lower()
                or s in str(row.get('program_name', '')).lower()
            ]
        if program_type:
            pt = program_type.lower().strip()
            rows = [row for row in rows if str(row.get('program_type', '')).lower() == pt]
        return rows

    def get_program(self, program_code: str) -> dict[str, Any] | None:
        target = program_code.upper().strip()
        for row in self.programs:
            if str(row.get('program_code', '')).upper() == target:
                return row
        return None

    def get_course_requirements(self, course_code: str, req_type: str) -> list[dict[str, Any]]:
        target = course_code.upper().strip()
        req_type = req_type.upper().strip()
        return [
            row for row in self.requirements_groups
            if str(row.get('course_code', '')).upper() == target and str(row.get('req_type', '')).upper() == req_type
        ]

    def get_requirement_items(self, group_id: int) -> list[dict[str, Any]]:
        return [row for row in self.requirement_items if int(row.get('group_id', -1)) == group_id]

    def get_program_requirement_groups(self, program_code: str) -> list[dict[str, Any]]:
        target = program_code.upper().strip()
        return [
            row for row in self.program_requirement
            if str(row.get('program_code', '')).upper() == target
        ]

    def get_program_requirement_courses(self, group_id: int) -> list[dict[str, Any]]:
        return [row for row in self.program_requirement_courses if int(row.get('group_id', -1)) == group_id]

    def get_course_exclusions(self, course_code: str) -> list[dict[str, Any]]:
        target = course_code.upper().strip()
        return [
            row for row in self.course_exclusions
            if str(row.get('course_code', '')).upper() == target or str(row.get('excluded_course', '')).upper() == target
        ]

    def get_course_offerings(self, course_code: str) -> list[dict[str, Any]]:
        db_path = EXISTING_PROJECT_DB_PATH
        if not db_path.exists():
            return []

        target = course_code.upper().strip()
        results: list[dict[str, Any]] = []
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                if 'past_offerings' in tables:
                    cursor = conn.execute(
                        'SELECT * FROM past_offerings WHERE UPPER(course_code) = UPPER(?) ORDER BY year DESC',
                        (target,),
                    )
                    results = [dict(row) for row in cursor.fetchall()]
                elif 'offerings' in tables:
                    cursor = conn.execute(
                        'SELECT * FROM offerings WHERE UPPER(course_code) = UPPER(?) ORDER BY year DESC',
                        (target,),
                    )
                    results = [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
        return results

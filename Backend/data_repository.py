import sqlite3
import pandas as pd
from config import EXISTING_PROJECT_DB_PATH, DATA_DIR


class DataRepository:
    def __init__(self):
        # Save the path to the main project database
        self.db_path = EXISTING_PROJECT_DB_PATH

    def get_main_db_conn(self):
        # Open the main database
        conn = sqlite3.connect(self.db_path)

        # Let us use column names like row["course_code"]
        conn.row_factory = sqlite3.Row

        return conn

    def _clean_df(self, df):
        return df.astype(object).where(pd.notna(df), None)

    def _clean_record(self, record):
        cleaned = {}

        for key, value in record.items():
            cleaned[key] = None if pd.isna(value) else value

        return cleaned

    def get_courses_made_complete_by_exclusion(self, taken_course_code):
        # Find courses that should count as completed because the user took an exclusion
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT course_code, excluded_course, note
                FROM course_exclusions
                WHERE excluded_course = ?
            """, (taken_course_code,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        csv_path = DATA_DIR / "course_exclusions.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["excluded_course"] == taken_course_code][["course_code", "excluded_course", "note"]]
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_all_programs(self):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM programs
                ORDER BY program_name
            """).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to programs.csv
        csv_path = DATA_DIR / "programs.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        df = self._clean_df(df)
        df = df.sort_values("program_name")

        return df.to_dict(orient="records")

    def get_program_by_code(self, program_code):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            row = conn.execute("""
                SELECT *
                FROM programs
                WHERE program_code = ?
            """, (program_code,)).fetchone()
        except:
            row = None

        conn.close()

        if row:
            return row

        # Otherwise fall back to programs.csv
        csv_path = DATA_DIR / "programs.csv"

        if not csv_path.exists():
            return None

        df = pd.read_csv(csv_path)
        df = self._clean_df(df)
        matches = df[df["program_code"] == program_code]

        if matches.empty:
            return None

        return self._clean_record(matches.iloc[0].to_dict())

    def get_all_courses(self):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM courses
                ORDER BY course_code
            """).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to courses.csv
        csv_path = DATA_DIR / "courses.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        df = self._clean_df(df)
        df = df.sort_values("course_code")

        return df.to_dict(orient="records")

    def get_course_by_code(self, course_code):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            row = conn.execute("""
                SELECT *
                FROM courses
                WHERE course_code = ?
            """, (course_code,)).fetchone()
        except:
            row = None

        conn.close()

        if row:
            return row

        # Otherwise fall back to courses.csv
        csv_path = DATA_DIR / "courses.csv"

        if not csv_path.exists():
            return None

        df = pd.read_csv(csv_path)
        df = self._clean_df(df)
        matches = df[df["course_code"] == course_code]

        if matches.empty:
            return None

        return self._clean_record(matches.iloc[0].to_dict())

    def search_courses(self, keyword):
        # First try the main database
        conn = self.get_main_db_conn()
        like_value = "%" + keyword + "%"

        try:
            rows = conn.execute("""
                SELECT *
                FROM courses
                WHERE course_code LIKE ?
                   OR course_name LIKE ?
                ORDER BY course_code
            """, (like_value, like_value)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to courses.csv
        csv_path = DATA_DIR / "courses.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        df = self._clean_df(df)

        if "course_name" not in df.columns:
            return []

        keyword_lower = keyword.lower()

        filtered = df[
            df["course_code"].astype(str).str.lower().str.contains(keyword_lower, na=False) |
            df["course_name"].astype(str).str.lower().str.contains(keyword_lower, na=False)
        ].sort_values("course_code")

        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_past_offerings(self, course_code):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM past_offerings
                WHERE course_code = ?
                ORDER BY year DESC, semester
            """, (course_code,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to past_offerings.csv
        csv_path = DATA_DIR / "past_offerings.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["course_code"] == course_code].sort_values(
            by=["year", "semester"],
            ascending=[False, True]
        )

        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_program_requirement_groups(self, program_code):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM program_requirement
                WHERE program_code = ?
                ORDER BY group_id
            """, (program_code,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to program_requirement.csv
        csv_path = DATA_DIR / "program_requirement.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["program_code"] == program_code].sort_values("group_id")
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_program_requirement_courses(self, group_id):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM program_requirement_courses
                WHERE group_id = ?
                ORDER BY course_code
            """, (group_id,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to program_requirement_courses.csv
        csv_path = DATA_DIR / "program_requirement_courses.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["group_id"] == group_id].sort_values("course_code")
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_requirement_groups_for_course(self, course_code):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM requirements_groups
                WHERE course_code = ?
                ORDER BY group_id
            """, (course_code,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to requirements_groups.csv
        csv_path = DATA_DIR / "requirements_groups.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["course_code"] == course_code].sort_values("group_id")
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_requirement_items(self, group_id):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM requirement_items
                WHERE group_id = ?
                ORDER BY item_id
            """, (group_id,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to requirement_items.csv
        csv_path = DATA_DIR / "requirement_items.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["group_id"] == group_id].sort_values("item_id")
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_course_exclusions(self, course_code):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM course_exclusions
                WHERE course_code = ?
            """, (course_code,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to course_exclusions.csv
        csv_path = DATA_DIR / "course_exclusions.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["course_code"] == course_code]
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_enrolment_requirements(self, program_code):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM enrolment_requirements
                WHERE program_code = ?
                ORDER BY group_id
            """, (program_code,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to enrolment_requirements.csv
        csv_path = DATA_DIR / "enrolment_requirements.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["program_code"] == program_code].sort_values("group_id")
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")

    def get_all_departments(self):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM departments
                ORDER BY department_name
            """).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to departments.csv
        csv_path = DATA_DIR / "departments.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        df = self._clean_df(df)
        df = df.sort_values("department_name")

        return df.to_dict(orient="records")

    def get_department_prefixes(self, department_id):
        # First try the main database
        conn = self.get_main_db_conn()

        try:
            rows = conn.execute("""
                SELECT *
                FROM department_prefixes
                WHERE department_id = ?
                ORDER BY course_code_prefix
            """, (department_id,)).fetchall()
        except:
            rows = []

        conn.close()

        if rows:
            return rows

        # Otherwise fall back to department_prefixes.csv
        csv_path = DATA_DIR / "department_prefixes.csv"

        if not csv_path.exists():
            return []

        df = pd.read_csv(csv_path)
        filtered = df[df["department_id"] == department_id].sort_values("course_code_prefix")
        filtered = self._clean_df(filtered)

        return filtered.to_dict(orient="records")
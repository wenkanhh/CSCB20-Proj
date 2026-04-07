import sqlite3
from config import EXISTING_PROJECT_DB_PATH


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

    def get_all_programs(self):
        # Get all programs
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM programs
            ORDER BY program_name
        """).fetchall()

        conn.close()
        return rows

    def get_program_by_code(self, program_code):
        # Get one program by program code
        conn = self.get_main_db_conn()

        row = conn.execute("""
            SELECT *
            FROM programs
            WHERE program_code = ?
        """, (program_code,)).fetchone()

        conn.close()
        return row

    def get_all_courses(self):
        # Get all courses
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM courses
            ORDER BY course_code
        """).fetchall()

        conn.close()
        return rows

    def get_course_by_code(self, course_code):
        # Get one course by course code
        conn = self.get_main_db_conn()

        row = conn.execute("""
            SELECT *
            FROM courses
            WHERE course_code = ?
        """, (course_code,)).fetchone()

        conn.close()
        return row

    def search_courses(self, keyword):
        # Search courses by code or name
        conn = self.get_main_db_conn()

        like_value = "%" + keyword + "%"

        rows = conn.execute("""
            SELECT *
            FROM courses
            WHERE course_code LIKE ?
               OR course_name LIKE ?
            ORDER BY course_code
        """, (like_value, like_value)).fetchall()

        conn.close()
        return rows

    def get_past_offerings(self, course_code):
        # Get past offerings for a course
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM past_offerings
            WHERE course_code = ?
            ORDER BY year DESC, semester
        """, (course_code,)).fetchall()

        conn.close()
        return rows

    def get_program_requirement_groups(self, program_code):
        # Get all requirement blocks for one program
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM program_requirement
            WHERE program_code = ?
            ORDER BY group_id
        """, (program_code,)).fetchall()

        conn.close()
        return rows

    def get_program_requirement_courses(self, group_id):
        # Get all courses inside one program requirement block
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM program_requirement_courses
            WHERE group_id = ?
            ORDER BY course_code
        """, (group_id,)).fetchall()

        conn.close()
        return rows

    def get_requirement_groups_for_course(self, course_code):
        # Get prerequisite/corequisite groups for one course
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM requirements_groups
            WHERE course_code = ?
            ORDER BY group_id
        """, (course_code,)).fetchall()

        conn.close()
        return rows

    def get_requirement_items(self, group_id):
        # Get all items inside one requirement group
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM requirement_items
            WHERE group_id = ?
            ORDER BY item_id
        """, (group_id,)).fetchall()

        conn.close()
        return rows

    def get_course_exclusions(self, course_code):
        # Get all exclusions for one course
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM course_exclusions
            WHERE course_code = ?
        """, (course_code,)).fetchall()

        conn.close()
        return rows

    def get_enrolment_requirements(self, program_code):
        # Get enrolment requirements for one program
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM enrolment_requirements
            WHERE program_code = ?
            ORDER BY group_id
        """, (program_code,)).fetchall()

        conn.close()
        return rows

    def get_all_departments(self):
        # Get all departments
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM departments
            ORDER BY department_name
        """).fetchall()

        conn.close()
        return rows

    def get_department_prefixes(self, department_id):
        # Get all prefixes for one department
        conn = self.get_main_db_conn()

        rows = conn.execute("""
            SELECT *
            FROM department_prefixes
            WHERE department_id = ?
            ORDER BY course_code_prefix
        """, (department_id,)).fetchall()

        conn.close()
        return rows
import sqlite3
import csv
import os
from pathlib import Path

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / 'database.db'
SCHEMA_PATH = PROJECT_ROOT / 'sql' / 'schema.sql'
CSV_DIR = PROJECT_ROOT / 'data' / 'data_cleaned'

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_schema(conn):
    print('Running schema.sql...')

    # schema.sql contains mixed old/new table names in DROP statements,
    # so clear both variants to keep reruns idempotent.
    conn.executescript('''
        DROP TABLE IF EXISTS program_requirement_courses;
        DROP TABLE IF EXISTS program_requirements;
        DROP TABLE IF EXISTS prog_req_courses;
        DROP TABLE IF EXISTS prog_req_groups;
    ''')

    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    print('  Schema created successfully.')


def load_csv(filepath):
    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert empty strings and the literal word NULL to Python None
            cleaned = {}
            for key, value in row.items():
                if value == '' or value == 'NULL' or value is None:
                    cleaned[key] = None
                else:
                    cleaned[key] = value.strip() if isinstance(value, str) else value
            rows.append(cleaned)
    return rows


def to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def to_int_or_default(value, default):
    parsed = to_int(value)
    if parsed is None:
        return default
    return parsed


def to_float_or_default(value, default):
    parsed = to_float(value)
    if parsed is None:
        return default
    return parsed


def report(table, count):
    print(f'  Loaded {count:>6} rows into {table}')


def fk_exists(conn, table, column, value):
    if value is None:
        return False
    row = conn.execute(
        f'SELECT 1 FROM {table} WHERE {column} = ? LIMIT 1',
        (value,)
    ).fetchone()
    return row is not None


def safe_course_code(conn, course_code):
    if course_code is None:
        return None
    if fk_exists(conn, 'courses', 'course_code', course_code):
        return course_code
    return None


# ─────────────────────────────────────────
# LOADERS — one function per table
# ─────────────────────────────────────────

def load_departments(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'departments.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        cursor.execute('''
            INSERT OR IGNORE INTO departments
                (department_id, department_name, faculty, notes)
            VALUES (?, ?, ?, ?)
        ''', (
            to_int(r['department_id']),
            r['department_name'],
            r['faculty'],
            r['notes']
        ))
        count += cursor.rowcount
    report('departments', count)


def load_department_prefixes(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'department_prefixes.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        cursor.execute('''
            INSERT OR IGNORE INTO department_prefixes
                (prefix_id, department_id, course_code_prefix, prefix_description)
            VALUES (?, ?, ?, ?)
        ''', (
            to_int(r['prefix_id']),
            to_int(r['department_id']),
            r['course_code_prefix'],
            r['prefix_description']
        ))
        count += cursor.rowcount
    report('department_prefixes', count)


def load_courses(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'courses.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        cursor.execute('''
            INSERT OR IGNORE INTO courses (
                course_code, course_prefix, offering_code,
                course_name, course_details, credits,
                breadth_requirements, course_experience, note, course_link
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r['course_code'],
            r['course_code_prefix'],
            r['offering_code'],
            r['course_name'],
            r['course_details'],
            to_float(r['credits']),
            r['breadth_requirements'],
            r['course_experience'],
            r['note'],
            r['course_link']
        ))
        count += cursor.rowcount
    report('courses', count)


def load_programs(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'programs.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        cursor.execute('''
            INSERT OR IGNORE INTO programs (
                program_code, program_name, department_id, program_type,
                is_coop, is_limited_enrolment, total_credits,
                min_enrolment_cgpa, description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r['program_code'],
            r['program_name'],
            to_int(r['department_id']),
            r['program_type'],
            to_int(r['is_coop']),
            to_int(r['is_limited_enrolment']),
            to_float(r['total_credits']),
            to_float(r['min_enrolment_cgpa']),
            r['description']
        ))
        count += cursor.rowcount
    report('programs', count)


def load_requirement_groups(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'requirements_groups.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        cursor.execute('''
            INSERT OR IGNORE INTO requirement_groups
                (group_id, course_code, req_type, group_logic, path_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            to_int(r['group_id']),
            r['course_code'],
            r['req_type'],
            r['group_logic'],
            to_int(r['path_id'])
        ))
        count += cursor.rowcount
    report('requirement_groups', count)


def department_id_from_prefix(conn, prefix):
    if prefix is None:
        return None
    row = conn.execute(
        '''
        SELECT department_id
        FROM department_prefixes
        WHERE course_code_prefix = ?
        LIMIT 1
        ''',
        (prefix,)
    ).fetchone()
    if row is None:
        return None
    return row['department_id']


def load_requirement_items(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'requirement_items.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        cursor.execute('''
            INSERT OR IGNORE INTO requirement_items (
                item_id, group_id, item_type, course_code,
                min_credits, department_id, min_cgpa,
                program_code, year_standing, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            to_int(r['item_id']),
            to_int(r['group_id']),
            r['item_type'],
            safe_course_code(conn, r['course_code']),
            to_float(r['min_credits']),
            department_id_from_prefix(conn, r['department_prefix']),
            to_float(r['min_cgpa']),
            r['program_code'],
            to_int(r['year_standing']),
            r['notes']
        ))
        count += cursor.rowcount
    report('requirement_items', count)


def load_course_exclusions(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'course_exclusions.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        course_code = safe_course_code(conn, r['course_code'])
        excluded_course = safe_course_code(conn, r['excluded_course'])
        if course_code is None or excluded_course is None:
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO course_exclusions
                (exclusion_id, course_code, excluded_course, notes)
            VALUES (?, ?, ?, ?)
        ''', (
            to_int(r['exclusion_id']),
            course_code,
            excluded_course,
            r['note']
        ))
        count += cursor.rowcount
    report('course_exclusions', count)


def load_enrolment_requirements(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'enrolment_requirements.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        if not fk_exists(conn, 'programs', 'program_code', r['program_code']):
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO enrolment_requirements (
                group_id, program_code, req_category, item_type,
                course_code, min_credits, max_credits,
                department_id, min_cgpa, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            to_int(r['group_id']),
            r['program_code'],
            r['req_category'],
            r['item_type'],
            safe_course_code(conn, r['course_code']),
            to_float(r['min_credits']),
            to_float(r['max_credits']),
            to_int(r['department_id']),
            to_float(r['min_cgpa']),
            r['notes']
        ))
        count += cursor.rowcount
    report('enrolment_requirements', count)


def load_prog_req_groups(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'program_requirement.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        if not fk_exists(conn, 'programs', 'program_code', r['program_code']):
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO program_requirements (
                group_id, program_code, group_type,
                min_courses, min_credits, path_id,
                combined_group_id, combined_min_credits,
                category, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            to_int(r['group_id']),
            r['program_code'],
            r['group_type'],
            to_int_or_default(r['min_courses'], 0),
            to_float_or_default(r['min_credits'], 0.0),
            to_int(r['path_id']),
            to_int(r['combined_group_id']),
            to_float(r['combined_min_credits']),
            r['category'],
            r['notes']
        ))
        count += cursor.rowcount
    report('program_requirements', count)


def load_prog_req_courses(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'program_requirement_courses.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        if not fk_exists(conn, 'program_requirements', 'group_id', to_int(r['group_id'])):
            continue

        course_code = safe_course_code(conn, r['course_code'])
        if course_code is None:
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO program_requirement_courses
                (id, group_id, course_code, is_mandatory, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            to_int(r['id']),
            to_int(r['group_id']),
            course_code,
            to_int(r['is_mandatory']),
            r['notes']
        ))
        count += cursor.rowcount
    report('program_requirement_courses', count)


def load_past_offerings(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'past_offerings.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        course_code = safe_course_code(conn, r['course_code'])
        if course_code is None:
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO past_offerings (
                offering_id, course_code, semester, year,
                instructor, delivery, day_time, campus
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            to_int(r['offering_id']),
            course_code,
            r['semester'],
            to_int(r['year']),
            r['instructor'],
            r['delivery'],
            r['day_time'],
            r['campus']
        ))
        count += cursor.rowcount
    report('past_offerings', count)


def load_users(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'users.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        cursor.execute('''
            INSERT OR IGNORE INTO users
                (user_id, username, password, email, cgpa, year_standing)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            to_int(r['user_id']),
            r['username'],
            r['password'],
            r['email'],
            to_float(r['cgpa']),
            to_int_or_default(r.get('year_standing'), 1)
        ))
        count += cursor.rowcount
    report('users', count)


def load_user_programs(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'user_programs.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        if not fk_exists(conn, 'users', 'user_id', to_int(r['user_id'])):
            continue
        if not fk_exists(conn, 'programs', 'program_code', r['program_code']):
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO user_programs
                (id, user_id, program_code, status, start_year, end_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            to_int(r['id']),
            to_int(r['user_id']),
            r['program_code'],
            r['status'],
            to_int(r['start_year']),
            to_int(r['end_year'])
        ))
        count += cursor.rowcount
    report('user_programs', count)


def load_completed_courses(conn):
    rows = load_csv(os.path.join(CSV_DIR, 'completed_courses.csv'))
    cursor = conn.cursor()
    count = 0
    for r in rows:
        if not fk_exists(conn, 'users', 'user_id', to_int(r['user_id'])):
            continue

        course_code = safe_course_code(conn, r['course_code'])
        if course_code is None:
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO completed_courses (
                record_id, user_id, course_code, semester, year,
                grade, numeric_grade, status, credits_earned
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            to_int(r['record_id']),
            to_int(r['user_id']),
            course_code,
            r['semester'],
            to_int(r['year']),
            r['grade'],
            to_float(r['numeric_grade']),
            r['status'],
            to_float(r['credits_earned'])
        ))
        count += cursor.rowcount
    report('completed_courses', count)


# ─────────────────────────────────────────
# MAIN — runs everything in correct order
# ─────────────────────────────────────────

def main():
    print(f'\nConnecting to {DB_PATH}...')
    conn = connect()

    try:
        # Step 1 — build the empty tables
        run_schema(conn)

        print('\nLoading CSV files...')

        # Step 2 — load in insert order
        # (parent tables before child tables)
        load_departments(conn)
        load_department_prefixes(conn)
        load_courses(conn)
        load_programs(conn)
        load_requirement_groups(conn)
        load_requirement_items(conn)
        load_course_exclusions(conn)
        load_enrolment_requirements(conn)
        load_prog_req_groups(conn)
        load_prog_req_courses(conn)
        load_past_offerings(conn)
        load_users(conn)
        load_user_programs(conn)
        load_completed_courses(conn)

        # Step 3 — save everything
        conn.commit()
        print('\nAll data committed successfully.')

    except Exception as e:
        # If anything goes wrong, undo everything
        conn.rollback()
        print(f'\nERROR: {e}')
        print('All changes rolled back. Database is unchanged.')
        raise

    finally:
        conn.close()
        print(f'Connection closed.\n')


if __name__ == '__main__':
    main()
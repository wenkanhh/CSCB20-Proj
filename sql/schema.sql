PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS completed_courses;
DROP TABLE IF EXISTS user_programs;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS past_offerings;
DROP TABLE IF EXISTS program_requirement_courses;
DROP TABLE IF EXISTS program_requirements;
DROP TABLE IF EXISTS enrolment_requirements;
DROP TABLE IF EXISTS course_exclusions;
DROP TABLE IF EXISTS requirement_items;
DROP TABLE IF EXISTS requirement_groups;
DROP TABLE IF EXISTS program_requirements;
DROP TABLE IF EXISTS programs;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS department_prefixes;
DROP TABLE IF EXISTS departments;

PRAGMA foreign_keys = ON;

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL,
    faculty TEXT,
    notes TEXT
);

CREATE TABLE department_prefixes (
    prefix_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    course_code_prefix TEXT NOT NULL,
    prefix_description TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON DELETE CASCADE
);

CREATE TABLE courses (
    course_code TEXT PRIMARY KEY,
    course_prefix TEXT NOT NULL,
    offering_code TEXT NOT NULL,
    course_name TEXT NOT NULL,
    course_details TEXT,
    credits REAL NOT NULL DEFAULT 0.5,
    breadth_requirements TEXT,
    course_experience TEXT,
    note TEXT,
    course_link TEXT
);

CREATE TABLE programs (
    program_code TEXT PRIMARY KEY,
    program_name TEXT NOT NULL,
    department_id INTEGER NOT NULL,
    program_type TEXT NOT NULL CHECK(program_type IN ('Specialist', 'Major', 'Minor', 'Certificate', 'Combined', 'Double')),
    is_coop INTEGER NOT NULL DEFAULT 0,
    is_limited_enrolment INTEGER NOT NULL DEFAULT 0,
    total_credits REAL,
    min_enrolment_cgpa REAL,
    description TEXT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON DELETE CASCADE
);

CREATE TABLE requirement_groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    req_type TEXT NOT NULL CHECK(req_type IN ('PREREQ', 'COREQ')),
    group_logic TEXT NOT NULL CHECK(group_logic IN ('AND', 'OR')),
    path_id INTEGER,
    FOREIGN KEY (course_code) REFERENCES courses(course_code)
        ON DELETE CASCADE
);

CREATE TABLE requirement_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    item_type TEXT NOT NULL CHECK(item_type IN (
                          'COURSE', 'MIN_CREDITS_TOTAL', 'MIN_CREDITS_DEPT', 'MIN_CGPA',
                          'PROGRAM_ENROLLMENT', 'YEAR_STANDING', 'PERMISSION')),
    course_code TEXT,
    min_credits REAL,
    department_id INTEGER,
    min_cgpa REAL,
    program_code TEXT,
    year_standing INTEGER,
    notes TEXT,
    FOREIGN KEY (group_id) REFERENCES requirement_groups(group_id)
        ON DELETE CASCADE,
    FOREIGN KEY (course_code) REFERENCES courses(course_code),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE course_exclusions (
    exclusion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    excluded_course TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (course_code) REFERENCES courses(course_code)
        ON DELETE CASCADE,
    FOREIGN KEY (excluded_course) REFERENCES courses(course_code)
        ON DELETE CASCADE,
    UNIQUE(course_code, excluded_course)
);

CREATE TABLE enrolment_requirements (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_code TEXT NOT NULL,
    req_category TEXT NOT NULL DEFAULT 'ENROLMENT',
    item_type TEXT NOT NULL CHECK(item_type IN ('COURSE', 'MIN_CREDITS_TOTAL', 'MIN_CREDITS_DEPT','MIN_CGPA')),
    course_code TEXT,
    min_credits REAL,
    max_credits REAL,
    department_id INTEGER,
    min_cgpa REAL,
    notes TEXT,
    FOREIGN KEY (program_code) REFERENCES programs(program_code)
        ON DELETE CASCADE,
    FOREIGN KEY (course_code)  REFERENCES courses(course_code)
);

CREATE TABLE program_requirements (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_code TEXT NOT NULL,
    group_type TEXT NOT NULL CHECK(group_type IN ('ALL','PICK', 'CREDIT_LEVEL', 'OPTIONAL')),
    min_courses INTEGER DEFAULT 0,
    min_credits REAL DEFAULT 0.0,
    path_id INTEGER,
    combined_group_id INTEGER,
    combined_min_credits REAL,
    category TEXT NOT NULL CHECK(category IN ('Required', 'Elective', 'Graduation Requirement', 'Co-op', 'Optional')),
    notes TEXT,
    FOREIGN KEY (program_code) REFERENCES programs(program_code)
        ON DELETE CASCADE
);

CREATE TABLE program_requirement_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    course_code TEXT NOT NULL,
    is_mandatory INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    FOREIGN KEY (group_id) REFERENCES program_requirements(group_id)
        ON DELETE CASCADE,
    FOREIGN KEY (course_code) REFERENCES courses(course_code),
    UNIQUE(group_id, course_code)
);

CREATE TABLE past_offerings (
    offering_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    semester TEXT NOT NULL CHECK(semester IN ('Fall', 'Winter', 'Summer')),
    year INTEGER NOT NULL,
    instructor TEXT,
    delivery TEXT CHECK(delivery IN ('In-person', 'Online', 'Hybrid')),
    day_time TEXT,
    campus TEXT,
    FOREIGN KEY (course_code) REFERENCES courses(course_code)
        ON DELETE CASCADE
);

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    cgpa REAL NOT NULL DEFAULT 0.0,
    year_standing INTEGER NOT NULL DEFAULT 1
    );

CREATE TABLE user_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    program_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
    CHECK(status IN ('ACTIVE', 'COMPLETED', 'WITHDRAWN')),
    start_year INTEGER,
    end_year INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (program_code) REFERENCES programs(program_code),
    UNIQUE(user_id, program_code)
);

CREATE TABLE completed_courses (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_code TEXT NOT NULL,
    semester TEXT CHECK(semester IN ('Fall', 'Winter', 'Summer')),
    year INTEGER,
    grade TEXT,
    numeric_grade REAL,
    status TEXT NOT NULL DEFAULT 'COMPLETED'
    CHECK(status IN ('COMPLETED', 'IN_PROGRESS', 'FAILED','TRANSFER')),
    credits_earned REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (course_code) REFERENCES courses(course_code),
    UNIQUE(user_id, course_code, semester, year)
);
# Course Planner Application — Technical Report

**Date:** April 13, 2026  
**Project:** CSCB20 Implementation (University of Toronto)

---

## 1. Project Overview

### What Problem Are You Solving?

This application addresses the course planning challenge for university students: discovering which courses they are eligible to take next, understanding program requirements, tracking completed courses, and visualizing progress toward degree completion. The underlying data problem is managing a complex web of prerequisites, corequisites, course exclusions, program requirements, and student academic profiles.

### What Is the Core Idea of Your Application?

The core idea is a **course recommendation and degree audit system** that:
- Stores a comprehensive catalog of 2,167+ courses, 240+ academic programs, and complex prerequisite/corequisite/exclusion graphs
- Allows students to register, log in, and save their academic progress
- Shows which courses in a given program the student has completed vs. still needs
- Provides a foundation for future eligibility checking and smart course recommendations based on prerequisites and CGPA/year standing

The system cleanly separates **institutional reference data** (courses, programs, requirements) from **user data** (accounts, saved programs, completed courses) using two independent SQLite databases.

---

## 2. System Description

### What Does Your Application Do?

**Authentication & Account Management:**
- User registration with validation (username, password, email, CGPA, year standing)
- Secure login/logout with session cookies and password hashing (werkzeug.security)
- Profile page showing account details, saved programs, and completed courses

**Course Discovery:**
- Browse all 2,167 courses in the catalog with search by code or name
- View detailed course pages with past semester offerings (semester, year, instructor, delivery mode)
- Display exclusions and prerequisite/corequisite groups for each course

**Program Management:**
- Dashboard for saving up to multiple academic programs
- Track program enrollment status (ACTIVE, COMPLETED, WITHDRAWN)
- View program requirements grouped into logical blocks
- Mark progress toward each requirement block (completed vs. remaining courses)

**Institutional Data:**
- 17 departments with course code prefixes
- Course metadata: credits, breadth requirements, restrictions, link to official description
- Program detail: type (Specialist/Major/Minor/Certificate), co-op status, limited enrollment, total credits required
- Prerequisite/corequisite structures with AND/OR logic and alternative paths
- Course exclusion pairs

### How Does a User Interact With It?

1. **First Visit:** User navigates to `/` (redirects to `/login`)
2. **Registration:** User creates account via `/register` (GET form, POST submission)
3. **Login:** User authenticates via `/login`
4. **Dashboard:** User saves programs via form on `/dashboard`
5. **Course Browsing:** User searches at `/courses?keyword=...` and views `/course/<code>`
6. **Program Planning:** User clicks "Open Planner" from saved program, views `/planner?program_code=...`
7. **Profile:** User reviews account and course history at `/profile`

All interactions flow through server-rendered Jinja templates + standard HTML form submissions. There is no rich client-side state management; each page is an independent request/response cycle.

### Are There Any Special or Notable Features?

**Strength: Data Model Completeness**
- The schema captures 7 tables for prerequisite/corequisite logic (requirement_groups, requirement_items with AND/OR logic and path-based alternatives)
- Tracks program requirements separately with group types (ALL, PICK, CREDIT_LEVEL, OPTIONAL), combined credit pools, and categorical labeling (Required, Elective, etc.)
- Exclusion pair tracking prevents students from registering for conflicting courses

**Limitation: No Live Eligibility Checking**
- The app displays completed vs. incomplete course lists but does not check whether a student actually satisfies prerequisites
- This would require evaluating complex AND/OR trees and handling path-based alternatives
- Foundation is in place; logic is not yet implemented

**Limitation: Session-Only State**
- Flask session cookie stores only `user_id` and `username`
- No CSRF tokens, CORS headers, or other security hardening for API use
- Designed for same-origin browser clients, not mobile or third-party integrations

---

## 3. Technical Overview

### 3.1 Frontend Responsibilities

**Rendering & Navigation**
- Jinja template engine renders pages server-side
- [templates/base.html](templates/base.html) provides shared header/nav/footer layout
- Each page template extends base.html and renders specific content (forms, lists, tables)
- Navbar conditionally shows login/register or dashboard/courses/profile/logout based on session state

**Form Submission**
- User input collected via HTML `<form method="POST">` elements
- Flash messages display validation errors and success feedback from Flask
- No client-side form validation; all validation happens server-side

**Styling & UX**
- [static/styles.css](static/styles.css) implements a dark theme (slate background, cyan accent color)
- Responsive grid layout with CSS Grid and Flexbox
- Card-based UI for sections: hero-card (title + description), table-card (forms/tables), list-card (items), audit-card (nested structures)
- Badge components for status indicators (Completed/Not Completed, ACTIVE/WITHDRAWN)
- Alert boxes for info, success, error, warning messages

**Client-Side JavaScript (Support Only)**
- [static/api.js](static/api.js): Provides fetch wrapper and localStorage-based API base URL switching; exports `CourseAPI` and `PlannerAPI` objects for future extensibility
- [static/common.js](static/common.js): Provides DOM helpers (`$()` selector, `getQueryParam()` for URL params), HTML escaping, alert rendering, JSON pretty-printing
- **Currently Unused:** These helpers are loaded but not actively called by any page. They exist to support future SPA-style features or dynamic interactions.

**Pages:**
- `login.html` — username/password login form
- `register.html` — registration form with CGPA and year standing
- `dashboard.html` — program selection dropdown + saved program list with planner links
- `profile.html` — account info (username, email, CGPA, year standing), saved programs, completed courses table
- `courses.html` — course search form + paginated course list with search highlighting
- `course-details.html` — individual course view with past offerings, exclusions, prerequisites/corequisites
- `recommendations.html` — program plan view with KPI cards (total/completed/remaining courses) + grouped requirement blocks

### 3.2 Backend/Server-Side Logic

**Framework & Structure**
- Flask 3.0.3 for HTTP routing and template rendering
- No ORM; raw SQLite3 with row factory for dictionary-like access
- Four route modules imported and initialized in [Backend/app.py](Backend/app.py)

**Route Modules:**

1. **[Backend/auth_routes.py](Backend/auth_routes.py)** — Authentication
   - `GET/POST /register` — user account creation with validation
   - `GET/POST /login` — session-based login with password hash verification
   - `GET /logout` — session destruction
   - Uses werkzeug.security.generate_password_hash / check_password_hash

2. **[Backend/user_routes.py](Backend/user_routes.py)** — User Pages
   - `GET /dashboard` — list saved programs, form to add new program
   - `POST /save-program` — insert user_programs row, validate program code exists
   - `GET /remove-program/<id>` — delete user_programs row
   - `GET /profile` — display user account, programs, completed courses table
   - `POST /save-completed-courses` — replace completed_courses rows for user

3. **[Backend/course_routes.py](Backend/course_routes.py)** — Course Catalog
   - `GET /courses` — list all courses or search by keyword (code/name)
   - `GET /course/<code>` — course detail page with offerings, exclusions, requirements
   - `GET /api/course/<code>` — JSON endpoint for course details
   - `GET /search-courses` — redirect wrapper for search

4. **[Backend/recommendation_routes.py](Backend/recommendation_routes.py)** — Program Planning
   - `GET /planner?program_code=...` — render program plan (HTML page)
   - `GET /api/planner?program_code=...` — return plan as JSON (requires login)
   - Calls planner_service.get_program_plan()

**Service Layer:**
- [Backend/planner_service.py](Backend/planner_service.py) — Domain Logic
  - `get_completed_course_codes(user_id)` — fetch completed courses from runtime DB
  - `get_program_plan(user_id, program_code)` — merge program structure with user progress
  - `get_course_details(course_code)` — assemble course info with offerings, exclusions, requirements
  - Returns structured dicts (not ORM objects) ready for template rendering

**Data Access:**
- [Backend/data_repository.py](Backend/data_repository.py) — Read-Only Catalog Access
  - Methods: `get_all_courses()`, `get_course_by_code()`, `search_courses(keyword)`, `get_program_by_code()`, `get_all_programs()`, `get_past_offerings()`, `get_program_requirement_groups()`, `get_program_requirement_courses()`, `get_requirement_groups_for_course()`, `get_requirement_items()`, `get_course_exclusions()`, `get_enrolment_requirements()`, `get_all_departments()`, `get_department_prefixes()`
  - Opens connection to catalog database on each read (no connection pooling)

**Database Connections:**
- [Backend/runtime_db.py](Backend/runtime_db.py) — User Data
  - `init_runtime_db()` — create user/user_programs/completed_courses tables if missing
  - `get_conn()` — return fresh SQLite connection with row factory

**Validation & Config:**
- [Backend/validation.py](Backend/validation.py) — Input Validation
  - Email format, username length (3+), password length (6+), CGPA (0.0–4.0), year standing (1–4)
  - Course code format (6 or 8 characters: MGTA01 or ACMB10H3)
  - Program code format (6+ alphanumeric)
  - Semester/delivery type validation
- [Backend/config.py](Backend/config.py) — Path Configuration
  - Resolves data directories and SQL folder paths
  - Defines `RUNTIME_DB_PATH` (sql/backend_runtime.db)
  - Defines `EXISTING_PROJECT_DB_PATH` (sql/database.db) for catalog

**Session & Security:**
- Secret key: hardcoded in app.py as "my_secret_key" (should use environment variable)
- Session storage: browser-side encrypted cookie
- Password hashing: PBKDF2 via werkzeug.security
- CSRF protection: None (forms are server-same-origin only, acceptable for traditional Flask sites)

### 3.3 Database Usage

**Architecture: Dual-Database Design**

Two independent SQLite databases avoid mixing reference data and transactional user data, making the catalog immutable and user data independently backupable.

**Database 1: Catalog Source/Staging** (`database.db` in project root)
- Primary location where data is generated and tested
- Created/populated by [scripts/csv_to_sql.py](scripts/csv_to_sql.py) from [data/data_cleaned/](data/data_cleaned/) CSV files
- Use this to update, regenerate, or validate course/program data before deploying changes
- Current row counts:
  - `courses`: 2,167
  - `programs`: 240
  - `departments`: 17
  - `department_prefixes`: 62
  - `requirement_groups`: 2,658 (prerequisites/corequisites)
  - `requirement_items`: 8,935 (individual conditions in those groups)
  - `course_exclusions`: 691
  - `enrolment_requirements`: 932
  - `program_requirements`: 807 (course groupings within programs)
  - `program_requirement_courses`: 4,950 (individual courses per group)
  - `past_offerings`: 2,427 (historical semester offerings)

**Database 2: Catalog Deployment** (`sql/database.db`)
- The synchronized copy that the Flask app reads from
- Mirrors the staged data from `database.db` (root)
- Updated whenever you copy/sync from the staging database
- Contains all 2,167 courses, 240 programs, and prerequisite/requirement data
- Read by Flask app via [Backend/config.py](Backend/config.py) `EXISTING_PROJECT_DB_PATH` setting

**Database 3: Runtime/User Database** (`sql/backend_runtime.db`)
- Created on first run by `init_runtime_db()`
- Stores user accounts, program enrollments, completed course records
- Schema has only 3 tables:
  - `users` (user_id, username, password hash, email, cgpa, year_standing)
  - `user_programs` (id, user_id, program_code, status, start_year, end_year)
  - `completed_courses` (record_id, user_id, course_code, semester, year, grade, numeric_grade, status, credits_earned)
- Currently empty (no test users in repo)

**Schema Design Highlights:**

*Prerequisite/Corequisite System:*
```
requirement_groups(group_id, course_code, req_type, group_logic, path_id)
  ├─ req_type: PREREQ or COREQ
  ├─ group_logic: AND (all items must pass) or OR (any one item passes)
  └─ path_id: NULL or integer (groups sharing same path_id are alternatives)

requirement_items(item_id, group_id, item_type, ...)
  ├─ item_type in: COURSE, MIN_CREDITS_TOTAL, MIN_CREDITS_DEPT, 
  │                MIN_CGPA, PROGRAM_ENROLLMENT, YEAR_STANDING, PERMISSION
  └─ Each row is one condition (e.g., "need MGTA01 AND MGTA02" = 2 items in same AND group)
```

*Program Requirements:*
```
program_requirements(group_id, program_code, group_type, ...)
  ├─ group_type in: ALL (every course required), PICK (student chooses N or X credits),
  │                 CREDIT_LEVEL (minimum credits at certain level), OPTIONAL
  ├─ category: Required, Elective, Graduation Requirement, Co-op, Optional
  ├─ combined_group_id: pools credits from multiple blocks toward shared total
  └─ path_id: alternative paths (student completes ONE path's blocks)

program_requirement_courses(id, group_id, course_code, is_mandatory, notes)
  └─ Lists individual courses in each requirement block
```

**Data Flow:**
1. CSV source files in [data/data_cleaned/](data/data_cleaned/) (13 files detailing courses, programs, prerequisites, offerings, etc.)
2. [scripts/csv_to_sql.py](scripts/csv_to_sql.py) reads CSVs, applies foreign key lookups, writes to `database.db`
3. Flask app reads from `sql/database.db` (expects catalog there)
4. User edits go to `sql/backend_runtime.db`
5. PlannerService joins them: fetches course/program metadata from catalog, user's completed courses from runtime DB, renders merged plan

**Critical Issue: Database Path Mismatch**
- Importer writes to: `database.db` (project root)
- Flask reads from: `sql/database.db` (empty)
- Result: App starts but shows no courses; planner queries fail silently

---

## 4. How to Run the Project

### Prerequisites
- Python 3.11.5 (or similar 3.10+)
- pip (Python package manager)
- Git (to clone repo, optional)

### Setup Steps

1. **Clone or Extract Repository**
   ```bash
   cd ...............
   ```

2. **Create Virtual Environment** (if not already present)
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r Backend/requirements.txt
   ```
   This installs Flask 3.0.3 and pandas.

4. **Sync Catalog Database** (Already Done)
   
   The populated catalog has been copied to `sql/database.db` for app use:
   ```bash
   copy database.db sql\database.db
   ```
   
   **Workflow for future updates:**
   - Update data in root `database.db` (via CSV import or manual changes)
   - Test/validate the updated data
   - Copy to `sql/database.db` when ready to deploy to app
   - Restart Flask app to reload the updated database

5. **Run Flask App**
   ```bash
   cd Backend
   python app.py
   ```

7. **Open Browser**
   Navigate to `http://127.0.0.1:5000/`
   - Redirects to `/login` if not authenticated
   - Create test account (any username/password/CGPA/year)
   - Access dashboard, save a program, explore planning

---

## 5. What Works and What Does Not

### What Works

**Core Functionality Implemented:**
- User registration with validation (username, password, email, CGPA, year standing)
- Secure login/logout with session cookies and password hashing
- Dashboard page with form to add program, list of saved programs
- Profile page showing account details, enrolled programs, completed course table
- Course catalog browse/search (once database is fixed)
- Course detail page with offerings, exclusions, requirement groups
- Planner page showing program structure and completion status (once database is fixed)
- Form validation and flash message feedback
- CSS styling and responsive layout (dark theme, grid, cards, badges)
- Server-side request handling and Jinja templating
- Session-based authentication with "login_required" pattern

**Code Quality:**
- Clean separation of concerns: routes, service, repository, validation
- Input validation before database operations
- Password hashing (werkzeug.security)
- Foreign key relationships in schema
- Comprehensive data model (courses, programs, prerequisites, offerings, requirements)

### What Does Not Work / Is Broken

**Missing/Incomplete Features:**
1. **Prerequisite Eligibility Checking** — App displays course lists but does NOT verify if student meets prerequisites
   - Would require evaluating complex AND/OR requirement trees
   - Would need CGPA and year standing checks
   - Foundation exists (schema, data structure) but logic not implemented

2. **Course Recommendation Engine** — No smart suggestions beyond "here's what you need"
   - Mentioned in README but never implemented
   - Could recommend courses based on prerequisites met, typical offerings, degree progress

3. **API Integration** — JavaScript API helpers (`CourseAPI`, `PlannerAPI`) are defined but never used
   - Rest of app uses traditional form submissions and server-side rendering
   - CORS headers missing (not configured for mobile/third-party clients)
   - Would require frontend refactoring to adopt

4. **Security Improvements Missing**
   - Hardcoded Flask secret key (should use environment variable)
   - No CSRF tokens (acceptable for same-origin forms, risky for API)
   - No rate limiting on login/register
   - No account lockout after failed login attempts
   - Passwords never expire
   - No SQL injection defense (app uses parameterized queries but no ORM abstraction)

5. **Performance Optimizations Missing**
   - New connection opened for each database read (no connection pooling)
   - No caching of frequently accessed data (programs, courses)
   - Templates render full course lists without pagination
   - Large tables (past offerings, requirement items) not indexed

6. **Data Quality Issues**
   - CSV import script references `course_code_prefix` column but populates as `course_prefix` elsewhere
   - Some CSV columns documented but not used in schema (e.g., breadth_requirements not queried)
   - Null handling inconsistent (empty strings vs None)

7. **Error Handling**
   - Silent failures if course/program not found (returns None, template renders empty)
   - No 404 pages (user sees blank page instead of clear "course not found")
   - Database connection errors not caught or reported

### ⚠️ Partially Working

- **API Endpoints** — `/api/course/<code>` and `/api/planner` were written but are never called by frontend; frontend uses server-rendered pages instead
- **Completed Courses Interface** — Form on profile page exists but allows bulk replace only; no fine-grained add/remove per course
- **Requirement Evaluation** — Requirement groups loaded and displayed, but AND/OR logic and path alternatives not evaluated (just shown to user)


## 7. External Libraries, Frameworks, and Tools

### Direct Dependencies (in requirements.txt)

| Library | Version | Purpose | Where Used |
|---------|---------|---------|-----------|
| Flask | 3.0.3 | Web framework, routing, templating, session management | [Backend/app.py](Backend/app.py), all route modules |
| pandas | 2.2.3 | Data manipulation (likely for CSV → DataFrame processing) | Not directly used in app.py; may be legacy (csv_to_sql.py uses built-in csv module) |

### Python Standard Library 

| Module | Purpose |
|--------|---------|
| `sqlite3` | SQLite database connections and queries |
| `pathlib.Path` | Cross-platform file path handling |
| `os` | Environment variable reading |
| `csv` | CSV file parsing in [scripts/csv_to_sql.py](scripts/csv_to_sql.py) |

### Werkzeug (Bundled with Flask)

| Component | Purpose |
|-----------|---------|
| `werkzeug.security.generate_password_hash` | Hash user passwords before storage |
| `werkzeug.security.check_password_hash` | Verify password on login |

### Frontend Dependencies 

| Resource | Type | Purpose |
|----------|------|---------|
| Jinja2 (Flask built-in) | Template engine | Server-side HTML rendering |
| CSS (handwritten) | Styling | Dark theme, responsive layout, component styling |
| JavaScript (handwritten) | Helpers | Fetch wrapper, DOM utilities, unused SPA hooks |
| HTML5 | Markup | Standard HTML form, table, nav elements |

### Development/Data Tools 

| Tool | Purpose |
|------|---------|
| Python venv | Virtual environment for dependency isolation |
| [scripts/csv_to_sql.py](scripts/csv_to_sql.py) | One-time data import utility (not deployed with app) |
| SQLite CLI / DB Browser | For manual database inspection (used during analysis, not app dependency) |


### Why These Choices?

- **Flask over Django/FastAPI:** Lightweight, suitable for course project; less boilerplate than Django; easier learning curve than async frameworks
- **SQLite over PostgreSQL/MySQL:** No deployment server required; single file database; sufficient for single-user course planner
- **Jinja templates over React/Vue:** Server-side rendering is simpler for traditional CRUD pages; no build step required
- **CSS-in-file over Tailwind/Bootstrap:** Demonstrates CSS knowledge; smaller footprint; custom design system (dark theme + accent colors)
- **No ORM:** Raw SQL queries keep framework count low; teaches SQL; adequate for this schema complexity

---

## 8. References & Attribution

### Original Work
All custom code (routes, templates, styling, database schema design, CSV import logic, service layer) is created from scratch for this assignment. No boilerplate generators or scaffold tools were used (e.g., no `flask-scaffold` or Django scaffolding).

### Inspired By / Informed By
- University of Toronto Course Catalog (original course data source, documented in [data/data_cleaned/README.md](data/data_cleaned/README.md))
- Flask documentation (https://flask.palletsprojects.com)
- Python sqlite3 documentation (https://docs.python.org/3/library/sqlite3.html)
- CSCB20 assignment specification (implied)

### Data Sources
- [data/data_cleaned/README.md](data/data_cleaned/README.md) — 13 CSV files containing course, program, requirement, and offering data extracted from UofT Course Timetable and Calendar
- The cleaned dataset is the intellectual output of a data engineering task (course scraping, parsing, normalization) separate from app development

### Documentation
- [sql/schema.sql](sql/schema.sql) — SQL schema definitions (original design for this project)
- [data/data_cleaned/README.md](data/data_cleaned/README.md) — Field-level documentation of CSV structure and linkage
- [Backend/README.md](Backend/README.md) — API and setup documentation (part of project, not external reference)

### Tools / Frameworks Listed
- **Flask 3.0.3** — Pallets (https://flask.palletsprojects.com)
- **Werkzeug** — Pallets (included with Flask, https://werkzeug.palletsprojects.com)
- **pandas 2.2.3** — pandas-dev (https://pandas.pydata.org) — included in requirements but not actively used in codebase
- **Python 3.11.5** — Python Software Foundation (https://www.python.org)
- **SQLite** — SQLite Consortium (https://www.sqlite.org) — pre-installed on Windows

### No External Attribution Needed For
- HTML5, CSS3, JavaScript (web standards, not third-party libraries)
- Algorithm/logic choices (all custom)
- Database design (custom schema, not based on published model)

---

## 9. Deployment & Scaling Notes

**Current Limitations (if deployed):**
- Single-threaded Flask development server (use Gunicorn/uWSGI for production)
- SQLite limits concurrency (fine for single user, problematic for multiple simultaneous users)
- No load balancing, caching, or CDN (suitable for small institution or demo, not campus-wide)
- Session cookie stored in browser (works for one server instance; would need Redis/Memcached for multi-server)



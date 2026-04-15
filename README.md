# UTSC Course Planner Application
## CSCB20 Web Application Project Report
University of Toronto Scarborough - April 14th, 2026  
- Anh Van Quynh Nguyen (1010280580)  
- Tien Khai Nguyen (1010041884)  
- Firdavs Ortikov (1010706568)

## 1. Project Overview  
### 1.1 Problem Statement  
University of Toronto Scarborough students face a recurring challenge when planning their academic journey: determining which courses they are eligible to take, understanding program requirements, tracking completed courses, and visualizing progress toward degree completion. Complicated courses with prerequisites, corequisites, exclusions, and varying program structures across hundreds of academic programs make navigating through the school year complex.

The current official tools provided by the University only provide course details, and students need to go back and forth to manually check for prerequisites, corequisites, and cross-check the program’s requirements. Information about past course offerings is sometimes missing, thus requiring students to manually read the archived courses' PDFs.

### 1.2 Core Idea  
This application is a course recommendation and degree audit system built for students at the University of Toronto Scarborough for reference purposes. The core functionality includes:
- A comprehensive catalog of 2,000+ courses and 240+ academic programs  
- Student registration, login, and academic progress tracking  
- Degree audit views showing completed vs. remaining requirements per program  
- Complex prerequisite, corequisite, and exclusion data model  
- Clean separation between institutional reference data and live user data using two independent SQLite databases

## 2. System Description  
Our application is designed to be used as a complementary reference resource along with the University’s Degree Planner. It has the following features:

### 2.1 Application Features

#### Authentication & Account Management
- User registration with full validation: username, password, email, CGPA, and year standing  
- Secure login and logout with session cookies and password hashing via Werkzeug.security  
- Profile page displaying account details, enrolled programs, and completed courses  
- Completion progress is displayed, along with the current user’s CGPA  

#### Course Discovery
- Browse all 2,000+ courses with keyword-based search by course code or name  
- Individual course detail pages showing past semester offerings, instructor, and delivery mode  
- Display of exclusions and prerequisite/corequisite groups for each course  

#### Program Planning
- Dashboard for saving and managing multiple academic programs  
- Track enrollment status per program (ACTIVE, COMPLETED, WITHDRAWN)  
- View program requirements organized into logical blocks  
- Visual progress tracking showing completed vs. remaining courses per block  

### 2.2 User Workflow
- Step 1 User navigates to / which redirects to /login  
- Step 2 User creates an account via the /register form if not yet registered  
- Step 3 User logs in and reaches the /dashboard  
- Step 4 User saves academic programs via the dashboard form  
- Step 5 User browses courses at /courses?keyword=... and views /course/<code>  
- Step 6 User opens the planner at /planner?program_code=... to track degree progress  
- Step 7 User reviews full history and details at /profile  
- Step 8 User logged out through /logout and got redirected to /login  

### 2.3 Notable Features and Limitations

#### Strengths
- Rich schema capturing prerequisite/corequisite logic with AND/OR group structures and path-based alternatives  
- Program requirements modeled with group types (ALL, PICK, CREDIT_LEVEL, OPTIONAL) and combined credit pools  
- Clean dual-database architecture separating reference data from transactional user data  

#### Current Limitations
- No live prerequisite eligibility checking  
- No “Forgot your password” function  
- No recommendation engine  
- JavaScript API helpers defined but not wired to frontend  
- No rate limiting, two-factor authentication, or account lockout  

## 3. Technical Overview  
### 3.1 Frontend
The frontend is built with server-side Jinja2 templates rendered by Flask. A shared base.html provides the header, navigation, and footer layout. All pages extend this base.

Forms use standard HTML POST submissions with Flask flash messages. No client-side validation.

Styling uses a dark theme with CSS Grid and Flexbox.

Pages:
- login.html  
- register.html  
- dashboard.html  
- profile.html  
- courses.html  
- course-details.html  
- recommendations.html  

### 3.2 Backend
Backend uses Flask 3.0.3 with raw SQLite3.

Route Modules:
- auth_routes.py  
- user_routes.py  
- course_routes.py  
- recommendation_routes.py  

Service & Data Layers:
- planner_service.py  
- data_repository.py  
- runtime_db.py  
- validation.py  
- config.py  

### 3.3 Database Integration

#### Database 1: University static database (sql/database.db)
Populated from 13 CSV files. Row counts:
- courses: 2,167  
- programs: 240  
- departments: 17  
- department_prefixes: 62  
- requirement_groups: 2,658  
- requirement_items: 8,935  
- course_exclusions: 691  
- enrolment_requirements: 932  
- program_requirements: 807  
- program_requirement_courses: 4,950  
- past_offerings: 2,427  

#### Database 2: User Data (sql/backend_runtime.db)
Tables:
- users  
- user_programs  
- completed_courses  

Schema uses group_logic (AND/OR), path_id, group_type (ALL, PICK, CREDIT_LEVEL, OPTIONAL), combined_group_id.

## 4. How to Run the Project  
Prerequisites:
- Python 3.10+  
- pip  

Setup:
- Activate venv  
- Install dependencies  
- Sync catalog database  
- Run Flask  
- Open browser at http://127.0.0.1  

## 5. What Works and What Does Not  
### 5.1 Working Features
- Registration  
- Login/logout  
- Dashboard  
- Profile  
- Course catalog  
- Course details  
- Program planner  
- Flash messages  
- Dark theme UI  
- Clean code structure  

### 5.2 Known Issues
- No prerequisite checking  
- No recommendation engine  
- No real-time UTSC sync  
- Cannot verify course offering term  
- JS helpers unused  
- No CSRF, rate limiting, lockout  
- Hardcoded secret key  
- No 404 pages  
- No connection pooling  

## 6. Division of Work  
Phases:
1. Planning & Setup  
2. Data Pipeline  
3. Database & SQL  
4. Backend Development  
5. Frontend Development  
6. Testing & Finalization  

### 6.1 Planning & Setup
- All: project idea, naming conventions  
- Anh: schema design  
- Anh & Khai: folder structure  
- Anh: GitHub repo  
- Khai & Firdavs: repo access  
- Anh: PDF collection  

### 6.2 Data Pipeline
- Anh: PDF analysis, text extraction  
- Anh: clean_data.py, verify_output.py, documentation  
- Anh: CSV generation  
- Anh: CSV validation, csv_to_sql.py  

### 6.3 Database & SQL
- Anh: table creation, queries  
- Khai: eligibility logic, remaining courses  
- Khai & Firdavs: search  
- All: degree progress testing  

### 6.4 Backend Development
- Khai & Firdavs: Flask setup  
- Khai: authentication, profile, course browsing, recommendation system, validation  

### 6.5 Frontend Development
- Firdavs: layout, profile page, CSS, JS  
- Khai: auth pages, course pages, recommendation UI  
- Khai: integration  

### 6.6 Testing & Finalization
All: testing, debugging, cleanup  

## 7. External Libraries, Frameworks, and Tools  
### 7.1 Direct Dependencies
- Flask 3.0.3  
- Werkzeug  
- pandas  
- sqlite3  
- pathlib / os  
- csv  

### 7.2 Frontend
- Jinja2  
- CSS  
- JavaScript  
- HTML5  

## 8. References and Attribution

### 8.1 Original Work
All custom code (routes, templates, CSS, database schema, and service layer) was written from scratch for this assignment.

### 8.2 AI Usage
The use of generative AI (ChatGPT, Claude) is applied in the following tasks:
- Idea generating
- Project planning
- Database brainstorming
- Data crawling and parsing

### 8.3 References
- (n.d.). *Welcome to Flask — Flask Documentation (3.1.x).* Retrieved April 14, 2026, from https://flask.palletsprojects.com
- *Built-in Functions — Python 3.14.4 documentation.* (n.d.). Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/functions.html
- *Built-in Types — Python 3.14.4 documentation.* (n.d.). Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str
- *csv — CSV File Reading and Writing — Python 3.14.4 documentation.* (n.d.). Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/csv.html
- Lemburg, M. (n.d.). *sqlite3 — DB-API 2.0 interface for SQLite databases.* Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/sqlite3.html
- Lemburg, M. (n.d.). *sqlite3 — DB-API 2.0 interface for SQLite databases.* Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/sqlite3.html
- *os.path — Common pathname manipulations — Python 3.14.4 documentation.* (n.d.). Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/os.path.html
- *pandas.read_csv — pandas 3.0.2 documentation.* (n.d.). Pandas. Retrieved April 14, 2026, from https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
- *pathlib — Object-oriented filesystem paths — Python 3.14.4 documentation.* (n.d.). Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/pathlib.html
- *Quickstart — Flask Documentation (3.1.x).* (n.d.). Flask. Retrieved April 14, 2026, from https://flask.palletsprojects.com/en/stable/quickstart/
- *re — Regular expression operations — Python 3.14.4 documentation.* (n.d.). Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/re.html
- *shutil — High-level file operations — Python 3.14.4 documentation.* (n.d.). Python documentation. Retrieved April 14, 2026, from https://docs.python.org/3/library/shutil.html
- *String.prototype.replaceAll() - JavaScript | MDN.* (n.d.). MDN Web Docs. Retrieved April 14, 2026, from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/replaceAll
- University of Toronto Scarborough. (n.d.). *Course Timetable Archive.* https://www.utsc.utoronto.ca/registrar/course-timetable-archive
- University of Toronto Scarborough. (n.d.). *PDF Calendar and Archives.* UTSC Calendar. https://utsc.calendar.utoronto.ca/calendar-pdfs
- *URLSearchParams - Web APIs | MDN.* (2025, February 26). MDN Web Docs. Retrieved April 14, 2026, from https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams
- *Using SQLite 3 with Flask — Flask Documentation (3.1.x).* (n.d.). Flask. Retrieved April 14, 2026, from https://flask.palletsprojects.com/en/stable/patterns/sqlite3/
- *Using the Fetch API - Web APIs | MDN.* (2025, August 20). MDN Web Docs. Retrieved April 14, 2026, from https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
- *Window: localStorage property - Web APIs | MDN.* (2025, November 30). MDN Web Docs. Retrieved April 14, 2026, from https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage


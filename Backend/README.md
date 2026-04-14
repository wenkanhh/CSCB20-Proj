# Backend (Flask) 

### 1) Core Setup
**Files:**
- `app.py` — Flask app setup and route registration
- `config.py` — project/data/sql path setup
- `runtime_db.py` — runtime SQLite DB connection and schema
- `data_repository.py` — CSV loading and read-only data access

Covers:
- Flask app + DB connection

### 2) Authentication
**Files:**
- `auth_routes.py`

Covers:
- register
- login
- logout
- session protection via `login_required`

### 3) User Features
**Files:**
- `user_routes.py`
- `planner_service.py`

Covers:
- profile
- add courses
- user programs

### 4) Course Features
**Files:**
- `course_routes.py`
- `data_repository.py`

Covers:
- browse courses
- course details
- offerings

### 5) Recommendation System
**Files:**
- `recommendation_routes.py`
- `planner_service.py`

Covers:
- recommendation logic
- planner dashboard
- save recommendation
- degree audit
- eligibility

### 6) Validation
**Files:**
- `validation.py`
- global error handlers inside `app.py`

Covers:
- error handling + forms / JSON validation

---

## Important note

This backend reads from:
- `data_cleaned/*.csv`
- `sql/database.db` 

This backend writes only to:
- `sql/backend_runtime.db`

---

## Main routes

### Core setup
- `GET /api/health`

### Authentication
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`

### User features
- `GET /api/me/profile`
- `PUT /api/me/profile`
- `POST /api/me/programs`
- `GET /api/me/programs`
- `POST /api/me/completed-courses`
- `GET /api/me/completed-courses`

### Course features
- `GET /api/courses`
- `GET /api/courses/<course_code>`
- `GET /api/courses/<course_code>/offerings`
- `GET /api/programs`
- `GET /api/programs/<program_code>`

### Recommendation system
- `GET /api/me/eligibility/<course_code>`
- `GET /api/me/recommendations`
- `GET /api/me/planner-dashboard`
- `GET /api/me/degree-audit/<program_code>`
- `POST /api/me/saved-recommendations`
- `GET /api/me/saved-recommendations`

---

## Run 

Open terminal inside this folder and run:

```bash
pip install -r requirements.txt
python app.py
```

Then test:

```text
http://127.0.0.1:5000/api/health
```

---

## Example register JSON

```json
{
  "username": "khai",
  "password": "test123",
  "email": "khai@example.com",
  "cgpa": 3.2,
  "year_standing": 2
}
```

## Example add completed course JSON

```json
{
  "course_code": "MGTA01H3",
  "semester": "Fall",
  "year": 2025,
  "grade": "A-",
  "numeric_grade": 82,
  "status": "COMPLETED",
  "credits_earned": 0.5
}
```

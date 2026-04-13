from flask import render_template, request, redirect, url_for, session, flash

from runtime_db import get_conn
from validation import is_valid_program_code, is_valid_course_code


def _safe_float(value):
    try:
        return float(value)
    except:
        return 0.0


def _letter_to_gpa_points(letter_grade):
    if not letter_grade:
        return None

    grade = str(letter_grade).strip().upper()

    mapping = {
        "A+": 4.0,
        "A": 4.0,
        "A-": 3.7,
        "B+": 3.3,
        "B": 3.0,
        "B-": 2.7,
        "C+": 2.3,
        "C": 2.0,
        "C-": 1.7,
        "D+": 1.3,
        "D": 1.0,
        "D-": 0.7,
        "F": 0.0
    }

    return mapping.get(grade)


def _numeric_to_gpa_points(numeric_grade):
    if numeric_grade is None:
        return None

    try:
        grade = float(numeric_grade)
    except:
        return None

    if grade >= 85:
        return 4.0
    if grade >= 80:
        return 3.7
    if grade >= 77:
        return 3.3
    if grade >= 73:
        return 3.0
    if grade >= 70:
        return 2.7
    if grade >= 67:
        return 2.3
    if grade >= 63:
        return 2.0
    if grade >= 60:
        return 1.7
    if grade >= 57:
        return 1.3
    if grade >= 53:
        return 1.0
    if grade >= 50:
        return 0.7

    return 0.0


def _numeric_to_letter_grade(numeric_grade):
    if numeric_grade is None:
        return None

    try:
        grade = float(numeric_grade)
    except:
        return None

    if grade >= 90:
        return "A+"
    if grade >= 85:
        return "A"
    if grade >= 80:
        return "A-"
    if grade >= 77:
        return "B+"
    if grade >= 73:
        return "B"
    if grade >= 70:
        return "B-"
    if grade >= 67:
        return "C+"
    if grade >= 63:
        return "C"
    if grade >= 60:
        return "C-"
    if grade >= 57:
        return "D+"
    if grade >= 53:
        return "D"
    if grade >= 50:
        return "D-"

    return "F"


def _grade_to_gpa_points(letter_grade, numeric_grade):
    points_from_numeric = _numeric_to_gpa_points(numeric_grade)

    if points_from_numeric is not None:
        return points_from_numeric

    return _letter_to_gpa_points(letter_grade)


def _calculate_year_standing(completed_credits):
    if completed_credits >= 15.0:
        return 4
    if completed_credits >= 10.0:
        return 3
    if completed_credits >= 5.0:
        return 2
    return 1


def _calculate_academic_summary(conn, user_id):
    rows = conn.execute("""
        SELECT *
        FROM completed_courses
        WHERE user_id = ?
          AND status IN ('COMPLETED', 'TRANSFER')
    """, (user_id,)).fetchall()

    completed_credits = 0.0
    quality_points = 0.0
    gpa_credits = 0.0

    for row in rows:
        credits = _safe_float(row["credits_earned"])
        completed_credits += credits

        gpa_points = _grade_to_gpa_points(row["grade"], row["numeric_grade"])

        if gpa_points is not None and credits > 0:
            quality_points += gpa_points * credits
            gpa_credits += credits

    cgpa = round(quality_points / gpa_credits, 2) if gpa_credits > 0 else 0.0
    completed_credits = round(completed_credits, 2)
    year_standing = _calculate_year_standing(completed_credits)
    can_graduate = completed_credits >= 20.0

    return {
        "completed_credits": completed_credits,
        "cgpa": cgpa,
        "year_standing": year_standing,
        "can_graduate": can_graduate
    }


def init_user_routes(app, repo):
    @app.route("/dashboard")
    def dashboard():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]
        programs = repo.get_all_programs()

        conn = get_conn()

        user_programs = conn.execute("""
            SELECT *
            FROM user_programs
            WHERE user_id = ?
            ORDER BY id
        """, (user_id,)).fetchall()

        conn.close()

        return render_template(
            "dashboard.html",
            programs=programs,
            user_programs=user_programs
        )

    @app.route("/profile")
    def profile():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]

        conn = get_conn()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        user_programs = conn.execute("""
            SELECT *
            FROM user_programs
            WHERE user_id = ?
            ORDER BY id
        """, (user_id,)).fetchall()

        completed_courses = conn.execute("""
            SELECT *
            FROM completed_courses
            WHERE user_id = ?
            ORDER BY course_code
        """, (user_id,)).fetchall()

        academic_summary = _calculate_academic_summary(conn, user_id)

        conn.close()

        return render_template(
            "profile.html",
            user=user,
            user_programs=user_programs,
            completed_courses=completed_courses,
            academic_summary=academic_summary
        )

    @app.route("/save-program", methods=["POST"])
    def save_program():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]
        program_code = request.form.get("program_code", "").strip().upper()

        if not is_valid_program_code(program_code):
            flash("Invalid program code.")
            return redirect(url_for("dashboard"))

        program = repo.get_program_by_code(program_code)

        if not program:
            flash("Program not found.")
            return redirect(url_for("dashboard"))

        conn = get_conn()

        existing_program = conn.execute("""
            SELECT *
            FROM user_programs
            WHERE user_id = ?
              AND program_code = ?
        """, (user_id, program_code)).fetchone()

        if existing_program:
            conn.close()
            flash("Program already saved.")
            return redirect(url_for("dashboard"))

        conn.execute("""
            INSERT INTO user_programs (user_id, program_code, status)
            VALUES (?, ?, 'ACTIVE')
        """, (user_id, program_code))

        conn.commit()
        conn.close()

        flash("Program saved.")
        return redirect(url_for("dashboard"))

    @app.route("/remove-program/<int:program_id>")
    def remove_program(program_id):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]

        conn = get_conn()

        conn.execute("""
            DELETE FROM user_programs
            WHERE id = ?
              AND user_id = ?
        """, (program_id, user_id))

        conn.commit()
        conn.close()

        flash("Program removed.")
        return redirect(url_for("dashboard"))

    @app.route("/save-completed-courses", methods=["POST"])
    def save_completed_courses():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]
        current_program_code = request.form.get("current_program_code", "").strip().upper()
        current_page = request.form.get("current_page", "").strip().lower()
        current_keyword = request.form.get("current_keyword", "").strip()

        checked_course_codes = []
        seen_checked = set()

        for code in request.form.getlist("course_codes"):
            cleaned = code.strip().upper()

            if cleaned and cleaned not in seen_checked:
                seen_checked.add(cleaned)
                checked_course_codes.append(cleaned)

        visible_course_codes = []
        seen_visible = set()

        for code in request.form.getlist("visible_course_codes"):
            cleaned = code.strip().upper()

            if cleaned and cleaned not in seen_visible:
                seen_visible.add(cleaned)
                visible_course_codes.append(cleaned)

        conn = get_conn()

        # Only planner pages should actively remove unchecked visible courses.
        if current_page == "planner":
            unchecked_visible_codes = [
                code for code in visible_course_codes
                if code not in seen_checked
            ]

            for course_code in unchecked_visible_codes:
                conn.execute("""
                    DELETE FROM completed_courses
                    WHERE user_id = ?
                    AND course_code = ?
                """, (user_id, course_code))

        for course_code in checked_course_codes:
            if not is_valid_course_code(course_code):
                continue

            course = repo.get_course_by_code(course_code)

            if not course:
                continue

            semester_raw = request.form.get(f"semester_{course_code}", "").strip()
            year_raw = request.form.get(f"year_{course_code}", "").strip()
            numeric_grade_raw = request.form.get(f"numeric_grade_{course_code}", "").strip()

            semester = semester_raw if semester_raw in ["Fall", "Winter", "Summer"] else None

            try:
                year = int(year_raw) if year_raw != "" else None
            except:
                year = None

            try:
                numeric_grade = float(numeric_grade_raw) if numeric_grade_raw != "" else None
            except:
                numeric_grade = None

            grade = _numeric_to_letter_grade(numeric_grade)

            credits_earned = course["credits"] if course["credits"] not in [None, "", "nan", "NaN"] else 0.5

            existing_row = conn.execute("""
                SELECT record_id
                FROM completed_courses
                WHERE user_id = ?
                AND course_code = ?
            """, (user_id, course_code)).fetchone()

            if existing_row:
                conn.execute("""
                    UPDATE completed_courses
                    SET semester = ?,
                        year = ?,
                        grade = ?,
                        numeric_grade = ?,
                        status = 'COMPLETED',
                        credits_earned = ?
                    WHERE user_id = ?
                    AND course_code = ?
                """, (
                    semester,
                    year,
                    grade,
                    numeric_grade,
                    credits_earned,
                    user_id,
                    course_code
                ))
            else:
                conn.execute("""
                    INSERT INTO completed_courses (
                        user_id,
                        course_code,
                        semester,
                        year,
                        grade,
                        numeric_grade,
                        status,
                        credits_earned
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'COMPLETED', ?)
                """, (
                    user_id,
                    course_code,
                    semester,
                    year,
                    grade,
                    numeric_grade,
                    credits_earned
                ))

        academic_summary = _calculate_academic_summary(conn, user_id)

        conn.execute("""
            UPDATE users
            SET cgpa = ?,
                year_standing = ?
            WHERE user_id = ?
        """, (
            academic_summary["cgpa"],
            academic_summary["year_standing"],
            user_id
        ))

        conn.commit()
        conn.close()

        flash("Completed courses updated.")
        flash(f"Calculated CGPA: {academic_summary['cgpa']}")
        flash(f"Completed credits: {academic_summary['completed_credits']}")

        if academic_summary["can_graduate"]:
            flash("You can graduate now. Congratulations!")

        if current_page == "courses":
            if current_keyword != "":
                return redirect(url_for("search_courses", keyword=current_keyword))
            return redirect(url_for("courses"))

        if current_program_code and is_valid_program_code(current_program_code):
            return redirect(url_for("planner", program_code=current_program_code))

        return redirect(url_for("dashboard"))
from flask import render_template, request, redirect, url_for, session, flash

from runtime_db import get_conn
from validation import is_valid_program_code, is_valid_course_code


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
            ORDER BY record_id
        """, (user_id,)).fetchall()

        conn.close()

        return render_template(
            "profile.html",
            user=user,
            user_programs=user_programs,
            completed_courses=completed_courses
        )

    @app.route("/save-program", methods=["POST"])
    def save_program():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]
        program_code = request.form.get("program_code", "").strip().upper()
        start_year = request.form.get("start_year", "").strip()

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

        if start_year == "":
            conn.execute("""
                INSERT INTO user_programs (user_id, program_code, status)
                VALUES (?, ?, 'ACTIVE')
            """, (user_id, program_code))
        else:
            conn.execute("""
                INSERT INTO user_programs (user_id, program_code, status, start_year)
                VALUES (?, ?, 'ACTIVE', ?)
            """, (user_id, program_code, int(start_year)))

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
        course_codes = request.form.getlist("course_codes")

        conn = get_conn()

        conn.execute("""
            DELETE FROM completed_courses
            WHERE user_id = ?
        """, (user_id,))

        for course_code in course_codes:
            course_code = course_code.strip().upper()

            if is_valid_course_code(course_code):
                course = repo.get_course_by_code(course_code)

                if course:
                    conn.execute("""
                        INSERT INTO completed_courses (
                            user_id,
                            course_code,
                            status,
                            credits_earned
                        )
                        VALUES (?, ?, 'COMPLETED', ?)
                    """, (user_id, course_code, course["credits"]))

        conn.commit()
        conn.close()

        flash("Completed courses updated.")
        return redirect(url_for("dashboard"))
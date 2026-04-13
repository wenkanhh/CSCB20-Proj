from flask import render_template, request, redirect, url_for, session, flash, jsonify

from runtime_db import get_conn
from validation import is_valid_course_code


def init_course_routes(app, repo, planner_service):
    def _get_completed_map(user_id):
        conn = get_conn()

        rows = conn.execute("""
            SELECT *
            FROM completed_courses
            WHERE user_id = ?
        """, (user_id,)).fetchall()

        conn.close()

        completed_map = {}

        for row in rows:
            completed_map[row["course_code"]] = {
                "course_code": row["course_code"],
                "semester": row["semester"],
                "year": row["year"],
                "grade": row["grade"],
                "numeric_grade": row["numeric_grade"],
                "status": row["status"],
                "credits_earned": row["credits_earned"]
            }

        return completed_map

    @app.route("/courses")
    def courses():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]
        keyword = request.args.get("keyword", "").strip()

        if keyword == "":
            course_list = repo.get_all_courses()
        else:
            course_list = repo.search_courses(keyword)

        completed_map = _get_completed_map(user_id)

        return render_template(
            "courses.html",
            courses=course_list,
            keyword=keyword,
            completed_map=completed_map
        )

    @app.route("/course/<course_code>")
    def course_page(course_code):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        course_code = course_code.strip().upper()

        if not is_valid_course_code(course_code):
            flash("Invalid course code.")
            return redirect(url_for("courses"))

        details = planner_service.get_course_details(course_code)

        if not details:
            flash("Course not found.")
            return redirect(url_for("courses"))

        return render_template("course-details.html", details=details)

    @app.route("/api/course/<course_code>")
    def api_course_details(course_code):
        if "user_id" not in session:
            return jsonify({"error": "Please log in first."}), 401

        course_code = course_code.strip().upper()

        if not is_valid_course_code(course_code):
            return jsonify({"error": "Invalid course code."}), 400

        details = planner_service.get_course_details(course_code)

        if not details:
            return jsonify({"error": "Course not found."}), 404

        return jsonify(details)

    @app.route("/search-courses")
    def search_courses():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]
        keyword = request.args.get("keyword", "").strip()

        if keyword == "":
            return redirect(url_for("courses"))

        course_list = repo.search_courses(keyword)
        completed_map = _get_completed_map(user_id)

        return render_template(
            "courses.html",
            courses=course_list,
            keyword=keyword,
            completed_map=completed_map
        )
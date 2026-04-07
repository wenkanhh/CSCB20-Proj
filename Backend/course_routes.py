from flask import render_template, request, redirect, url_for, session, flash, jsonify

from validation import is_valid_course_code

def init_course_routes(app, repo, planner_service):
    @app.route("/courses")
    def courses():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        keyword = request.args.get("keyword", "").strip()

        if keyword == "":
            course_list = repo.get_all_courses()
        else:
            course_list = repo.search_courses(keyword)

        return render_template("courses.html", courses=course_list, keyword=keyword)

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

        keyword = request.args.get("keyword", "").strip()

        if keyword == "":
            return redirect(url_for("courses"))

        course_list = repo.search_courses(keyword)

        return render_template("courses.html", courses=course_list, keyword=keyword)
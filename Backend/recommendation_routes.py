from flask import render_template, request, redirect, url_for, session, flash, jsonify

from validation import is_valid_program_code


def init_recommendation_routes(app, planner_service):
    @app.route("/planner")
    def planner():
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))

        user_id = session["user_id"]
        program_code = request.args.get("program_code", "").strip().upper()

        if not is_valid_program_code(program_code):
            flash("Invalid program code.")
            return redirect(url_for("dashboard"))

        plan = planner_service.get_program_plan(user_id, program_code)

        if not plan:
            flash("Program plan not found.")
            return redirect(url_for("dashboard"))

        return render_template("recommendations.html", plan=plan)

    @app.route("/api/planner")
    def api_planner():
        if "user_id" not in session:
            return jsonify({"error": "Please log in first."}), 401

        user_id = session["user_id"]
        program_code = request.args.get("program_code", "").strip().upper()

        if not is_valid_program_code(program_code):
            return jsonify({"error": "Invalid program code."}), 400

        plan = planner_service.get_program_plan(user_id, program_code)

        if not plan:
            return jsonify({"error": "Program plan not found."}), 404

        return jsonify(plan)
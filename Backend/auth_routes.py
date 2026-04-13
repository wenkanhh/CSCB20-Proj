from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from runtime_db import get_conn
from validation import (
    is_valid_email,
    is_valid_username,
    is_valid_password
)


def init_auth_routes(app):
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "GET":
            return render_template("register.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        email = request.form.get("email", "").strip()

        if not is_valid_username(username):
            flash("Username must be at least 3 characters.")
            return render_template("register.html")

        if not is_valid_password(password):
            flash("Password must be at least 6 characters.")
            return render_template("register.html")

        if not is_valid_email(email):
            flash("Please enter a valid email.")
            return render_template("register.html")

        conn = get_conn()

        existing_user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        if existing_user:
            conn.close()
            flash("Username already exists.")
            return render_template("register.html")

        existing_email = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if existing_email:
            conn.close()
            flash("Email already exists.")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        conn.execute("""
            INSERT INTO users (username, password, email, cgpa, year_standing)
            VALUES (?, ?, ?, ?, ?)
        """, (username, hashed_password, email, 0.0, 1))

        conn.commit()
        conn.close()

        flash("Account created successfully. Please log in.")
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")

        login_value = request.form.get("login_value", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_conn()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
               OR email = ?
        """, (login_value, login_value)).fetchone()

        conn.close()

        if not user:
            flash("Invalid username/email or password.")
            return render_template("login.html")

        if not check_password_hash(user["password"], password):
            flash("Invalid username/email or password.")
            return render_template("login.html")

        session["user_id"] = user["user_id"]
        session["username"] = user["username"]

        flash("Login successful.")
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        session.pop("username", None)

        flash("You have been logged out.")
        return redirect(url_for("login"))
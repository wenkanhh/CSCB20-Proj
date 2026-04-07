from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from runtime_db import get_conn
from validation import (
    is_valid_email,
    is_valid_username,
    is_valid_password,
    is_valid_cgpa,
    is_valid_year_standing
)
#when you sign up, it will guide you through one by one step if done wrong, flash a message

#app in the bracket here cus it substitutes app = Flask(__name__)
def init_auth_routes(app):
    @app.route("/register", methods=["GET", "POST"])
    def register():
        # If user just opened the page, show the form
        if request.method == "GET":
            return render_template("register.html")

        # Get form data
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        email = request.form.get("email", "").strip()
        cgpa = request.form.get("cgpa", "").strip()
        year_standing = request.form.get("year_standing", "").strip()

        # Check the input
        if not is_valid_username(username):
            flash("Username must be at least 3 characters.")
            return render_template("register.html")

        if not is_valid_password(password):
            flash("Password must be at least 6 characters.")
            return render_template("register.html")

        if not is_valid_email(email):
            flash("Please enter a valid email.")
            return render_template("register.html")

        if not is_valid_cgpa(cgpa):
            flash("CGPA must be between 0.0 and 4.0.")
            return render_template("register.html")

        if not is_valid_year_standing(year_standing):
            flash("Year standing must be between 1 and 4.")
            return render_template("register.html")

        conn = get_conn()

        # Check if username already exists
        existing_user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        if existing_user:
            conn.close()
            flash("Username already exists.")
            return render_template("register.html")

        # Check if email already exists
        existing_email = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if existing_email:
            conn.close()
            flash("Email already exists.")
            return render_template("register.html")

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        # Save new user
        conn.execute("""
            INSERT INTO users (username, password, email, cgpa, year_standing)
            VALUES (?, ?, ?, ?, ?)
        """, (username, hashed_password, email, float(cgpa), int(year_standing)))

        conn.commit()
        conn.close()

        flash("Account created successfully. Please log in.")
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        # If user just opened the page, show the form
        if request.method == "GET":
            return render_template("login.html")

        # Get form data
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_conn()

        # Find user by username
        user = conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        conn.close()

        # Check if user exists
        if not user:
            flash("Invalid username or password.")
            return render_template("login.html")

        # Check password
        if not check_password_hash(user["password"], password):
            flash("Invalid username or password.")
            return render_template("login.html")

        # Save login info in session
        session["user_id"] = user["user_id"]
        session["username"] = user["username"]

        flash("Login successful.")
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    def logout():
        # Remove login data from session
        session.pop("user_id", None)
        session.pop("username", None)

        flash("You have been logged out.")
        return redirect(url_for("login"))
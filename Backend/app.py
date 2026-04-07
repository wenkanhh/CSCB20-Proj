from flask import Flask, redirect, url_for, session

from runtime_db import init_runtime_db
from data_repository import DataRepository
from planner_service import PlannerService

from auth_routes import init_auth_routes
from user_routes import init_user_routes
from course_routes import init_course_routes
from recommendation_routes import init_recommendation_routes

app = Flask(__name__)
app.secret_key = "my_secret_key"

init_runtime_db()

repo = DataRepository()
planner_service = PlannerService(repo)


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


init_auth_routes(app)
init_user_routes(app, repo)
init_course_routes(app, repo, planner_service)
init_recommendation_routes(app, planner_service)


if __name__ == "__main__":
    app.run()
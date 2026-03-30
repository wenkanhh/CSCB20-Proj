from __future__ import annotations

from typing import Any

from flask import Flask, jsonify

from auth_routes import auth_bp
from config import DATA_DIR, DEBUG, EXISTING_PROJECT_DB_PATH, PROJECT_ROOT, RUNTIME_DB_PATH, SECRET_KEY, SQL_DIR
from course_routes import create_course_blueprint
from data_repository import DataRepository
from planner_service import PlannerService
from recommendation_routes import create_recommendation_blueprint
from runtime_db import init_runtime_db
from user_routes import create_user_blueprint
from validation import ValidationError


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['JSON_SORT_KEYS'] = False

    init_runtime_db()
    repo = DataRepository.load()
    service = PlannerService(repo)

    app.register_blueprint(auth_bp)
    app.register_blueprint(create_user_blueprint(service, repo))
    app.register_blueprint(create_course_blueprint(repo))
    app.register_blueprint(create_recommendation_blueprint(service))

    @app.get('/api/health')
    def health() -> Any:
        return jsonify({
            'status': 'ok',
            'project_root': str(PROJECT_ROOT),
            'data_dir': str(DATA_DIR),
            'sql_dir': str(SQL_DIR),
            'runtime_db': str(RUNTIME_DB_PATH),
            'existing_project_db': str(EXISTING_PROJECT_DB_PATH),
        })

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> Any:
        return jsonify({'error': str(error)}), 400

    @app.errorhandler(404)
    def handle_not_found(_: Any) -> Any:
        return jsonify({'error': 'Route not found.'}), 404

    @app.errorhandler(500)
    def handle_server_error(error: Exception) -> Any:
        return jsonify({'error': 'Internal server error.', 'detail': str(error)}), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=DEBUG)

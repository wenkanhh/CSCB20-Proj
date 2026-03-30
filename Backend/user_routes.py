from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request, session

from auth_routes import login_required
from data_repository import DataRepository
from planner_service import PlannerService
from runtime_db import get_conn, init_runtime_db
from validation import ValidationError, optional_float, optional_int, optional_str, parse_json, required_str


def create_user_blueprint(service: PlannerService, repo: DataRepository) -> Blueprint:
    user_bp = Blueprint('users', __name__, url_prefix='/api')

    @user_bp.get('/me/profile')
    @login_required
    def get_profile() -> Any:
        user = service.get_user(int(session['user_id']))
        if not user:
            return jsonify({'error': 'User not found.'}), 404
        return jsonify(user)

    @user_bp.put('/me/profile')
    @login_required
    def update_profile() -> Any:
        try:
            data = parse_json(request)
            email = optional_str(data, 'email')
            cgpa = optional_float(data, 'cgpa')
            year_standing = optional_int(data, 'year_standing')
        except ValidationError as exc:
            return jsonify({'error': str(exc)}), 400

        fields = []
        values = []
        if email is not None:
            fields.append('email = ?')
            values.append(email)
        if cgpa is not None:
            fields.append('cgpa = ?')
            values.append(cgpa)
        if year_standing is not None:
            fields.append('year_standing = ?')
            values.append(year_standing)
        if not fields:
            return jsonify({'error': 'Nothing to update.'}), 400

        values.append(int(session['user_id']))
        init_runtime_db()
        with get_conn() as conn:
            conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", tuple(values))
        return jsonify({'message': 'Profile updated.'})

    @user_bp.post('/me/programs')
    @login_required
    def add_program() -> Any:
        try:
            data = parse_json(request)
            program_code = required_str(data, 'program_code').upper()
            status = optional_str(data, 'status', 'ACTIVE') or 'ACTIVE'
            start_year = optional_int(data, 'start_year')
            end_year = optional_int(data, 'end_year')
        except ValidationError as exc:
            return jsonify({'error': str(exc)}), 400

        if not repo.get_program(program_code):
            return jsonify({'error': 'Program not found in programs.csv.'}), 400
        row_id = service.add_user_program(int(session['user_id']), program_code, status, start_year, end_year)
        return jsonify({'message': 'Program added.', 'id': row_id}), 201

    @user_bp.get('/me/programs')
    @login_required
    def list_my_programs() -> Any:
        return jsonify(service.get_user_programs(int(session['user_id'])))

    @user_bp.post('/me/completed-courses')
    @login_required
    def add_completed_course() -> Any:
        try:
            data = parse_json(request)
            course_code = required_str(data, 'course_code').upper()
            semester = optional_str(data, 'semester')
            year = optional_int(data, 'year')
            grade = optional_str(data, 'grade')
            numeric_grade = optional_float(data, 'numeric_grade')
            status = optional_str(data, 'status', 'COMPLETED') or 'COMPLETED'
            credits_earned = optional_float(data, 'credits_earned', 0.5) or 0.5
        except ValidationError as exc:
            return jsonify({'error': str(exc)}), 400

        if not repo.get_course(course_code):
            return jsonify({'error': 'Course not found in courses.csv.'}), 400
        record_id = service.add_completed_course(
            int(session['user_id']),
            course_code,
            semester,
            year,
            grade,
            numeric_grade,
            status,
            credits_earned,
        )
        return jsonify({'message': 'Course saved to profile.', 'record_id': record_id}), 201

    @user_bp.get('/me/completed-courses')
    @login_required
    def list_completed_courses() -> Any:
        return jsonify(service.get_completed_courses(int(session['user_id'])))

    return user_bp

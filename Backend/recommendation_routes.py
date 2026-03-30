from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request, session

from auth_routes import login_required
from planner_service import PlannerService
from validation import ValidationError, optional_str, parse_json, required_str


def create_recommendation_blueprint(service: PlannerService) -> Blueprint:
    recommendation_bp = Blueprint('recommendations', __name__, url_prefix='/api')

    @recommendation_bp.get('/me/eligibility/<course_code>')
    @login_required
    def eligibility(course_code: str) -> Any:
        return jsonify(service.can_take_course(int(session['user_id']), course_code))

    @recommendation_bp.get('/me/recommendations')
    @login_required
    def recommendations() -> Any:
        program_code = request.args.get('program_code')
        limit = int(request.args.get('limit', 20))
        return jsonify(service.recommend_courses(int(session['user_id']), program_code=program_code, limit=limit))

    @recommendation_bp.get('/me/planner-dashboard')
    @login_required
    def dashboard() -> Any:
        program_code = request.args.get('program_code')
        return jsonify(service.planner_dashboard(int(session['user_id']), program_code=program_code))

    @recommendation_bp.get('/me/degree-audit/<program_code>')
    @login_required
    def degree_audit(program_code: str) -> Any:
        audit = service.degree_audit(int(session['user_id']), program_code)
        if not audit.get('program'):
            return jsonify({'error': audit.get('reason', 'Program not found.')}), 404
        return jsonify(audit)

    @recommendation_bp.post('/me/saved-recommendations')
    @login_required
    def save_recommendation() -> Any:
        try:
            data = parse_json(request)
            course_code = required_str(data, 'course_code')
            program_code = optional_str(data, 'program_code')
            reason = optional_str(data, 'reason')
        except ValidationError as exc:
            return jsonify({'error': str(exc)}), 400
        recommendation_id = service.save_recommendation(int(session['user_id']), course_code, program_code, reason)
        return jsonify({'message': 'Recommendation saved.', 'recommendation_id': recommendation_id}), 201

    @recommendation_bp.get('/me/saved-recommendations')
    @login_required
    def list_saved_recommendations() -> Any:
        return jsonify(service.get_saved_recommendations(int(session['user_id'])))

    return recommendation_bp

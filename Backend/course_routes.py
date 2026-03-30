from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from data_repository import DataRepository


def create_course_blueprint(repo: DataRepository) -> Blueprint:
    course_bp = Blueprint('courses', __name__, url_prefix='/api')

    @course_bp.get('/courses')
    def list_courses() -> Any:
        search = request.args.get('search', '')
        prefix = request.args.get('prefix', '')
        limit = int(request.args.get('limit', 200))
        return jsonify(repo.list_courses(search=search, prefix=prefix, limit=limit))

    @course_bp.get('/courses/<course_code>')
    def get_course(course_code: str) -> Any:
        course = repo.get_course(course_code)
        if not course:
            return jsonify({'error': 'Course not found.'}), 404
        exclusions = repo.get_course_exclusions(course_code)
        prereq_groups = repo.get_course_requirements(course_code, 'PREREQ')
        coreq_groups = repo.get_course_requirements(course_code, 'COREQ')
        for group in prereq_groups + coreq_groups:
            group['items'] = repo.get_requirement_items(int(group['group_id']))
        return jsonify({
            'course': course,
            'exclusions': exclusions,
            'prereq_groups': prereq_groups,
            'coreq_groups': coreq_groups,
        })

    @course_bp.get('/courses/<course_code>/offerings')
    def get_course_offerings(course_code: str) -> Any:
        offerings = repo.get_course_offerings(course_code)
        return jsonify({
            'course_code': course_code.upper().strip(),
            'offerings': offerings,
            'source': 'sql/database.db' if offerings else 'No offering rows found in sql/database.db',
        })

    @course_bp.get('/programs')
    def list_programs() -> Any:
        search = request.args.get('search', '')
        program_type = request.args.get('type', '')
        return jsonify(repo.list_programs(search=search, program_type=program_type))

    @course_bp.get('/programs/<program_code>')
    def get_program(program_code: str) -> Any:
        program = repo.get_program(program_code)
        if not program:
            return jsonify({'error': 'Program not found.'}), 404
        groups = repo.get_program_requirement_groups(program_code)
        for group in groups:
            group['courses'] = repo.get_program_requirement_courses(int(group['group_id']))
        return jsonify({'program': program, 'requirement_groups': groups})

    return course_bp

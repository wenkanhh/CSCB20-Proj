from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from runtime_db import get_conn, init_runtime_db
from validation import ValidationError, optional_float, optional_int, parse_json, required_str


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required.'}), 401
        return view(*args, **kwargs)

    return wrapped


@auth_bp.post('/register')
def register() -> Any:
    try:
        data = parse_json(request)
        username = required_str(data, 'username')
        password = required_str(data, 'password')
        email = required_str(data, 'email')
        cgpa = optional_float(data, 'cgpa', 0.0) or 0.0
        year_standing = optional_int(data, 'year_standing', 1) or 1
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400

    init_runtime_db()
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO users (username, password_hash, email, cgpa, year_standing) VALUES (?, ?, ?, ?, ?)',
                (username, generate_password_hash(password), email, cgpa, year_standing),
            )
            user_id = int(cursor.lastrowid)
    except Exception as exc:
        return jsonify({'error': f'Could not register user: {exc}'}), 400

    session['user_id'] = user_id
    return jsonify({'message': 'Registered successfully.', 'user_id': user_id}), 201


@auth_bp.post('/login')
def login() -> Any:
    try:
        data = parse_json(request)
        username = required_str(data, 'username')
        password = required_str(data, 'password')
    except ValidationError as exc:
        return jsonify({'error': str(exc)}), 400

    init_runtime_db()
    with get_conn() as conn:
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if not row or not check_password_hash(row['password_hash'], password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    session['user_id'] = int(row['user_id'])
    return jsonify({'message': 'Logged in.', 'user_id': int(row['user_id'])})


@auth_bp.post('/logout')
def logout() -> Any:
    session.clear()
    return jsonify({'message': 'Logged out.'})


@auth_bp.get('/session')
@login_required
def get_session_info() -> Any:
    return jsonify({'authenticated': True, 'user_id': session.get('user_id')})

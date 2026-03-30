from __future__ import annotations

from typing import Any

from flask import Request
from werkzeug.exceptions import BadRequest


class ValidationError(ValueError):
    pass


def parse_json(request: Request) -> dict[str, Any]:
    try:
        data = request.get_json(force=True)
    except BadRequest as exc:
        raise ValidationError(f'Invalid JSON body: {exc.description}') from exc
    if not isinstance(data, dict):
        raise ValidationError('JSON body must be an object.')
    return data


def required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None or str(value).strip() == '':
        raise ValidationError(f'{key} is required.')
    return str(value).strip()


def optional_str(data: dict[str, Any], key: str, default: str | None = None) -> str | None:
    value = data.get(key, default)
    if value is None:
        return None
    return str(value).strip()


def optional_int(data: dict[str, Any], key: str, default: int | None = None) -> int | None:
    value = data.get(key, default)
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f'{key} must be an integer.') from exc


def optional_float(data: dict[str, Any], key: str, default: float | None = None) -> float | None:
    value = data.get(key, default)
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f'{key} must be a number.') from exc

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from data_repository import DataRepository
from runtime_db import get_conn


@dataclass
class PlannerService:
    repo: DataRepository

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        with get_conn() as conn:
            row = conn.execute('SELECT user_id, username, email, cgpa, year_standing, created_at FROM users WHERE user_id = ?', (user_id,)).fetchone()
        return dict(row) if row else None

    def get_user_programs(self, user_id: int) -> list[dict[str, Any]]:
        with get_conn() as conn:
            rows = conn.execute('SELECT * FROM user_programs WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
        return [dict(row) for row in rows]

    def add_user_program(self, user_id: int, program_code: str, status: str, start_year: int | None, end_year: int | None) -> int:
        with get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO user_programs (user_id, program_code, status, start_year, end_year) VALUES (?, ?, ?, ?, ?)',
                (user_id, program_code.upper().strip(), status, start_year, end_year),
            )
            return int(cursor.lastrowid)

    def get_completed_courses(self, user_id: int) -> list[dict[str, Any]]:
        with get_conn() as conn:
            rows = conn.execute('SELECT * FROM completed_courses WHERE user_id = ? ORDER BY year DESC, semester DESC, record_id DESC', (user_id,)).fetchall()
        return [dict(row) for row in rows]

    def add_completed_course(
        self,
        user_id: int,
        course_code: str,
        semester: str | None,
        year: int | None,
        grade: str | None,
        numeric_grade: float | None,
        status: str,
        credits_earned: float,
    ) -> int:
        with get_conn() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO completed_courses (user_id, course_code, semester, year, grade, numeric_grade, status, credits_earned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (user_id, course_code.upper().strip(), semester, year, grade, numeric_grade, status, credits_earned),
            )
            return int(cursor.lastrowid)

    def save_recommendation(self, user_id: int, course_code: str, program_code: str | None, reason: str | None) -> int:
        with get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO saved_recommendations (user_id, course_code, program_code, reason) VALUES (?, ?, ?, ?)',
                (user_id, course_code.upper().strip(), program_code, reason),
            )
            return int(cursor.lastrowid)

    def get_saved_recommendations(self, user_id: int) -> list[dict[str, Any]]:
        with get_conn() as conn:
            rows = conn.execute('SELECT * FROM saved_recommendations WHERE user_id = ? ORDER BY recommendation_id DESC', (user_id,)).fetchall()
        return [dict(row) for row in rows]

    def _completed_course_codes(self, user_id: int) -> set[str]:
        records = self.get_completed_courses(user_id)
        completed = {
            str(row['course_code']).upper()
            for row in records
            if str(row.get('status', '')).upper() in {'COMPLETED', 'TRANSFER', 'IN_PROGRESS'}
        }
        expanded = set(completed)
        changed = True
        while changed:
            changed = False
            for row in self.repo.course_exclusions:
                a = str(row.get('course_code', '')).upper()
                b = str(row.get('excluded_course', '')).upper()
                if a in expanded and b and b not in expanded:
                    expanded.add(b)
                    changed = True
                if b in expanded and a and a not in expanded:
                    expanded.add(a)
                    changed = True
        return expanded

    def _total_credits(self, user_id: int) -> float:
        records = self.get_completed_courses(user_id)
        total = 0.0
        for row in records:
            if str(row.get('status', '')).upper() in {'COMPLETED', 'TRANSFER'}:
                total += float(row.get('credits_earned') or 0.0)
        return total

    def _dept_credits(self, user_id: int) -> dict[str, float]:
        completed = self._completed_course_codes(user_id)
        totals: dict[str, float] = defaultdict(float)
        for code in completed:
            course = self.repo.get_course(code)
            if course:
                prefix = str(course.get('course_code_prefix', '')).upper().strip()
                credits = float(course.get('credits') or 0.0)
                totals[prefix] += credits
        return dict(totals)

    def _program_names(self, user_id: int) -> list[str]:
        names: list[str] = []
        for row in self.get_user_programs(user_id):
            code = str(row.get('program_code', '')).upper()
            program = self.repo.get_program(code)
            if program:
                names.append(str(program.get('program_name', '')).lower())
        return names

    def _user_context(self, user_id: int) -> dict[str, Any] | None:
        user = self.get_user(user_id)
        if not user:
            return None
        return {
            'user': user,
            'completed': self._completed_course_codes(user_id),
            'total_credits': self._total_credits(user_id),
            'dept_credits': self._dept_credits(user_id),
            'program_names': self._program_names(user_id),
        }

    def _item_satisfied(self, item: dict[str, Any], context: dict[str, Any]) -> tuple[bool, str | None]:
        item_type = str(item.get('item_type', '')).upper()
        completed: set[str] = context['completed']
        user = context['user']

        if item_type == 'COURSE':
            code = str(item.get('course_code') or '').upper()
            return code in completed, f'Requires {code}'
        if item_type == 'MIN_CREDITS_TOTAL':
            need = float(item.get('min_credits') or 0.0)
            return context['total_credits'] >= need, f'Requires {need} credits total'
        if item_type == 'MIN_CREDITS_DEPT':
            prefix = str(item.get('department_prefix') or '').upper()
            need = float(item.get('min_credits') or 0.0)
            have = float(context['dept_credits'].get(prefix, 0.0))
            return have >= need, f'Requires {need} credits in {prefix}'
        if item_type == 'MIN_CGPA':
            need = float(item.get('min_cgpa') or 0.0)
            have = float(user.get('cgpa') or 0.0)
            return have >= need, f'Requires CGPA {need}'
        if item_type == 'PROGRAM_ENROLLMENT':
            program_name = str(item.get('program_name') or '').lower().strip()
            ok = any(program_name and program_name in name for name in context['program_names'])
            return ok, f'Requires enrollment in {program_name}'
        if item_type == 'YEAR_STANDING':
            need = int(item.get('year_standing') or 0)
            have = int(user.get('year_standing') or 0)
            return have >= need, f'Requires year standing {need}'
        if item_type.startswith('MIN_CREDITS_LEVEL_'):
            need = float(item.get('min_credits') or 0.0)
            level = item_type.rsplit('_', 1)[-1]
            have = 0.0
            for code in completed:
                if len(code) >= 5 and code[4:5].upper() == level:
                    course = self.repo.get_course(code)
                    if course:
                        have += float(course.get('credits') or 0.0)
            return have >= need, f'Requires {need} {level}-level credits'
        note = str(item.get('notes') or item_type)
        return False, f'Manual review required: {note}'

    def _group_satisfied(self, group_id: int, group_logic: str, context: dict[str, Any]) -> dict[str, Any]:
        items = self.repo.get_requirement_items(group_id)
        evaluations = []
        for item in items:
            satisfied, detail = self._item_satisfied(item, context)
            evaluations.append({'item': item, 'satisfied': satisfied, 'detail': detail})

        logic = str(group_logic or 'AND').upper()
        if not evaluations:
            return {'satisfied': True, 'items': evaluations}
        if logic == 'OR':
            satisfied = any(entry['satisfied'] for entry in evaluations)
        else:
            satisfied = all(entry['satisfied'] for entry in evaluations)
        return {'satisfied': satisfied, 'items': evaluations}

    def _paths_for_course(self, course_code: str, req_type: str, context: dict[str, Any]) -> dict[str, Any]:
        groups = self.repo.get_course_requirements(course_code, req_type)
        if not groups:
            return {'satisfied': True, 'paths': []}

        path_map: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for group in groups:
            path_id = int(group.get('path_id') or 1)
            path_map[path_id].append(group)

        path_results = []
        any_path = False
        for path_id, path_groups in sorted(path_map.items()):
            evaluated_groups = []
            path_ok = True
            for group in path_groups:
                group_id = int(group['group_id'])
                result = self._group_satisfied(group_id, str(group.get('group_logic') or 'AND'), context)
                evaluated_groups.append({**group, **result})
                if not result['satisfied']:
                    path_ok = False
            path_results.append({'path_id': path_id, 'satisfied': path_ok, 'groups': evaluated_groups})
            if path_ok:
                any_path = True
        return {'satisfied': any_path, 'paths': path_results}

    def can_take_course(self, user_id: int, course_code: str) -> dict[str, Any]:
        context = self._user_context(user_id)
        if not context:
            return {'eligible': False, 'reason': 'User not found'}

        code = course_code.upper().strip()
        if code in context['completed']:
            return {'eligible': False, 'course_code': code, 'reason': 'Already completed or excluded by equivalent credit.'}

        prereq = self._paths_for_course(code, 'PREREQ', context)
        coreq = self._paths_for_course(code, 'COREQ', context)
        blocked_by_exclusion = any(
            str(row.get('course_code', '')).upper() in context['completed'] or str(row.get('excluded_course', '')).upper() in context['completed']
            for row in self.repo.get_course_exclusions(code)
        )

        eligible = prereq['satisfied'] and coreq['satisfied'] and not blocked_by_exclusion
        reason = 'Eligible.' if eligible else 'Unmet requirements, corequisites, or exclusions.'
        return {
            'eligible': eligible,
            'course_code': code,
            'reason': reason,
            'prerequisites': prereq,
            'corequisites': coreq,
            'blocked_by_exclusion': blocked_by_exclusion,
        }

    def degree_audit(self, user_id: int, program_code: str) -> dict[str, Any]:
        context = self._user_context(user_id)
        if not context:
            return {'program': None, 'reason': 'User not found'}

        program = self.repo.get_program(program_code)
        if not program:
            return {'program': None, 'reason': 'Program not found'}

        completed = context['completed']
        requirement_groups = self.repo.get_program_requirement_groups(program_code)
        results = []
        required_missing_codes: list[str] = []

        for group in requirement_groups:
            group_id = int(group['group_id'])
            courses = self.repo.get_program_requirement_courses(group_id)
            course_codes = [str(row.get('course_code', '')).upper() for row in courses]
            completed_in_group = [code for code in course_codes if code in completed]
            missing_in_group = [code for code in course_codes if code and code not in completed]

            group_type = str(group.get('group_type') or 'ALL').upper()
            min_courses = int(float(group.get('min_courses') or 0)) if group.get('min_courses') not in (None, '') else None
            min_credits = float(group.get('min_credits') or 0.0) if group.get('min_credits') not in (None, '') else None

            satisfied = False
            if group_type == 'OPTIONAL':
                satisfied = True
            elif group_type == 'PICK':
                if min_courses is not None and min_courses > 0:
                    satisfied = len(completed_in_group) >= min_courses
                elif min_credits is not None and min_credits > 0:
                    earned = 0.0
                    for code in completed_in_group:
                        course = self.repo.get_course(code)
                        if course:
                            earned += float(course.get('credits') or 0.0)
                    satisfied = earned >= min_credits
            else:
                satisfied = len(missing_in_group) == 0

            if not satisfied and str(group.get('category') or 'Required').lower() != 'optional':
                required_missing_codes.extend(missing_in_group)

            results.append({
                'group': group,
                'courses': courses,
                'completed_in_group': completed_in_group,
                'missing_in_group': missing_in_group,
                'satisfied': satisfied,
            })

        return {
            'program': program,
            'overall_satisfied': all(entry['satisfied'] for entry in results) if results else False,
            'required_missing_courses': sorted(set(required_missing_codes)),
            'groups': results,
        }

    def recommend_courses(self, user_id: int, program_code: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        context = self._user_context(user_id)
        if not context:
            return []

        completed = context['completed']
        priority_codes: set[str] = set()
        if program_code:
            audit = self.degree_audit(user_id, program_code)
            priority_codes.update(audit.get('required_missing_courses', []))
        else:
            for row in self.get_user_programs(user_id):
                code = str(row.get('program_code', '')).upper()
                if code:
                    audit = self.degree_audit(user_id, code)
                    priority_codes.update(audit.get('required_missing_courses', []))

        recommendations = []
        seen: set[str] = set()
        candidate_codes = list(priority_codes) + [str(row.get('course_code', '')).upper() for row in self.repo.courses]
        for code in candidate_codes:
            if not code or code in seen or code in completed:
                continue
            seen.add(code)
            eligibility = self.can_take_course(user_id, code)
            if not eligibility['eligible']:
                continue
            course = self.repo.get_course(code)
            if not course:
                continue
            score = 0
            reasons = []
            if code in priority_codes:
                score += 100
                reasons.append('Missing required course for selected/active program')
            if self.repo.get_course_offerings(code):
                score += 10
                reasons.append('Has offering data in sql/database.db')
            if str(course.get('prerequisites') or '').strip():
                score += 5
                reasons.append('Unlocked after satisfying prerequisites')
            recommendations.append({
                'course_code': code,
                'course_name': course.get('course_name'),
                'score': score,
                'reasons': reasons,
                'course': course,
            })

        recommendations.sort(key=lambda row: (-int(row['score']), str(row['course_code'])))
        return recommendations[:limit]

    def planner_dashboard(self, user_id: int, program_code: str | None = None) -> dict[str, Any]:
        user = self.get_user(user_id)
        if not user:
            return {'error': 'User not found'}
        active_programs = self.get_user_programs(user_id)
        completed_courses = self.get_completed_courses(user_id)
        recommendations = self.recommend_courses(user_id, program_code=program_code, limit=10)
        audit = self.degree_audit(user_id, program_code) if program_code else None

        return {
            'profile': user,
            'active_programs': active_programs,
            'completed_courses_count': len(completed_courses),
            'completed_credits_total': self._total_credits(user_id),
            'recommendations_count': len(recommendations),
            'recommendations': recommendations,
            'selected_program_audit': audit,
            'saved_recommendations': self.get_saved_recommendations(user_id),
        }

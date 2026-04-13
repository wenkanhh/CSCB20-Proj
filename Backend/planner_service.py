from runtime_db import get_conn


class PlannerService:
    def __init__(self, repo):
        self.repo = repo

    def _clean_text(self, value):
        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() == "nan":
            return ""

        return text

    def _credit_value(self, value):
        try:
            return float(value)
        except:
            return 0.0

    def _is_coop_value(self, value):
        return str(value).strip().lower() in {"1", "true", "yes"}

    def _normalize_program_name_for_match(self, name):
        if not name:
            return ""

        text = str(name).upper()
        text = text.replace("(CO-OPERATIVE)", "")
        text = text.replace("CO-OPERATIVE", "")
        text = text.replace("(COOP)", "")
        text = text.replace("COOP", "")
        text = " ".join(text.split())

        return text

    def get_completed_course_records(self, user_id):
        conn = get_conn()

        rows = conn.execute("""
            SELECT *
            FROM completed_courses
            WHERE user_id = ?
        """, (user_id,)).fetchall()

        conn.close()

        records = {}

        for row in rows:
            records[row["course_code"]] = {
                "course_code": row["course_code"],
                "semester": row["semester"],
                "year": row["year"],
                "grade": row["grade"],
                "numeric_grade": row["numeric_grade"],
                "status": row["status"],
                "credits_earned": row["credits_earned"]
            }

        return records

    def get_completed_course_codes(self, user_id):
        completed_records = self.get_completed_course_records(user_id)

        completed_codes = []

        for course_code, row in completed_records.items():
            status = (row["status"] or "").upper()

            if status in ["COMPLETED", "TRANSFER"]:
                completed_codes.append(course_code)

        return completed_codes

    def _get_related_program_codes(self, program_code):
        selected_program = self.repo.get_program_by_code(program_code)

        if not selected_program:
            return [program_code]

        selected_program = dict(selected_program) if not isinstance(selected_program, dict) else selected_program

        all_programs = self.repo.get_all_programs()
        selected_name = self._normalize_program_name_for_match(selected_program.get("program_name"))
        selected_type = selected_program.get("program_type")
        selected_department_id = selected_program.get("department_id")

        related_codes = [program_code]

        for row in all_programs:
            program = dict(row) if not isinstance(row, dict) else row
            code = program.get("program_code")

            if not code or code == program_code:
                continue

            other_name = self._normalize_program_name_for_match(program.get("program_name"))

            if other_name != selected_name:
                continue

            if selected_type and program.get("program_type") != selected_type:
                continue

            if selected_department_id not in [None, "", "nan", "NaN"]:
                if program.get("department_id") != selected_department_id:
                    continue

            related_codes.append(code)

        seen = set()
        deduped = []

        for code in related_codes:
            if code not in seen:
                seen.add(code)
                deduped.append(code)

        return deduped

    def get_program_plan(self, user_id, program_code):
        program = self.repo.get_program_by_code(program_code)

        if not program:
            return None

        program = dict(program) if not isinstance(program, dict) else program

        completed_records = self.get_completed_course_records(user_id)
        completed_codes = self.get_completed_course_codes(user_id)
        completed_codes_set = set(completed_codes)

        planner_program_codes = self._get_related_program_codes(program_code)

        requirement_groups = []
        seen_group_ids = set()

        for code in planner_program_codes:
            groups_for_code = self.repo.get_program_requirement_groups(code)

            for group in groups_for_code:
                group_dict = dict(group) if not isinstance(group, dict) else group
                group_id = group_dict["group_id"]

                if group_id in seen_group_ids:
                    continue

                seen_group_ids.add(group_id)
                group_dict["source_program_code"] = code
                requirement_groups.append(group_dict)

        requirement_groups.sort(
            key=lambda g: (
                1 if str(g.get("category", "")).strip().upper() == "CO-OP" else 0,
                g.get("group_id", 0)
            )
        )

        all_groups = []
        total_required_groups = 0
        satisfied_required_groups = 0

        for group in requirement_groups:
            group_id = group["group_id"]
            group_courses = self.repo.get_program_requirement_courses(group_id)

            course_list = []

            for course_row in group_courses:
                course_row = dict(course_row) if not isinstance(course_row, dict) else course_row
                course_code = course_row["course_code"]
                course_info = self.repo.get_course_by_code(course_code)

                if not course_info:
                    continue

                course_info = dict(course_info) if not isinstance(course_info, dict) else course_info
                saved_record = completed_records.get(course_code)

                exclusion_rows = self.repo.get_course_exclusions(course_code)
                completed_by_exclusion_code = None

                for exclusion_row in exclusion_rows:
                    exclusion_row = dict(exclusion_row) if not isinstance(exclusion_row, dict) else exclusion_row
                    excluded_code = exclusion_row.get("excluded_course")

                    if excluded_code in completed_codes_set:
                        completed_by_exclusion_code = excluded_code
                        break

                is_direct_completed = course_code in completed_codes_set
                is_completed_by_exclusion = completed_by_exclusion_code is not None
                is_completed = is_direct_completed or is_completed_by_exclusion

                course_item = {
                    "course_code": course_info.get("course_code"),
                    "course_name": course_info.get("course_name"),
                    "credits": course_info.get("credits"),
                    "is_completed": is_completed,
                    "is_completed_by_exclusion": is_completed_by_exclusion,
                    "completed_by_exclusion_code": completed_by_exclusion_code,
                    "is_mandatory": course_row.get("is_mandatory"),
                    "notes": self._clean_text(course_row.get("notes")),
                    "saved_semester": saved_record["semester"] if saved_record else "",
                    "saved_year": saved_record["year"] if saved_record else "",
                    "saved_grade": saved_record["grade"] if saved_record else "",
                    "saved_numeric_grade": saved_record["numeric_grade"] if saved_record else ""
                }

                course_list.append(course_item)

            group_type = str(group.get("group_type") or "ALL").strip().upper()
            category = str(group.get("category") or "").strip().upper()

            completed_count = sum(1 for course in course_list if course["is_completed"])
            completed_credits = sum(
                self._credit_value(course["credits"])
                for course in course_list
                if course["is_completed"]
            )

            group_is_optional = (group_type == "OPTIONAL") or (category == "OPTIONAL")

            if group_is_optional:
                group_is_satisfied = True
                group_progress_text = "Optional group."
            elif group_type == "PICK":
                min_credits = group.get("min_credits")
                min_courses = group.get("min_courses")

                if min_credits not in [None, "", "nan", "NaN"]:
                    required_credits = self._credit_value(min_credits)
                    group_is_satisfied = completed_credits >= required_credits
                    group_progress_text = f"Need {required_credits:g} credits. Completed {min(completed_credits, required_credits):g}."
                elif min_courses not in [None, "", "nan", "NaN"]:
                    required_courses = int(float(min_courses))
                    group_is_satisfied = completed_count >= required_courses
                    group_progress_text = f"Need {required_courses} courses. Completed {min(completed_count, required_courses)}."
                else:
                    group_is_satisfied = completed_count > 0
                    group_progress_text = f"Completed {completed_count} courses."
            else:
                required_courses = len(course_list)
                group_is_satisfied = completed_count >= required_courses and required_courses > 0
                group_progress_text = f"Completed {completed_count} of {required_courses} courses."

            for course in course_list:
                course["is_optional_now"] = (
                    group_type == "PICK"
                    and group_is_satisfied
                    and not course["is_completed"]
                )

            if not group_is_optional:
                total_required_groups += 1

                if group_is_satisfied:
                    satisfied_required_groups += 1

            group_item = {
                "group_id": group.get("group_id"),
                "group_type": group.get("group_type"),
                "min_courses": group.get("min_courses"),
                "min_credits": group.get("min_credits"),
                "path_id": group.get("path_id"),
                "combined_group_id": group.get("combined_group_id"),
                "combined_min_credits": group.get("combined_min_credits"),
                "category": group.get("category"),
                "notes": self._clean_text(group.get("notes")),
                "source_program_code": group.get("source_program_code"),
                "group_is_optional": group_is_optional,
                "group_is_satisfied": group_is_satisfied,
                "group_progress_text": group_progress_text,
                "courses": course_list
            }

            all_groups.append(group_item)

        summary = {
            "total_groups": total_required_groups,
            "satisfied_groups": satisfied_required_groups,
            "remaining_groups": total_required_groups - satisfied_required_groups
        }

        return {
            "program": program,
            "summary": summary,
            "groups": all_groups
        }

    def get_course_details(self, course_code):
        course = self.repo.get_course_by_code(course_code)

        if not course:
            return None

        course = dict(course) if not isinstance(course, dict) else course

        past_offerings = self.repo.get_past_offerings(course_code)
        exclusions = self.repo.get_course_exclusions(course_code)
        requirement_groups = self.repo.get_requirement_groups_for_course(course_code)

        all_requirement_groups = []

        for group in requirement_groups:
            group = dict(group) if not isinstance(group, dict) else group
            group_id = group["group_id"]
            items = self.repo.get_requirement_items(group_id)

            item_list = []

            for item in items:
                item_list.append(dict(item) if not isinstance(item, dict) else item)

            group_item = {
                "group_id": group.get("group_id"),
                "req_type": group.get("req_type"),
                "group_logic": group.get("group_logic"),
                "path_id": group.get("path_id"),
                "items": item_list
            }

            all_requirement_groups.append(group_item)

        offering_list = []
        for row in past_offerings:
            offering_list.append(dict(row) if not isinstance(row, dict) else row)

        exclusion_list = []
        for row in exclusions:
            exclusion_list.append(dict(row) if not isinstance(row, dict) else row)

        return {
            "course": course,
            "past_offerings": offering_list,
            "exclusions": exclusion_list,
            "requirements": all_requirement_groups
        }
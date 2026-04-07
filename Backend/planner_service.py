from runtime_db import get_conn

#repo is the thing you passed in
#self.repo is where it gets stored in the object

class PlannerService:
    def __init__(self, repo):
        # Save the main database repository
        self.repo = repo

    def get_completed_course_codes(self, user_id):
        # Get all completed course codes for one user from the runtime database
        conn = get_conn()

        rows = conn.execute("""
            SELECT course_code
            FROM completed_courses
            WHERE user_id = ?
              AND status = 'COMPLETED'
        """, (user_id,)).fetchall()

        conn.close()

        completed_codes = []

        for row in rows:
            completed_codes.append(row["course_code"])

        return completed_codes

    def get_program_plan(self, user_id, program_code):
        # Get the selected program
        program = self.repo.get_program_by_code(program_code)

        if not program:
            return None

        # Get the courses this user already completed
        completed_codes = self.get_completed_course_codes(user_id)

        # Get all requirement blocks for the program
        requirement_groups = self.repo.get_program_requirement_groups(program_code)

        all_groups = []

        # Use a set so the same course is not counted twice in the summary
        all_course_codes = set()
        completed_course_codes = set()

        for group in requirement_groups:
            group_id = group["group_id"]

            # Get all courses in this requirement block
            group_courses = self.repo.get_program_requirement_courses(group_id)

            course_list = []

            for course_row in group_courses:
                course_code = course_row["course_code"]

                # Get the full course info
                course_info = self.repo.get_course_by_code(course_code)

                if course_info:
                    is_completed = course_code in completed_codes

                    all_course_codes.add(course_code)

                    if is_completed:
                        completed_course_codes.add(course_code)

                    course_item = {
                        "course_code": course_info["course_code"],
                        "course_name": course_info["course_name"],
                        "credits": course_info["credits"],
                        "is_completed": is_completed,
                        "is_mandatory": course_row["is_mandatory"],
                        "notes": course_row["notes"]
                    }

                    course_list.append(course_item)

            group_item = {
                "group_id": group["group_id"],
                "group_type": group["group_type"],
                "min_courses": group["min_courses"],
                "min_credits": group["min_credits"],
                "path_id": group["path_id"],
                "combined_group_id": group["combined_group_id"],
                "combined_min_credits": group["combined_min_credits"],
                "category": group["category"],
                "notes": group["notes"],
                "courses": course_list
            }

            all_groups.append(group_item)

        summary = {
            "total_courses": len(all_course_codes),
            "completed_courses": len(completed_course_codes),
            "remaining_courses": len(all_course_codes) - len(completed_course_codes)
        }

        return {
            "program": dict(program),
            "summary": summary,
            "groups": all_groups
        }

    def get_course_details(self, course_code):
        # Get the main course row
        course = self.repo.get_course_by_code(course_code)

        if not course:
            return None

        # Get past offerings
        past_offerings = self.repo.get_past_offerings(course_code)

        # Get exclusions
        exclusions = self.repo.get_course_exclusions(course_code)

        # Get prereq/coreq groups
        requirement_groups = self.repo.get_requirement_groups_for_course(course_code)

        all_requirement_groups = []

        for group in requirement_groups:
            group_id = group["group_id"]

            # Get all items in this requirement group
            items = self.repo.get_requirement_items(group_id)

            item_list = []

            for item in items:
                item_list.append(dict(item))

            group_item = {
                "group_id": group["group_id"],
                "req_type": group["req_type"],
                "group_logic": group["group_logic"],
                "path_id": group["path_id"],
                "items": item_list
            }

            all_requirement_groups.append(group_item)

        offering_list = []
        for row in past_offerings:
            offering_list.append(dict(row))

        exclusion_list = []
        for row in exclusions:
            exclusion_list.append(dict(row))

        return {
            "course": dict(course),
            "past_offerings": offering_list,
            "exclusions": exclusion_list,
            "requirements": all_requirement_groups
        }
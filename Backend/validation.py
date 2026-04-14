VALID_USER_PROGRAM_STATUSES = ["ACTIVE", "COMPLETED", "WITHDRAWN"]
VALID_COMPLETED_COURSE_STATUSES = ["COMPLETED", "IN_PROGRESS", "FAILED", "TRANSFER"]
VALID_SEMESTERS = ["FALL", "WINTER", "SUMMER"]
VALID_DELIVERY_TYPES = ["IN-PERSON", "ONLINE", "HYBRID"]
VALID_PROGRAM_GROUP_TYPES = ["ALL", "PICK", "CREDIT_LEVEL", "OPTIONAL"]
VALID_PROGRAM_CATEGORIES = ["REQUIRED", "ELECTIVE", "GRADUATION REQUIREMENT", "CO-OP", "OPTIONAL"]
VALID_REQ_TYPES = ["PREREQ", "COREQ"]
VALID_GROUP_LOGIC = ["AND", "OR"]
VALID_REQUIREMENT_ITEM_TYPES = [
    "COURSE",
    "MIN_CREDITS_TOTAL",
    "MIN_CREDITS_DEPT",
    "MIN_CGPA",
    "PROGRAM_ENROLLMENT",
    "YEAR_STANDING",
    "PERMISSION"
]
VALID_ENROLMENT_ITEM_TYPES = [
    "COURSE",
    "MIN_CREDITS_TOTAL",
    "MIN_CREDITS_DEPT",
    "MIN_CGPA"
]


def is_valid_email(email):
    if not email:
        return False

    email = email.strip()

    if email.count("@") != 1:
        return False

    parts = email.split("@")
    left_part = parts[0]
    right_part = parts[1]

    if left_part == "" or right_part == "":
        return False

    if "." not in right_part:
        return False

    if right_part[0] == "." or right_part[-1] == ".":
        return False

    return True


def is_valid_username(username):
    if not username:
        return False

    username = username.strip()

    if len(username) < 3:
        return False

    return True


def is_valid_password(password):
    if not password:
        return False

    password = password.strip()

    if len(password) < 6:
        return False

    return True


def is_valid_cgpa(cgpa):
    if cgpa is None or cgpa == "":
        return False

    try:
        cgpa = float(cgpa)
    except:
        return False

    if cgpa < 0.0 or cgpa > 4.0:
        return False

    return True


def is_valid_year_standing(year_standing):
    if year_standing is None or year_standing == "":
        return False

    try:
        year_standing = int(year_standing)
    except:
        return False

    if year_standing < 1 or year_standing > 4:
        return False

    return True


def normalize_course_code(course_code):
    if not course_code:
        return ""

    course_code = course_code.strip()
    course_code = course_code.upper()
    course_code = course_code.replace(" ", "")

    return course_code


# Check if course code looks valid
# Supports both:
# 1) MGAC03   -> 4 letters + 2 digits
# 2) ACMB10H3 -> 4 letters + 2 digits + 1 letter + 1 digit
def is_valid_course_code(course_code):
    course_code = normalize_course_code(course_code)

    # Case 1: MGAC03
    if len(course_code) == 6:
        if not course_code[:4].isalpha():
            return False
        if not course_code[4:].isdigit():
            return False
        return True

    # Case 2: ACMB10H3
    if len(course_code) == 8:
        if not course_code[:4].isalpha():
            return False
        if not course_code[4:6].isdigit():
            return False
        if not course_code[6].isalpha():
            return False
        if not course_code[7].isdigit():
            return False
        return True

    return False


def normalize_program_code(program_code):
    if not program_code:
        return ""

    program_code = program_code.strip()
    program_code = program_code.upper()
    program_code = program_code.replace(" ", "")

    return program_code


def is_valid_program_code(program_code):
    program_code = normalize_program_code(program_code)

    if program_code == "":
        return False

    if len(program_code) < 6:
        return False

    if not program_code.isalnum():
        return False

    return True


def is_valid_semester(semester):
    if not semester:
        return False

    semester = semester.strip().upper()

    if semester in VALID_SEMESTERS:
        return True

    return False


def is_valid_delivery_type(delivery):
    if not delivery:
        return False

    delivery = delivery.strip().upper()

    if delivery in VALID_DELIVERY_TYPES:
        return True

    return False


def is_valid_user_program_status(status):
    if not status:
        return False

    status = status.strip().upper()

    if status in VALID_USER_PROGRAM_STATUSES:
        return True

    return False


def is_valid_completed_course_status(status):
    if not status:
        return False

    status = status.strip().upper()

    if status in VALID_COMPLETED_COURSE_STATUSES:
        return True

    return False


def is_valid_credits_earned(credits_earned):
    if credits_earned is None or credits_earned == "":
        return False

    try:
        credits_earned = float(credits_earned)
    except:
        return False

    if credits_earned < 0:
        return False

    return True


def is_valid_year(year):
    if year is None or year == "":
        return False

    try:
        year = int(year)
    except:
        return False

    if year < 1900 or year > 2100:
        return False

    return True


def is_valid_program_group_type(group_type):
    if not group_type:
        return False

    group_type = group_type.strip().upper()

    if group_type in VALID_PROGRAM_GROUP_TYPES:
        return True

    return False


def is_valid_program_category(category):
    if not category:
        return False

    category = category.strip().upper()

    if category in VALID_PROGRAM_CATEGORIES:
        return True

    return False


def is_valid_req_type(req_type):
    if not req_type:
        return False

    req_type = req_type.strip().upper()

    if req_type in VALID_REQ_TYPES:
        return True

    return False


def is_valid_group_logic(group_logic):
    if not group_logic:
        return False

    group_logic = group_logic.strip().upper()

    if group_logic in VALID_GROUP_LOGIC:
        return True

    return False


def is_valid_requirement_item_type(item_type):
    if not item_type:
        return False

    item_type = item_type.strip().upper()

    if item_type in VALID_REQUIREMENT_ITEM_TYPES:
        return True

    return False


def is_valid_enrolment_item_type(item_type):
    if not item_type:
        return False

    item_type = item_type.strip().upper()

    if item_type in VALID_ENROLMENT_ITEM_TYPES:
        return True

    return False


def is_valid_min_credits(min_credits):
    if min_credits is None or min_credits == "":
        return False

    try:
        min_credits = float(min_credits)
    except:
        return False

    if min_credits < 0:
        return False

    return True


def is_valid_department_code(department_code):
    if not department_code:
        return False

    department_code = department_code.strip().upper()

    if len(department_code) < 2:
        return False

    if not department_code.isalpha():
        return False

    return True


def clean_course_list(course_list):
    cleaned_list = []

    for course in course_list:
        code = normalize_course_code(course)

        if is_valid_course_code(code):
            if code not in cleaned_list:
                cleaned_list.append(code)

    return cleaned_list
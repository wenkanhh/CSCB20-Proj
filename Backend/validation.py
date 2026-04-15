VALID_SEMESTERS = ["FALL", "WINTER", "SUMMER"]


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


def normalize_course_code(course_code):
    if not course_code:
        return ""

    course_code = course_code.strip()
    course_code = course_code.upper()
    course_code = course_code.replace(" ", "")

    return course_code


def is_valid_course_code(course_code):
    course_code = normalize_course_code(course_code)

    if len(course_code) == 6:
        if not course_code[:4].isalpha():
            return False
        if not course_code[4:].isdigit():
            return False
        return True

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
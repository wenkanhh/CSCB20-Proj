import pdfplumber
import pandas as pd
import re

PDF_FILES = [
    "UTSC_Calendar_2025-2026.pdf",
    "UTSC_Calendar_2024-2025.pdf"
]

BBA_PREFIXES = ["MGA", "MGT", "ECO", "MAT", "STA"]

# ===== CLEAN TEXT =====
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ===== PARSE COURSE =====
def parse_course(block):
    lines = block.strip().split("\n")
    if not lines:
        return None

    header = lines[0]

    match = re.match(r'([A-Z]{3,4}\d{2}H3)\s+(.*)', header)
    if not match:
        return None

    full_code, name = match.groups()

    prefix = full_code[:3]
    if prefix not in BBA_PREFIXES:
        return None

    details = clean_text(" ".join(lines[1:]))

    prereq = re.search(r'Prerequisite[s]?: (.*?)(?=Corequisite|Exclusion|$)', details)
    coreq = re.search(r'Corequisite[s]?: (.*?)(?=Prerequisite|Exclusion|$)', details)
    exclusion = re.search(r'Exclusion[s]?: (.*?)(?=Prerequisite|Corequisite|$)', details)

    return {
        "course_code": full_code,
        "course_prefix": prefix,
        "course_name": name.strip(),
        "course_details": details,
        "credits": 0.5,
        "prereq_text": prereq.group(1).strip() if prereq else "",
        "coreq_text": coreq.group(1).strip() if coreq else "",
        "exclusions": exclusion.group(1).strip() if exclusion else ""
    }

# ===== PROCESS PDF (SAFE, PAGE BY PAGE) =====
def process_pdfs(files):
    courses = []

    for file in files:
        print(f"Reading {file}...")

        with pdfplumber.open(file) as pdf:
            for i, page in enumerate(pdf.pages):
                if i % 20 == 0:
                    print(f"  Page {i}/{len(pdf.pages)}")

                text = page.extract_text()
                if not text:
                    continue

                blocks = re.split(r'\n(?=[A-Z]{3,4}\d{2}H3)', text)

                for block in blocks:
                    course = parse_course(block)
                    if course:
                        courses.append(course)

    return courses

# ===== BUILD PREREQ TABLES =====
def build_prereqs(courses):
    groups = []
    group_courses = []
    gid = 1

    for course in courses:
        text = course["prereq_text"]

        if not text:
            continue

        or_groups = re.split(r'\s+OR\s+', text)

        for group in or_groups:
            codes = re.findall(r'[A-Z]{3,4}\d{2}', group)

            if not codes:
                continue

            groups.append({
                "group_id": gid,
                "course_code": course["course_code"],
                "group_type": "AND",
                "req_type": "PREREQ",
                "raw_text": text
            })

            for c in codes:
                group_courses.append({
                    "group_id": gid,
                    "required_course_code": c
                })

            gid += 1

    return groups, group_courses

# ===== MAIN =====
def main():
    print("Processing PDFs...")
    courses = process_pdfs(PDF_FILES)

    print(f"Parsed {len(courses)} courses")

    df_courses = pd.DataFrame(courses)

    print("Building prerequisites...")
    groups, group_courses = build_prereqs(courses)

    df_groups = pd.DataFrame(groups)
    df_group_courses = pd.DataFrame(group_courses)

    # Drop temp fields
    df_courses_final = df_courses.drop(columns=["prereq_text", "coreq_text"])

    print("Saving CSVs...")

    df_courses_final.to_csv("courses.csv", index=False)
    df_groups.to_csv("prerequisite_groups.csv", index=False)
    df_group_courses.to_csv("prerequisite_courses.csv", index=False)

    print("Done ✅")

if __name__ == "__main__":
    main()
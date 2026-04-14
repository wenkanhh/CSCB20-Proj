import argparse
import csv
import shutil
from pathlib import Path

DATA_DIR = Path('data/data_cleaned')

def load_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def save_csv(path, rows, fieldnames):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def backup(path):
    bak = Path(str(path) + '.bak')
    shutil.copy2(path, bak)
    print(f'  backup → {bak.name}')

def section(title):
    print('\n' + '=' * 60)
    print(title)
    print('=' * 60)

def load_all():
    courses      = load_csv(DATA_DIR / 'courses.csv')
    req_groups   = load_csv(DATA_DIR / 'requirements_groups.csv')
    req_items    = load_csv(DATA_DIR / 'requirement_items.csv')
    exclusions   = load_csv(DATA_DIR / 'course_exclusions.csv')
    prog_reqs    = load_csv(DATA_DIR / 'program_requirement.csv')
    prog_req_crs = load_csv(DATA_DIR / 'program_requirement_courses.csv')
    return courses, req_groups, req_items, exclusions, prog_reqs, prog_req_crs

def run_checks(courses, req_groups, req_items, exclusions, prog_reqs, prog_req_crs):
    course_codes  = {r['course_code'] for r in courses}
    group_ids     = {r['group_id'] for r in req_groups}
    prog_req_ids  = {r['group_id'] for r in prog_reqs}

    section('DATASET SUMMARY')
    print(f'  Courses:                  {len(course_codes)}')
    print(f'  Prereq/coreq groups:      {len(req_groups)}')
    print(f'  Prereq/coreq items:       {len(req_items)}')
    print(f'  Course exclusions:        {len(exclusions)}')
    print(f'  Program req groups:       {len(prog_reqs)}')
    print(f'  Program req courses:      {len(prog_req_crs)}')

    issues = 0

    # 1. requirement_items → courses (COURSE type)
    section('1. PREREQ/COREQ ITEMS: broken course references')
    broken = [r for r in req_items
              if r['item_type'] == 'COURSE' and r['course_code'] not in course_codes]
    if broken:
        issues += len(broken)
        print(f'  {len(broken)} broken item(s):')
        for r in broken[:20]:
            print(f'    item_id={r["item_id"]}  group_id={r["group_id"]}  -> \'{r["course_code"]}\'')
        if len(broken) > 20:
            print(f'    ... and {len(broken) - 20} more')
    else:
        print('  OK — all COURSE items point to valid courses')

    # 2. requirement_items → group_id orphans
    section('2. PREREQ/COREQ ITEMS: orphaned group_id (no parent group)')
    orphan_items = [r for r in req_items if r['group_id'] not in group_ids]
    if orphan_items:
        issues += len(orphan_items)
        print(f'  {len(orphan_items)} orphaned item(s):')
        for r in orphan_items[:20]:
            print(f'    item_id={r["item_id"]}  group_id={r["group_id"]}')
    else:
        print('  OK — all items belong to a valid group')

    # 3. requirement_groups → courses
    section('3. PREREQ/COREQ GROUPS: broken course references')
    broken_groups = [r for r in req_groups if r['course_code'] not in course_codes]
    if broken_groups:
        issues += len(broken_groups)
        print(f'  {len(broken_groups)} broken group(s):')
        for r in broken_groups[:20]:
            print(f'    group_id={r["group_id"]}  -> \'{r["course_code"]}\'')
    else:
        print('  OK — all groups point to valid courses')

    # 4. course_exclusions → courses
    section('4. COURSE EXCLUSIONS: broken references')
    bad_main = [r for r in exclusions if r['course_code'] not in course_codes]
    bad_excl = [r for r in exclusions if r['excluded_course'] not in course_codes]
    if bad_main:
        issues += len(bad_main)
        print(f'  {len(bad_main)} exclusion(s) where course_code is unknown:')
        for r in bad_main[:15]:
            print(f'    \'{r["course_code"]}\' -> \'{r["excluded_course"]}\'')
    else:
        print('  OK — all course_code values are valid')
    if bad_excl:
        issues += len(bad_excl)
        print(f'  {len(bad_excl)} exclusion(s) where excluded_course is unknown:')
        for r in bad_excl[:15]:
            print(f'    \'{r["course_code"]}\' -> \'{r["excluded_course"]}\'')
    else:
        print('  OK — all excluded_course values are valid')

    # 5. program_requirement_courses → courses
    section('5. PROGRAM REQ COURSES: broken course references')
    bad_prc = [r for r in prog_req_crs if r['course_code'] not in course_codes]
    if bad_prc:
        issues += len(bad_prc)
        print(f'  {len(bad_prc)} broken reference(s):')
        for r in bad_prc[:20]:
            print(f'    group_id={r["group_id"]}  -> \'{r["course_code"]}\'')
        if len(bad_prc) > 20:
            print(f'    ... and {len(bad_prc) - 20} more')
    else:
        print('  OK — all program req courses point to valid courses')

    # 6. program_requirement_courses → program_requirements group_id
    section('6. PROGRAM REQ COURSES: orphaned group_id (no parent prog req)')
    orphan_prc = [r for r in prog_req_crs if r['group_id'] not in prog_req_ids]
    if orphan_prc:
        issues += len(orphan_prc)
        print(f'  {len(orphan_prc)} orphaned reference(s):')
        for r in orphan_prc[:20]:
            print(f'    id={r["id"]}  group_id={r["group_id"]}  course={r["course_code"]}')
    else:
        print('  OK — all program req courses have a valid parent group')

    # 7. coverage: courses with no prereq/coreq groups
    section('7. COVERAGE: courses that have NO prereq/coreq groups at all')
    courses_with_reqs = {r['course_code'] for r in req_groups}
    print(f'  Courses with req groups:    {len(courses_with_reqs)}')
    print(f'  Courses WITHOUT any reqs:   {len(course_codes - courses_with_reqs)}')

    # 8. coverage: program courses with no prereqs
    section('8. COVERAGE: courses that appear in program reqs but have no prereqs')
    courses_in_programs = {r['course_code'] for r in prog_req_crs}
    print(f'  Courses in program reqs:    {len(courses_in_programs)}')
    print(f'  Of those, with no prereqs:  {len(courses_in_programs - courses_with_reqs)}')

    # 9. exclusion symmetry
    section('9. EXCLUSION SYMMETRY: one-sided exclusion pairs')
    excl_pairs = {(r['course_code'], r['excluded_course']) for r in exclusions
                  if r['course_code'] in course_codes and r['excluded_course'] in course_codes}
    asymmetric = [(a, b) for (a, b) in excl_pairs if (b, a) not in excl_pairs]
    if asymmetric:
        print(f'  {len(asymmetric)} one-sided pair(s) (A excludes B but B doesn\'t exclude A):')
        for a, b in asymmetric[:20]:
            print(f'    {a} -> {b}  (no reverse)')
        if len(asymmetric) > 20:
            print(f'    ... and {len(asymmetric) - 20} more')
    else:
        print('  OK — all exclusions are symmetric')

    section('SUMMARY')
    if issues == 0:
        print('  All integrity checks passed.')
    else:
        print(f'  {issues} fixable issue(s) found. Run with --fix to resolve them.')

    return issues

def run_fixes(course_codes):
    section('FIX 1/3 — requirement_items: broken COURSE refs → PERMISSION')
    path = DATA_DIR / 'requirement_items.csv'
    rows = load_csv(path)
    fieldnames = list(rows[0].keys()) if rows else []
    fixed = 0
    for row in rows:
        if row['item_type'] == 'COURSE' and row['course_code'] not in course_codes:
            stale = row['course_code']
            existing = row.get('notes', '') or ''
            row['notes'] = f'Was COURSE: {stale}' + (f'; {existing}' if existing else '')
            row['item_type'] = 'PERMISSION'
            row['course_code'] = ''
            fixed += 1
    print(f'  Converted {fixed} item(s)')
    backup(path)
    save_csv(path, rows, fieldnames)
    print(f'  Saved {path.name}')

    section('FIX 2/3 — course_exclusions: drop rows with unknown excluded_course')
    path = DATA_DIR / 'course_exclusions.csv'
    rows = load_csv(path)
    fieldnames = list(rows[0].keys()) if rows else []
    kept = [r for r in rows if r['excluded_course'] in course_codes]
    print(f'  Dropped {len(rows) - len(kept)} row(s), kept {len(kept)}')
    backup(path)
    save_csv(path, kept, fieldnames)
    print(f'  Saved {path.name}')

    section('FIX 3/3 — program_requirement_courses: drop rows with unknown course_code')
    path = DATA_DIR / 'program_requirement_courses.csv'
    rows = load_csv(path)
    fieldnames = list(rows[0].keys()) if rows else []
    kept = [r for r in rows if r['course_code'] in course_codes]
    print(f'  Dropped {len(rows) - len(kept)} row(s), kept {len(kept)}')
    backup(path)
    save_csv(path, kept, fieldnames)
    print(f'  Saved {path.name}')

def main():
    parser = argparse.ArgumentParser(description='Check and optionally fix broken FK references in cleaned CSVs.')
    parser.add_argument('--fix', action='store_true', help='Auto-fix all broken references after checking')
    args = parser.parse_args()

    courses, req_groups, req_items, exclusions, prog_reqs, prog_req_crs = load_all()
    course_codes = {r['course_code'] for r in courses}

    issues = run_checks(courses, req_groups, req_items, exclusions, prog_reqs, prog_req_crs)

    if args.fix:
        if issues == 0:
            print('\nNothing to fix.')
        else:
            print('\nApplying fixes...')
            run_fixes(course_codes)
            print('\nRe-running checks after fix...')
            courses, req_groups, req_items, exclusions, prog_reqs, prog_req_crs = load_all()
            run_checks(courses, req_groups, req_items, exclusions, prog_reqs, prog_req_crs)

if __name__ == '__main__':
    main()

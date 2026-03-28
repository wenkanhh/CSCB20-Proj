import pandas as pd
import numpy as np
import re

print("=" * 80)
print("COMPREHENSIVE DATA VERIFICATION")
print("=" * 80)

# Load all CSVs
progs = pd.read_csv('programs.csv')
req = pd.read_csv('program_requirement.csv')
courses = pd.read_csv('program_requirement_courses.csv')
depts = pd.read_csv('departments.csv')
prefixes = pd.read_csv('department_prefixes.csv')
prog_req = req
prog_req_courses = courses

# ============================================================================
# 1. PROGRAM TYPE DISTRIBUTION
# ============================================================================
print("\n1. PROGRAM TYPE DISTRIBUTION:")
print("-" * 80)
type_counts = progs['program_type'].value_counts().sort_index()
print(type_counts)
print(f"\nTotal programs: {len(progs)}")

# ============================================================================
# 2. DOUBLE DEGREE PROGRAMS
# ============================================================================
print("\n2. DOUBLE DEGREE PROGRAMS:")
print("-" * 80)
doubles = progs[progs['program_type'] == 'Double']
print(f"Found {len(doubles)} Double Degree programs:")
if len(doubles) > 0:
    print(doubles[['program_name', 'program_code', 'program_type', 'is_coop']].to_string())
else:
    print("No Double Degree programs found")

# ============================================================================
# 3. MINOR PROGRAMS
# ============================================================================
print("\n3. MINOR PROGRAMS:")
print("-" * 80)
minors = progs[progs['program_type'] == 'Minor']
print(f"Found {len(minors)} MINOR programs")
print("Sample MINOR programs:")
if len(minors) > 0:
    print(minors[['program_name', 'program_code', 'program_type', 'department_id']].head(5).to_string())

# ============================================================================
# 4. MANAGEMENT PROGRAMS
# ============================================================================
print("\n4. MANAGEMENT PROGRAMS SAMPLE:")
print("-" * 80)
mgmt = progs[progs['program_name'].str.contains('MANAGEMENT.*BACHELOR', case=False, na=False, regex=True)]
print(f"Found {len(mgmt)} Management programs (BBA)")
if len(mgmt) > 0:
    print(mgmt[['program_name', 'program_code', 'program_type', 'department_id']].head(3).to_string())

# ============================================================================
# 5. DEPARTMENT ID COVERAGE
# ============================================================================
print("\n5. DEPARTMENT ID COVERAGE:")
print("-" * 80)
empty_dept = progs[progs['department_id'].isna() | (progs['department_id'].astype(str).str.strip()=='')]
print(f"Programs with empty department_id: {len(empty_dept)}")
if len(empty_dept) > 0:
    print("\nPrograms missing department_id:")
    print(empty_dept[['program_name', 'program_code', 'program_type']].to_string())
else:
    print("[OK] All programs have department_id populated")

# ============================================================================
# 6. DEPARTMENT ID VALIDATION
# ============================================================================
print("\n6. DEPARTMENT ID VALIDATION:")
print("-" * 80)
dept_ids = set(depts['department_id'].unique())
prog_dept_ids = set(progs['department_id'].dropna().unique())
invalid_depts = prog_dept_ids - dept_ids
if invalid_depts:
    print(f"WARNING: Programs have invalid department_ids: {invalid_depts}")
else:
    print(f"[OK] All program department_ids are valid (1-{max(dept_ids)})")

# ============================================================================
# 7. PROGRAM_REQUIREMENT CSV VALIDATION
# ============================================================================
print("\n7. PROGRAM_REQUIREMENT CSV VALIDATION:")
print("-" * 80)
print(f"Requirement columns: {list(req.columns)}")
print(f"Has group_name column: {'group_name' in req.columns}")
if 'group_name' in req.columns:
    print("WARNING: group_name column should not be present")
else:
    print("[OK] group_name column correctly removed")
print(f"Total requirement groups: {len(req)}")

# ============================================================================
# 8. PROGRAMS CSV VALIDATION
# ============================================================================
print("\n8. PROGRAMS CSV VALIDATION:")
print("-" * 80)
print(f"Programs columns: {list(progs.columns)}")
print(f"Has total_credits_required: {'total_credits_required' in progs.columns}")
if 'total_credits_required' in progs.columns:
    print("WARNING: total_credits_required column should not be present")
else:
    print("[OK] total_credits_required column correctly removed")
print(f"Has notes column: {'notes' in progs.columns}")
if 'notes' in progs.columns:
    print("WARNING: notes column was renamed to description")
else:
    print("[OK] notes column correctly renamed to description")

# ============================================================================
# 8b. NEW PROGRAMS CSV COLUMNS VALIDATION
# ============================================================================
print("\n8b. NEW PROGRAMS CSV COLUMNS:")
print("-" * 80)
print(f"Is_limited_enrolment values: {progs['is_limited_enrolment'].unique()}")
print(f"Programs with limited enrolment: {(progs['is_limited_enrolment'] == 1).sum()}")
print(f"Programs with non-null total_credits: {progs['total_credits'].notna().sum()}")
print(f"Programs with non-null min_enrolment_cgpa: {progs['min_enrolment_cgpa'].notna().sum()}")
print(f"Description field populated: {progs['description'].notna().sum()}/{len(progs)}")

# ============================================================================
# 9. REQUIREMENT COURSES VALIDATION
# ============================================================================
print("\n9. REQUIREMENT_COURSES CSV VALIDATION:")
print("-" * 80)
print(f"Courses columns: {list(courses.columns)}")
print(f"Total course requirements: {len(courses)}")
print(f"Unique course codes: {courses['course_code'].nunique()}")
print(f"All is_mandatory values are 1: {(courses['is_mandatory'] == 1).all()}")

# ============================================================================
# 10. CO-OP PROGRAMS
# ============================================================================
print("\n10. CO-OP PROGRAMS:")
print("-" * 80)
coop = progs[progs['is_coop'] == 1]
print(f"Total co-op programs: {len(coop)}")
print("Co-op program breakdown by type:")
print(coop['program_type'].value_counts().sort_index())

# ============================================================================
# 11. SAMPLE DATA FROM EACH TABLE
# ============================================================================
print("\n11. SAMPLE ROWS FROM EACH TABLE:")
print("-" * 80)
print("\nPrograms sample:")
print(progs[['program_code', 'program_name', 'program_type', 'is_coop']].head(3).to_string())
print("\nRequirements sample:")
print(req[['group_id', 'program_code', 'group_type', 'min_credits']].head(3).to_string())
print("\nCourses sample:")
print(courses[['id', 'group_id', 'course_code', 'is_mandatory']].head(3).to_string())

# ============================================================================
# 12. PROGRAM REQUIREMENT LOGIC VALIDATION
# ============================================================================
print("\n" + "=" * 80)
print("PROGRAM REQUIREMENT LOGIC VALIDATION")
print("=" * 80)

# Check valid group_types
print("\n12. GROUP_TYPE VALUES:")
print("-" * 80)
print("   Valid values: ALL, PICK, CREDIT_LEVEL, OPTIONAL")
group_types = prog_req['group_type'].unique()
print(f"   Found: {sorted([str(x) for x in group_types if pd.notna(x)])}")
invalid_types = [x for x in group_types if pd.notna(x) and x not in ['ALL', 'PICK', 'CREDIT_LEVEL', 'OPTIONAL']]
if invalid_types:
    print(f"   ❌ INVALID types found: {invalid_types}")
else:
    print("   ✓ All group_types are valid")

# Check min_courses only appears for PICK
print("\n13. MIN_COURSES VALIDATION:")
print("-" * 80)
min_courses_non_null = prog_req[prog_req['min_courses'].notna()]
pick_groups = prog_req[prog_req['group_type'] == 'PICK']
min_courses_in_pick = min_courses_non_null[min_courses_non_null['group_type'] == 'PICK']
min_courses_outside_pick = min_courses_non_null[min_courses_non_null['group_type'] != 'PICK']
print(f"   Total rows with min_courses: {len(min_courses_non_null)}")
print(f"   PICK groups total: {len(pick_groups)}")
print(f"   min_courses in PICK groups: {len(min_courses_in_pick)}")
if len(min_courses_outside_pick) > 0:
    print(f"   ❌ min_courses found in non-PICK groups: {len(min_courses_outside_pick)}")
    print("      Examples:")
    for idx, row in min_courses_outside_pick.head(3).iterrows():
        print(f"        group_id={row['group_id']}, group_type={row['group_type']}, min_courses={row['min_courses']}")
else:
    print("   ✓ min_courses only appears in PICK groups")

# Check min_credits only appears for PICK
print("\n14. MIN_CREDITS VALIDATION:")
print("-" * 80)
min_credits_non_null = prog_req[prog_req['min_credits'].notna()]
min_credits_in_pick = min_credits_non_null[min_credits_non_null['group_type'] == 'PICK']
min_credits_outside_pick = min_credits_non_null[min_credits_non_null['group_type'] != 'PICK']
print(f"   Total rows with min_credits: {len(min_credits_non_null)}")
print(f"   min_credits in PICK groups: {len(min_credits_in_pick)}")
if len(min_credits_outside_pick) > 0:
    print(f"   ❌ min_credits found in non-PICK groups: {len(min_credits_outside_pick)}")
    print("      Examples:")
    for idx, row in min_credits_outside_pick.head(3).iterrows():
        print(f"        group_id={row['group_id']}, group_type={row['group_type']}, min_credits={row['min_credits']}")
else:
    print("   ✓ min_credits only appears in PICK groups")

# Check category values
print("\n15. CATEGORY VALUES:")
print("-" * 80)
print("   Valid values: Required, Elective, Graduation Requirement, Co-op, Optional")
categories = prog_req['category'].unique()
print(f"   Found: {sorted([str(x) for x in categories if pd.notna(x)])}")
valid_categories = ['Required', 'Elective', 'Graduation Requirement', 'Co-op', 'Optional']
invalid_cats = [x for x in categories if pd.notna(x) and x not in valid_categories]
if invalid_cats:
    print(f"   ❌ INVALID categories found: {invalid_cats}")
else:
    print("   ✓ All categories are valid")

# Check program_code references
print("\n16. PROGRAM_CODE REFERENCES:")
print("-" * 80)
valid_prog_codes = set(progs['program_code'].dropna().unique())
req_prog_codes = prog_req[prog_req['program_code'].notna()]['program_code'].unique()
missing_prog_codes = [x for x in req_prog_codes if x not in valid_prog_codes]
if missing_prog_codes:
    print(f"   ❌ INVALID program_codes (not in programs.csv): {len(missing_prog_codes)}")
    print(f"      Examples: {missing_prog_codes[:5]}")
else:
    print("   ✓ All program_codes reference valid programs")

# Check combined_group_id logic
print("\n17. COMBINED_GROUP_ID LOGIC:")
print("-" * 80)
combined_groups = prog_req[prog_req['combined_group_id'].notna()]
print(f"   Groups with combined_group_id: {len(combined_groups)}")
if len(combined_groups) > 0:
    inconsistencies = 0
    for cgid in combined_groups['combined_group_id'].unique():
        rows_in_combined = prog_req[prog_req['combined_group_id'] == cgid]
        min_credits = rows_in_combined['combined_min_credits'].unique()
        if len(min_credits) > 1:
            inconsistencies += 1
            print(f"   ❌ combined_group_id={cgid} has inconsistent combined_min_credits: {min_credits}")
    if inconsistencies == 0:
        print("   ✓ All combined_group_ids have consistent combined_min_credits")
else:
    print("   ✓ No combined_group_ids (OK if not applicable)")

# Check path_id logic
print("\n18. PATH_ID LOGIC:")
print("-" * 80)
paths = prog_req[prog_req['path_id'].notna()]
print(f"   Groups with path_id: {len(paths)}")
if len(paths) > 0:
    for program_subset in prog_req['program_code'].unique():
        prog_paths = prog_req[(prog_req['program_code'] == program_subset) & (prog_req['path_id'].notna())]
        if len(prog_paths) > 0:
            path_ids = sorted([int(x) for x in prog_paths['path_id'].unique() if pd.notna(x)])
            print(f"   Program {program_subset}: path_ids = {path_ids}")
            break
else:
    print("   ✓ No path_ids (OK if not applicable)")

# Check group_id linkage to courses
print("\n19. GROUP_ID LINKAGE TO COURSES:")
print("-" * 80)
req_group_ids = set(prog_req['group_id'].unique())
course_group_ids = set(prog_req_courses['group_id'].unique())
orphan_req_groups = req_group_ids - course_group_ids
orphan_course_groups = course_group_ids - req_group_ids
print(f"   Total groups in program_requirement.csv: {len(req_group_ids)}")
print(f"   Total groups in program_requirement_courses.csv: {len(course_group_ids)}")
if orphan_req_groups:
    print(f"   ❌ NO COURSES: {len(orphan_req_groups)} groups have no courses")
    print(f"      Examples: {list(orphan_req_groups)[:5]}")
else:
    print("   ✓ All groups have courses")
if orphan_course_groups:
    print(f"   ❌ ORPHANED: {len(orphan_course_groups)} course groups not in requirements")
else:
    print("   ✓ No orphaned course groups")

# Additional data quality checks
print("\n20. DATA QUALITY CHECKS:")
print("-" * 80)
print(f"   Total requirement rows: {len(prog_req)}")
print(f"   Rows with group_id: {prog_req['group_id'].notna().sum()}")
print(f"   Rows with program_code: {prog_req['program_code'].notna().sum()}")
print(f"   Rows with group_type: {prog_req['group_type'].notna().sum()}")
print(f"   Rows with category: {prog_req['category'].notna().sum()}")
print(f"   Unique programs: {prog_req['program_code'].nunique()}")

# ============================================================================
# 21. LEGACY DATA LINKAGE VERIFICATION (requirements_groups.csv & requirement_items.csv)
# ============================================================================
print("\n" + "=" * 80)
print("LEGACY DATA LINKAGE VERIFICATION")
print("=" * 80)

# Check if legacy files exist
try:
    req_groups = pd.read_csv('requirements_groups.csv')
    req_items = pd.read_csv('requirement_items.csv')
    
    print('\n22. FINAL LINKAGE VERIFICATION:')
    print("-" * 80)
    groups_in_req_groups = set(req_groups['group_id'].unique())
    groups_in_req_items = set(req_items['group_id'].unique())
    
    common_groups = groups_in_req_groups & groups_in_req_items
    missing_in_items = groups_in_req_groups - groups_in_req_items
    
    print(f'Groups in requirements_groups.csv: {len(groups_in_req_groups)}')
    print(f'Groups in requirement_items.csv: {len(groups_in_req_items)}')
    print(f'Common groups (properly linked): {len(common_groups)}')
    print(f'Groups missing from requirement_items: {len(missing_in_items)}')
    print(f'Linkage success rate: {len(common_groups)/len(groups_in_req_groups)*100:.1f}%')
    
    print('\n23. SAMPLE LINKAGE:')
    print("-" * 80)
    sample_groups = req_groups.head(3)
    for _, group in sample_groups.iterrows():
        group_id = group['group_id']
        course_code = group['course_code']
        req_type = group['req_type']
    
        items = req_items[req_items['group_id'] == group_id]
        print(f'\nGroup {group_id}: {course_code} ({req_type}) - {len(items)} items')
        for _, item in items.iterrows():
            item_type = item['item_type']
            if item_type == 'COURSE':
                print(f'  - COURSE: {item["course_code"]}')
            elif item_type == 'MIN_CREDITS_TOTAL':
                print(f'  - MIN_CREDITS_TOTAL: {item["min_credits"]}')
            elif item_type == 'MIN_CGPA':
                print(f'  - MIN_CGPA: {item["min_cgpa"]}')
            elif item_type == 'PERMISSION':
                print(f'  - PERMISSION')
except FileNotFoundError:
    print("\n22-23. LEGACY DATA VERIFICATION:")
    print("-" * 80)
    print("Legacy CSV files (requirements_groups.csv, requirement_items.csv) not found - skipping linkage verification")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

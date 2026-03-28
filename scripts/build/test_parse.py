#!/usr/bin/env python3
"""
Unified test and verification suite for course parsing and data validation

This module consolidates:
- test_parse.py: Testing parser functionality from build_past_offerings.py
- verify.py: Comprehensive data verification for all CSV files
"""

import pandas as pd
import numpy as np
import re
import sys
from scripts.build.build_past_offerings import parse_fall_format


# ============================================================================
# PARSER TESTING FUNCTIONS
# ============================================================================

def test_parser():
    """
    Test the parse_fall_format function from build_past_offerings.py
    
    Prints:
    - Number of offerings extracted
    - First 10 offerings with course code, delivery type, and instructor
    - Delivery type distribution
    """
    print("\n" + "=" * 80)
    print("PARSER TESTING")
    print("=" * 80)
    
    filepath = r"c:\Users\admin\Documents\UNIVERSITY\UofT\Third year\CSCB20-Proj\data\data_raw\Course Timetable Fall 2025.txt"
    offerings = parse_fall_format(filepath, 2025)
    
    print(f"\nDirect call to parse_fall_format:")
    print(f"  Offerings returned: {len(offerings)}")
    
    if offerings:
        print(f"\nFirst 10 offerings:")
        for o in offerings[:10]:
            print(f"  {o['course_code']} | {o['delivery'][:12]:12} | {o['instructor'][:30]:30}")
        
        print(f"\nDelivery distribution:")
        delivery_count = {}
        for o in offerings:
            delivery_count[o['delivery']] = delivery_count.get(o['delivery'], 0) + 1
        for delivery, count in sorted(delivery_count.items()):
            print(f"  {delivery}: {count}")


# ============================================================================
# DATA VERIFICATION FUNCTIONS
# ============================================================================

def verify_comprehensive():
    """
    Comprehensive data verification for all CSV files
    
    Validates:
    - Program type distribution
    - Double degree and minor programs
    - Department ID coverage and validation
    - CSV structure and columns
    - Co-op program counts
    - Group type and category validation
    - Program code references
    - Group ID linkage to courses
    """
    print("\n" + "=" * 80)
    print("COMPREHENSIVE DATA VERIFICATION")
    print("=" * 80)
    
    # Load all CSVs
    progs = pd.read_csv('programs.csv')
    req = pd.read_csv('program_requirement.csv')
    courses = pd.read_csv('program_requirement_courses.csv')
    depts = pd.read_csv('departments.csv')
    prefixes = pd.read_csv('department_prefixes.csv')
    
    # ========================================================================
    # 1. PROGRAM TYPE DISTRIBUTION
    # ========================================================================
    print("\n1. PROGRAM TYPE DISTRIBUTION:")
    print("-" * 80)
    type_counts = progs['program_type'].value_counts().sort_index()
    print(type_counts)
    print(f"\nTotal programs: {len(progs)}")
    
    # ========================================================================
    # 2. DOUBLE DEGREE PROGRAMS
    # ========================================================================
    print("\n2. DOUBLE DEGREE PROGRAMS:")
    print("-" * 80)
    doubles = progs[progs['program_type'] == 'Double']
    print(f"Found {len(doubles)} Double Degree programs:")
    if len(doubles) > 0:
        print(doubles[['program_name', 'program_code', 'program_type', 'is_coop']].to_string())
    else:
        print("No Double Degree programs found")
    
    # ========================================================================
    # 3. MINOR PROGRAMS
    # ========================================================================
    print("\n3. MINOR PROGRAMS:")
    print("-" * 80)
    minors = progs[progs['program_type'] == 'Minor']
    print(f"Found {len(minors)} MINOR programs")
    print("Sample MINOR programs:")
    if len(minors) > 0:
        print(minors[['program_name', 'program_code', 'program_type', 'department_id']].head(5).to_string())
    
    # ========================================================================
    # 4. MANAGEMENT PROGRAMS
    # ========================================================================
    print("\n4. MANAGEMENT PROGRAMS SAMPLE:")
    print("-" * 80)
    mgmt = progs[progs['program_name'].str.contains('MANAGEMENT.*BACHELOR', case=False, na=False, regex=True)]
    print(f"Found {len(mgmt)} Management programs (BBA)")
    if len(mgmt) > 0:
        print(mgmt[['program_name', 'program_code', 'program_type', 'department_id']].head(3).to_string())
    
    # ========================================================================
    # 5. DEPARTMENT ID COVERAGE
    # ========================================================================
    print("\n5. DEPARTMENT ID COVERAGE:")
    print("-" * 80)
    empty_dept = progs[progs['department_id'].isna() | (progs['department_id'].astype(str).str.strip()=='')]
    print(f"Programs with empty department_id: {len(empty_dept)}")
    if len(empty_dept) > 0:
        print("\nPrograms missing department_id:")
        print(empty_dept[['program_name', 'program_code', 'program_type']].to_string())
    else:
        print("[OK] All programs have department_id populated")
    
    # ========================================================================
    # 6. DEPARTMENT ID VALIDATION
    # ========================================================================
    print("\n6. DEPARTMENT ID VALIDATION:")
    print("-" * 80)
    dept_ids = set(depts['department_id'].unique())
    prog_dept_ids = set(progs['department_id'].dropna().unique())
    invalid_depts = prog_dept_ids - dept_ids
    if invalid_depts:
        print(f"WARNING: Programs have invalid department_ids: {invalid_depts}")
    else:
        print(f"[OK] All program department_ids are valid (1-{max(dept_ids)})")
    
    # ========================================================================
    # 7. PROGRAM_REQUIREMENT CSV VALIDATION
    # ========================================================================
    print("\n7. PROGRAM_REQUIREMENT CSV VALIDATION:")
    print("-" * 80)
    print(f"Requirement columns: {list(req.columns)}")
    print(f"Has group_name column: {'group_name' in req.columns}")
    if 'group_name' in req.columns:
        print("WARNING: group_name column should not be present")
    else:
        print("[OK] group_name column correctly removed")
    print(f"Total requirement groups: {len(req)}")
    
    # ========================================================================
    # 8. PROGRAMS CSV VALIDATION
    # ========================================================================
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
    
    # ========================================================================
    # 8b. NEW PROGRAMS CSV COLUMNS VALIDATION
    # ========================================================================
    print("\n8b. NEW PROGRAMS CSV COLUMNS:")
    print("-" * 80)
    print(f"Is_limited_enrolment values: {progs['is_limited_enrolment'].unique()}")
    print(f"Programs with limited enrolment: {(progs['is_limited_enrolment'] == 1).sum()}")
    print(f"Programs with non-null total_credits: {progs['total_credits'].notna().sum()}")
    print(f"Programs with non-null min_enrolment_cgpa: {progs['min_enrolment_cgpa'].notna().sum()}")
    print(f"Description field populated: {progs['description'].notna().sum()}/{len(progs)}")
    
    # ========================================================================
    # 9. REQUIREMENT COURSES VALIDATION
    # ========================================================================
    print("\n9. REQUIREMENT_COURSES CSV VALIDATION:")
    print("-" * 80)
    print(f"Courses columns: {list(courses.columns)}")
    print(f"Total course requirements: {len(courses)}")
    print(f"Unique course codes: {courses['course_code'].nunique()}")
    print(f"All is_mandatory values are 1: {(courses['is_mandatory'] == 1).all()}")
    
    # ========================================================================
    # 10. CO-OP PROGRAMS
    # ========================================================================
    print("\n10. CO-OP PROGRAMS:")
    print("-" * 80)
    coop = progs[progs['is_coop'] == 1]
    print(f"Total co-op programs: {len(coop)}")
    print("Co-op program breakdown by type:")
    print(coop['program_type'].value_counts().sort_index())
    
    # ========================================================================
    # 11. SAMPLE DATA FROM EACH TABLE
    # ========================================================================
    print("\n11. SAMPLE ROWS FROM EACH TABLE:")
    print("-" * 80)
    print("\nPrograms sample:")
    print(progs[['program_code', 'program_name', 'program_type', 'is_coop']].head(3).to_string())
    print("\nRequirements sample:")
    print(req[['group_id', 'program_code', 'group_type', 'min_credits']].head(3).to_string())
    print("\nCourses sample:")
    print(courses[['id', 'group_id', 'course_code', 'is_mandatory']].head(3).to_string())
    
    # ========================================================================
    # 12. PROGRAM REQUIREMENT LOGIC VALIDATION
    # ========================================================================
    print("\n" + "=" * 80)
    print("PROGRAM REQUIREMENT LOGIC VALIDATION")
    print("=" * 80)
    
    # Check valid group_types
    print("\n12. GROUP_TYPE VALUES:")
    print("-" * 80)
    print("   Valid values: ALL, PICK, CREDIT_LEVEL, OPTIONAL")
    group_types = req['group_type'].unique()
    print(f"   Found: {sorted([str(x) for x in group_types if pd.notna(x)])}")
    invalid_types = [x for x in group_types if pd.notna(x) and x not in ['ALL', 'PICK', 'CREDIT_LEVEL', 'OPTIONAL']]
    if invalid_types:
        print(f"   INVALID types found: {invalid_types}")
    else:
        print("   All group_types are valid")
    
    # Check min_courses only appears for PICK
    print("\n13. MIN_COURSES VALIDATION:")
    print("-" * 80)
    min_courses_non_null = req[req['min_courses'].notna()]
    pick_groups = req[req['group_type'] == 'PICK']
    min_courses_in_pick = min_courses_non_null[min_courses_non_null['group_type'] == 'PICK']
    min_courses_outside_pick = min_courses_non_null[min_courses_non_null['group_type'] != 'PICK']
    print(f"   Total rows with min_courses: {len(min_courses_non_null)}")
    print(f"   PICK groups total: {len(pick_groups)}")
    print(f"   min_courses in PICK groups: {len(min_courses_in_pick)}")
    if len(min_courses_outside_pick) > 0:
        print(f"   min_courses found in non-PICK groups: {len(min_courses_outside_pick)}")
        print("      Examples:")
        for idx, row in min_courses_outside_pick.head(3).iterrows():
            print(f"        group_id={row['group_id']}, group_type={row['group_type']}, min_courses={row['min_courses']}")
    else:
        print("   min_courses only appears in PICK groups")
    
    # Check min_credits only appears for PICK
    print("\n14. MIN_CREDITS VALIDATION:")
    print("-" * 80)
    min_credits_non_null = req[req['min_credits'].notna()]
    min_credits_in_pick = min_credits_non_null[min_credits_non_null['group_type'] == 'PICK']
    min_credits_outside_pick = min_credits_non_null[min_credits_non_null['group_type'] != 'PICK']
    print(f"   Total rows with min_credits: {len(min_credits_non_null)}")
    print(f"   min_credits in PICK groups: {len(min_credits_in_pick)}")
    if len(min_credits_outside_pick) > 0:
        print(f"   min_credits found in non-PICK groups: {len(min_credits_outside_pick)}")
        print("      Examples:")
        for idx, row in min_credits_outside_pick.head(3).iterrows():
            print(f"        group_id={row['group_id']}, group_type={row['group_type']}, min_credits={row['min_credits']}")
    else:
        print("   min_credits only appears in PICK groups")
    
    # Check category values
    print("\n15. CATEGORY VALUES:")
    print("-" * 80)
    print("   Valid values: Required, Elective, Graduation Requirement, Co-op, Optional")
    categories = req['category'].unique()
    print(f"   Found: {sorted([str(x) for x in categories if pd.notna(x)])}")
    valid_categories = ['Required', 'Elective', 'Graduation Requirement', 'Co-op', 'Optional']
    invalid_cats = [x for x in categories if pd.notna(x) and x not in valid_categories]
    if invalid_cats:
        print(f"   INVALID categories found: {invalid_cats}")
    else:
        print("   All categories are valid")
    
    # Check program_code references
    print("\n16. PROGRAM_CODE REFERENCES:")
    print("-" * 80)
    valid_prog_codes = set(progs['program_code'].dropna().unique())
    req_prog_codes = req[req['program_code'].notna()]['program_code'].unique()
    missing_prog_codes = [x for x in req_prog_codes if x not in valid_prog_codes]
    if missing_prog_codes:
        print(f"   INVALID program_codes (not in programs.csv): {len(missing_prog_codes)}")
        print(f"      Examples: {missing_prog_codes[:5]}")
    else:
        print("   All program_codes reference valid programs")
    
    # Check group_id linkage to courses
    print("\n17. GROUP_ID LINKAGE TO COURSES:")
    print("-" * 80)
    req_group_ids = set(req['group_id'].unique())
    course_group_ids = set(courses['group_id'].unique())
    orphan_req_groups = req_group_ids - course_group_ids
    orphan_course_groups = course_group_ids - req_group_ids
    print(f"   Total groups in program_requirement.csv: {len(req_group_ids)}")
    print(f"   Total groups in program_requirement_courses.csv: {len(course_group_ids)}")
    if orphan_req_groups:
        print(f"   NO COURSES: {len(orphan_req_groups)} groups have no courses")
        print(f"      Examples: {list(orphan_req_groups)[:5]}")
    else:
        print("   All groups have courses")
    if orphan_course_groups:
        print(f"   ORPHANED: {len(orphan_course_groups)} course groups not in requirements")
    else:
        print("   No orphaned course groups")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for test and verification suite."""
    print("\n" + "=" * 80)
    print("TEST AND VERIFICATION SUITE")
    print("=" * 80)
    
    print("\nAvailable functions:")
    print("  1. test_parser        - Test parser functionality")
    print("  2. verify_comprehensive - Comprehensive data verification")
    print("  3. Run all tests")
    print("  0. Exit")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter choice (0-3): ").strip()
    
    try:
        if choice == '1':
            test_parser()
        elif choice == '2':
            verify_comprehensive()
        elif choice == '3':
            test_parser()
            verify_comprehensive()
        elif choice == '0':
            print("Exiting...")
            return 0
        else:
            print("Invalid choice")
            return 1
    
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 80)
    print("TEST AND VERIFICATION COMPLETE")
    print("=" * 80 + "\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())

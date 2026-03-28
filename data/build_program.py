"""
UNIFIED PROGRAM BUILDER
Consolidates all program data building into one comprehensive script.
This script parses program data from data_raw/programs.txt and generates:
- program_requirement.csv: requirement groups for each program
- program_requirement_courses.csv: individual course assignments to groups
- enrolment_requirements.csv: enrolment conditions for each program

Usage:
    python build_program.py              # Build all files
    python build_program.py --preview    # Preview raw data sample before building
"""

import re
import pandas as pd
from collections import defaultdict
import sys
import argparse

# ============================================================================
# CONFIGURATION
# ============================================================================
INPUT_FILE = 'data_raw/programs.txt'
OUTPUT_REQ_FILE = 'program_requirement.csv'
OUTPUT_COURSES_FILE = 'program_requirement_courses.csv'
OUTPUT_ENROL_FILE = 'enrolment_requirements.csv'

# Choose parsing strategy: 'v2' (two-pass, recommended), 'v1' (numbered sections), 'enhanced' (with collections)
PARSING_STRATEGY = 'v2'

# Build options
BUILD_PROGRAM_REQUIREMENTS = True
BUILD_ENROLMENT_REQUIREMENTS = True

# ============================================================================
# LOAD SOURCE DATA
# ============================================================================
print("Loading source data...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Validate program codes
programs_df = pd.read_csv('programs.csv')
valid_prog_codes = set(programs_df['program_code'].dropna().unique())

# ============================================================================
# PARSING HELPER FUNCTIONS
# ============================================================================

def extract_program_code(heading):
    """Extract program code from heading line."""
    program_code = ''
    
    # Try pattern like "NAME - CODE"
    if ' - ' in heading:
        parts = heading.split(' - ')
        code_part = parts[-1].strip()
        m = re.search(r'([A-Z]{2}[A-Z0-9]+(?:[A-Z])?)\s*$', code_part)
        if m:
            program_code = m.group(1).upper()
    
    # Fallback pattern
    if not program_code:
        m = re.match(r'^(?:CERTIFICATE|MAJOR|SPECIALIST).*?-\s*([A-Z0-9]+)\s*$', heading, re.IGNORECASE)
        if m:
            program_code = m.group(1)
    
    return program_code

def find_requirements_section(section_text):
    """Find and extract the requirements body from a program section."""
    req_start_patterns = [
        r'Program Requirements\s*\n',
        r'Certificate Requirements\s*\n',
        r'Academic Program Requirements\s*\n'
    ]
    
    req_match = None
    for pattern in req_start_patterns:
        m = re.search(pattern, section_text, re.IGNORECASE)
        if m:
            req_match = m
            break
    
    if not req_match:
        return None
    
    req_start = req_match.end()
    calendar_match = re.search(r'\nCalendar Section:', section_text)
    req_end = calendar_match.start() if calendar_match else len(section_text)
    
    return section_text[req_start:req_end]

def parse_heading(heading_text):
    """Determine group properties from heading text."""
    heading_lower = heading_text.lower()
    
    # Group type determination
    group_type = 'ALL'
    if any(kw in heading_lower for kw in ['choose from', 'select from', 'one of the following', 'from the following']):
        group_type = 'PICK'
    elif re.search(r'at least.*(?:credit|credits).*at the\s+[CD]-level|[CD]-\s*&\s*[CD]-level', heading_text, re.IGNORECASE):
        group_type = 'CREDIT_LEVEL'
    elif any(kw in heading_lower for kw in ['optional', 'encouraged']):
        group_type = 'OPTIONAL'
    elif re.search(r'\d+\.\d+\s+credit.*from.*(?:bin|option|list)', heading_text, re.IGNORECASE):
        group_type = 'PICK'
    
    # Extract min_credits
    min_credits = None
    credits_match = re.search(r'([\d\.]+)\s+(?:credit|credits|FCE)', heading_text, re.IGNORECASE)
    if credits_match:
        min_credits = float(credits_match.group(1))
    
    # Extract min_courses
    min_courses = None
    course_count_match = re.search(r'(?:choose|select)\s+(\d+)\s+(?:course|courses)', heading_text, re.IGNORECASE)
    if course_count_match and group_type == 'PICK':
        min_courses = float(course_count_match.group(1))
    
    # Category determination
    category = 'Required'
    if any(kw in heading_lower for kw in ['elective', 'bin', 'choose']):
        category = 'Elective'
    elif any(kw in heading_lower for kw in ['co-op', 'work term', 'cop']):
        category = 'Co-op'
    elif any(kw in heading_lower for kw in ['optional', 'research', 'directed']):
        category = 'Optional'
    elif re.search(r'graduation|cr/ncr|cr ncr', heading_lower):
        category = 'Graduation Requirement'
    
    return {
        'group_type': group_type,
        'min_credits': min_credits,
        'min_courses': min_courses,
        'category': category
    }

def is_heading(line):
    """Check if a line is a section heading."""
    if re.match(r'^\d+\.\s+', line):
        return True
    if re.match(r'^[A-Z]\.\s+', line):
        return True
    if re.search(r'Bin\s+\d+:', line, re.IGNORECASE):
        return True
    if re.search(r'Choose\s+from|Select\s+from', line, re.IGNORECASE):
        return True
    if re.search(r'Required|Elective|Core|Co-op|Work Term|Preparation|Graduation', line, re.IGNORECASE) \
            and not re.match(r'^\s*[A-Z]{3,4}\d{2}[HY]\d', line):
        return True
    return False

def extract_courses(text):
    """Extract course codes from text."""
    courses = re.findall(r'\b([A-Z]{3,4}\d{2}[HY]\d)\b', text)
    # Dedupe while preserving order
    seen = set()
    unique_courses = []
    for c in courses:
        if c not in seen:
            seen.add(c)
            unique_courses.append(c)
    return unique_courses

# ============================================================================
# ENROLMENT REQUIREMENTS PARSING FUNCTIONS
# ============================================================================

def parse_enrolment_requirements(content, valid_prog_codes):
    """
    Parse enrolment requirements from program blocks.
    Returns list of enrolment requirement rows.
    """
    enrolment_reqs = []
    group_id = 1
    
    # Split program blocks by "Calendar Section:"
    calendars = list(re.finditer(r'^Calendar Section:(.*)$', content, flags=re.MULTILINE))
    blocks = []
    start = 0
    for cal in calendars:
        block = content[start:cal.start()].strip()
        if block:
            blocks.append(block)
        start = cal.end()
    blocks.append(content[start:].strip())
    
    print(f"  Processing {len(blocks)} program blocks for enrolment requirements...")
    
    for block in blocks:
        if not block.strip():
            continue
        
        lines = block.split('\n')
        heading = lines[0].strip() if lines else ''
        
        # Extract program_code from heading
        program_code = extract_program_code(heading)
        
        # Skip if no valid program code
        if not program_code or program_code not in valid_prog_codes:
            continue
        
        sec = '\n'.join(lines)
        
        # Find "Enrolment Requirements" section
        enrol_req_match = re.search(
            r'Enrolment Requirements\s*\n(.+?)(?=\n(?:[A-Z][a-z]+ (?:Requirement|Program)|Certificate|Admission|Calendar Section:|$))',
            sec, re.IGNORECASE | re.DOTALL
        )
        
        if not enrol_req_match:
            continue
        
        enrol_req_section = enrol_req_match.group(1).strip()
        
        # Parse each requirement line
        for line in enrol_req_section.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Pattern: Minimum CGPA requirement (e.g., "CGPA of x.x" or "GPA of x.x")
            cgpa_match = re.search(r'(?:CGPA|GPA|average GPA)\s+(?:of\s+)?(\d+\.\d+|\d+)', line, re.IGNORECASE)
            if cgpa_match:
                min_cgpa = float(cgpa_match.group(1))
                enrolment_reqs.append({
                    'group_id': group_id,
                    'program_code': program_code,
                    'req_category': 'ENROLMENT',
                    'item_type': 'MIN_CGPA',
                    'course_code': None,
                    'min_credits': None,
                    'max_credits': None,
                    'department_id': None,
                    'min_cgpa': min_cgpa,
                    'notes': line
                })
                group_id += 1
            
            # Pattern: Minimum total credits (e.g., "at least X credits", "X.0 credits completed")
            if not cgpa_match:
                total_credits_match = re.search(r'(?:at least|minimum|complete)\s+(\d+(?:\.\d+)?)\s+credit', line, re.IGNORECASE)
                if total_credits_match:
                    min_credits = float(total_credits_match.group(1))
                    # Check if there's a max credits mentioned
                    max_match = re.search(r'(?:(?:to|through)\s+)?(?:a maximum of|up to|maximum)\s+(\d+(?:\.\d+)?)\s+credit', line, re.IGNORECASE)
                    max_credits = float(max_match.group(1)) if max_match else None
                    
                    enrolment_reqs.append({
                        'group_id': group_id,
                        'program_code': program_code,
                        'req_category': 'ENROLMENT',
                        'item_type': 'MIN_CREDITS_TOTAL',
                        'course_code': None,
                        'min_credits': min_credits,
                        'max_credits': max_credits,
                        'department_id': None,
                        'min_cgpa': None,
                        'notes': line
                    })
                    group_id += 1
            
            # Pattern: Specific course requirement (e.g., "must have completed CSCA20H3")
            course_codes = extract_courses(line)
            for course_code in course_codes:
                enrolment_reqs.append({
                    'group_id': group_id,
                    'program_code': program_code,
                    'req_category': 'ENROLMENT',
                    'item_type': 'COURSE',
                    'course_code': course_code,
                    'min_credits': None,
                    'max_credits': None,
                    'department_id': None,
                    'min_cgpa': None,
                    'notes': line
                })
                group_id += 1
            
            # Pattern: Department-specific credits (e.g., "X.0 credits in [Department/subject]")
            if not course_codes:
                dept_credits_match = re.search(r'(\d+(?:\.\d+)?)\s+credit.*?(?:in|from|of)\s+([A-Za-z\s]+?)(?:\s+(?:course|program|subject|prerequisite))?(?:\s*\(or|or\s+|$|\.)', line, re.IGNORECASE)
                if dept_credits_match:
                    min_credits = float(dept_credits_match.group(1))
                    dept_text = dept_credits_match.group(2).strip()
                    
                    enrolment_reqs.append({
                        'group_id': group_id,
                        'program_code': program_code,
                        'req_category': 'ENROLMENT',
                        'item_type': 'MIN_CREDITS_DEPT',
                        'course_code': None,
                        'min_credits': min_credits,
                        'max_credits': None,
                        'department_id': None,
                        'min_cgpa': None,
                        'notes': line
                    })
                    group_id += 1
            
            # Pattern: Program enrollment requirement
            program_pattern = re.search(r'(?:enrolled in|admission to|registered in|member of)\s+(?:the|a|any)?\s+([A-Za-z\s]+?)(?:\s+program)?(?:\s*\.|\s*$)', line, re.IGNORECASE)
            if program_pattern and not any([cgpa_match, total_credits_match, course_codes, dept_credits_match]):
                # Only add if no other type was already matched
                program_desc = program_pattern.group(1).strip()
                enrolment_reqs.append({
                    'group_id': group_id,
                    'program_code': program_code,
                    'req_category': 'ENROLMENT',
                    'item_type': 'PROGRAM_ENROLLMENT',
                    'course_code': None,
                    'min_credits': None,
                    'max_credits': None,
                    'department_id': None,
                    'min_cgpa': None,
                    'notes': line
                })
                group_id += 1
    
    return enrolment_reqs
def parse_programs_v2(content):
    """
    Two-pass parsing approach:
    Pass 1: Find all section headings and their line indices
    Pass 2: Process each section and attach courses between headings
    """
    requirements = []
    req_courses = []
    group_id = 1
    course_row_id = 1
    
    # Split program blocks by "Calendar Section:"
    calendars = list(re.finditer(r'^Calendar Section:(.*)$', content, flags=re.MULTILINE))
    blocks = []
    start = 0
    for cal in calendars:
        block = content[start:cal.start()].strip()
        if block:
            blocks.append(block)
        start = cal.end()
    blocks.append(content[start:].strip())
    
    print(f"Processing {len(blocks)} program blocks...")
    
    for block_idx, block in enumerate(blocks):
        if not block.strip():
            continue
        
        lines = block.split('\n')
        heading = lines[0].strip() if lines else ''
        
        # Extract program code
        program_code = extract_program_code(heading)
        
        # Skip if no valid program code
        if not program_code or program_code not in valid_prog_codes:
            continue
        
        sec = '\n'.join(lines)
        
        # Find requirements section
        req_body = find_requirements_section(sec)
        if not req_body:
            continue
        
        req_lines = req_body.split('\n')
        
        # Pass 1: Find all headings
        headings_list = []
        
        for line_idx, raw_line in enumerate(req_lines):
            line = raw_line.strip()
            if not line or not is_heading(line):
                continue
            
            heading_props = parse_heading(line)
            headings_list.append({
                'line_idx': line_idx,
                'heading_text': line,
                **heading_props
            })
        
        # Pass 2: Process each heading and collect courses
        for i, heading_info in enumerate(headings_list):
            start_line = heading_info['line_idx'] + 1
            end_line = headings_list[i + 1]['line_idx'] if i + 1 < len(headings_list) else len(req_lines)
            
            # Collect courses in this section
            courses_in_section = []
            for j in range(start_line, end_line):
                if j >= len(req_lines):
                    break
                line = req_lines[j].strip()
                courses = extract_courses(line)
                courses_in_section.extend(courses)
            
            # Dedupe while preserving order
            unique_courses = extract_courses(' '.join(courses_in_section))
            
            # Only create group if it has courses
            if unique_courses:
                requirements.append({
                    'group_id': group_id,
                    'program_code': program_code,
                    'group_type': heading_info['group_type'],
                    'min_courses': heading_info['min_courses'],
                    'min_credits': heading_info['min_credits'],
                    'path_id': None,
                    'combined_group_id': None,
                    'combined_min_credits': None,
                    'category': heading_info['category'],
                    'notes': heading_info['heading_text'][:200]
                })
                
                # Add courses for this group
                for course_code in unique_courses:
                    req_courses.append({
                        'id': course_row_id,
                        'group_id': group_id,
                        'course_code': course_code,
                        'is_mandatory': 1 if heading_info['group_type'] in ['ALL', 'CREDIT_LEVEL'] else 0,
                        'notes': None
                    })
                    course_row_id += 1
                
                group_id += 1
    
    return requirements, req_courses

# ============================================================================
# PREVIEW FUNCTION
# ============================================================================

def preview_data(content):
    """
    Display a sample from the raw data to preview structure.
    Finds and displays the first SPECIALIST program section.
    """
    print("=" * 80)
    print("DATA PREVIEW: First SPECIALIST Program Section")
    print("=" * 80)
    
    match = re.search(r'(SPECIALIST.*?(?=\nCalendar Section:|$))', content, re.DOTALL | re.IGNORECASE)
    if match:
        section = match.group(1)
        preview_text = section[:3000]
        print(preview_text)
        remaining = len(section) - len(preview_text)
        if remaining > 0:
            print(f"\n... ({remaining} more characters)")
    else:
        print("No SPECIALIST program found in data")
    
    print("\n" + "=" * 80)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Build program, requirement, and enrolment CSVs from raw program data'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview raw data sample before building'
    )
    parser.add_argument(
        '--no-requirements',
        action='store_true',
        help='Skip building program requirements'
    )
    parser.add_argument(
        '--no-enrolment',
        action='store_true',
        help='Skip building enrolment requirements'
    )
    
    args = parser.parse_args()
    
    # Override build options based on CLI args
    global BUILD_PROGRAM_REQUIREMENTS, BUILD_ENROLMENT_REQUIREMENTS
    if args.no_requirements:
        BUILD_PROGRAM_REQUIREMENTS = False
    if args.no_enrolment:
        BUILD_ENROLMENT_REQUIREMENTS = False
    
    # Preview mode
    if args.preview:
        preview_data(content)
        return
    
    print(f"\nUsing parsing strategy: {PARSING_STRATEGY}")

    # Build program requirements
    if BUILD_PROGRAM_REQUIREMENTS:
        print("\n" + "=" * 80)
        print("BUILDING PROGRAM REQUIREMENTS")
        print("=" * 80)
        
        if PARSING_STRATEGY == 'v2':
            requirements, req_courses = parse_programs_v2(content)
        else:
            print(f"Strategy '{PARSING_STRATEGY}' not implemented. Using 'v2'.")
            requirements, req_courses = parse_programs_v2(content)
        
        reqs_df = pd.DataFrame(requirements)
        courses_df = pd.DataFrame(req_courses)
        
        # Replace empty strings with NaN
        reqs_df = reqs_df.replace('', None)
        courses_df = courses_df.replace('', None)
        
        # Write to CSV
        reqs_df.to_csv(OUTPUT_REQ_FILE, index=False)
        courses_df.to_csv(OUTPUT_COURSES_FILE, index=False)
        
        print(f"\n[OK] Created {OUTPUT_REQ_FILE}")
        print(f"  - Total requirement groups: {len(requirements)}")
        print(f"  - Programs processed: {reqs_df['program_code'].nunique()}")
        
        print(f"\n[OK] Created {OUTPUT_COURSES_FILE}")
        print(f"  - Total course assignments: {len(req_courses)}")

    # Build enrolment requirements
    if BUILD_ENROLMENT_REQUIREMENTS:
        print("\n" + "=" * 80)
        print("BUILDING ENROLMENT REQUIREMENTS")
        print("=" * 80)
        
        enrolment_reqs = parse_enrolment_requirements(content, valid_prog_codes)
        
        enrol_df = pd.DataFrame(enrolment_reqs)
        enrol_df = enrol_df.replace('', None)
        enrol_df.to_csv(OUTPUT_ENROL_FILE, index=False)
        
        print(f"\n[OK] Created {OUTPUT_ENROL_FILE}")
        print(f"  - Total enrolment requirements: {len(enrolment_reqs)}")
        print(f"  - Programs with requirements: {enrol_df['program_code'].nunique()}")

    # ============================================================================
    # SUMMARY AND REPORTING
    # ============================================================================

    print("\n" + "=" * 80)
    print("BUILD SUMMARY")
    print("=" * 80)

    if BUILD_PROGRAM_REQUIREMENTS:
        print(f"\nGroup Type Distribution:")
        for gtype, count in sorted(reqs_df['group_type'].value_counts().items()):
            print(f"  {gtype:15} : {count:4} groups")
        
        print(f"\nCategory Distribution:")
        for cat, count in sorted(reqs_df['category'].value_counts().items()):
            print(f"  {cat:25} : {count:4} groups")
        
        print(f"\nSample Program Requirement Groups:")
        for idx, row in reqs_df.head(10).iterrows():
            courses_count = len(courses_df[courses_df['group_id'] == row['group_id']])
            print(f"  Group {row['group_id']:3} | {row['program_code']:15} | {row['category']:25} | {row['group_type']:12} | {courses_count:2} courses")

    if BUILD_ENROLMENT_REQUIREMENTS:
        print(f"\nEnrolment Requirement Types:")
        for itype, count in sorted(enrol_df['item_type'].value_counts().items()):
            print(f"  {itype:20} : {count:4} requirements")
        
        print(f"\nSample Enrolment Requirements:")
        for idx, row in enrol_df.head(5).iterrows():
            print(f"  Group {row['group_id']:3} | {row['program_code']:15} | {row['item_type']:20} | Notes: {str(row['notes'])[:50]}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()

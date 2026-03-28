import re
import pandas as pd
import os

path = 'data_raw/programs.txt'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Load departments and prefixes mapping
depts_df = pd.read_csv('departments.csv')
dept_map = dict(zip(depts_df['department_name'], depts_df['department_id']))

prefixes_df = pd.read_csv('department_prefixes.csv')
# Build mapping from prefix_description to department_id
prefix_to_dept = {}
for idx, row in prefixes_df.iterrows():
    desc = str(row['prefix_description']).strip()
    dept_id = row['department_id']
    if desc and desc != 'nan':
        prefix_to_dept[desc] = dept_id

# Load programs limitations mapping
limitations_path = 'data_raw/programs_limitations.txt'
limitations_map = {}
try:
    with open(limitations_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip header rows and empty lines
            if not line or line.startswith('Program Name') or line.startswith('Deregulated') or re.match(r'^[A-Z]$', line):
                continue
            # Parse tab-separated values
            parts = [p.strip() for p in line.split('\t')]
            if len(parts) >= 3:
                # ACORN code is typically the last or second-to-last column
                acorn_code = parts[-1].strip() if parts[-1].strip() != 'Y' else (parts[-2].strip() if len(parts) > 2 else '')
                status = parts[1].strip() if len(parts) > 1 else ''
                if acorn_code:
                    limitations_map[acorn_code] = 1 if status == 'Limited' else 0
except:
    pass

# Split program blocks by Calendar Section delimiters
calendars = list(re.finditer(r'^Calendar Section:(.*)$', content, flags=re.MULTILINE))
blocks = []
block_sections = []
start = 0
for cal in calendars:
    block = content[start:cal.start()].strip()
    if block:
        blocks.append(block)
        # Extract calendar section name
        section_line = cal.group(1).strip()
        block_sections.append(section_line)
    start = cal.end()
# optionally add trailing block item
if start < len(content):
    tail = content[start:].strip()
    if tail:
        blocks.append(tail)
        block_sections.append('')

programs = []
requirements = []
req_courses = []

group_id = 1
course_row_id = 1

for sec, calendar_section in zip(blocks, block_sections):
    lines = [l.strip() for l in sec.splitlines() if l.strip()]
    if not lines:
        continue
    heading = lines[0].strip()
    program_name = heading
    program_code = ''
    is_limited_enrolment = 0
    is_coop = 0
    total_credits = ''
    min_enrolment_cgpa = ''
    description = ''
    department_id = ''
    program_type = 'Program'

    # Extract program_name + program_code from last hyphen-separated suffix
    if ' - ' in heading:
        left, right = heading.rsplit(' - ', 1)
        program_name = left.strip()
        program_code = right.strip().upper()

    # Determine type from normalized program_name
    normalized = program_name.upper()
    if normalized.startswith('CERTIFICATE IN'):
        program_type = 'Certificate'
    elif normalized.startswith('COMBINED DEGREE PROGRAMS'):
        program_type = 'Combined'
    elif normalized.startswith('DOUBLE DEGREE'):
        program_type = 'Double'
    elif 'MINOR' in normalized:
        program_type = 'Minor'
    elif 'SPECIALIST' in normalized:
        program_type = 'Specialist'
    elif 'MAJOR' in normalized:
        program_type = 'Major'

    # coop detection (cooperative programs)
    if re.search(r'CO-?OPERATIVE|CO-?OP|COOP', normalized):
        is_coop = 1

    # Map department_id from calendar section using prefix_description lookup
    if calendar_section:
        # Handle multi-department sections like "Dept1, Dept2" by checking first part
        dept_name = calendar_section.split(',')[0].strip()
        if dept_name in prefix_to_dept:
            department_id = prefix_to_dept[dept_name]
        elif dept_name in dept_map:
            department_id = dept_map[dept_name]

    # Fallback: map department_id from program name patterns for edge cases
    if not department_id:
        norm_name = program_name.upper()
        if 'MANAGEMENT' in norm_name or 'FINANCE' in norm_name or 'ACCOUNTING' in norm_name or 'HUMAN RESOURCES' in norm_name or 'ECONOMICS FOR MANAGEMENT' in norm_name:
            department_id = 11
        elif 'JOURNALISM' in norm_name or 'MUSIC' in norm_name or 'MEDIA' in norm_name or 'NEW MEDIA' in norm_name or 'ARTS MANAGEMENT' in norm_name:
            department_id = 2
        elif 'PARAMEDICINE' in norm_name or 'SOCIAL WORK' in norm_name:
            department_id = 7
        elif 'ANTHROPOLOGY' in norm_name:
            department_id = 1
        elif 'DEVELOPMENT' in norm_name and 'GLOBAL' in norm_name:
            department_id = 6
        elif 'ENGLISH' in norm_name:
            department_id = 5
        elif 'PSYCHOLOGY' in norm_name:
            department_id = 15
        elif 'STATISTICS' in norm_name or 'QUANTITATIVE' in norm_name:
            department_id = 4
        elif 'SUSTAINABILITY' in norm_name or 'ENVIRONMENT' in norm_name:
            department_id = 13
        elif 'PHYSICS' in norm_name or 'ASTROPHYSICS' in norm_name:
            department_id = 13  # Physical and Environmental Sciences
        elif 'PUBLIC LAW' in norm_name or 'PUBLIC POLICY' in norm_name:
            department_id = 14  # Political Science
        elif 'GLOBAL LEADERSHIP' in norm_name:
            department_id = 9  # Human Geography

    # Use limitations map to set is_limited_enrolment based on program_code
    if program_code and program_code in limitations_map:
        is_limited_enrolment = limitations_map[program_code]


    # Certificate-specific fallbacks (for security) if code is not set by dash split
    if program_type == 'Certificate' and not program_code:
        m = re.match(r'^CERTIFICATE IN\s+(.+?)\s*-\s*([A-Z0-9]+)\s*$', heading, re.IGNORECASE)
        if m:
            program_name = m.group(1).strip()
            program_code = m.group(2).strip().upper()
        else:
            m2 = re.match(r'^CERTIFICATE IN\s+(.+?)\s*-\s*([A-Z0-9 ]+)\s*$', heading, re.IGNORECASE)
            if m2:
                program_name = m2.group(1).strip()
                program_code = re.sub(r'[^A-Z0-9]+', '', m2.group(2).strip().upper())
            else:
                program_name = heading.replace('CERTIFICATE IN ', '').strip()


    # attempt to get first content lines for description
    note_lines = []
    for line in lines[1:10]:
        if line.strip():
            note_lines.append(line.strip())
        if len(note_lines) >= 3:
            break
    description = ' '.join(note_lines)

    # Extract is_limited_enrolment - check if text mentions limited enrolment
    if re.search(r'limited\s+enrolment|limited\s+enrollment|enrolment\s+limited|enrollment\s+limited|restricted\s+enrolment', sec, re.IGNORECASE):
        is_limited_enrolment = 1

    # find total credits phrase - search within "Program Requirements" section first
    # Look for "Program Requirements" section
    prog_req_match = re.search(r'Program Requirements\s*\n(.+?)(?=\n(?:Calendar Section:|$))', sec, re.IGNORECASE | re.DOTALL)
    if prog_req_match:
        prog_req_section = prog_req_match.group(1)
        # Search for patterns like "This program requires the completion of X.X credits" or "This Program consists of X.X credits"
        total_match = re.search(r'(?:This\s+[Pp]rogram\s+)?(?:requires\s+(?:the\s+)?completion\s+(?:of\s+)?|consists\s+of\s+)([\d\.]+)\s+credits', prog_req_section, re.IGNORECASE)
        if total_match:
            total_credits = total_match.group(1)
    
    # If still not found, try searching the entire section
    if not total_credits:
        total_match = re.search(r'(?:This\s+[Pp]rogram\s+)?(?:requires\s+(?:the\s+)?completion\s+(?:of\s+)?|consists\s+of\s+)([\d\.]+)\s+credits', sec, re.IGNORECASE)
        if total_match:
            total_credits = total_match.group(1)

    # Extract min_enrolment_cgpa - search in multiple places
    # For co-op programs, prioritize co-op CGPA requirements
    if is_coop == 1:
        # Priority 1 (co-op): Check for "Cumulative GPA" or "Cumulative CGPA" (co-op qualifications format)
        cgpa_match = re.search(r'Cumulative GPA[:\s]+([\d\.]+)|Cumulative CGPA[:\s]+([\d\.]+)', sec, re.IGNORECASE)
        if cgpa_match:
            min_enrolment_cgpa = cgpa_match.group(1) or cgpa_match.group(2)
        else:
            # Priority 2 (co-op): Check for maintenance CGPA
            cgpa_match = re.search(r'maintain a CGPA of ([\d\.]+)', sec, re.IGNORECASE)
            if cgpa_match:
                min_enrolment_cgpa = cgpa_match.group(1)
            else:
                # Priority 3 (co-op): Check for admission/enrolment CGPA
                cgpa_match = re.search(r'(?:with a |)minimum cumulative (?:grade point average )?(?:\()?CGPA(?:\))? of at least ([\d\.]+)', sec, re.IGNORECASE)
                if cgpa_match:
                    min_enrolment_cgpa = cgpa_match.group(1)
                else:
                    # Priority 4 (co-op): Check for "students must achieve" pattern
                    cgpa_match = re.search(r'students must achieve a minimum CGPA of ([\d\.]+)', sec, re.IGNORECASE)
                    if cgpa_match:
                        min_enrolment_cgpa = cgpa_match.group(1)
    else:
        # For non-co-op programs, use standard priority order
        # Priority 1: Check for maintenance CGPA (In order to remain in the Program)
        cgpa_match = re.search(r'maintain a CGPA of ([\d\.]+)', sec, re.IGNORECASE)
        if cgpa_match:
            min_enrolment_cgpa = cgpa_match.group(1)
        else:
            # Priority 2: Check for admission/enrolment CGPA
            cgpa_match = re.search(r'(?:with a |)minimum cumulative (?:grade point average )?(?:\()?CGPA(?:\))? of at least ([\d\.]+)', sec, re.IGNORECASE)
            if cgpa_match:
                min_enrolment_cgpa = cgpa_match.group(1)
            else:
                # Priority 3: Check for "students must achieve" pattern
                cgpa_match = re.search(r'students must achieve a minimum CGPA of ([\d\.]+)', sec, re.IGNORECASE)
                if cgpa_match:
                    min_enrolment_cgpa = cgpa_match.group(1)
                else:
                    # Priority 4: Check for "Cumulative GPA" (typically co-op qualifications format)
                    cgpa_match = re.search(r'Cumulative GPA[:\s]+([\d\.]+)|Cumulative CGPA[:\s]+([\d\.]+)', sec, re.IGNORECASE)
                    if cgpa_match:
                        min_enrolment_cgpa = cgpa_match.group(1) or cgpa_match.group(2)
                    # If no CGPA found anywhere, leave as empty string

    programs.append({
        'program_code': program_code,
        'program_name': program_name,
        'department_id': department_id,
        'program_type': program_type,
        'is_coop': is_coop,
        'is_limited_enrolment': is_limited_enrolment,
        'total_credits': total_credits,
        'min_enrolment_cgpa': min_enrolment_cgpa,
        'description': description
    })

    # Identify course codes in the section
    course_codes = re.findall(r'\b([A-Z]{3,4}\d{2}[HY]\d)\b', sec)
    # preserve order and dedupe
    seen = set()
    final_codes = []
    for c in course_codes:
        if c not in seen:
            seen.add(c)
            final_codes.append(c)

    # create one requirement group per program if any course codes exist
    if final_codes:
        # For ALL groups: don't populate min_credits or min_courses (per README spec)
        # min_credits and min_courses are only for PICK groups where student chooses options
        requirements.append({
            'group_id': group_id,
            'program_code': program_code,
            'group_type': 'ALL',
            'min_courses': None,
            'min_credits': None,
            'path_id': None,
            'combined_group_id': None,
            'combined_min_credits': None,
            'category': 'Required',
            'notes': ''
        })

        for c in final_codes:
            req_courses.append({
                'id': course_row_id,
                'group_id': group_id,
                'course_code': c,
                'is_mandatory': 1,
                'notes': ''
            })
            course_row_id += 1

        group_id += 1

# write files with proper file handling
progs_df = pd.DataFrame(programs)
reqs_df = pd.DataFrame(requirements)
courses_df = pd.DataFrame(req_courses)

# Remove old files if they exist
for fname in ['programs.csv', 'program_requirement.csv', 'program_requirement_courses.csv']:
    try:
        if os.path.exists(fname):
            os.remove(fname)
    except:
        pass

progs_df.to_csv('programs.csv', index=False)
reqs_df.to_csv('program_requirement.csv', index=False)
courses_df.to_csv('program_requirement_courses.csv', index=False)

print('Created programs.csv with', len(programs), 'rows')
print('Created program_requirement.csv with', len(requirements), 'rows')
print('Created program_requirement_courses.csv with', len(req_courses), 'rows')

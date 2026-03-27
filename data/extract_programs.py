import re
import pandas as pd

path = 'data_raw/programs.txt'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Load departments mapping
depts_df = pd.read_csv('departments.csv')
dept_map = dict(zip(depts_df['department_name'], depts_df['department_id']))

# Map calendar section names to department_ids (handles variations and aliases)
calendar_to_dept_id = {
    'Anthropology': 1,
    'Anthropology, Arts and Science Co-op': 1,
    'Anthropology, Certificates': 1,
    'Arts and Science Co-op, Anthropology': 1,
    'African Studies': 8,  # Historical and Cultural Studies
    'Art History and Visual Culture': 8,  # Historical and Cultural Studies
    'Arts Management': 2,  # Arts Culture and Media
    'Astronomy': 13,  # Physical and Environmental Sciences
    'Biological Sciences': 3,
    'Biological Sciences, Arts and Science Co-op': 3,
    'Biological Sciences, Certificates': 3,
    'Chemistry': 13,  # Physical and Environmental Sciences
    'Chemistry, Arts and Science Co-op': 13,
    'Classical Studies': 8,  # Historical and Cultural Studies
    'City Studies': 9,  # Human Geography
    'City Studies, Arts and Science Co-op': 9,
    'Climate Change Studies': 13,  # Physical and Environmental Sciences
    'Computer Science': 4,  # Computer and Mathematical Sciences
    'Computer Science, Arts and Science Co-op': 4,
    'English': 5,
    'English, Arts and Science Co-op': 5,
    'Environmental Science': 13,  # Physical and Environmental Sciences
    'Environmental Science, Arts and Science Co-op': 13,
    'Environmental Studies': 13,  # Physical and Environmental Sciences
    'Food Studies': 13,  # Physical and Environmental Sciences
    'French': 10,  # Language Studies
    'French, Arts and Science Co-op': 10,
    'Geography': 9,  # Human Geography
    'Global Asia Studies': 2,  # Arts Culture and Media
    'Global Leadership': 9,  # Human Geography
    'Health and Society': 7,
    'Health and Society, Arts and Science Co-op': 7,
    'Health and Society, Certificates': 7,
    'History': 8,  # Historical and Cultural Studies
    'History, Arts and Science Co-op': 8,
    'International Development Studies': 6,  # Global Development Studies
    'Languages': 10,  # Language Studies
    'Linguistics': 10,  # Language Studies
    'Linguistics, Arts and Science Co-op': 10,
    'Management': 11,
    'Management, Certificates': 11,
    'Management, Management Co~op': 11,
    'Mathematics': 4,  # Computer and Mathematical Sciences
    'Mathematics, Arts and Science Co-op': 4,
    'Media Studies': 2,  # Arts Culture and Media
    'Music': 2,  # Arts Culture and Media
    'Neuroscience': 15,  # Psychology
    'Neuroscience, Arts and Science Co-op': 15,
    'Philosophy': 12,
    'Philosophy, Arts and Science Co-op': 12,
    'Physical Sciences': 13,  # Physical and Environmental Sciences
    'Physics and Astrophysics': 13,  # Physical and Environmental Sciences
    'Physics and Astrophysics, Arts and Science Co-op': 13,
    'Political Science': 14,
    'Psychology': 15,
    'Psychology, Arts and Science Co-op': 15,
    'Public Law': 14,  # Political Science
    'Public Policy': 14,  # Political Science
    'Public Policy, Arts and Science Co-op': 14,
    'Sociology': 16,
    'Sociology, Certificates': 16,
    'Statistics': 4,  # Computer and Mathematical Sciences
    'Statistics, Arts and Science Co-op': 4,
    'Studio Art': 2,  # Arts Culture and Media
    'Theatre and Performance': 2,  # Arts Culture and Media
    'Women\'s and Gender Studies': 8,  # Historical and Cultural Studies
    'Women\'s and Gender Studies, Arts and Science Co-op': 8,
}

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
    its_coop = 0
    department_id = ''
    program_type = 'Program'
    total_credits = ''
    notes = ''

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
    elif 'MINOR' in normalized:
        program_type = 'Minor'
    elif 'SPECIALIST' in normalized:
        program_type = 'Specialist'
    elif 'MAJOR' in normalized:
        program_type = 'Major'

    # coop detection (cooperative programs)
    if re.search(r'CO-?OPERATIVE|CO-?OP|COOP', normalized):
        its_coop = 1

    # Map department_id from calendar section using lookup table
    if calendar_section:
        dept_name = calendar_section.split(',')[0].strip()  # handle "Dept, Certificates" format
        if dept_name in calendar_to_dept_id:
            department_id = calendar_to_dept_id[dept_name]
        elif dept_name in dept_map:
            department_id = dept_map[dept_name]

    # Fallback: map department_id from program name patterns for joint/combined programs
    if not department_id:
        norm_name = program_name.upper()
        if 'MANAGEMENT' in norm_name or 'FINANCE' in norm_name or 'ACCOUNTING' in norm_name or 'HUMAN RESOURCES' in norm_name:
            department_id = 11
        elif 'JOURNALISM' in norm_name or 'MUSIC' in norm_name or 'MEDIA' in norm_name or 'NEW MEDIA' in norm_name or 'ARTS MANAGEMENT' in norm_name:
            department_id = 2
        elif 'PARAMEDICINE' in norm_name or 'SOCIAL WORK' in norm_name:
            department_id = 7
        elif 'ANTHROPOLOGY' in norm_name:
            department_id = 1
        elif 'DEVELOPMENT' in norm_name or 'GLOBAL' in norm_name:
            department_id = 6
        elif 'ENGLISH' in norm_name:
            department_id = 5
        elif 'PSYCHOLOGY' in norm_name:
            department_id = 15
        elif 'STATISTICS' in norm_name or 'QUANTITATIVE' in norm_name:
            department_id = 4
        elif 'SUSTAINABILITY' in norm_name or 'ENVIRONMENT' in norm_name:
            department_id = 13


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


    # attempt to get first content lines for notes
    note_lines = []
    for line in lines[1:10]:
        if line.strip():
            note_lines.append(line.strip())
        if len(note_lines) >= 3:
            break
    notes = ' '.join(note_lines)

    # find total credits phrase
    total_match = re.search(r'minimum of ([\d\.]+) credits', sec, re.IGNORECASE)
    if not total_match:
        total_match = re.search(r'total of ([\d\.]+) credits', sec, re.IGNORECASE)
    if total_match:
        total_credits = total_match.group(1)
    else:
        # try a broader search for credit numbers nearest first list
        total_match = re.search(r'complete.*?([\d\.]+) credits', sec, re.IGNORECASE)
        if total_match:
            total_credits = total_match.group(1)

    programs.append({
        'program_code': program_code,
        'program_name': program_name,
        'department_id': department_id,
        'program_type': program_type,
        'its_coop': its_coop,
        'total_credits_required': total_credits,
        'notes': notes
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
        # short block name heuristics
        min_credits = total_credits
        # if there is an explicit first list with "1.", "2." etc, we leave as ALL
        requirements.append({
            'group_id': group_id,
            'program_code': program_code,
            'group_type': 'ALL',
            'min_courses': '',
            'min_credits': min_credits,
            'path_id': '',
            'combined_group_id': '',
            'combined_min_credits': '',
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

# write files
pd.DataFrame(programs).to_csv('programs.csv', index=False)
pd.DataFrame(requirements).to_csv('program_requirement.csv', index=False)
pd.DataFrame(req_courses).to_csv('program_requirement_courses.csv', index=False)

print('Created programs.csv with', len(programs), 'rows')
print('Created program_requirement.csv with', len(requirements), 'rows')
print('Created program_requirement_courses.csv with', len(req_courses), 'rows')

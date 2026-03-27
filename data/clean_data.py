import re
import pandas as pd
from html.parser import HTMLParser
import html

class CourseExtractor:
    """Extracts course information from HTML course data"""
    
    def __init__(self):
        self.courses = {}
        self.prerequisites = {}
        
    def clean_html(self, text):
        """Remove HTML tags and decode HTML entities"""
        # Decode HTML entities
        text = html.unescape(text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_course_code(self, text):
        """Extract course code from text like 'ACMB10H3: Course Name'
        
        course_code_prefix: first 3 characters (e.g., 'ACM' from 'ACMB10H3')
        course_code: exclude last 2 characters (e.g., 'ACMB10' from 'ACMB10H3')
        offering_code: letter (A-D) + two digits (e.g., 'B10' from 'ACMB10H3')
        course_name: text before the first <p> tag
        """
        # Extract course code and name from header
        match = re.match(r'([A-Z0-9]+)\s*:\s*(.*)', text.strip())
        if not match:
            return None
        
        full_code = match.group(1).strip()
        header_name = match.group(2).strip()
        
        # Remove last 2 characters (H3, Y3, etc.) to get clean course code
        course_code = full_code[:-2]  # Remove last 2 characters
        
        # Extract prefix (first 3 characters) and offering code (letter + 2 digits)
        prefix = course_code[:3]  # First 3 characters
        offering = course_code[3:]  # Everything after first 3 (letter + digits)
        
        # Course name: take header name, or split at first <p>
        if '<p>' in header_name.lower():
            course_name = header_name.split('<p>')[0].strip()
        else:
            course_name = header_name.strip()
        
        return {
            'course_code': course_code,
            'course_prefix': prefix,
            'offering_code': offering,
            'course_name': course_name
        }
    
    def extract_field(self, text, pattern, group=1):
        """Extract a field using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(group)
            return self.clean_html(content).strip()
        return None
    
    def parse_course_block(self, block):
        """Parse a course block from the text"""
        lines = block.strip().split('\n', 1)
        if not lines:
            return None
        
        header = lines[0]
        body = lines[1] if len(lines) > 1 else ""
        
        # Extract course code and name
        course_info = self.extract_course_code(header)
        if not course_info:
            return None
        
        # Full raw text includes header + body
        full_text = header + body
        
        # Extract course description: between "<p>Course Description</p><p>" and next "</p>"
        course_details = ""
        desc_match = re.search(
            r'<p>\s*Course Description\s*</p>\s*<p>(.*?)</p>',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        if desc_match:
            course_details = self.clean_html(desc_match.group(1))
        
        # Extract prerequisite: after "</p><p>Prerequisite</p>Prerequisite:" and before next "<p>"
        prerequisites = ""
        prereq_match = re.search(
            r'</p>\s*<p>\s*Prerequisite\s*</p>\s*Prerequisite\s*:\s*(.*?)<p>',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        if prereq_match:
            prerequisites = self.clean_html(prereq_match.group(1))
        
        # Extract corequisite: after "<p>Corequisite</p>Corequisite:" and before next "<p>"
        corequisites = ""
        coreq_match = re.search(
            r'<p>\s*Corequisite\s*</p>\s*Corequisite\s*:\s*(.*?)<p>',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        if coreq_match:
            corequisites = self.clean_html(coreq_match.group(1))
        
        # Extract exclusion: after "<p>Exclusion</p>Exclusion:" and before next "<p>"
        exclusions = ""
        excl_match = re.search(
            r'<p>\s*Exclusion\s*</p>\s*Exclusion\s*:\s*(.*?)<p>',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        if excl_match:
            exclusions = self.clean_html(excl_match.group(1))
        
        # Extract breadth requirements: after "<p>Breadth Requirements</p>Breadth Requirements:" and before next span or div or p
        breadth = ""
        breadth_match = re.search(
            r'<p>\s*Breadth Requirements\s*</p>\s*Breadth Requirements\s*:\s*(.*?)(?=</span>|<div|<p|$)',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        if breadth_match:
            breadth = self.clean_html(breadth_match.group(1))
        
        # Extract course experience: after "Course Experience:" and before next "</span>" or "<p>" or "<div>"
        course_experience = ""
        exp_match = re.search(
            r'Course Experience\s*:\s*(.*?)(?=</span>|<p>|<div|$)',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        if exp_match:
            course_experience = self.clean_html(exp_match.group(1))
        
        # Extract note: after "<p>Note</p>Note:" and before next "</span>"
        note = ""
        note_match = re.search(
            r'<p>\s*Note\s*</p>\s*Note\s*:\s*(.*?)</span>',
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        if note_match:
            note = self.clean_html(note_match.group(1))
        
        # Extract course link: prefer ttb.utoronto.ca link (timetable), otherwise get last href
        course_link = ""
        # First try to find timetable link (ttb.utoronto.ca/cp/)
        ttb_match = re.search(
            r'href\s*=\s*["\']?\s*(https?://ttb\.utoronto\.ca/cp/[^"\'>]+)',
            full_text,
            re.IGNORECASE
        )
        if ttb_match:
            course_link = ttb_match.group(1).strip()
        else:
            # If no timetable link, get the last href
            all_hrefs = re.findall(
                r'href\s*=\s*["\']?\s*([^"\'>]+)',
                full_text,
                re.IGNORECASE
            )
            if all_hrefs:
                course_link = all_hrefs[-1].strip()
        
        return {
            'course_code': course_info['course_code'],
            'course_prefix': course_info['course_prefix'],
            'offering_code': course_info['offering_code'],
            'course_name': course_info['course_name'],
            'course_details': course_details,
            'credits': 0.5,  # Default for H3 courses
            'prerequisites': prerequisites,
            'corequisites': corequisites,
            'exclusions': exclusions,
            'breadth_requirements': breadth,
            'course_experience': course_experience,
            'note': note,
            'course_link': course_link
        }
    
    def parse_file(self, filepath):
        """Parse courses from sample_courses.txt"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by course codes (pattern: CODE##[A-Z]#: Name)
        course_blocks = re.split(
            r'(?=^[A-Z]{3,4}\d{2}[A-Z]\d\s*:)',
            content,
            flags=re.MULTILINE
        )
        
        for block in course_blocks:
            if not block.strip():
                continue
            
            course = self.parse_course_block(block)
            if course:
                self.courses[course['course_code']] = course
        
        return self.courses
    
    def save_courses_csv(self, output_path):
        """Save courses to clean CSV file"""
        df = pd.DataFrame([
            {
                'course_code': c['course_code'],
                'course_code_prefix': c['course_prefix'],
                'offering_code': c['offering_code'],
                'course_name': c['course_name'],
                'course_details': c['course_details'],
                'credits': c['credits'],
                'prerequisites': c['prerequisites'],
                'corequisites': c['corequisites'],
                'exclusions': c['exclusions'],
                'breadth_requirements': c['breadth_requirements'],
                'course_experience': c['course_experience'],
                'note': c['note'],
                'course_link': c['course_link']
            }
            for c in self.courses.values()
        ])
        
        df = df.sort_values('course_code')
        df.to_csv(output_path, index=False)
        return df
    
    def parse_requirement_logic(self, requirement_text):
        """
        Parse requirement text to detect AND/OR logic and split into paths.
        Returns list of tuples: (group_logic, path_id)
        """
        if not requirement_text:
            return []
        
        # Normalize text for easier parsing
        text = requirement_text.lower().strip()
        
        # Detect if this contains OR logic (alternative paths)
        # Look for standalone "or" surrounded by spaces or at boundaries
        or_pattern = r'\s+or\s+|\s+or$|^or\s+'
        has_or = bool(re.search(or_pattern, text))
        
        # If it contains OR, split into paths
        if has_or:
            # Split by "or" to get individual paths
            or_split = re.split(or_pattern, text)
            or_split = [part.strip() for part in or_split if part.strip()]
            
            # Each path is an alternative, so each gets its own path_id
            results = []
            for path_idx, path_text in enumerate(or_split, start=1):
                # Within each path, check for AND logic
                has_and = bool(re.search(r'\s+and\s+', path_text))
                group_logic = 'AND' if has_and else 'OR'
                results.append((group_logic, path_idx))
            return results
        else:
            # Single path - check for AND logic within it
            has_and = bool(re.search(r'\s+and\s+', text))
            group_logic = 'AND' if has_and else 'OR'
            return [(group_logic, 1)]
    
    def parse_prerequisites(self):
        """Parse prerequisite information and create requirement groups"""
        req_groups = []
        group_id = 1
        
        for course_code, course_data in self.courses.items():
            # Parse prerequisites
            if course_data['prerequisites']:
                prereq_logic = self.parse_requirement_logic(course_data['prerequisites'])
                for group_logic, path_id in prereq_logic:
                    req_groups.append({
                        'group_id': group_id,
                        'course_code': course_code,
                        'req_type': 'PREREQ',
                        'group_logic': group_logic,
                        'path_id': path_id
                    })
                    group_id += 1
            
            # Parse corequisites
            if course_data['corequisites']:
                coreq_logic = self.parse_requirement_logic(course_data['corequisites'])
                for group_logic, path_id in coreq_logic:
                    req_groups.append({
                        'group_id': group_id,
                        'course_code': course_code,
                        'req_type': 'COREQ',
                        'group_logic': group_logic,
                        'path_id': path_id
                    })
                    group_id += 1
        
        return pd.DataFrame(req_groups)
    
    def parse_requirement_items_from_text(self, req_text, group_id, item_id_counter):
        """Parse prerequisite/corequisite text to extract individual items"""
        items = []
        
        if not req_text:
            return items
        
        text = req_text.lower()
        
        # Handle explicit "None" or "N/A" cases
        if re.search(r'\bnone\b|\bn/?a\b', text):
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'NONE',
                'course_code': None,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': None,
                'notes': 'No prerequisites/corequisites required'
            })
            item_id_counter += 1
            return items
        
        # 1. Extract course codes (pattern: [A-Z]{3,4}\d{2}[A-Z]\d)
        course_pattern = r'([A-Z]{3,4}\d{2}[A-Z]\d)'
        courses_found = re.findall(course_pattern, req_text)
        for course_code in courses_found:
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'COURSE',
                'course_code': course_code,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': None,
                'notes': None
            })
            item_id_counter += 1
        
        # 2. Extract MIN_CGPA (pattern: cgpa?.*?([\d.]+))
        cgpa_pattern = r'cgpa.*?(?:of\s+at\s+)?(?:least\s+)?([\d.]+)'
        cgpa_match = re.search(cgpa_pattern, text)
        if cgpa_match:
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'MIN_CGPA',
                'course_code': None,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': float(cgpa_match.group(1)),
                'program_name': None,
                'year_standing': None,
                'notes': None
            })
            item_id_counter += 1
        
        # 3. Extract PROGRAM_ENROLLMENT (pattern: enrolment|enrollment.*?in\s+(.*?)(?:program|$))
        program_pattern = r'(?:enrol(?:l)?ment\s+(?:in\s+)?(?:(?:any|the)\s+)?([A-Za-z\s&()]+)\s*(?:program|\(JOINT\)\s*PROGRAM)|restricted\s+to\s+students\s+in\s+(?:the\s+)?([A-Za-z\s&]+)(?:\s+program)?)'
        program_match = re.search(program_pattern, text)
        if program_match:
            program_name = program_match.group(1) or program_match.group(2)
            if program_name:
                program_name = program_name.strip()
                items.append({
                    'item_id': item_id_counter,
                    'group_id': group_id,
                    'item_type': 'PROGRAM_ENROLLMENT',
                    'course_code': None,
                    'min_credits': None,
                    'department_prefix': None,
                    'min_cgpa': None,
                    'program_name': program_name,
                    'year_standing': None,
                    'notes': None
                })
                item_id_counter += 1
        
        # 4. Extract PERMISSION (pattern: permission|consent|instructor's permission)
        if re.search(r'permission|consent.*supervisor|obtain.*consent', text):
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'PERMISSION',
                'course_code': None,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': None,
                'notes': 'Instructor or program permission/consent required'
            })
            item_id_counter += 1
        
        # 5. Extract YEAR_STANDING (pattern: \d+(?:st|nd|rd|th)\s+year)
        year_pattern = r'(\d+)(?:st|nd|rd|th)\s+year'
        year_match = re.search(year_pattern, text)
        if year_match:
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'YEAR_STANDING',
                'course_code': None,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': int(year_match.group(1)),
                'notes': None
            })
            item_id_counter += 1
        
        # 6. Extract MIN_CREDITS with optional department prefix
        # Handle various credit formats: credits, full credits, FCE, cr
        credits_patterns = [
            (r'(\d+\.?\d*)\s*(?:full\s+)?(?:credit|cr|fce)s?', 1),  # "4.0 credits", "4.0 full credits", "4.0 cr", "2.0 FCE"
            (r'one\s+(?:[A-Z]-level\s+)?(?:full\s+)?(?:credit|fce)', 0),  # "One full credit", "One B-level full credit", "One credit", "One FCE"
            (r'two\s+(?:[A-Z]-level\s+)?(?:full\s+)?(?:credit|fce)s?', 0),  # "Two full credits", etc.
            (r'three\s+(?:[A-Z]-level\s+)?(?:full\s+)?(?:credit|fce)s?', 0),
            (r'four\s+(?:[A-Z]-level\s+)?(?:full\s+)?(?:credit|fce)s?', 0),
            (r'five\s+(?:[A-Z]-level\s+)?(?:full\s+)?(?:credit|fce)s?', 0)
        ]
        
        credit_value_map = {
            'one': 1.0,
            'two': 2.0,
            'three': 3.0,
            'four': 4.0,
            'five': 5.0
        }
        
        for pattern, group_idx in credits_patterns:
            for match in re.finditer(pattern, req_text, re.IGNORECASE):
                if group_idx > 0 and match.group(group_idx):  # Numeric value
                    min_credits = float(match.group(group_idx))
                else:  # Word-based value
                    word = match.group(0).lower().split()[0]
                    min_credits = credit_value_map.get(word, 1.0)  # Default to 1.0
                
                # Check if this is department-specific
                start_idx = match.start()
                before_text = req_text[:start_idx].lower()
                
                # Check if preceded by department info
                dept_pattern = r'(?:in|from|at)\s+(?:the\s+)?(?:department\s+of\s+)?([A-Za-z\s&]+?)(?:\s+(?:course|program|level))?$'
                dept_match = re.search(dept_pattern, before_text)
                
                dept_prefix = None
                item_type = 'MIN_CREDITS_TOTAL'
                
                if dept_match:
                    dept_name = dept_match.group(1).strip()
                    # Extract department code from name (first 3 letters usually)
                    if len(dept_name) > 0:
                        dept_prefix = dept_name[:3].upper()
                        item_type = 'MIN_CREDITS_DEPT'
                
                # Check for level specification (B-level, C-level, etc.) - look in the full match context
                level_match = re.search(r'([A-Z])-level', req_text[match.start()-20:match.end()+20])
                if level_match:
                    level = level_match.group(1)
                    item_type = f'MIN_CREDITS_LEVEL_{level}'
                
                # Only add if we haven't already added this credit requirement
                existing_credit_items = [i for i in items if i['item_type'].startswith('MIN_CREDITS')]
                if not any(i['min_credits'] == min_credits and i['item_type'] == item_type for i in existing_credit_items):
                    items.append({
                        'item_id': item_id_counter,
                        'group_id': group_id,
                        'item_type': item_type,
                        'course_code': None,
                        'min_credits': min_credits,
                        'department_prefix': dept_prefix,
                        'min_cgpa': None,
                        'program_name': None,
                        'year_standing': None,
                        'notes': None
                    })
                    item_id_counter += 1
        
        # 7. Extract HIGH_SCHOOL_REQUIREMENTS
        if re.search(r'grade\s+12|high\s+school', text):
            # Extract specific subjects mentioned
            subjects = []
            if 'calculus' in text:
                subjects.append('Calculus and Vectors')
            if 'advanced functions' in text:
                subjects.append('Advanced Functions')
            if 'biology' in text:
                subjects.append('Biology')
            if 'english' in text or 'creative writing' in text:
                subjects.append('English/Creative Writing')
            if 'physics' in text:
                subjects.append('Physics')
            
            subject_str = ', '.join(subjects) if subjects else 'Grade 12 subjects'
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'HIGH_SCHOOL',
                'course_code': None,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': None,
                'notes': f'High school requirement: {subject_str}'
            })
            item_id_counter += 1
        
        # 8. Extract EXPERIENCE_REQUIREMENTS
        if re.search(r'experience|working\s+knowledge|communication\s+skills', text):
            exp_type = 'Programming experience' if 'programming' in text else 'Language/Subject experience'
            if 'communication skills' in text:
                exp_type = 'Communication skills in specific languages'
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'EXPERIENCE',
                'course_code': None,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': None,
                'notes': f'Required experience: {exp_type}'
            })
            item_id_counter += 1
        
        # 9. Extract "ANY" course requirements (e.g., "Any B-level course in X, Y, Z")
        any_course_pattern = r'any\s+([A-Z])-level\s+(?:full\s+)?(?:credit|course)\s+in\s+([A-Za-z\s,&]+)'
        any_match = re.search(any_course_pattern, req_text, re.IGNORECASE)
        if any_match:
            level = any_match.group(1)
            subjects = any_match.group(2).strip()
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': f'ANY_COURSE_LEVEL_{level}',
                'course_code': None,
                'min_credits': 1.0,  # Any course is typically 1.0 credit
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': None,
                'notes': f'Any {level}-level course in: {subjects}'
            })
            item_id_counter += 1
        
        # 10. Extract program-specific course completion
        if re.search(r'successful\s+completion.*group|specialist.*program', text):
            items.append({
                'item_id': item_id_counter,
                'group_id': group_id,
                'item_type': 'PROGRAM_SPECIFIC',
                'course_code': None,
                'min_credits': None,
                'department_prefix': None,
                'min_cgpa': None,
                'program_name': None,
                'year_standing': None,
                'notes': 'Program-specific course completion required'
            })
            item_id_counter += 1
        
        return items
    
    def parse_requirement_items(self):
        """Parse all requirement items from requirements_groups"""
        req_items = []
        item_id_counter = 1
        
        # First get the requirements groups
        req_groups_df = self.parse_prerequisites()
        
        for _, group_row in req_groups_df.iterrows():
            group_id = group_row['group_id']
            course_code = group_row['course_code']
            req_type = group_row['req_type']
            
            # Get the prerequisite/corequisite text for this course
            course_data = self.courses.get(course_code, {})
            req_text = course_data.get('prerequisites' if req_type == 'PREREQ' else 'corequisites', '')
            
            if req_text:
                # Parse items for this specific group
                items = self.parse_requirement_items_from_text(req_text, group_id, item_id_counter)
                req_items.extend(items)
                item_id_counter += len(items)
        
        return pd.DataFrame(req_items)
    
    def generate_all_csvs(self, input_file, output_dir):
        """Generate all required CSV files"""
        # Parse courses
        self.parse_file(input_file)
        
        # Save courses.csv
        courses_df = self.save_courses_csv(f"{output_dir}/courses.csv")
        print(f"✓ Generated courses.csv with {len(courses_df)} courses")
        
        # Generate requirement groups
        req_groups_df = self.parse_prerequisites()
        if not req_groups_df.empty:
            req_groups_df.to_csv(f"{output_dir}/requirements_groups.csv", index=False)
            print(f"✓ Generated requirements_groups.csv with {len(req_groups_df)} groups")
        
        # Generate requirement items
        req_items_df = self.parse_requirement_items()
        if not req_items_df.empty:
            req_items_df.to_csv(f"{output_dir}/requirement_items.csv", index=False)
            print(f"✓ Generated requirement_items.csv with {len(req_items_df)} items")
        
        # Create empty program_requirements.csv structure
        program_req_df = pd.DataFrame({
            'program_code': [],
            'program_name': [],
            'course_code': [],
            'is_mandatory': []
        })
        program_req_df.to_csv(f"{output_dir}/program_requirements.csv", index=False)
        print(f"✓ Generated program_requirements.csv (empty, ready for data)")
        
        return courses_df, req_groups_df


if __name__ == "__main__":
    import os
    
    # Set file paths
    data_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(data_dir, "data_raw", "sample_courses.txt")
    
    # Create extractor and generate CSVs
    extractor = CourseExtractor()
    courses_df, prereqs_df = extractor.generate_all_csvs(input_file, data_dir)
    
    print("\n" + "="*60)
    print("DATA CLEANING COMPLETE")
    print("="*60)
    print(f"\nSummary:")
    print(f"  Courses parsed: {len(courses_df)}")
    print(f"  Prerequisite groups: {len(prereqs_df) if not prereqs_df.empty else 0}")
    print(f"\nNext steps:")
    print(f"  1. Review generated CSV files")
    print(f"  2. Add program requirements to program_requirements.csv")
    print(f"  3. Further refine prerequisite parsing if needed")

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
    
    def parse_prerequisites(self):
        """Parse prerequisite information and create prerequisite groups"""
        prereq_groups = []
        group_id = 1
        
        for course_code, course_data in self.courses.items():
            # Parse prerequisites
            if course_data['prerequisites']:
                prereq_groups.append({
                    'group_id': group_id,
                    'course_code': course_code,
                    'group_type': 'AND',
                    'req_type': 'PREREQ',
                    'min_credits': 0,
                    'min_courses': 0
                })
                group_id += 1
            
            # Parse corequisites
            if course_data['corequisites']:
                prereq_groups.append({
                    'group_id': group_id,
                    'course_code': course_code,
                    'group_type': 'AND',
                    'req_type': 'COREQ',
                    'min_credits': 0,
                    'min_courses': 0
                })
                group_id += 1
        
        return pd.DataFrame(prereq_groups)
    
    def generate_all_csvs(self, input_file, output_dir):
        """Generate all required CSV files"""
        # Parse courses
        self.parse_file(input_file)
        
        # Save courses.csv
        courses_df = self.save_courses_csv(f"{output_dir}/courses.csv")
        print(f"✓ Generated courses.csv with {len(courses_df)} courses")
        
        # Generate prerequisite files
        prereq_groups_df = self.parse_prerequisites()
        if not prereq_groups_df.empty:
            prereq_groups_df.to_csv(f"{output_dir}/prerequisite_groups.csv", index=False)
            print(f"✓ Generated prerequisite_groups.csv with {len(prereq_groups_df)} groups")
        
        # Create empty prerequisite_courses.csv structure if needed
        prereq_courses_df = pd.DataFrame({
            'group_id': [],
            'required_course_code': []
        })
        prereq_courses_df.to_csv(f"{output_dir}/prerequisite_courses.csv", index=False)
        
        # Create empty program_requirements.csv structure
        program_req_df = pd.DataFrame({
            'program_code': [],
            'program_name': [],
            'course_code': [],
            'is_mandatory': []
        })
        program_req_df.to_csv(f"{output_dir}/program_requirements.csv", index=False)
        print(f"✓ Generated prerequisite_courses.csv and program_requirements.csv (empty, ready for data)")
        
        return courses_df, prereq_groups_df


if __name__ == "__main__":
    import os
    
    # Set file paths
    data_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(data_dir, "sample_courses.txt")
    
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

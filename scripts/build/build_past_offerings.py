#!/usr/bin/env python3
"""
Unified build system for past_offerings.csv

This module combines:
- PDF conversion functionality (convert_timetable_to_text.py)
- Timetable parsing for all formats (Fall, Winter, Summer)
- CSV building and merging operations

Main entry point: python build_past_offerings.py [--convert-only] [--build-only]
"""

import re
import os
import pandas as pd
import pdfplumber
from pathlib import Path


# ============================================================================
# PDF CONVERSION FUNCTIONS
# ============================================================================

def convert_pdf_to_text(pdf_file, output_file):
    """
    Convert PDF file to text format using pdfplumber.
    
    Args:
        pdf_file: Path to input PDF file
        output_file: Path to output text file
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return True, f"Converted {pdf_file} to {output_file}"
    except Exception as e:
        return False, f"Error converting {pdf_file}: {str(e)}"


def convert_all_timetables(data_dir):
    """
    Convert all course timetable PDFs to text format.
    
    Args:
        data_dir: Directory containing data files
    
    Returns:
        dict: Results for each PDF file
    """
    data_raw_dir = os.path.join(data_dir, 'data_raw')
    
    print(f"Looking in directory: {data_raw_dir}")
    print(f"Directory exists: {os.path.exists(data_raw_dir)}\n")
    
    pdf_files = [
        'Course Timetable Fall 2025.pdf',
        'Course Timetable Summer 2025.pdf',
        'Course Timetable Winter 2025.pdf'
    ]
    
    print("Converting course timetable PDFs to text format...\n")
    
    results = {}
    for pdf_file in pdf_files:
        pdf_path = os.path.join(data_raw_dir, pdf_file)
        
        if not os.path.exists(pdf_path):
            print(f"[OK] {pdf_file} not found")
            results[pdf_file] = "NOT_FOUND"
            continue
        
        output_file = pdf_path.replace('.pdf', '.txt')
        
        if os.path.exists(output_file):
            print(f"[OK] {Path(output_file).name} already exists")
            results[pdf_file] = "SKIPPED"
            continue
        
        print(f"Converting {pdf_file}...")
        success, message = convert_pdf_to_text(pdf_path, output_file)
        
        if success:
            file_size = os.path.getsize(output_file) / 1024
            print(f"[OK] {Path(output_file).name} ({file_size:.1f} KB)")
            results[pdf_file] = "SUCCESS"
        else:
            print(f"Error: {message}")
            results[pdf_file] = "ERROR"
    
    print("\nConversion complete!")
    return results


# ============================================================================
# UTILITY FUNCTIONS FOR PARSING
# ============================================================================

def map_delivery(delivery_code):
    """
    Map delivery code to human readable format.
    
    Args:
        delivery_code: Raw delivery code (e.g., 'INPER', 'ONLIN', 'HYBR')
    
    Returns:
        str: Standardized delivery type
    """
    mapping = {
        'INPER': 'In-person',
        'ONLIN': 'Online',
        'HYBR': 'Hybrid',
        'SYNC': 'Online',
        'ASYNC': 'Online'
    }
    return mapping.get(delivery_code, delivery_code)


def get_year_from_filename(filename):
    """
    Extract year from timetable filename.
    
    Args:
        filename: Timetable filename
    
    Returns:
        int: Year (defaults to 2025)
    """
    match = re.search(r'(\d{4})', filename)
    if match:
        return int(match.group(1))
    return 2025


# ============================================================================
# PARSING FUNCTIONS FOR DIFFERENT FORMATS
# ============================================================================

def parse_fall_format(filepath, year):
    """
    Parse Fall format with Component/Section/Day/Time/Delivery/Instructor keywords.
    
    Format:
        XXXN##H# (F) - Course Name
        Component Section Day Time Delivery Instructor
        LEC 1 MO 10:00-12:00 INPER Instructor Name
    
    Args:
        filepath: Path to timetable text file
        year: Academic year
    
    Returns:
        list: Offerings extracted from file
    """
    offerings = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_course = None
    current_semester = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for course code pattern: XXXN##H# (F/W/S) - Course Name
        course_match = re.match(r'([A-Z]{4}\d{2}[HY]\d)\s*\(([FWS])\)\s*-\s*(.+)', line)
        if course_match:
            current_course = course_match.group(1)
            sem_code = course_match.group(2)
            
            semester_map = {'F': 'Fall', 'W': 'Winter', 'S': 'Summer'}
            current_semester = semester_map.get(sem_code, 'Fall')
        
        # Look for table header: "Component Section Day Time Delivery Instructor"
        elif line.startswith('Component') and 'Delivery' in line and 'Instructor' in line:
            i += 1
            # Process all LEC lines that follow
            while i < len(lines):
                data_line = lines[i].strip()
                
                # Stop on empty line
                if not data_line:
                    break
                
                # Stop on next course
                if re.match(r'[A-Z]{4}\d{2}[HY]\d\s*\([FWS]\)', data_line):
                    i -= 1
                    break
                
                # Parse LEC lines
                if data_line.startswith('LEC'):
                    tokens = data_line.split()
                    if len(tokens) >= 2:
                        remaining = ' '.join(tokens[2:])
                        
                        # Extract day
                        day = ''
                        day_pattern = r'(MO|TU|WE|TH|FR|SA|SU|MTWTF|MW|MWF|TTh)'
                        day_match = re.search(day_pattern, remaining)
                        if day_match:
                            day = day_match.group(1)
                        
                        # Extract delivery and instructor
                        delivery = 'In-person'
                        instructor = ''
                        
                        delivery_codes = ['INPER', 'ONLIN', 'HYBR', 'SYNC', 'ASYNC']
                        for code in delivery_codes:
                            if code in remaining:
                                delivery_map = {
                                    'INPER': 'In-person',
                                    'ONLIN': 'Online',
                                    'HYBR': 'Hybrid',
                                    'SYNC': 'Online',
                                    'ASYNC': 'Online'
                                }
                                delivery = delivery_map.get(code, 'In-person')
                                parts = remaining.split(code, 1)
                                if len(parts) > 1:
                                    instructor = parts[1].strip()
                                break
                        
                        # Create offering
                        if instructor and current_course:
                            offerings.append({
                                'course_code': current_course,
                                'semester': current_semester,
                                'year': year,
                                'instructor': instructor,
                                'delivery': delivery,
                                'day_time': day,
                                'campus': 'UTSC'
                            })
                
                i += 1
        else:
            i += 1
    
    return offerings


def parse_table_format(content, year):
    """
    Parse Winter/Summer table format with columns.
    
    Columns: Meeting Section Day(s) Start(s) End Location Current Max Wait Delivery Mode Instructor Notes
    
    Format:
        1. COURSE CODE (YEAR Semester) - Name
        LEC01 WE 10:00 12:00 Available on 36 60 Y In-person deChamplain-Leverenz, D.
    
    Args:
        content: File content as string
        year: Academic year
    
    Returns:
        list: Offerings extracted from content
    """
    offerings = []
    
    course_pattern = r'^\d+\.\s+([A-Z]{4}\d{2}[HY]\d[STY]?)\s*\((\d{4})\s+(Winter|Summer|Fall)\)\s*-'
    
    lines = content.split('\n')
    current_course = None
    current_semester = None
    current_year = year
    
    for i, line in enumerate(lines):
        # Look for course header
        course_match = re.match(course_pattern, line)
        if course_match:
            course_code_full = course_match.group(1)
            current_course = re.sub(r'[STY]$', '', course_code_full)
            
            current_year = int(course_match.group(2))
            current_semester = course_match.group(3)
        
        # Look for table rows starting with LEC
        elif current_course and line.strip().startswith('LEC'):
            tokens = line.split()
            if len(tokens) >= 3:
                day_code = ''
                delivery = ''
                instructor = ''
                
                # Look for day code in first few tokens
                for j in range(1, min(5, len(tokens))):
                    if tokens[j] in ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU', 'MTWTF', 'MW', 'TTh', 'MWF']:
                        day_code = tokens[j]
                        break
                
                # Look for delivery mode
                for j in range(len(tokens)):
                    if tokens[j] in ['In-person', 'Online', 'Hybrid', 'INPER', 'ONLIN', 'HYBR']:
                        delivery = tokens[j]
                        if j + 1 < len(tokens):
                            instructor = ' '.join(tokens[j+1:]).strip()
                        break
                
                # Fallback: search for name pattern
                if not instructor:
                    name_match = re.search(r'([A-Z][a-z]+(?:-[A-Z][a-z]+)*(?:,\s*[A-Z]\.)?)', line)
                    if name_match:
                        instructor = name_match.group(1).strip()
                
                # Create offering record
                if current_course and current_semester and instructor:
                    offering = {
                        'course_code': current_course,
                        'semester': current_semester,
                        'year': current_year,
                        'instructor': instructor,
                        'delivery': map_delivery(delivery) if delivery else 'In-person',
                        'day_time': day_code,
                        'campus': 'UTSC'
                    }
                    offerings.append(offering)
    
    return offerings


def parse_summer_format(content, year):
    """
    Parse Summer format where each course entry is followed by data lines.
    
    Format:
        XXXN##H (20255)
        Component Section Day Time Delivery Instructor
        LEC 1 MO 10:00-12:00 SYNC Nargolwalla, M.
    
    Args:
        content: File content as string
        year: Academic year
    
    Returns:
        list: Offerings extracted from content
    """
    offerings = []
    
    course_pattern = r'^([A-Z]{4}\d{2}[HY]\d)\s*\((\d{4,5})\)'
    
    lines = content.split('\n')
    current_course = None
    current_year = year
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Look for course code
        course_match = re.match(course_pattern, line_stripped)
        if course_match:
            current_course = course_match.group(1)
            year_str = course_match.group(2)
            if len(year_str) == 5:
                current_year = int(year_str[:4])
            else:
                current_year = int(year_str)
        
        # Look for LEC entries
        elif current_course and line_stripped.startswith('LEC'):
            tokens = line_stripped.split()
            if len(tokens) >= 5:
                component = tokens[0]
                section = tokens[1] if tokens[1].isdigit() else ''
                
                day_code = ''
                delivery = 'In-person'
                instructor = ''
                
                # Search for day code
                for t in tokens[2:]:
                    if t in ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU', 'MTWTF', 'MW', 'TTh', 'MWF']:
                        day_code = t
                        break
                
                # Search for delivery mode
                delivery_tokens = ['SYNC', 'INPER', 'ONLIN', 'HYBR', 'In-person', 'Online', 'Hybrid', 'Synchronous', 'Asynchronous']
                for t in tokens:
                    if t in delivery_tokens:
                        delivery = 'In-person' if t in ['SYNC', 'Synchronous', 'INPER', 'In-person'] else 'Online' if t in ['ONLIN', 'Online', 'Asynchronous'] else 'Hybrid'
                        break
                
                # Extract instructor
                instructor_start = -1
                for j, t in enumerate(tokens):
                    if t in delivery_tokens or re.match(r'\d{2}:\d{2}', t):
                        instructor_start = j + 1
                        break
                
                if instructor_start > 0 and instructor_start < len(tokens):
                    instructor = ' '.join(tokens[instructor_start:]).strip()
                
                # Create offering
                if component == 'LEC' and current_course and instructor:
                    offering = {
                        'course_code': current_course,
                        'semester': 'Summer',
                        'year': current_year,
                        'instructor': instructor,
                        'delivery': delivery,
                        'day_time': day_code,
                        'campus': 'UTSC'
                    }
                    offerings.append(offering)
    
    return offerings


# ============================================================================
# MAIN TIMETABLE PARSING
# ============================================================================

def parse_timetable_file(filepath):
    """
    Parse a timetable text file. Detects format and uses appropriate parser.
    
    Supported formats:
    - Fall: Component-based vertical table
    - Winter: Numbered course entries with table format
    - Summer: Course code with year code pattern
    
    Args:
        filepath: Path to timetable text file
    
    Returns:
        list: Offerings extracted from file
    """
    year = get_year_from_filename(os.path.basename(filepath))
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Detect file format
    if 'Total Courses :' in content or re.search(r'^\d+\.\s+[A-Z]{4}\d{2}[HY]\d[STY]\s*\(\d{4}', content, re.MULTILINE):
        return parse_table_format(content, year)
    elif re.search(r'^[A-Z]{4}\d{2}[HY]\d\s*\(\d{5}\)', content, re.MULTILINE):
        return parse_summer_format(content, year)
    else:
        return parse_fall_format(filepath, year)


# ============================================================================
# CSV BUILDING AND MERGING
# ============================================================================

def build_past_offerings(data_dir):
    """
    Build past_offerings.csv from all timetable files.
    
    Args:
        data_dir: Directory containing data files
    
    Returns:
        pd.DataFrame: Final offerings dataframe
    """
    data_raw_dir = os.path.join(data_dir, 'data_raw')
    
    timetable_files = [
        'Course Timetable Fall 2025.txt',
        'Course Timetable Winter 2025.txt',
        'Course Timetable Summer 2025.txt'
    ]
    
    all_offerings = []
    
    print("=" * 80)
    print("BUILDING PAST OFFERINGS FROM TIMETABLE TEXT FILES")
    print("=" * 80)
    
    for filename in timetable_files:
        filepath = os.path.join(data_raw_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"\n[!] File not found: {filename}")
            continue
        
        print(f"\nProcessing: {filename}")
        offerings = parse_timetable_file(filepath)
        all_offerings.extend(offerings)
        print(f"  Extracted {len(offerings)} LEC offerings")
    
    if not all_offerings:
        print("\n[ERROR] No offerings extracted from timetable files")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(all_offerings)
    df['offering_id'] = range(1, len(df) + 1)
    
    # Reorder columns
    df = df[['offering_id', 'course_code', 'semester', 'year', 'instructor', 'delivery', 'day_time', 'campus']]
    
    # Save to CSV
    output_file = os.path.join(data_dir, 'past_offerings.csv')
    df.to_csv(output_file, index=False)
    
    print("\n" + "=" * 80)
    print("CREATION SUCCESSFUL")
    print("=" * 80)
    print(f"\n[OK] Created past_offerings.csv")
    print(f"  - Total offerings: {len(df)}")
    
    # Show statistics
    print(f"\nSemester Distribution:")
    for sem, count in df['semester'].value_counts().items():
        print(f"  {sem:12} : {count:4} offerings")
    
    print(f"\nDelivery Distribution:")
    for del_type, count in df['delivery'].value_counts().items():
        print(f"  {del_type:12} : {count:4} offerings")
    
    print(f"\nSample Offerings:")
    sample_count = min(5, len(df))
    for idx, row in df.head(sample_count).iterrows():
        print(f"  {row['offering_id']:4} | {row['course_code']:10} | {row['semester']:8} {row['year']} | {row['day_time']:15} | {row['instructor'][:20]:20} | {row['delivery']}")
    
    return df


def merge_fall_offerings(data_dir):
    """
    Merge fresh Fall 2025 offerings into existing past_offerings.csv.
    
    This function:
    1. Parses the fresh Fall 2025 timetable
    2. Removes old Fall data from the CSV
    3. Inserts new Fall data
    4. Regenerates offering IDs
    
    Args:
        data_dir: Directory containing data files
    
    Returns:
        pd.DataFrame: Updated offerings dataframe
    """
    fall_file = os.path.join(data_dir, 'data_raw', 'Course Timetable Fall 2025.txt')
    csv_file = os.path.join(data_dir, 'past_offerings.csv')
    
    print("=" * 80)
    print("MERGING FALL 2025 INTO PAST_OFFERINGS.CSV")
    print("=" * 80)
    
    # Parse Fall file
    print("\n[1] Parsing Fall 2025 timetable...")
    fall_offerings = parse_timetable_file(fall_file)
    print(f"    Extracted: {len(fall_offerings)} Fall offerings")
    
    # Read existing CSV
    print(f"\n[2] Reading existing past_offerings.csv...")
    df_existing = pd.read_csv(csv_file)
    print(f"    Found: {len(df_existing)} total offerings")
    
    sem_counts = df_existing['semester'].value_counts().to_dict()
    for sem in ['Winter', 'Fall', 'Summer']:
        print(f"      {sem:8}: {sem_counts.get(sem, 0):4} offerings")
    
    # Remove existing Fall data and merge new
    print(f"\n[3] Merging data...")
    df_without_fall = df_existing[df_existing['semester'] != 'Fall'].copy()
    df_fall_new = pd.DataFrame(fall_offerings)
    df_merged = pd.concat([df_without_fall, df_fall_new], ignore_index=True)
    print(f"    Removed old Fall: {len(df_existing) - len(df_without_fall)} offerings")
    print(f"    Added new Fall: {len(fall_offerings)} offerings")
    print(f"    New total: {len(df_merged)} offerings")
    
    # Regenerate offering_id
    print(f"\n[4] Regenerating offering_id...")
    df_merged['offering_id'] = range(1, len(df_merged) + 1)
    
    # Reorder columns
    columns = ['offering_id', 'course_code', 'semester', 'year', 
               'instructor', 'delivery', 'day_time', 'campus']
    df_merged = df_merged[columns]
    
    # Save
    print(f"\n[5] Saving updated past_offerings.csv...")
    df_merged.to_csv(csv_file, index=False)
    print(f"    Done!")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    final_counts = df_merged['semester'].value_counts().sort_index().to_dict()
    print(f"\nFinal semester breakdown:")
    total = 0
    for sem in ['Fall', 'Winter', 'Summer']:
        count = final_counts.get(sem, 0)
        total += count
        print(f"  {sem:8}: {count:4} offerings")
    print(f"  --------")
    print(f"  Total   : {total:4} offerings")
    
    return df_merged


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for build system."""
    import sys
    
    data_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Parse command line arguments
    convert_only = '--convert-only' in sys.argv
    build_only = '--build-only' in sys.argv
    merge = '--merge' in sys.argv
    
    try:
        if not build_only:
            print("\n" + "=" * 80)
            print("STEP 1: CONVERTING PDFS TO TEXT")
            print("=" * 80 + "\n")
            convert_all_timetables(data_dir)
        
        if not convert_only:
            if merge:
                print("\n" + "=" * 80)
                print("STEP 2: MERGING FALL 2025 OFFERINGS")
                print("=" * 80 + "\n")
                merge_fall_offerings(data_dir)
            else:
                print("\n" + "=" * 80)
                print("STEP 2: BUILDING PAST_OFFERINGS.CSV")
                print("=" * 80 + "\n")
                build_past_offerings(data_dir)
        
        print("\n" + "=" * 80)
        print("ALL OPERATIONS COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")
    
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

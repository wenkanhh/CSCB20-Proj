#!/usr/bin/env python3
"""
Debug utilities for course timetable parsing and data extraction

This module consolidates all debugging scripts:
- debug_codes.py: Program code validation
- debug_detail.py: File structure analysis for Fall timetable
- debug_timetable.py: Timetable pattern searching
- debug_winter.py: Winter format file analysis
"""

import os
import re
import pandas as pd


# ============================================================================
# DEBUG UTILITIES FOR PROGRAM CODES
# ============================================================================

def debug_program_codes():
    """
    Validate program codes extracted from programs.txt against programs.csv
    
    Checks:
    - Total valid program codes in programs.csv
    - First 10 program block extractions
    - Code extraction accuracy
    """
    print("\n" + "=" * 80)
    print("DEBUG: PROGRAM CODE VALIDATION")
    print("=" * 80)
    
    # Load valid program codes
    programs_df = pd.read_csv('programs.csv')
    valid_prog_codes = set(programs_df['program_code'].dropna().unique())
    print(f"Valid program codes in programs.csv: {len(valid_prog_codes)}")
    print(f"Sample codes: {list(valid_prog_codes)[:10]}")
    
    # Read program blocks
    with open('data_raw/programs.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    calendars = list(re.finditer(r'^Calendar Section:(.*)$', content, flags=re.MULTILINE))
    blocks = []
    start = 0
    for cal in calendars:
        block = content[start:cal.start()].strip()
        if block:
            blocks.append(block)
        start = cal.end()
    blocks.append(content[start:].strip())
    
    print(f"\nTotal program blocks: {len(blocks)}")
    
    # Check first 10 blocks
    print("\nFirst 10 block extractions:")
    extracted_codes = []
    for i, block in enumerate(blocks[:10]):
        lines = block.split('\n')
        heading = lines[0].strip() if lines else ''
        
        program_code = ''
        if ' - ' in heading:
            parts = heading.split(' - ')
            code_part = parts[-1].strip()
            m = re.search(r'([A-Z]{2}[A-Z0-9]+(?:[A-Z])?)\s*$', code_part)
            if m:
                program_code = m.group(1).upper()
        
        if not program_code:
            m = re.match(r'^(?:CERTIFICATE|MAJOR|SPECIALIST).*?-\s*([A-Z0-9]+)\s*$', heading, re.IGNORECASE)
            if m:
                program_code = m.group(1)
        
        in_programs = program_code in valid_prog_codes
        has_req = 'Program Requirements' in block
        
        print(f"{i+1}. Code='{program_code}' | InDB={in_programs} | HasReqs={has_req}")
        print(f"   Heading: {heading[:80]}")
        extracted_codes.append(program_code)
    
    valid_count = len([c for c in extracted_codes if c])
    matched_count = len([c for c in extracted_codes if c in valid_prog_codes])
    print(f"\nExtracted {valid_count} codes, {matched_count} valid")


# ============================================================================
# DEBUG UTILITIES FOR FILE STRUCTURE ANALYSIS (FALL TIMETABLE)
# ============================================================================

def debug_fall_structure():
    """
    Analyze Fall timetable file structure and show course data organization
    
    Shows:
    - Number of courses found
    - First 3 courses with their structure
    - Location of 'Component' keyword
    - Table structure for each course
    """
    print("\n" + "=" * 80)
    print("DEBUG: FALL TIMETABLE STRUCTURE")
    print("=" * 80)
    
    filepath = r"c:\Users\admin\Documents\UNIVERSITY\UofT\Third year\CSCB20-Proj\data\data_raw\Course Timetable Fall 2025.txt"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the first course with data
    course_pattern = r'([A-Z]{4}\d{2}[HY]\d)\s*\(([FWS])\)\s*-'
    
    matches = list(re.finditer(course_pattern, ''.join(lines)))
    print(f"Found {len(matches)} courses\n")
    
    # For the first course, show the structure
    for match_idx, match in enumerate(matches[:3]):
        # Get the line number
        text_before = ''.join(lines)[:match.start()]
        course_line_num = text_before.count('\n')
        
        course_code = match.group(1)
        sem_code = match.group(2)
        
        print(f"\nCourse {match_idx + 1}: {course_code} ({sem_code})")
        print(f"Line {course_line_num}: {lines[course_line_num].strip()}")
        
        # Look for Component keyword in next 200 lines
        found_component = False
        for i in range(course_line_num + 1, min(course_line_num + 200, len(lines))):
            if lines[i].strip() == 'Component':
                print(f"\nFound 'Component' at line {i}")
                # Show the next 50 lines
                print("\nTable structure (next 50 lines):")
                for j in range(i, min(i + 50, len(lines))):
                    print(f"  Line {j:5}: {repr(lines[j].rstrip())}")
                found_component = True
                break
        
        if not found_component:
            print("  [!] No 'Component' found in next 200 lines")


# ============================================================================
# DEBUG UTILITIES FOR TIMETABLE PATTERN SEARCHING
# ============================================================================

def debug_timetable_patterns():
    """
    Search for course patterns and LEC entries in timetable files
    
    Shows:
    - First 10 course patterns found in first 500 lines
    - Sample of first 200 characters
    - LEC pattern occurrences with context
    """
    print("\n" + "=" * 80)
    print("DEBUG: TIMETABLE PATTERN SEARCH")
    print("=" * 80)
    
    filepath = r"c:\Users\admin\Documents\UNIVERSITY\UofT\Third year\CSCB20-Proj\data\data_raw\Course Timetable Fall 2025.txt"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}\n")
    
    # Look for course codes
    course_pattern = r'([A-Z]{4}\d{2}[HY]\d)\s*\(([FWS])\)\s*-'
    count = 0
    print("First 10 course patterns in first 500 lines:")
    for i, line in enumerate(lines[:500]):
        if re.search(course_pattern, line):
            print(f"Line {i}: {line.strip()}")
            count += 1
            if count >= 10:
                break
    
    print(f"\nFound {count} course patterns in first 500 lines")
    
    # Sample of first 200 lines
    print("\n" + "=" * 80)
    print("FIRST 200 CHARACTERS:")
    print("=" * 80)
    content = ''.join(lines[:50])
    print(repr(content[:200]))
    
    # Look for LEC pattern
    print("\n" + "=" * 80)
    print("Looking for LEC pattern in first 500 lines...")
    print("=" * 80)
    lec_count = 0
    for i, line in enumerate(lines[:500]):
        if line.strip() == 'LEC':
            print(f"Line {i}: Found LEC")
            # Show context
            for j in range(max(0, i-5), min(len(lines), i+10)):
                print(f"  {j}: {lines[j].rstrip()}")
            lec_count += 1
            if lec_count >= 3:
                break


# ============================================================================
# DEBUG UTILITIES FOR WINTER TIMETABLE FORMAT
# ============================================================================

def debug_winter_format():
    """
    Analyze Winter timetable file format and structure
    
    Checks:
    - Presence of "Total Courses :" marker
    - Numbered course entry pattern
    - First 50 lines of file
    - LEC entry patterns
    """
    print("\n" + "=" * 80)
    print("DEBUG: WINTER TIMETABLE FORMAT")
    print("=" * 80)
    
    filepath = r"c:\Users\admin\Documents\UNIVERSITY\UofT\Third year\CSCB20-Proj\data\data_raw\Course Timetable Winter 2025.txt"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("File characteristics:")
    print(f"  Contains 'Total Courses :'? {'Total Courses :' in content}")
    pattern = r'^\d+\.\s+[A-Z]{4}\d{2}[HY]\d[STY]\s*\(\d{4}'
    has_numbered = bool(re.search(pattern, content, re.MULTILINE))
    print(f"  Contains numbered courses pattern? {has_numbered}")
    
    # Show first course entry
    lines = content.split('\n')
    print("\nFirst 50 lines of file:")
    for i, line in enumerate(lines[:50]):
        print(f"{i:3}: {line[:100]}")
    
    print("\n\nSearching for LEC entries:")
    lec_count = 0
    for i, line in enumerate(lines):
        if line.startswith('LEC'):
            print(f"Line {i}: {line}")
            lec_count += 1
            if lec_count >= 5:
                break
    print(f"Total LEC lines found: {lec_count}")


# ============================================================================
# MAIN DEBUG MENU
# ============================================================================

def main():
    """Main entry point for debug utilities."""
    import sys
    
    print("\n" + "=" * 80)
    print("COURSE TIMETABLE DEBUG UTILITIES")
    print("=" * 80)
    
    print("\nAvailable debug functions:")
    print("  1. debug_program_codes       - Validate program codes")
    print("  2. debug_fall_structure      - Analyze Fall timetable structure")
    print("  3. debug_timetable_patterns  - Search timetable patterns")
    print("  4. debug_winter_format       - Analyze Winter format")
    print("  5. Run all debug functions")
    print("  0. Exit")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter choice (0-5): ").strip()
    
    try:
        if choice == '1':
            debug_program_codes()
        elif choice == '2':
            debug_fall_structure()
        elif choice == '3':
            debug_timetable_patterns()
        elif choice == '4':
            debug_winter_format()
        elif choice == '5':
            debug_program_codes()
            debug_fall_structure()
            debug_timetable_patterns()
            debug_winter_format()
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
    print("DEBUG COMPLETE")
    print("=" * 80 + "\n")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

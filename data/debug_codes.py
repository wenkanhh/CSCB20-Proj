import re
import pandas as pd

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

print(f"\nExtracted {len([c for c in extracted_codes if c])} codes, {len([c for c in extracted_codes if c in valid_prog_codes])} valid")

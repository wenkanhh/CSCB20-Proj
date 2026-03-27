import re

with open('data_raw/programs.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Find calendar sections for these specific programs
programs_to_check = [
    'MINOR PROGRAM IN AFRICAN STUDIES',
    'MINOR PROGRAM IN APPLIED CLIMATOLOGY',
    'MINOR PROGRAM IN APPLIED STATISTICS'
]

for prog in programs_to_check:
    match = re.search(rf'{re.escape(prog)}.*?(?=Calendar Section:|$)', content, re.DOTALL)
    if match:
        block = match.group(0)
        cal_match = re.search(r'Calendar Section:\s*(.+)$', block, re.MULTILINE)
        if cal_match:
            print(f"{prog} -> {cal_match.group(1).strip()}")
        else:
            print(f"{prog} -> NO CALENDAR SECTION FOUND")

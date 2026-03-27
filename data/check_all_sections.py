import re
import pandas as pd

with open('data_raw/programs.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Load departments
depts_df = pd.read_csv('departments.csv')

# Extract all calendar sections in the file
calendars = re.findall(r'Calendar Section:\s*(.+)$', content, re.MULTILINE)
print("All Calendar Sections in programs.txt:")
for cal in sorted(set(calendars)):
    print(f"  - {cal}")

print("\nDepartment names in departments.csv:")
for dept in sorted(depts_df['department_name'].tolist()):
    print(f"  - {dept}")

# Check which calendar sections don't match any department name
print("\nMissing mappings (Calendar Sections not in departments.csv):")
for cal in set(calendars):
    dept_name = cal.split(',')[0].strip()
    if dept_name not in depts_df['department_name'].values:
        print(f"  - '{dept_name}'")

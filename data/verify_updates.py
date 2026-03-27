import pandas as pd

# Check MINOR type
progs = pd.read_csv('programs.csv')
print("Program types:", progs['program_type'].value_counts().to_dict())
print()

# Check MINOR programs specifically
minors = progs[progs['program_type'] == 'Minor']
print(f"Found {len(minors)} MINOR programs")
if len(minors) > 0:
    print(minors[['program_name', 'program_code', 'program_type', 'department_id']].head().to_string())
print()

# Check sample Management program has correct department_id
mgmt = progs[progs['program_name'].str.contains('MANAGEMENT.*BACHELOR', case=False, na=False, regex=True)]
print(f"Management programs sample:")
if len(mgmt) > 0:
    print(mgmt[['program_name', 'program_code', 'program_type', 'department_id']].head(3).to_string())
print()

# Check program_requirement.csv has no group_name column
req = pd.read_csv('program_requirement.csv')
print("Requirement columns:", list(req.columns))
print("Has group_name:", 'group_name' in req.columns)

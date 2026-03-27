import pandas as pd

df = pd.read_csv('programs.csv')
missing = df[df['department_id'].isna() | (df['department_id'].astype(str).str.strip()=='')]
print(f"Programs with missing department_id ({len(missing)} total):")
print(missing[['program_name', 'program_code', 'program_type']].to_string())

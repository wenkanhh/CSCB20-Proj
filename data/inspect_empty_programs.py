import pandas as pd
p = pd.read_csv('programs.csv')
empty = p[p['program_code'].isna() | (p['program_code'] == '')]
print('empty count', len(empty))
print(empty[['program_code', 'program_name']].head(50).to_string(index=False))

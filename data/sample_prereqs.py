import pandas as pd

df = pd.read_csv('courses.csv')

# Show some non-empty prerequisites
print("Sample prerequisites:")
for i, (idx, row) in enumerate(df[df['prerequisites'].notna() & (df['prerequisites'] != '')].iterrows()):
    if i < 15:
        print(f"\n{row['course_code']}: {row['prerequisites'][:200]}")

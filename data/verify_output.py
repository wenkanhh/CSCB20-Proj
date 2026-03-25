import pandas as pd

df = pd.read_csv('courses.csv')

# Show ACMC01 as an example 
sample = df[df['course_code'] == 'ACMC01'].iloc[0]
print(f"Course: {sample['course_code']} - {sample['course_name']}")
print(f"\nCourse Link: {sample['course_link']}")
print(f"\nNote: {sample['note'] if pd.notna(sample['note']) and sample['note'] != '' else 'None'}")
print(f"Breadth Requirements: {sample['breadth_requirements']}")
print(f"Course Experience: {sample['course_experience']}")

print(f"\n{'='*80}")
print("\nSample courses with note and link:")

for idx, row in df[['course_code', 'course_name', 'note', 'course_link']].head(8).iterrows():
    print(f"\n{row['course_code']}: {row['course_name']}")
    print(f"  Note: {str(row['note'])[:80] if pd.notna(row['note']) and row['note'] != '' else 'None'}")
    print(f"  Link: {str(row['course_link'])[:60] if pd.notna(row['course_link']) and row['course_link'] != '' else 'None'}")


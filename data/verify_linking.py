import pandas as pd

req_groups = pd.read_csv('requirements_groups.csv')
req_items = pd.read_csv('requirement_items.csv')
courses = pd.read_csv('courses.csv')

# Find a complex course example
sample_courses = ['ACMC01', 'ACMD98', 'ACMD99']

for course in sample_courses:
    if course in courses['course_code'].values:
        print(f"\n{'='*70}")
        print(f"Course: {course}")
        print(f"{'='*70}")
        
        # Get course info
        course_info = courses[courses['course_code'] == course].iloc[0]
        print(f"Prerequisites: {course_info['prerequisites']}")
        print(f"\nCorequisites: {course_info['corequisites']}")
        
        # This is a simplified example - in reality we'd need to match groups to items
        # For now, let's show all items and groups
        print(f"\nNumber of prerequisite items in dataset: {len(req_items)}")
        print(f"Sample items by type:")
        
        for item_type in ['COURSE', 'MIN_CREDITS_TOTAL', 'MIN_CGPA', 'PERMISSION']:
            sample = req_items[req_items['item_type'] == item_type].head(2)
            if len(sample) > 0:
                print(f"\n  {item_type}:")
                for _, row in sample.iterrows():
                    if item_type == 'COURSE':
                        print(f"    - {row['course_code']} (group_id: {row['group_id']})")
                    elif item_type == 'MIN_CREDITS_TOTAL':
                        print(f"    - {row['min_credits']} credits (group_id: {row['group_id']})")
                    elif item_type == 'MIN_CGPA':
                        print(f"    - CGPA {row['min_cgpa']} (group_id: {row['group_id']})")
                    elif item_type == 'PERMISSION':
                        print(f"    - {row['notes']} (group_id: {row['group_id']})")

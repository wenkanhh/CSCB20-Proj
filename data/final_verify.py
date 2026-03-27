import pandas as pd

req_groups = pd.read_csv('requirements_groups.csv')
req_items = pd.read_csv('requirement_items.csv')

print('=== FINAL LINKAGE VERIFICATION ===')
groups_in_req_groups = set(req_groups['group_id'].unique())
groups_in_req_items = set(req_items['group_id'].unique())

common_groups = groups_in_req_groups & groups_in_req_items
missing_in_items = groups_in_req_groups - groups_in_req_items

print(f'Groups in requirements_groups.csv: {len(groups_in_req_groups)}')
print(f'Groups in requirement_items.csv: {len(groups_in_req_items)}')
print(f'Common groups (properly linked): {len(common_groups)}')
print(f'Groups missing from requirement_items: {len(missing_in_items)}')
print(f'Linkage success rate: {len(common_groups)/len(groups_in_req_groups)*100:.1f}%')

print('\n=== SAMPLE LINKAGE ===')
sample_groups = req_groups.head(3)
for _, group in sample_groups.iterrows():
    group_id = group['group_id']
    course_code = group['course_code']
    req_type = group['req_type']

    items = req_items[req_items['group_id'] == group_id]
    print(f'\nGroup {group_id}: {course_code} ({req_type}) - {len(items)} items')
    for _, item in items.iterrows():
        item_type = item['item_type']
        if item_type == 'COURSE':
            print(f'  - COURSE: {item["course_code"]}')
        elif item_type == 'MIN_CREDITS_TOTAL':
            print(f'  - MIN_CREDITS_TOTAL: {item["min_credits"]}')
        elif item_type == 'MIN_CGPA':
            print(f'  - MIN_CGPA: {item["min_cgpa"]}')
        elif item_type == 'PERMISSION':
            print(f'  - PERMISSION')
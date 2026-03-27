import pandas as pd

req_df = pd.read_csv('requirements_groups.csv')
courses_df = pd.read_csv('courses.csv')

# Find courses with multiple paths (path_id > 1)
has_multiple_paths = req_df[req_df['path_id'] > 1]['course_code'].unique()
if len(has_multiple_paths) > 0:
    sample_course = has_multiple_paths[0]
    print(f'Sample course with multiple paths: {sample_course}')
    
    # Show requirement groups for this course
    print('\nRequirement groups for', sample_course, ':')
    groups = req_df[req_df['course_code'] == sample_course]
    print(groups.to_string())
    
    # Show the raw prerequisite text
    print('\nRaw prerequisite text:')
    course_info = courses_df[courses_df['course_code'] == sample_course]
    if not course_info.empty:
        print(course_info['prerequisites'].values[0])
else:
    print('No courses with multiple paths found')
    
# Show distribution of path_ids
print('\n\nPath ID distribution:')
print(req_df['path_id'].value_counts().sort_index())

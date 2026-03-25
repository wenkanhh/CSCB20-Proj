The cleaned dataset includes the following files:

1. courses.csv — include cleaned courses information with the following columns:
- course_code: the code for the course (e.g: MGAC03 is a course code). the H3 does not stand for anything and can be removed
- course_code_prefix: the subject indication from the course code (e.g.: MGA in MGAC03 is the subject code). each department's calendar section has their own unique course code prefixes
- offering_code: the specific course offering from the course code (e.g: C03 in MGAC03 is the offering code)
- course_name: the name for the course (e.g:  Intermediate Management Accounting is the name for MGAC03 course)
- course_details: the paragraph that describe the course 
- credits: the number of credits that can be earned for this course, usually most courses are 0.5 credits
- prerequisites: Courses students must already have passed before taking the described course, usually will be either a fixed number of taken credits or some specific course codes. if there is no prerequisite, 'None' will appear in this value, a list of strings for everything
- corequisites: Corequisites: Courses students must take in the same semester as, or already have passed before taking the described course, a list of strings for everything
- exclusions: Students who have already passed a course listed as an exclusion, or received transfer credit for a course listed as an exclusion, cannot take the described course for credit
- breadth_requirements: the breath requirement of the corresponding course (e.g.:  Social and Behavioural Sciences for MGAC03)
- course_experience: course experience if available
- note: some course has its specific special notes
- course_link: url to the course website

2. prerequisite_groups.csv — Defines each logical grouping of prerequisites for a course with the following columns:
- group_id: Unique ID for this group (normal integers should work, e.g.: 1)
- course code: the code for the course, this is the key column to link to courses.csv
- group_type: AND or OR logic within the group
- req_type: PREREQ or COREQ — when it must be satisfied
- min_credits: starts with 0, Minimum credits needed from this group, 0 = none required
- min_courses: Minimum number of courses needed from group, 0 = none required


3. prerequisite_courses.csv - Lists every course that belongs to each group
- group_id: Links back to prerequisite_groups.csv
- required_course_code: A course in this group, a list of strings for everything

4. program_requirements.csv — cleaned degree requirements with the following columns:
- program code: the code for the program (e.g.:SCSPE24320)
- program name: the name for the program (e.g.: SPECIALIST PROGRAM IN STRATEGIC MANAGEMENT - Management Strategy Stream (BACHELOR OF BUSINESS ADMINISTRATION))
- course code: the courses that are required for the program, One row per course required in a program. If a course is required in 2 programs, it gets 2 rows
- is_mandatory: 1 = required, 0 = elective/optional


IMPORTANT REMARKS:
1. this is how everything should be linked together:
courses.csv is the central file everything else points back to. The course_code column is the primary key — every other file uses it as a foreign key to reference a course.
prerequisite_groups.csv links to courses.csv through course_code — this tells you which course the requirement belongs to. It also generates its own group_id which becomes the link for the next file.
prerequisite_courses.csv links to prerequisite_groups.csv through group_id — this tells you which group each required course belongs to. It also links back to courses.csv through required_course_code — this is the indirect dashed arrow in the diagram, meaning the required course must also exist in your courses table.
program_requirements.csv links to courses.csv through course_code — telling you which course is required for that program.


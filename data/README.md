The cleaned dataset includes the following files:

1. courses.csv - the central table that stores every course offered by the institution, all other tables link back to this one:
- course_code: unique code that identifies the course (e.g. MGAC03), used as the primary key across the entire system
- course_code_prefix: the subject area prefix extracted from the course code (e.g. MGA), identifies which department the course belongs to
- offering_code: the specific offering identifier extracted from the course code (e.g. C03)
- course_name: the full official name of the course
- course_details: the full paragraph description of what the course covers 
- credits: the number of credits earned by completing this course, typically 0.5
- prerequisites: Courses students must already have passed before taking the described course, usually will be either a fixed number of taken credits or some specific course codes. if there is no prerequisite, 'None' will appear in this value, a list of strings for everything
- corequisites: Corequisites: Courses students must take in the same semester as, or already have passed before taking the described course, a list of strings for everything
- exclusions: Students who have already passed a course listed as an exclusion, or received transfer credit for a course listed as an exclusion, cannot take the described course for credit
- breadth_requirements: the breadth requirement category this course satisfies if any
- course_experience: any specific learning experience associated with this course
- note: any special notes attached to this course such as enrolment restrictions
- course_link: the URL to the official course page on the institution's website


2. users.csv - stores the account information for every student who registers on the platform
- user_id: unique number that identifies each student, used by other tables to reference this student
- username: the login name chosen by the student
- password: the hashed password for the student's account
- email: the student's email address
- cgpa: the student's current cumulative GPA, used to check CGPA-based prerequisites
- year_standing: the student's current year of study (1, 2, 3, 4), used to check year-based prerequisites


3. programs.csv - stores every academic program offered by the institution (majors, specialists, minors)
- program_code: unique identifier for the program extracted from the calendar heading such as SCSPE1150C or SCMAJ1762C, used as the primary key and referenced by all program-related tables
- program_name: the full official title of the program exactly as it appears in the calendar heading such as SPECIALIST (CO-OPERATIVE) PROGRAM IN CONSERVATION AND BIODIVERSITY (SCIENCE)
- department_id: the department this program belongs to as listed at the bottom of each program block such as Biological Sciences or Management Co-op, used to infer which department owns this program 
- program_type: the category of the program, one of Specialist, Specialist Co-op, Major, Major Co-op, Minor, Certificate, or Combined Degreem
- is_coop: 1 for coop program, 0 for non-coop program
- is_limited_enrolment: 1 if the program explicitly states enrolment is limited or limited enrolment in its text, 0 otherwise
- total_credits: the total number of required credits of specified courses groups a student must complete to finish this program, extracted from phrases like students must complete a total of 14.5 credits
- min_enrolment_cgpa: the minimum cumulative GPA required to apply for or be admitted into this program, extracted from the enrolment requirements section
- description: the full descriptive paragraph that appears at the start of each program block explaining what the program is about and what graduates can expect


4. user_programs.csv - junction table that links students to the programs they are enrolled in, allowing one student to be in multiple programs simultaneously
- id: unique number that identifies each enrolment record
- user_id: references the student from the users table
- program_code: references the program from the programs table
- status: whether the student is currently ACTIVE in this program, has COMPLETED it, or has WITHDRAWN
- start_year: the year the student started this program
- end_year: the year the student finished or left this program, NULL if still active


5. requirement_groups.csv - groups individual prerequisite or corequisite conditions together into logical blocks, one group represents one logical chunk of a requirement:
- group_id: unique number that identifies each group, referenced by requirement_items to know which group each condition belongs to
- course_code: references the course from the courses table that this requirement belongs to
- req_type: whether this group is a PREREQ (must be done before) or COREQ (must be done at the same time or before)
- group_logic: whether ALL items in this group must be satisfied (AND) or just any ONE of them (OR)
- path_id: identifies which alternative path this group belongs to, students only need to satisfy all groups in ONE path to meet the full requirement


6. requirement_items.csv - stores each individual condition inside a requirement group, one row per single condition such as a specific course, a credit minimum, a CGPA threshold, or a program enrollment requirement
- item_id: unique number that identifies each individual condition
- group_id: references the group from requirement_groups that this condition belongs to
- item_type: the kind of condition this row represents, one of COURSE, MIN_CREDITS_TOTAL, MIN_CREDITS_DEPT, MIN_CGPA, PROGRAM_ENROLLMENT, YEAR_STANDING, or PERMISSION
- course_code: the specific course that must be completed, only filled when item_type is COURSE
- min_credits: the minimum number of credits required, only filled when item_type is MIN_CREDITS_TOTAL or MIN_CREDITS_DEPT
- department_id: the department the minimum credits must come from, only filled when item_type is MIN_CREDITS_DEPT
- min_cgpa: the minimum CGPA the student must have, only filled when item_type is MIN_CGPA
- program_code: the program the student must be enrolled in, only filled when item_type is PROGRAM_ENROLLMENT
- year_standing: the minimum year of study required, only filled when item_type is YEAR_STANDING
- notes: a human readable fallback description for any condition that does not fit neatly into the other columns


7. course_exclusions.csv - stores pairs of courses that cannot both be taken for credit, if a student has already completed an excluded course they cannot take the described course
- exclusion_id: unique number that identifies each exclusion pair
- course_code: the course being described, references the courses table
- excluded_course: the course that conflicts with it, also references the courses table, a student who has completed this course cannot take course_code
- note: for other exclusions that special for the course and can't be fit into the other columns


8. program_requirement.csv - stores each requirement block for a program, one row per logical chunk of requirements such as Core Courses or Bin 1 Electives, separating the group structure from the individual courses inside it
- group_id: unique number identifying each requirement block, referenced by program_requirement_courses to know which block each course belongs to
- program_code: references the program from programs.csv that this requirement block belongs to
- group_type: how the student satisfies this block, one of ALL meaning every course in the block must be taken, PICK meaning the student chooses a minimum number or credit amount from the listed options, CREDIT_LEVEL meaning a credit threshold at a specific course level must be met without a fixed course list such as at least 1.0 credit at D-level, or OPTIONAL meaning the courses are encouraged but not required for graduation
- min_courses: the minimum number of courses the student must take from this block, only relevant when group_type is PICK
- min_credits: the minimum credits the student must earn from this block, only relevant when group_type is PICK
- path_id: NULL for most blocks, an integer when this block is one of several mutually exclusive ways to satisfy a requirement such as Calculus Option A versus Calculus Option B where the student only needs to complete all blocks sharing ONE path_id value to satisfy the requirement
- combined_group_id: NULL for most blocks, an integer when credits from multiple separate blocks are pooled together toward a shared total minimum such as Bin 1 and Bin 2 electives which separately each require 1.0 credit but together must total 4.0 credits, all blocks sharing the same combined_group_id contribute to the same combined pool
- combined_min_credits: the total shared credit minimum that must be reached by summing all credits earned across every block sharing the same combined_group_id, NULL if this block does not participate in a combined pool
- category:  the category label for this block indicating its role in the program, one of Required for mandatory core courses, Elective for optional or choice-based courses, Graduation Requirement for zero-credit CR/NCR courses that must be completed to graduate, Co-op for work term and co-op preparation courses, or Optional for research or enrichment courses that are encouraged but not required
- notes: the original text of the section heading or any special instruction associated with this block copied from the calendar, used to preserve context that does not fit into the structured columns above


9. past_offerings.csv - records every time a course has been offered in a past semester, used by the recommendation engine to show students when a course is typically available
- offering_id: unique number that identifies each offering record
- course_code: references the course from the courses table that was offered
- semester: the semester in which the course was offered, one of Fall, Winter, or Summer
- year: the calendar year in which the course was offered
- section: the section code if multiple sections of the same course were offered simultaneously
- instructor: the name of the instructor who taught this offering
- delivery: how the course was delivered, one of In-person, Online, or Hybrid
- day_time: the scheduled days and times for this offering if available
- capacity: the number of seats available in this offering
- campus: the campus location where this offering was held


10. completed_courses.csv - records every course a student has taken or is currently taking, the core table used by the recommendation engine to determine what a student has done and what they are eligible for next
- record_id: unique number that identifies each completion record
- user_id: references the student from the users table who took this course
- course_code: references the course from the courses table that was taken
- semester: the semester in which the student took this course
- year: the calendar year in which the student took this course
- grade: the letter grade the student received
- numeric_grade: the numeric grade the student received if available
- status: the outcome of this course attempt, one of COMPLETED (passed), IN_PROGRESS (currently taking), FAILED (did not pass), or TRANSFER (credit transferred from another institution)
- credits_earned: the actual number of credits the student earned, 0.0 if the course was failed or is still in progress


11. departments.csv - stores each academic department as its own entity, separate from the prefixes it owns
- department_id: unique number identifying the department
- department_name: the full name of the department (e.g. Management, Computer Science)
- faculty: the faculty this department belongs to (e.g. Faculty of Arts and Science)
- notes: any special notes about the department


12. department_prefixes.csv - junction table that links each department to all the course code prefixes it owns, one row per prefix
- prefix_id: unique number identifying each prefix row
- department_id: references the department from the departments table that owns this prefix
- course_code_prefix: the actual prefix string that appears in course codes (e.g. MGA, MGH, MGE, MGO)
- prefix_description: optional human readable note about what this prefix covers

13. program_requirement_courses.csv - stores each individual course that belongs to a requirement block, one row per course per block, keeps course-level detail separate from block-level structure
- id: unique number identifying each row
- group_id: references the requirement block from program_requirements.csv that this course belongs to
- course_code: references the course from courses.csv that is part of this requirement block
- is_mandatory: 1 if this specific course is always required within the block, 0 if it is one of several options the student can choose from
- notes: any course-specific note within this block such as zero credit CR/NCR graduation requirement


14. enrolment_requirements.csv - stores the individual conditions a student must meet before they can apply to or be admitted into a program, parsed from the Enrolment Requirements section of each program block, one row per individual condition
- group_id: unique number identifying each condition row, used as the primary key for this table
- program_code: references the program from programs.csv that this enrolment condition belongs to
- req_category: always ENROLMENT for every row in this file, distinguishes these conditions from program completion requirements
- item_type: the kind of condition this row represents, one of COURSE meaning a specific course must be completed, MIN_CREDITS_TOTAL meaning a minimum number of total credits must be earned, MIN_CREDITS_DEPT meaning a minimum number of credits from a specific department must be earned, or MIN_CGPA meaning a minimum cumulative GPA must be achieved
- course_code: the specific course that must be completed before applying, only filled when item_type is COURSE, references courses.csv, NULL otherwise
- min_credits: the minimum number of credits required, only filled when item_type is MIN_CREDITS_TOTAL or MIN_CREDITS_DEPT such as 4.0 for programs requiring at least 4.0 credits before applying, NULL otherwise
- max_credits: the maximum number of credits allowed at time of application, only filled for programs that specify a credit window such as minimum 4.0 to maximum 10.0 credits, NULL otherwise
- department_id: the course_code_prefix identifying which department the minimum credits must come from such as BIO for biology credits, only filled when item_type is MIN_CREDITS_DEPT, NULL otherwise
- min_cgpa: the minimum cumulative GPA the student must have achieved, only filled when item_type is MIN_CGPA such as 2.5 for most co-op programs, NULL otherwise
- notes: a human readable explanation of this condition copied or summarised from the original calendar text, used as a fallback description and for any condition that does not fit neatly into the other columns

IMPORTANT REMARKS:
1. this is how everything should be linked together:
1 — the three independent anchors with no incoming foreign keys. departments, courses, and programs are inserted first. Everything else points to at least one of them.
Row 1.5 — dept_prefixes sits just below departments because it only depends on departments.
2 — the prerequisite and exclusion system. requirement_groups links to courses for which course has the requirement. requirement_items links to requirement_groups for the block, back to courses for COURSE-type items, and to departments for MIN_CREDITS_DEPT items. course_exclusions links to courses twice.
3 — the program requirement system. enrolment_requirements and prog_req_groups both link to programs. prog_req_groups generates a group_id that prog_req_courses uses. Both enrolment_requirements and prog_req_courses link back to courses.
4 — the student layer. past_offerings links to courses. users links down to user_programs and completed_courses. user_programs bridges users and programs. completed_courses bridges users and courses.


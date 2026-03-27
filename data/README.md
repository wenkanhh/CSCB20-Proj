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
- program_code: unique short code that identifies the program, used as the primary key and referenced by other tables
- program_name: the full official name of the program
- department: the department prefix associated with this program (e.g. MGA for management)
- program_type: whether this is a Major, Specialist, or Minor
- total_credits_required: the total number of credits a student must complete to finish this program
- notes: any special notes about the program such as limited enrolment conditions


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
- department_prefix: the department the minimum credits must come from, only filled when item_type is MIN_CREDITS_DEPT
- min_cgpa: the minimum CGPA the student must have, only filled when item_type is MIN_CGPA
- program_name: the program the student must be enrolled in, only filled when item_type is PROGRAM_ENROLLMENT
- year_standing: the minimum year of study required, only filled when item_type is YEAR_STANDING
- notes: a human readable fallback description for any condition that does not fit neatly into the other columns


7. course_exclusions.csv - stores pairs of courses that cannot both be taken for credit, if a student has already completed an excluded course they cannot take the described course
- exclusion_id: unique number that identifies each exclusion pair
- course_code: the course being described, references the courses table
- excluded_course: the course that conflicts with it, also references the courses table, a student who has completed this course cannot take course_code


8. program_requirements.csv - stores which courses are required for each program, and how those requirements are grouped so that elective rules like pick 2 from this list can be expressed
- req_id: unique number that identifies each requirement row
- program_code: references the program from the programs table that this requirement belongs to
- group_id: groups multiple rows together into one requirement block, rows with the same group_id belong to the same rule
- group_name: a human readable label for this requirement block such as Core Courses or 300-level Electives
- group_type: whether the student must take ALL courses in this group or just PICK some of them
- min_courses: the minimum number of courses the student must pick from this group, only relevant when group_type is PICK
- min_credits: the minimum number of credits the student must pick from this group, only relevant when group_type is PICK
- course_code: references the specific course from the courses table that belongs to this requirement group
- is_mandatory: 1 if this specific course is always required within the group, 0 if it is one of several options
- year_level: the suggested year of study when the student should take this course
- category: the category label for this requirement such as Core, Elective, or Breadth


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


IMPORTANT REMARKS:
1. this is how everything should be linked together:
courses.csv is the central file everything else points back to. The course_code column is the primary key — every other file uses it as a foreign key to reference a course.
prerequisite_groups.csv links to courses.csv through course_code — this tells you which course the requirement belongs to. It also generates its own group_id which becomes the link for the next file.
prerequisite_courses.csv links to prerequisite_groups.csv through group_id — this tells you which group each required course belongs to. It also links back to courses.csv through required_course_code — this is the indirect dashed arrow in the diagram, meaning the required course must also exist in your courses table.
program_requirements.csv links to courses.csv through course_code — telling you which course is required for that program.


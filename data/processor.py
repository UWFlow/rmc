import rmc.shared.constants as c
import rmc.models as m

from datetime import datetime
import glob
import json
import mongoengine as me
import os
import re
import sys

def import_departments():

    m.Department.objects._collection.drop()

    def clean_uwdata_department(department):
        return {
            'id': department['Acronym'].lower(),
            'name': department['Name'],
            'faculty_id': department['Faculty'].lower(),
            'url': department['CoursesURL'],
        }

    def clean_ucalendar_department(department):
        return department


    sources = [
        {
            'name': 'ucalendar',
            'clean_fn': clean_ucalendar_department,
            'file_name': 'ucalendar_departments.txt',
        },
        {
            'name': 'uwdata',
            'clean_fn': clean_uwdata_department,
            'file_name': 'uwdata_departments.txt',
        },
    ]

    for source in sources:
        file_name = os.path.join(
                sys.path[0], c.DEPARTMENTS_DATA_DIR, source['file_name'])

        with open(file_name, 'r') as f:
            data = json.load(f)

        for department in data:
            department = source['clean_fn'](department)
            if m.Department.objects.with_id(department['id']):
                continue

            m.Department(**department).save()

    print 'imported departments:', m.Department.objects.count()

def import_courses():
    m.Course.objects._collection.drop()

    def get_department_name_from_file_path(file_path):
        return re.findall(r'([^/]*).txt$', file_path)[0].lower()

    def build_keywords(department, number, course_title):
        department = department.lower()
        number = str(number)
        course_title = course_title.lower()
        course_title = re.sub(r'\s+', ' ', course_title)
        keywords = [department, number, department + number]
        keywords.extend(course_title.split(' '))
        return keywords

    # TODO(mack): rs215 seems to be duplicated. see,
    # http://www.ucalendar.uwaterloo.ca/1213/COURSE/course-RS.html
    def clean_ucalendar_course(dep, course):
        try:
            # Fails on courses from:
            # http://www.ucalendar.uwaterloo.ca/1213/COURSE/course-BUS.html
            number = re.findall(
                r'^.*? (\d+[A-Za-z]*?) .*$', course['intro'])[0].lower()
        except:
            return None

        name = course['name'].strip()
        course_obj = {
            'id': '%s%s' % (dep, number),
            'department_id': dep,
            'number': number,
            'name': name,
            'description': course['description'].strip(),
            '_keywords': build_keywords(dep, number, name),
        }
        for note in course['notes']:
            if re.findall('^Antireq: ', note):
                course_obj['antireqs'] = re.sub('^Antireq:', '', note).strip()
            elif re.findall('^Coreq: ', note):
                course_obj['coreqs'] = re.sub('^Coreq:', '', note).strip()
            elif re.findall('^Prereq: ', note):
                course_obj['prereqs'] = re.sub('^Prereq:', '', note).strip()

        return course_obj

    def clean_opendata_course(dep, course):
        number = course['Number'].lower()
        return {
            'id': '%s%s' % (dep, number),
            'department_id': dep,
            'number': number,
            'name': course['Title'],
            'description': course['Description'],
            '_keywords': build_keywords(
                dep, number, course['Title']),
        }

    def clean_uwdata_course(dep, course):
        course = course['course']
        number = course['course_number'].lower()
        return {
            'id': '%s%s' % (dep, number),
            'department_id': dep,
            'number': number,
            'name': course['title'],
            'description': course['description'],
            '_keywords': build_keywords(
                    dep, number, course['title']),
        }


    sources = [
        {
            'name': 'ucalendar',
            'clean_fn': clean_ucalendar_course,
            'dir': c.UCALENDAR_COURSES_DATA_DIR,
        },
        {
            'name': 'opendata',
            'clean_fn': clean_opendata_course,
            'dir': c.OPENDATA_COURSES_DATA_DIR,
        },
        {
            'name': 'uwdata',
            'clean_fn': clean_uwdata_course,
            'dir': c.UWDATA_COURSES_DATA_DIR,
        },
    ]


    for source in sources:
        source['added'] = 0
        source['ignored'] = 0
        for file_name in glob.glob(os.path.join(
                sys.path[0], source['dir'], '*.txt')):

            with open(file_name, 'r') as f:
                courses = json.load(f)

            dep_name = get_department_name_from_file_path(file_name)
            if not m.Department.objects.with_id(dep_name):
                print 'could not find department %s' % dep_name
                continue

            # The input data can be a list or dict (with course number as key)
            if type(courses) == dict:
                courses = courses.values()
            for course in courses:
                course = source['clean_fn'](dep_name, course)
                if course and not m.Course.objects.with_id(course['id']):
                    m.Course(**course).save()
                    source['added'] += 1
                else:
                    source['ignored'] += 1


    # Update courses with terms offered data
    with open(os.path.join(
            sys.path[0], c.TERMS_OFFERED_DATA_DIR, 'terms_offered.txt')) as f:

        def map_term(term):
            return {
                'W': '01',
                'S': '05',
                'F': '09',
            }[term]

        terms_offered_by_course = json.load(f)
        for course_id, terms_offered in terms_offered_by_course.items():
            course = m.Course.objects.with_id(course_id)
            if not course:
                continue

            course.terms_offered = map(map_term, terms_offered)
            course.save()

    for course in m.Course.objects:
        if course.prereqs:
            course.prereqs = normalize_reqs_str(course.prereqs)
        if course.coreqs:
            course.coreqs = normalize_reqs_str(course.coreqs)
        if course.antireqs:
            course.antireqs = normalize_reqs_str(course.antireqs)
        course.save()

    for source in sources:
        print 'source: %s, added: %d, ignored: %d' % (
                source['name'], source['added'], source['ignored'])

    print 'imported courses:', m.Course.objects.count()


def normalize_reqs_str(str_):
    """Normalize the prereq string of a course

    TODO(mack): handle the following special cases:
        1) "CS/ECE 121"
    """

    # Split on non-alphanumeric characters (includes chars we split on)
    old_splits = re.compile('(\W+)').split(str_)
    # Newly normalized splits
    new_splits = []
    # Last department id encountered as we traverse prereq str
    last_dep_id = None

    # Traverse the splits
    for split in old_splits:
        new_split = split
        if last_dep_id and re.findall(r'^[0-9]{3}[a-z]?$', split.lower()):
            # If there's a previous dep id and this matches the number portion
            # of a course, check if this is a valid course
            # NOTE: we're not validating whether the course exists since
            # we should still normalize to make the output to look consistent,
            # even when the course does not exist
            new_split = last_dep_id.upper() + split
        elif (# Check it's uppercase, so we don't have false positives like "Earth"
              # that was part of "Earth Science student"
                re.findall('^[A-Z]+', split)
                and m.Department.objects.with_id(split.lower())):
            last_dep_id = split.lower()
            # Do not include the department id since it will be included
            # with the course we find
            new_split = ''

        new_splits.append(new_split)

        # We're here if this split matches a department id
        # Increment idx by 1 more to skip the next non-alphanum character

    new_str = ''.join(new_splits)
    # While removing department ids, we could have left redundant spaces
    # (e.g. "CS 247" => " CS247", so remove them now.
    return re.sub('\s+', ' ', new_str).strip()


# TODO(mack): should return (first_name, last_name)
def get_prof_name(prof_name_menlo):
    matches = re.findall(r'^(.+?), (.+)$', prof_name_menlo)[0]
    return {
        'first_name': matches[1],
        'last_name': matches[0],
    }

def import_professors():

    # NOTE: not safe to drop table anymore since users can add their own
    # professors now

    def clean_professor(professor):
        def clean_name(name):
            return re.sub(r'\s+', ' ', name.strip())

        prof_name = get_prof_name(professor['prof_name'])
        return {
            'first_name': clean_name(prof_name['first_name']),
            'last_name': clean_name(prof_name['last_name']),
        }


    file_names = glob.glob(
            os.path.join(sys.path[0], c.REVIEWS_DATA_DIR, '*.txt'))
    for file_name in file_names:
        with open(file_name, 'r') as f:
            data = json.load(f)
        professor = clean_professor(data)
        # Since user's can now add professors, gotta first check
        # that the professor does not aleady exist
        if not m.Professor.objects(**professor):
            m.Professor(**professor).save()

    print 'imported professors:', m.Professor.objects.count()

def import_reviews():

    m.MenloCourse.objects._collection.drop()

    def clean_review(review):
        course = review['class']
        if course is None:
            return {}

        course = course.lower()
        matches = re.findall(r'([a-z]+).*?([0-9]{3}[a-z]?)(?:[^0-9]|$)', course)
        # TODO(mack): investigate if we are missing any good courses with
        # this regex
        if len(matches) != 1 or len(matches[0]) != 2:
            return {}

        department_id = matches[0][0].lower()
        course_number = matches[0][1].lower()
        course_id = department_id + course_number
        prof_name = get_prof_name(data['prof_name'])
        prof_id = m.Professor.get_id_from_name(
                prof_name['first_name'], prof_name['last_name'])

        clean_review = {
            'professor_id': prof_id,
            'course_id': course_id,
            'course_review': m.CourseReview(),
            'professor_review': m.ProfessorReview(),
        }

        def normalize_rating(menlo_rating):
            # normalize 1..5 to Yes/No:
            # 1,2 => No, 3 => None, 4,5 => Yes
            try:
                menlo_rating = int(menlo_rating)
                if menlo_rating <= 2:
                    return 0
                elif menlo_rating >=4:
                    return 1
                else:
                    return None
            except:
                return None

        # TODO(mack): include 'r_helpful'?
        if 'r_clarity' in review:
            clean_review['professor_review'].clarity = normalize_rating(review['r_clarity'])
        if 'r_easy' in review:
            clean_review['course_review'].easiness = normalize_rating(review['r_easy'])
        if 'r_interest' in review:
            clean_review['course_review'].interest = normalize_rating(review['r_interest'])

        clean_review['professor_review'].comment = review['comment']
        clean_review['professor_review'].comment_date = datetime.strptime(
            review['date'], '%m/%d/%y')

        return clean_review

    file_names = glob.glob(
            os.path.join(sys.path[0], c.REVIEWS_DATA_DIR, '*.txt'))
    for file_name in file_names:
        with open(file_name, 'r') as f:
            data = json.load(f)

        for review in data['ratings']:
            review = clean_review(review)
            if (not 'course_id' in review
                    or not m.Course.objects.with_id(review['course_id'])):
                #print 'skipping rating because invalid course_id ' + course_id
                continue

            try:
                m.MenloCourse(**review).save()
            except:
                print 'failed on review', review

    print 'imported reviews:', m.MenloCourse.objects.count()

if __name__ == '__main__':
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
    import_professors()
    import_departments()
    import_courses() # must be after departments
    import_reviews() # must be after courses

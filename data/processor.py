import rmc.shared.constants as c
import rmc.models as m

from datetime import datetime
import glob
import json
import mongoengine
import os
import re
import sys

def import_departments():

    m.Department.objects._collection.drop()

    def clean_department(department):
        return {
            'id': department['Acronym'].lower(),
            'name': department['Name'],
            'faculty_id': department['Faculty'].lower(),
            'url': department['CoursesURL'],
        }

    for file_name in glob.glob(
            os.path.join(sys.path[0], c.DEPARTMENTS_DATA_DIR, '*.txt')):
        f = open(file_name, 'r')
        data = json.load(f)
        f.close()
        for department in data:
            department = clean_department(department)
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

    def clean_opendata_course(dep, course):
        dep = dep.lower()
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


    for file_name in glob.glob(os.path.join(
            sys.path[0], c.OPENDATA_COURSES_DATA_DIR, '*.txt')):

        with open(file_name, 'r') as f:
            data = json.load(f)

        dep_name = get_department_name_from_file_path(file_name)
        if not m.Department.objects.with_id(dep_name):
            print 'could not find department %s' % dep_name
            continue

        for course in data.values():
            course = clean_opendata_course(dep_name, course)
            m.Course(**course).save()

    def clean_uwdata_course(dep, course):
        course = course['course']
        dep = dep.lower()
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

    uwdata_count = 0
    uwdata_ignored = 0
    for file_name in glob.glob(os.path.join(
            sys.path[0], c.UWDATA_COURSES_DATA_DIR, '*.txt')):

        with open(file_name, 'r') as f:
            data = json.load(f)

        dep_name = get_department_name_from_file_path(file_name)
        if not m.Department.objects.with_id(dep_name):
            print 'could not find department %s' % dep_name
            continue

        for course in data:
            course = clean_uwdata_course(dep_name, course)

            if not m.Course.objects.with_id(course['id']):
                uwdata_count += 1
                m.Course(**course).save()
            else:
                uwdata_ignored += 1

    print 'backfilled %d courses from uwdata' % uwdata_count
    print 'ignored %d courses from uwdata' % uwdata_ignored
    print 'imported courses:', m.Course.objects.count()


# TODO(mack): should return (first_name, last_name)
def get_prof_name(prof_name_menlo):
    matches = re.findall(r'^(.+?), (.+)$', prof_name_menlo)[0]
    return {
        'first_name': matches[1],
        'last_name': matches[0],
    }

def import_professors():

    m.Professor.objects._collection.drop()

    def clean_professor(professor):
        # department_name = None
        # if 'info' in professor and 'Department' in professor['info']:
        #     department_name = data['info']['Department'].strip()

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
            # normalize 1..5 to 0..1
            try:
                return float(int(menlo_rating) - 1) / 4
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
    mongoengine.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
    import_professors()
    import_departments()
    import_courses() # must be after departments
    import_reviews() # must be after courses

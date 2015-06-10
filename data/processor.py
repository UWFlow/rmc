import rmc.shared.constants as c
import rmc.shared.util as rmc_util
import rmc.models as m

import argparse
from datetime import datetime
import dateutil.parser
import glob
import json
import mongoengine as me
import os
import time
import re
import sys


def import_departments():
    def clean_opendata_department(department):
        return {
            'id': department['subject'].lower(),
            'name': department['name'],
            'faculty_id': department['faculty_id'].lower(),
            'url': 'http://ugradcalendar.uwaterloo.ca/courses/{0}'.format(
                    department['subject'].lower()),
        }

    file_name = os.path.join(os.path.dirname(__file__),
            c.DEPARTMENTS_DATA_DIR, 'opendata2_departments.json')

    with open(file_name, 'r') as f:
        data = json.load(f)

    for department in data:
        department = clean_opendata_department(department)
        if m.Department.objects.with_id(department['id']):
            continue

        m.Department(**department).save()

    print 'imported departments:', m.Department.objects.count()


def import_courses():
    def get_department_name_from_file_path(file_path):
        return re.findall(r'([^/]*).json$', file_path)[0].lower()

    def build_keywords(department, number, course_title):
        department = department.lower()
        number = str(number)
        course_title = course_title.lower()
        course_title = re.sub(r'\s+', ' ', course_title)
        # Separate on hypens in title for keywords list
        course_title = re.sub(r'-', ' ', course_title)
        keywords = [department, number, department + number]
        keywords.extend(course_title.split(' '))
        return keywords

    def clean_description(des):
        return des or "No description"

    def clean_opendata_course(dep, course):
        number = course['catalog_number'].lower()
        return {
            'id': '%s%s' % (dep, number),
            'department_id': dep,
            'number': number,
            'name': course['title'],
            'description': clean_description(course['description']),
            '_keywords': build_keywords(
                    dep, number, course['title']),
            'antireqs': course['antirequisites'],
            'coreqs': course['corequisites'],
            'prereqs': course['prerequisites'],
        }

    added = 0
    updated = 0
    for file_name in glob.glob(os.path.join(os.path.dirname(__file__),
            c.OPENDATA2_COURSES_DATA_DIR, '*.json')):
        with open(file_name, 'r') as f:
            courses = json.load(f)

        dep_name = get_department_name_from_file_path(file_name)
        if not m.Department.objects.with_id(dep_name):
            print 'could not find department %s' % dep_name
            continue

        # The input data can be a list or dict (with course number as key)
        if isinstance(courses, dict):
            courses = courses.values()

        # For each course, update it if it already exists, else insert it
        for course in courses:
            if not course:
                continue
            course = clean_opendata_course(dep_name, course)
            old_course = m.Course.objects.with_id(course['id'])
            if old_course:
                for key, value in course.iteritems():
                    if key == 'id':
                        continue
                    old_course[key] = value
                old_course.save()
                updated += 1
            else:
                m.Course(**course).save()
                added += 1

    # Update courses with terms offered data
    with open(os.path.join(os.path.dirname(__file__),
            c.TERMS_OFFERED_DATA_DIR, 'terms_offered.txt')) as f:

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

    print 'OpenData courses, added: %d, updated: %d' % (added, updated)
    print 'Total courses:', m.Course.objects.count()


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
        elif (re.findall('^[A-Z]+', split) and
              m.Department.objects.with_id(split.lower())):
            # We check it's uppercase, so we don't have false positives like
            # "Earth" that was part of "Earth Science student"

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

    file_names = glob.glob(os.path.join(os.path.dirname(__file__),
            c.REVIEWS_DATA_DIR, '*.txt'))
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
        matches = re.findall(r'([a-z]+).*?([0-9]{3}[a-z]?)(?:[^0-9]|$)',
                             course)
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
                elif menlo_rating >= 4:
                    return 1
                else:
                    return None
            except:
                return None

        # TODO(mack): include 'r_helpful'?
        if 'r_clarity' in review:
            clean_review['professor_review'].clarity = \
                normalize_rating(review['r_clarity'])
        if 'r_easy' in review:
            clean_review['course_review'].easiness = \
                normalize_rating(review['r_easy'])
        if 'r_interest' in review:
            clean_review['course_review'].interest = \
                normalize_rating(review['r_interest'])

        clean_review['professor_review'].comment = review['comment']
        clean_review['professor_review'].comment_date = datetime.strptime(
            review['date'], '%m/%d/%y')

        return clean_review

    file_names = glob.glob(os.path.join(os.path.dirname(__file__),
            c.REVIEWS_DATA_DIR, '*.txt'))
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


def group_similar_exam_sections(exam_sections):
    """Groups together exam sections that have the same date, time,
       and location.

    Args:
        exam_sections: A list of sections for an exam as returned by OpenData's
            examschedule.json endpoint.

    Returns a consolidated list of sections in the same format, where each item
        has a unique date/time/location.
    """
    def order_sections(sections):
        sections_list = sorted(sections.split(', '))
        return ', '.join(sections_list)

    def is_similar(first, second):
        return (first.get('start_time') == second.get('start_time') and
                first.get('end_time') == second.get('end_time') and
                first.get('date') == second.get('date') and
                first.get('location') == second.get('location'))

    different_sections = []
    for section in exam_sections:
        similar_exams = [s for s in different_sections if
                is_similar(s, section)]
        if similar_exams:
            similar_exams[0]['section'] += ', ' + section.get('section')
        else:
            different_sections.append(section)

    for section in different_sections:
        section['section'] = order_sections(section.get('section'))

    return different_sections


def import_opendata_exam_schedules():
    """Import exam schedules data from the OpenData API"""
    today = datetime.today()
    file_name = os.path.join(
            os.path.dirname(__file__),
            '%s/uw_exams_%s.txt' % (c.EXAMS_DATA_DIR,
                                    today.strftime('%Y_%m_%d')))

    processed_exams = []
    errors = []
    with open(file_name, 'r') as f:
        data = json.load(f)

        # Data will contain something like this:
        #
        #   [{
        #       "course": "AFM 131",
        #       "sections": [
        #           {
        #               "date": "2014-04-17",
        #               "day": "Thursday",
        #               "end_time": "10:00 PM",
        #               "location": "DC 1350",
        #               "notes": "",
        #               "section": "001",
        #               "start_time": "7:30 PM"
        #           },
        #           {
        #               "date": "",
        #               "day": "",
        #               "end_time": "",
        #               "location": "",
        #               "notes": "See blah blah blah",
        #               "section": "081 Online",
        #               "start_time": ""
        #           }
        #       ]
        #   }, ...]
        #
        # TODO(jlfwong): Refactor this to separate concerns of file IO, db
        # storage, and data processing so that the data processing step can be
        # tested, and this example can be moved into tests.

        for exam_data in data:
            course_id = m.Course.code_to_id(exam_data.get('course'))
            grouped_sections = group_similar_exam_sections(
                    exam_data.get('sections', []))
            for section_data in grouped_sections:
                section = section_data.get('section')
                day = section_data.get('day')

                # Catch these to be more detailed in our errors
                if section.endswith('Online'):
                    errors.append("Skipping online course: %s %s"
                                % (course_id, section))
                    continue
                if 'Exam removed' in day:
                    errors.append("Skipping removed course: %s" % (course_id))
                    continue
                if 'See http:' in day:
                    errors.append("Skipping url for course: %s" % (course_id))
                    continue

                # E.g. 2014-04-17
                date = section_data.get('date')
                # E.g. 11:30 AM
                start_time = section_data.get('start_time')
                end_time = section_data.get('end_time')
                # E.g. 2014-04-17 7:30 PM
                #      2014-04-17 10:00 PM
                date_format = "%Y-%m-%d %I:%M %p"
                start_date_string = "%s %s" % (date, start_time)
                end_date_string = "%s %s" % (date, end_time)

                try:
                    start_date = rmc_util.eastern_to_utc(
                        datetime.fromtimestamp(
                            time.mktime(
                                time.strptime(start_date_string,
                                            date_format))))
                    end_date = rmc_util.eastern_to_utc(
                        datetime.fromtimestamp(
                            time.mktime(
                                time.strptime(end_date_string, date_format))))
                except Exception as exp:
                    errors.append("Could not get date (%s)\n%s" %
                                  (section_data, exp))
                    continue

                exam = m.Exam(
                    course_id=course_id,
                    sections=section,
                    start_date=start_date,
                    end_date=end_date,
                    location=section_data.get('location'),
                    info_known=bool(start_date and end_date),
                )
                processed_exams.append(exam)

    # Do some sanity checks to make sure OpenData is being reasonable.
    # This number is arbitrary and just reminds us to double-check
    # TODO(Sandy): This ranges from 775 (Fall & Winter) to 325 (Spring)
    season = m.Term.get_season_from_id(m.Term.get_current_term_id())
    EXAM_ITEMS_THRESHOLD = 325 if season == 'Spring' else 775
    if len(processed_exams) < EXAM_ITEMS_THRESHOLD:
        raise ValueError("processor.py: too few exam items %d (< %d)"
                         % (len(processed_exams), EXAM_ITEMS_THRESHOLD))

    # Everything should be fine by here, drop the old exams collection
    m.Exam.objects.delete()
    for exam in processed_exams:
        exam.save()

    return errors


def _opendata_to_section_meeting(data, term_year):
    """Converts OpenData class section info to a SectionMeeting instance.

    Args:
        data: An object from the `classes` field returned by OpenData.
        term_year: The year this term is in.
    """
    date = data['date']
    days = []
    if date['weekdays']:
        days = re.findall(r'[A-Z][a-z]?',
                date['weekdays'].replace('U', 'Su'))

    # TODO(david): Actually use the term begin/end dates when we get nulls
    date_format = '%m/%d'
    start_date = datetime.strptime(date['start_date'], date_format).replace(
            year=term_year) if date['start_date'] else None
    end_date = datetime.strptime(date['end_date'], date_format).replace(
            year=term_year) if date['end_date'] else None

    time_format = '%H:%M'

    # TODO(david): DRY-up
    start_seconds = None
    if date['start_time']:
        start_time = datetime.strptime(date['start_time'], time_format)
        start_seconds = (start_time -
                start_time.replace(hour=0, minute=0, second=0)).seconds

    end_seconds = None
    if date['end_time']:
        end_time = datetime.strptime(date['end_time'], time_format)
        end_seconds = (end_time -
                end_time.replace(hour=0, minute=0, second=0)).seconds

    meeting = m.SectionMeeting(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        days=days,
        start_date=start_date,
        end_date=end_date,
        building=data['location']['building'],
        room=data['location']['room'],
        is_tba=date['is_tba'],
        is_cancelled=date['is_cancelled'],
        is_closed=date['is_closed'],
    )

    if data['instructors']:
        last_name, first_name = data['instructors'][0].split(',')
        prof_id = m.Professor.get_id_from_name(first_name, last_name)
        if not m.Professor.objects.with_id(prof_id):
            m.Professor(id=prof_id, first_name=first_name,
                    last_name=last_name).save()
        meeting.prof_id = prof_id

    return meeting


def _clean_section(data):
    """Converts OpenData section info to a dict that can be consumed by
    Section.
    """
    course_id = m.Course.code_to_id(data['subject'] + data['catalog_number'])
    term_id = m.Term.get_term_id_from_quest_id(data['term'])
    section_type, section_num = data['section'].split(' ')
    last_updated = dateutil.parser.parse(data['last_updated'])

    year = m.Term.get_year_from_id(term_id)
    meetings = map(lambda klass: _opendata_to_section_meeting(klass, year),
            data['classes'])

    return {
        'course_id': course_id,
        'term_id': term_id,
        'section_type': section_type.upper(),
        'section_num': section_num,
        'campus': data['campus'],
        'enrollment_capacity': data['enrollment_capacity'],
        'enrollment_total': data['enrollment_total'],
        'waiting_capacity': data['waiting_capacity'],
        'waiting_total': data['waiting_total'],
        'meetings': meetings,
        'class_num': str(data['class_number']),
        'units': data['units'],
        'note': data['note'],
        'last_updated': last_updated,
    }

def _clean_scholarship(data):
    """Converts OpenData scholarship data in to a dict that can be used by
    Scholarship
    """
    return {
        'id': str(data['id']),
        'title': data['title'],
        'description': data['description'],
        'citizenship': data['citizenship'],
        'programs': data['programs'],
        'eligibility': data['application']['eligibility'],
        'instructions': data['application']['instructions'],
        'enrollment_year': data['application']['enrollment_year'],
        'contact': data['contact'],
        'link': data['link'],
    }

def import_opendata_sections():
    num_added = 0
    num_updated = 0

    filenames = glob.glob(os.path.join(os.path.dirname(__file__),
            c.SECTIONS_DATA_DIR, '*.json'))

    for filename in filenames:
        with open(filename, 'r') as f:
            data = json.load(f)

            for section_data in data:
                section_dict = _clean_section(section_data)

                # TODO(david): Is there a more natural way of doing an
                #     upsert with MongoEngine?
                existing_section = m.Section.objects(
                        course_id=section_dict['course_id'],
                        term_id=section_dict['term_id'],
                        section_type=section_dict['section_type'],
                        section_num=section_dict['section_num'],
                ).first()

                if existing_section:
                    for key, val in section_dict.iteritems():
                        existing_section[key] = val
                    existing_section.save()
                    num_updated += 1
                else:
                    m.Section(**section_dict).save()
                    num_added += 1

    print 'Added %s sections and updated %s sections' % (
            num_added, num_updated)

def import_scholarships():
    num_added = 0
    num_updated = 0

    filenames = glob.glob(os.path.join(os.path.dirname(__file__),
            c.SCHOLARSHIPS_DATA_DIR, '*.json'))

    for filename in filenames:
        with open(filename, 'r') as f:
            data = json.load(f).get('data')

            for scholarship_data in data:
                scholarship_dict = _clean_scholarship(scholarship_data)

                existing_scholarship = m.Scholarship.objects(
                        id=scholarship_dict['id']
                ).first()

                if existing_scholarship:
                    for key, val in scholarship_dict.iteritems():
                        if key != 'id':
                            existing_scholarship[key] = val
                    existing_scholarship.save()
                    num_updated += 1
                else:
                    m.Scholarship(**scholarship_dict).save()
                    num_added += 1

    print 'Added %s scholarships and updated %s scholarships' % (
          num_added, num_updated)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    supported_modes = ['professors', 'departments', 'courses', 'reviews']
    parser.add_argument('mode', help='one of %s' % ','.join(supported_modes))
    args = parser.parse_args()

    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)

    if args.mode == 'professors':
        import_professors()
    elif args.mode == 'departments':
        import_departments()
    elif args.mode == 'courses':
        import_courses()
    elif args.mode == 'reviews':
        import_reviews()
    elif args.mode == 'exams':
        import_opendata_exam_schedules()
    elif args.mode == 'sections':
        import_opendata_sections()
    elif args.mode == 'scholarships':
        import_scholarships()
    else:
        sys.exit('The mode %s is not supported' % args.mode)

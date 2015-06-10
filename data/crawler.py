import argparse
import datetime
import json
import logging
import os
import sys
import time
import traceback
import urllib2
import requests

from lxml.html import soupparser

import rmc.shared.secrets as s
import rmc.shared.constants as c
import rmc.models as m
import mongoengine as me


API_UWATERLOO_V2_URL = 'https://api.uwaterloo.ca/v2'

reload(sys)
sys.setdefaultencoding('utf-8')

errors = []


def html_parse(url, num_tries=5, parsers=[soupparser]):
    # TODO(mack): should also try lxml.html parser since soupparser could also
    # potentially not parse correctly
    #for parser in [soupparser]:
    for parser in parsers:
        tries = 0
        while True:
            try:
                u = urllib2.urlopen(url)
                result = u.read()
                u.close()
                return parser.fromstring(result)
            except:
                tries += 1
                if tries == num_tries:
                    break

                wait = 2 ** (tries + 1)
                error = 'Exception parsing %s. Sleeping for %s secs'.format(
                            url=url, wait=wait)
                errors.append(error)
                print error
                time.sleep(wait)

    return None


def get_departments():
    def clean_department(d):
        return {
            'subject': d['subject'],
            'name': d['description'],
            'faculty_id': d['group'],
        }

    response = requests.get('%s/codes/subjects.json?key=%s' % (
        API_UWATERLOO_V2_URL, s.OPEN_DATA_API_KEY)).text
    open_data_deps_json = json.loads(response)

    departments = []
    for d in open_data_deps_json['data']:
        departments.append(clean_department(d))

    file_name = os.path.join(os.path.realpath(os.path.dirname(__file__)),
            '%s/opendata2_departments.json' % c.DEPARTMENTS_DATA_DIR)
    with open(file_name, 'w') as f:
        json.dump(departments, f)

    print 'found: %d departments' % len(departments)


def get_data_from_url(url, num_tries=5):
    tries = 0
    while True:
        try:
            u = urllib2.urlopen(url)
            result = u.read()
            u.close()
            if result:
                data = json.loads(result)
                return data
            return None
        except:
            tries += 1
            if tries == num_tries:
                break

            wait = 2 ** (tries + 1)
            error = 'Exception for {url}. Sleeping for {wait} secs'.format(
                    url=url, wait=wait)
            errors.append(error)
            print error
            traceback.print_exc(file=sys.stdout)
            time.sleep(wait)

    return None


def file_exists(path):
    try:
        with open(path):
            pass
        return True
    except:
        return False


def get_opendata2_courses():
    good_courses = 0

    file_name = os.path.join(os.path.realpath(os.path.dirname(__file__)),
        '%s/opendata2_departments.json' % c.DEPARTMENTS_DATA_DIR)
    with open(file_name) as departments_file:
        departments = json.load(departments_file)

    # Create a text file for every department
    for d in departments:
        department = d['subject']
        open_data_json = requests.get(
                'https://api.uwaterloo.ca/v2/courses/{0}.json?key={1}'.format(
                department.upper(), s.OPEN_DATA_API_KEY)).json
        open_data_catalog_numbers = []

        for course in open_data_json['data']:
            open_data_catalog_numbers.append(course['catalog_number'])

        # We now poll the individual endpoints of each course for the data
        current_dep_json = []
        course_url = 'https://api.uwaterloo.ca/v2/courses/{0}/{1}.json?key={2}'
        for course in open_data_catalog_numbers:
            good_courses += 1
            json_data = requests.get(course_url.format(department.upper(),
                    course, s.OPEN_DATA_API_KEY)).json
            current_dep_json.append(json_data['data'])

        out_file_name = os.path.join(
                os.path.realpath(os.path.dirname(__file__)),
                'opendata2_courses/%s.json' % department.lower())
        with open(out_file_name, 'w') as courses_out:
            json.dump(current_dep_json, courses_out)

    print 'Found {num} good courses'.format(num=good_courses)


def get_opendata_exam_schedule():
    api_key = s.OPEN_DATA_API_KEY
    current_term_id = m.Term.get_current_term_id()
    current_quest_termid = m.Term.get_quest_id_from_term_id(current_term_id)
    url = ('http://api.uwaterloo.ca/v2/terms/{term_id}/examschedule.json'
           '?key={api_key}').format(api_key=api_key,
                                    term_id=current_quest_termid)

    data = get_data_from_url(url)
    try:
        data = data['data']
    except KeyError:
        print 'crawler.py: ExamSchedule API call failed with data:\n%s' % data
        raise

    today = datetime.datetime.today()
    file_name = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '%s/uw_exams_%s.txt' % (c.EXAMS_DATA_DIR, today.strftime('%Y_%m_%d')))
    with open(file_name, 'w') as f:
        json.dump(data, f)


# TODO(david): This needs to be updated on a regular basis and not use
#     uwlive.ca (hopefully get data from OpenData)
def get_terms_offered():
    found = 0
    missing_course_ids = []

    terms_offered_by_course = {}
    css_class_to_term = {
        'offer-spring': 'S',
        'offer-winter': 'W',
        'offer-fall': 'F',
    }

    def save_data():
        print 'writing to file'

        file_name = os.path.join(
                sys.path[0], '%s/terms_offered.txt' % c.TERMS_OFFERED_DATA_DIR)
        with open(file_name, 'w') as f:
            json.dump(terms_offered_by_course, f)

        file_name = os.path.join(
                        sys.path[0],
                        '%s/missing_courses.txt' % c.TERMS_OFFERED_DATA_DIR)
        with open(file_name, 'w') as f:
            json.dump(missing_course_ids, f)

    for course in list(m.Course.objects):
        terms_offered_by_course[course.id] = []

        if len(terms_offered_by_course) % 100 == 0:
            save_data()

        department_id = course.department_id
        number = course.number

        url = 'http://uwlive.ca/courselect/courses/%s/%s' % (
                department_id, number)
        html_tree = html_parse(url, num_tries=1)
        if html_tree is None:
            missing_course_ids.append(course.id)
        else:
            for css_class, term_code in css_class_to_term.items():
                if html_tree.xpath('.//li[@class="%s"]' % css_class):
                    terms_offered_by_course[course.id].append(term_code)

        if len(terms_offered_by_course[course.id]):
            found += 1
            print '+ %s' % course.id
        else:
            print '- %s' % course.id

        time.sleep(0.5)

    save_data()

    print 'FOUND: %d' % found
    print 'MISSING: %d' % len(missing_course_ids)


def get_subject_sections_from_opendata(subject, term):
    """Get info on all sections offered for all courses of a given subject and
    term.

    Args:
        subject: The department ID (eg. CS)
        term: The 4-digit Quest term code (defaults to current term)
    """
    url = ('{api_url}/terms/{term}/{subject}/schedule.json'
            '?key={api_key}'.format(
                api_url=API_UWATERLOO_V2_URL,
                api_key=s.OPEN_DATA_API_KEY,
                subject=subject,
                term=term,
    ))

    data = get_data_from_url(url)
    try:
        sections = data['data']
    except (KeyError, TypeError):
        logging.exception('crawler.py: Schedule API call failed with'
                " url %s and data:\n%s" % (url, data))
        raise

    return sections


def get_opendata_sections():
    current_term_id = m.Term.get_current_term_id()
    next_term_id = m.Term.get_next_term_id()

    # We resolve the query (list()) because Mongo's cursors can time out
    for department in list(m.Department.objects):
        sections = []
        for term_id in [current_term_id, next_term_id]:
            quest_term_id = m.Term.get_quest_id_from_term_id(term_id)
            sections += get_subject_sections_from_opendata(
                    department.id.upper(), quest_term_id)

        # Now write all that data to file
        filename = os.path.join(os.path.dirname(__file__),
                '%s/%s.json' % (c.SECTIONS_DATA_DIR, department.id))
        with open(filename, 'w') as f:
            json.dump(sections, f)

def get_scholarships():
    url = ('https://api.uwaterloo.ca/v2/awards/undergraduate.json?'
          'key=%s' % s.OPEN_DATA_API_KEY)
    response = requests.get(url).text

    scholarship_data = json.loads(response)

    filename = os.path.join(os.path.dirname(__file__),
            '%s/scholarships.json' % c.SCHOLARSHIPS_DATA_DIR)

    with open(filename, 'w') as f:
        json.dump(scholarship_data, f)


if __name__ == '__main__':
    me.connect(c.MONGO_DB_RMC)

    parser = argparse.ArgumentParser()
    supported_modes = ['departments', 'opendata2_courses', 'terms_offered',
            'opendata_sections', 'scholarships']

    parser.add_argument('mode', help='one of %s' % ','.join(supported_modes))
    args = parser.parse_args()

    if args.mode == 'departments':
        get_departments()
    elif args.mode == 'opendata2_courses':
        get_opendata2_courses()
    elif args.mode == 'terms_offered':
        get_terms_offered()
    elif args.mode == 'opendata_exam_schedule':
        get_opendata_exam_schedule()
    elif args.mode == 'opendata_sections':
        get_opendata_sections()
    elif args.mode == 'scholarships':
        get_scholarships()
    else:
        sys.exit('The mode %s is not supported' % args.mode)

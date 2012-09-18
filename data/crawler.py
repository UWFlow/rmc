import rmc.shared.constants as c

import argparse
import glob
from lxml import html
import json
import os
import time
import sys
import re
import traceback
import urllib2

reload(sys)
sys.setdefaultencoding('utf-8')

errors = []

def html_parse(url):
    for parser in [html]:
        tries = 0
        while True:
            try:
                u = urllib2.urlopen(url)
                result = u.read()
                u.close()
                return parser.fromstring(result)
            except:
                wait = 2 ** (tries + 1)
                error = 'Exception parsing {url}. Sleeping for {wait} secs'.format(url=url, wait=wait)
                errors.append(error)
                print error
                time.sleep(wait)
                tries += 1
                if tries == 5:
                    break
    raise

def get_departments():
    faculties = ['Applied Health Sciences', 'Arts', 'Engineering', 'Environment', 'Mathematics', 'Science']
    count = 0
    for faculty in faculties:
        print 'FACULTY: ' + faculty
        url = 'http://ugradcalendar.uwaterloo.ca/group/Courses-Faculty-of-{0}'.format(faculty.replace(' ', '-'))
        print 'url is', url
        tree = html_parse(url)
        for e_department in tree.xpath('.//span[@id="ctl00_contentMain_lblContent"]/ul/ul/li/a'):
            count += 1
            print 'text: ' + e_department.text_content() + ', link: ' + e_department.attrib['href']
    print 'found: {0} departments'.format(count)

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

def get_department_codes():
    all_deps = set()
    f = open(os.path.join(sys.path[0], '%s/departments.txt' % c.DEPARTMENTS_DATA_DIR))
    data = json.load(f)
    f.close()
    for result in data:
        all_deps.add(result['Acronym'].strip().lower())
    return all_deps

def file_exists(path):
    try:
        with open(path) as f: pass
        return True
    except:
        return False

def get_uwdata_courses():
    deps = get_department_codes()
    api_keys = [
        '66e3d70ec73751bc2c97e5ed0928d540',
        '29d72333db3101ba4116f8f53a43ec1a',
        'f3de93555ceb01c4a3549c9246e26e80',
    ]

    for idx, dep in enumerate(deps):
        try:
            file_path = os.path.join(
                sys.path[0], '%s/%s.txt' % (c.UWDATA_COURSES_DATA_DIR, dep))

            if file_exists(file_path):
                continue

            api_key = api_keys[idx % len(api_keys)]
            url = 'http://api.uwdata.ca/v1/faculty/%s/courses.json?key=%s' % (dep, api_key)
            data = get_data_from_url(url, num_tries=1)
            courses = data['courses']

            with open(file_path, 'w') as f:
                f.write(json.dumps(courses))
            print 'good dep: %s' % dep

        except Exception as ex:
            print 'exp: %s' % ex
            print 'bad dep: %s' % dep

        time.sleep(121)

def get_opendata_courses():
    deps = get_department_codes()

    courses = {}
    file_names = glob.glob(os.path.join(sys.path[0], '%s/*.txt' % c.RATINGS_DATA_DIR))
    for file_name in file_names:
        f = open(file_name, 'r')
        data = json.load(f)
        f.close()
        for rating in data['ratings']:
            course = rating['class']
            if course is None:
                continue
            course = course.strip().lower()
            matches = re.findall(r'([a-z]+).*?([0-9]{3}[a-z]?)(?:[^0-9]|$)', course)
            if len(matches) != 1 or len(matches[0]) != 2:
                continue
            dep = matches[0][0]
            if dep not in deps:
                continue
            if not dep in courses:
                courses[dep] = set()
            print 'Matched regex {dep}{num}'.format(dep=dep, num=matches[0][1])
            courses[dep].add(matches[0][1])

    errors = []
    api_key = 'ead3606c6f096657ebd283b58bf316b6'
    bad_courses = 0
    bad_course_names = set()
    good_courses = 0
    for dep in courses:
        dep_courses = {}
        print 'Processing department {dep}'.format(dep=dep)
        for num in courses[dep]:
            if num in dep_courses:
                continue
            print '  Processing number {num}'.format(num=num)
            query = dep + num
            url = 'http://api.uwaterloo.ca/public/v1/' + \
                    '?key={api_key}&service=CourseInfo&q={query}&output=json'.format(api_key=api_key, query=query)
            data = get_data_from_url(url)
            try:
                data = data['response']['data']
            except:
                is_bad_course = True

            if not data:
                is_bad_course = True
            elif isinstance(data['result'], list):
                is_bad_course = True
                print 'More than one result for query {query}'.format(query=query)

            if is_bad_course:
                bad_courses += 1
                bad_course_names.add(query)
                error = 'Found new bad course {course}'.format(course=query)
                print error
                errors.append(error)
            else:
                good_courses += 1
                dep_courses[num] = data['result']
                print 'Found new course {query}'.format(query=query)
        try:
            f = open(os.path.join(sys.path[0], '%s/%s.txt' % (c.OPENDATA_COURSES_DATA_DIR, dep)), 'w')
            f.write(json.dumps(dep_courses))
            f.close()
        except Exception:
            errors = 'Exception writing to file {dep}.txt'.format(dep=dep)
            errors.append(error)
            print error
            traceback.print_exc(file=sys.stdout)

    print 'Found {num} errors'.format(num=len(errors))
    count = 0
    for error in errors:
        count += 1
        print count, ':', error

    print 'Found {num} bad courses'.format(num=bad_courses)
    print 'Found {num} good courses'.format(num=good_courses)
    print 'Bad course names: {names}'.format(names=bad_course_names)


def get_bad_courses():
    # PLAN OF ATTACK:
    # 1) run all courses against uwlive.ca, any good courses processed
    # 2) run remaining against uwaterloo api search, if multiple results returned, ignore
    f = open(os.path.join(sys.path[0], 'misc/bad_courses.txt'))
    data = json.load(f)
    count = 0
    errors = []
    for course in data:
        count += 1
        url = 'http://uwlive.ca/courselect/search?q={query}'.format(query=course)
        tries = 0
        try:
            u = urllib2.urlopen(url)
            result = u.read()
            u.close()
            if result and result.find('Your search returned 0 results') < 0:
                print 'good: ' + course
            else:
                print 'bad: ' + course
        except:
            print 'exception: ' + course
            #wait = 2 ** (tries + 1)
            #error = 'Exception for {url}. Sleeping for {wait} secs'.format(url=url, wait=wait)
            #errors.append(error)
            #print error
            #traceback.print_exc(file=sys.stdout)
            #time.sleep(wait)
            #tries += 1
            #if tries == 5:
            #  break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    supported_modes = ['departments', 'courses', 'bad_courses']
    parser.add_argument('mode', help='one of %s' % ','.join(supported_modes))
    args = parser.parse_args()

    if args.mode == 'departments':
        get_departments()
    elif args.mode == 'opendata_courses':
        get_opendata_courses()
    elif args.mode == 'uwdata_courses':
        get_uwdata_courses()
    elif args.mode == 'bad_courses':
        get_bad_courses()
    else:
        sys.exit('The mode %s is not supported' % args.mode)

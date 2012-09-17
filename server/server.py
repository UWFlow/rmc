import flask
import pymongo
import re
import functools

import rmc.shared.constants as c

app = flask.Flask(__name__)
db = pymongo.Connection(c.MONGO_HOST, c.MONGO_PORT).rmc

@app.route('/')
def index():
    return flask.render_template('index_page.html')

@app.route('/profile', defaults={'fbid': None})
@app.route('/profile/<int:fbid>')
def profile(fbid):
    if not fbid:
        return flask.render_template('profile_page.html')
    else:
        # TODO(mack): handle viewing another user's profile
        pass

@app.route('/courses')
def courses():
    # TODO(mack): move into COURSES_SORT_MODES
    def clean_sort_modes(sort_mode):
        return {
            'value': sort_mode['value'],
            'name': sort_mode['name'],
            'direction': sort_mode['direction'],
        }
    sort_modes = map(clean_sort_modes, COURSES_SORT_MODES)
    directions = [
        { 'value': pymongo.ASCENDING, 'name': 'increasing' },
        { 'value': pymongo.DESCENDING, 'name': 'decreasing' },
    ]
    return flask.render_template(
        'course_page.html',
        sort_modes=sort_modes,
        directions=directions,
    )
# TODO(mack): move API's to separate file
# TODO(mack): add security measures (e.g. require auth, xsrf cookie)
###############################
######## API ##################
###############################

import random

@app.route('/api/courses/<string:course_names>', methods=['GET'])
# TODO(mack): find a better name for function
def get_courses(course_names):
    course_names = course_names.upper()
    course_names = course_names.split(',')
    courses_list = list(db.courses.find(
      {'name': { '$in': course_names }},
      {'_id': 0}
    ))

# XXX(Sandy): Use the filters instead of find() all
    '''
    critiques = list(db.course_evals.find(
      {'course': { '$in': course_names }},
      {'_id': 0}
    ))
    '''
    critiques = [dict(x) for x in db.course_evals.find()]

    clean_course_func = get_clean_course_func(critiques)
    # TODO(mack): do this more cleanly
    courses_list = map(clean_course_func, courses_list)
    courses = {}
    for course in courses_list:
        courses[course['id']] = course

    return flask.jsonify(courses=courses)

COURSES_SORT_MODES = [
    # TODO(mack): 'num_friends'
    { 'value': 'num_ratings', 'name': 'by popularity', 'direction': pymongo.DESCENDING, 'field': 'ratings.count'},
    { 'value': 'alphabetical', 'name': 'alphabetically', 'direction': pymongo.ASCENDING, 'field': 'name'},
    { 'value': 'overall', 'name': 'by overall rating', 'direction': pymongo.DESCENDING, 'field': 'ratings.aggregate.average'},
    { 'value': 'interest', 'name': 'by interest', 'direction': pymongo.DESCENDING, 'field': 'ratings.interest.average'},
    { 'value': 'easiness', 'name': 'by easiness' , 'direction': pymongo.DESCENDING, 'field': 'ratings.easy.average'},
]
COURSES_SORT_MODES_BY_VALUE = {}
for sort_mode in COURSES_SORT_MODES:
    COURSES_SORT_MODES_BY_VALUE[sort_mode['value']] = sort_mode


@app.route('/api/course-search', methods=['GET'])
# TODO(mack): find a better name for function
def search_courses():
    # TODO(mack): create enum of sort options
    # num_friends, num_ratings, overall, interest, easiness

    request = flask.request
    keywords = request.values.get('keywords')
    sort_mode = request.values.get('sort_mode', 'num_ratings')
    direction = int(request.values.get('direction', pymongo.DESCENDING))
    count = int(request.values.get('count', 10))
    offset = int(request.values.get('offset', 0))

    filters = []
    if keywords:
        keywords_re = re.compile(keywords, re.IGNORECASE)
        keywords_filters = []
        for field in ['name', 'title']:
            keywords_filters.append({field: {'$regex': keywords_re}})
        filters.append({'$or': keywords_filters})
    if len(filters) > 0:
        unsorted_courses = db.courses.find({'$and': filters})
        critiques = db.course_evals.find({'$and': filters})
    else:
        unsorted_courses = db.courses.find()
        critiques = db.course_evals.find()

    sort_options = COURSES_SORT_MODES_BY_VALUE[sort_mode]
    sorted_courses = unsorted_courses.sort(
        sort_options['field'],
        direction=direction,
    )
    limited_courses = sorted_courses.skip(offset).limit(count)

    clean_course_func = get_clean_course_func(critiques)
    courses = map(clean_course_func, limited_courses)
    has_more = len(courses) == count
    return flask.jsonify(courses=courses, has_more=has_more)


# Helper functions

def clean_course(course, critiques):
    NORMALIZE_FACTOR = 5
    interest_count = course['ratings']['interest']['count']
    interest_total = float(course['ratings']['interest']['total']) / NORMALIZE_FACTOR
    easiness_count = course['ratings']['easy']['count']
    easiness_total = float(course['ratings']['easy']['total']) / NORMALIZE_FACTOR
    overall_course_count = course['ratings']['aggregate']['count']
    overall_course_total = float(course['ratings']['aggregate']['average']) / NORMALIZE_FACTOR * overall_course_count

    if course['name'] in critiques:
        print course['name'] + ' found in critiques'
# TODO(Sandy): eventually pass in prof specific info here (from crit)
        for crit in critiques[course['name']]:
            int_count = crit['interest_count']
            eas_count = crit['easiness_count']
            co_count = crit['overall_course_count']

            interest_total += crit['interest'] * int_count
            easiness_total += crit['easiness'] * eas_count
            overall_course_total += crit['overall_course'] * co_count
            interest_count += int_count
            easiness_count += eas_count
            overall_course_count += co_count
    else:
# TODO(Sandy): log somewhere so we can track this
        print course['name'] + ' not found in critiques'

# TODO(Sandy): Might we want to normalize the overall on the client-side too?
    overall_course = overall_course_total / overall_course_count * NORMALIZE_FACTOR
    overall_course = round(overall_course*10)/10

    def format_professor_name(professor_name):
        splits = professor_name.split(',', 1)
        professor_name = splits[0]
        if len(splits) == 2:
            professor_name = '%s %s' % (splits[1].strip(), splits[0].strip())
        else:
            professor_name = splits[0].strip()
        return professor_name

    professor_names = []
    for professor in course['professors']:
        professor_name = format_professor_name(professor['name'])
        professor_names.append(professor_name)
    professor_names = sorted(professor_names)

    return {
        'id': course['name'],
        'name': course['title'],
        'professorNames': professor_names,
        'numRatings': overall_course_count,
        'description': course['description'],
        'availFall': bool(int(course['availFall'])),
        'availSpring': bool(int(course['availSpring'])),
        'availWinter': bool(int(course['availWinter'])),
        # TODO(mack): get actual number for this
        'numFriendsTook': random.randrange(0, 20),
# XXX(Sandy): factor in critique data into overall
        'rating': overall_course,
        'ratings': [{
            'name': 'interest',
            'count': interest_count,
            'total': interest_total,
        }, {
            'name': 'easiness',
            'count': easiness_count,
            'total': easiness_total,
        }]
    }

def get_clean_course_func(critiques_data):
    course_crit_map = {}
    for critique in critiques_data:
        if not critique['course'] in course_crit_map:
            course_crit_map[critique['course']] = []
        course_crit_map[critique['course']].append(critique)

    return functools.partial(clean_course, critiques=course_crit_map)

if __name__ == '__main__':
  app.debug = True
  app.run()

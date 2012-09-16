import flask
import pymongo
import re

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

    # TODO(mack): do this more cleanly
    courses_list = map(clean_course, courses_list)
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
    direction = request.values.get('direction')
    if direction:
        direction = int(direction)
    else:
        direction = pymongo.DESCENDING
    count = request.values.get('count', 10)
    offset = request.values.get('offset', 0)

    filters = []
    if keywords:
        keywords_re = re.compile(keywords, re.IGNORECASE)
        keywords_filters = []
        for field in ['name', 'title']:
            keywords_filters.append({field: {'$regex': keywords_re}})
        filters.append({'$or': keywords_filters})
    if len(filters) > 0:
        unsorted_courses = db.courses.find({'$and': filters})
    else:
        unsorted_courses = db.courses.find()

    sort_options = COURSES_SORT_MODES_BY_VALUE[sort_mode]
    sorted_courses = unsorted_courses.sort(
        sort_options['field'],
        direction=direction,
    )
    limited_courses = sorted_courses.skip(offset).limit(count)
    courses = map(clean_course, limited_courses)
    print 'clean_course', courses
    return flask.jsonify(courses=courses)


# Helper functions

def clean_course(course):
    NORMALIZE_FACTOR = 5
    interest_count = course['ratings']['interest']['count']
    interest_total = float(course['ratings']['interest']['total']) / NORMALIZE_FACTOR
    easiness_count = course['ratings']['easy']['count']
    easiness_total = float(course['ratings']['easy']['total']) / NORMALIZE_FACTOR
    return {
        'id': course['name'],
        'name': course['title'],
        'numRatings': course['ratings']['aggregate']['count'],
        'description': course['description'],
        'availFall': bool(int(course['availFall'])),
        'availSpring': bool(int(course['availSpring'])),
        'availWinter': bool(int(course['availWinter'])),
        # TODO(mack): get actual number for this
        'numFriendsTook': random.randrange(0, 20),
        'rating': round(course['ratings']['aggregate']['average']*10)/10,
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


if __name__ == '__main__':
  app.debug = True
  app.run()

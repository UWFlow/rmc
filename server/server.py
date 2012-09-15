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
    return flask.render_template('course_page.html')

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

COURSES_SORT_MODES = {
    # TODO(mack): 'num_friends'
    'num_ratings': {'dir': pymongo.DESCENDING, 'field': 'ratings.count'},
    'overall': {'dir': pymongo.DESCENDING, 'field': 'ratings.aggregate.average'},
    'interest': {'dir': pymongo.DESCENDING, 'field': 'ratings.interest.average'},
    'easiness': {'dir': pymongo.DESCENDING, 'field': 'ratings.easy.average'},
}

@app.route('/api/course-search', methods=['GET'])
# TODO(mack): find a better name for function
def search_courses():
    # TODO(mack): create enum of sort options
    # num_friends, num_ratings, overall, interest, easiness

    request = flask.request
    search = request.values.get('search')
    sort_by = request.values.get('sort_by', 'num_ratings')
    count = request.values.get('count', 10)
    offset = request.values.get('offset', 0)

    filters = []
    if search:
        search_re = re.compile(search, re.IGNORECASE)
        search_filters = []
        for field in ['name', 'title']:
            search_filters.append({field: {'$regex': search_re}})
        filters.append({'$or': search_filters})
    if len(filters) > 0:
        unsorted_courses = db.courses.find({'$and': filters})
    else:
        unsorted_courses = db.courses.find()

    sort_options = COURSES_SORT_MODES[sort_by]
    sorted_courses = unsorted_courses.sort(
        sort_options['field'],
        # TODO(mack): add sort direction
        direction=sort_options['dir']
    )
    limited_courses = sorted_courses.skip(offset).limit(count)
    courses = map(clean_course, limited_courses)
    return flask.jsonify(courses=courses)


# Helper functions

def clean_course(course):
    return {
        'id': course['name'],
        'name': course['title'],
        'rating': round(course['ratings']['aggregate']['average']*10)/10,
        'numRatings': course['ratings']['aggregate']['count'],
        'description': course['description'],
        'availFall': bool(int(course['availFall'])),
        'availSpring': bool(int(course['availSpring'])),
        'availWinter': bool(int(course['availWinter'])),
        # TODO(mack): get actual number for this
        'numFriendsTook': random.randrange(0, 20),
    }


if __name__ == '__main__':
  app.debug = True
  app.run()

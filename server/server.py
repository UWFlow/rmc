import flask
import pymongo

import rmc.shared.constants as c

app = flask.Flask(__name__)
db = pymongo.Connection(c.MONGO_HOST, c.MONGO_PORT).rmc

@app.route('/')
def index():
    return flask.render_template('index_page.html')

@app.route('/profile')
def profile():
    return flask.render_template('profile_page.html')


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
    courses = list(db.courses.find(
      {'name': { '$in': course_names }},
      {'_id': 0}
    ))

    def clean_courses(course):
        return {
            'id': course['name'],
            'name': course['name'],
            'rating': round(course['ratings']['aggregate']['average']*10)/10,
            'num_ratings': course['ratings']['aggregate']['count'],
            'description': course['description'],
            # TODO(mack): get actual number for this
            'num_friends_took': random.randrange(0, 20)
        }
    # TODO(mack): do this more cleanly
    courses = map(clean_courses, courses)

    return flask.jsonify(courses=courses)

if __name__ == '__main__':
  app.debug = True
  app.run()

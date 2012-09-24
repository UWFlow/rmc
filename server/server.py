from bson import json_util
from datetime import datetime
import flask
import mongoengine as me
import pymongo
import re
import functools
import time

import rmc.shared.constants as c
import rmc.models as m

app = flask.Flask(__name__)
app.config.from_envvar('FLASK_CONFIG')
me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)

flask.render_template = functools.partial(flask.render_template,
        env=app.config['ENV'])


class ApiError(Exception):
    """
        All errors during api calls should use this rather than Exception
        directly.
    """
    pass


def get_current_user():
    """
        Get the logged in user (if it exists) based on fbid and fb_access_token.
        Cache the user across multiple calls during the same request.
    """
    req = flask.request

    if hasattr(req, 'current_user'):
        return req.current_user

    # TODO(Sandy): Eventually support non-fb users?
    fbid = req.cookies.get('fbid')
    fb_access_token = req.cookies.get('fb_access_token')
    if fbid is None or fb_access_token is None:
        req.current_user = None
    else:
        req.current_user = m.User.objects(
                fbid=fbid, fb_access_token=fb_access_token).first()

    return req.current_user

def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not get_current_user():
            resp = flask.make_response(flask.redirect('/'))
            resp.set_cookie('fbid', None)
            resp.set_cookie('fb_access_token', None)
            return resp

        return f(*args, **kwargs)

    return wrapper


@app.route('/')
def index():
    return flask.render_template('index_page.html',
            page_script='index_page.js')

@app.route('/profile', defaults={'fbid': None})
@app.route('/profile/<int:fbid>')
@login_required
def profile(fbid):
    req = flask.request
    user = get_current_user()
    if fbid:
        # Fbid's stored in our DB are unicode types
        fbid = unicode(fbid)

    def get_sorted_transcript_for_user(user):
        transcript = {}
        courses = m.Course.objects(id__in=user.course_history)
        courses = map(clean_course, courses)

        for course in courses:
            # TODO(Sandy): UserCourse is already fetched inside clean_course, don't do this twice
            user_course = m.UserCourse.objects(course_id=course['id'], user_id=user.id).first()
            transcript.setdefault(user_course.term_id, []).append(course)

        # TODO(Sandy): Do this more cleanly?
        sorted_transcript = []
        for term_id, course_models in sorted(transcript.items(), reverse=True):
            cur_term = m.Term(id=term_id)
            term_name = cur_term.name
            term_data = {
                'term_name': term_name,
                'course_models': course_models,
            }

            sorted_transcript.append(term_data)

        return sorted_transcript

    if not fbid or fbid == user.fbid:
        sorted_transcript = get_sorted_transcript_for_user(user)

    else:
        other_user = m.User.objects(fbid=fbid).first()
        sorted_transcript = get_sorted_transcript_for_user(other_user)
        # TODO(Sandy): Figure out what should and shouldn't be displayed when viewing someone else's profile

    return flask.render_template('profile_page.html',
            page_script='profile_page.js',
            transcript_data=json_util.dumps(sorted_transcript))

@app.route('/course')
def course():
    return flask.redirect('/courses', 301)  # Moved permanently

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
        'search_page.html',
        page_script='search_page.js',
        sort_modes=sort_modes,
        directions=directions,
    )

@app.route('/courses/<string:course_id>')
def courses_page(course_id):
    return flask.redirect('/course/%s' % course_id, 301)  # Moved permanently

@app.route('/course/<string:course_id>')
def course_page(course_id):
    return flask.render_template('course_page.html',
            page_script='course_page.js')

@app.route('/login', methods=['POST'])
def login():
    # TODO(Sandy): Differentiate between new account and update account
    req = flask.request
# TODO(Sandy): Use Flask Sessions instead of raw cookie
# TODO(Sandy): Security: Authenticate with fbsr (FB signed request) to ensure these are legit values

    fbid = req.cookies.get('fbid')
    fb_access_token = req.cookies.get('fb_access_token')
    # Compensate for network latency by subtracting 10 seconds
    fb_access_token_expiry_time = int(time.time()) + int(req.cookies.get('fb_access_token_expires_in')) - 10;
    fb_access_token_expiry_time = datetime.fromtimestamp(fb_access_token_expiry_time)

    if (fbid is None or
        fb_access_token is None or
        fb_access_token_expiry_time is None):
# TODO(Sandy): redirect to landing page, or nothing
            #print 'No fbid/access_token specified'
            return 'Error'

    # XXX(mack): Someone could pass fake fb_access_token for an fbid, need to
    # validate on facebook before creating the user
    user = m.User.objects(fbid=fbid).first()
    if user:
        user.fb_access_token = fb_access_token
        user.fb_access_token_expiry_time = fb_access_token_expiry_time
        user.save()
        return ''

    try:
        friend_fbids = flask.json.loads(req.form.get('friend_fbids'))
        gender = req.form.get('gender')
        first_name = req.form.get('first_name')
        middle_name = req.form.get('middle_name')
        last_name = req.form.get('last_name')
        email = req.form.get('email')

        now = datetime.now()
        user_obj = {
            'fbid': fbid,
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'email': email,
            'gender': gender,
            'fb_access_token': fb_access_token,
            'fb_access_token_expiry_time': fb_access_token_expiry_time,
#TODO(Sandy): Count visits properly
            'join_time': now,
            'join_source': m.User.JoinSource.FACEBOOK,
            'num_visits': 1,
            'last_visit_time': now,
#TODO(Sandy): Fetch from client side and pass here: name, email, school, program, faculty
        }
        user = m.User(**user_obj)
        user.add_friend_fbids(friend_fbids)

        user.save()
    except KeyError as ex:
        # Invalid key (shouldn't be happening)
# TODO(Sandy): redirect to landing page, or nothing
        print 'Exception while saving user: %s' % ex
        return 'Error'
    return ''


# TODO(mack): move API's to separate file
# TODO(mack): add security measures (e.g. require auth, xsrf cookie)
###############################
######## API ##################
###############################

@app.route('/api/courses/<string:course_ids>', methods=['GET'])
# TODO(mack): find a better name for function
def get_courses(course_ids):
    course_ids = [c.lower() for c in course_ids.split(',')]
    courses = m.Course.objects(
      id__in=course_ids,
    )

    # TODO(mack): do this more cleanly
    courses = map(clean_course, courses)
    course_map = {}
    for course in courses:
        course_map[course['id']] = course

    return json_util.dumps({ 'courses': course_map })

COURSES_SORT_MODES = [
    # TODO(mack): 'num_friends'
    { 'value': 'num_ratings', 'name': 'by popularity', 'direction': pymongo.DESCENDING, 'field': 'overall.count' },
    { 'value': 'alphabetical', 'name': 'alphabetically', 'direction': pymongo.ASCENDING, 'field': 'id' },
    { 'value': 'overall', 'name': 'by overall rating', 'direction': pymongo.DESCENDING, 'field': 'overall.rating' },
    { 'value': 'interest', 'name': 'by interest', 'direction': pymongo.DESCENDING, 'field': 'interest.rating' },
    { 'value': 'easiness', 'name': 'by easiness' , 'direction': pymongo.DESCENDING, 'field': 'easiness.rating' },
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

    if keywords:
        keywords = re.sub('\s+', ' ', keywords)
        keywords = keywords.split(' ')

        def regexify_keywords(keyword):
            keyword = keyword.lower()
            return re.compile('^%s' % keyword)
            #return '^%s' % keyword

        keywords = map(regexify_keywords, keywords)

    if keywords:
        unsorted_courses = m.Course.objects(_keywords__all=keywords)
    else:
        unsorted_courses = m.Course.objects()

    sort_options = COURSES_SORT_MODES_BY_VALUE[sort_mode]
    sort_instr = ''
    if direction < 0:
        sort_instr = '-'
    sort_instr += sort_options['field']

    sorted_courses = unsorted_courses.order_by(sort_instr)
    limited_courses = sorted_courses.skip(offset).limit(count)

    courses = map(clean_course, limited_courses)
    has_more = len(courses) == count

    return json_util.dumps({
        'courses': courses,
        'has_more': has_more,
    })


@app.route('/api/transcript', methods=['POST'])
@login_required
def upload_transcript():
    req = flask.request
    # TODO(Sandy): The following two cases involve users trying to import their transcript without being logged in.
    # We have to decide how we treat those users. E.g. we might prevent this from the frontend, or maybe save it and
    # tell them to make an account, etc

    user = get_current_user()
    user_id = user.id
    course_history_list = []

    try:
        courses_by_term = json_util.loads(req.form['courses_by_term'])

        for term in courses_by_term:
            season, year = term['name'].split()
            term_id = m.Term.get_id_from_year_season(year, season)

            for course_id in term['courseIds']:
                course_id = course_id.lower()
                # TODO(Sandy): Fill in course weight and grade info here
                user_course = m.UserCourse.objects(user_id=user_id, course_id=course_id, term_id=term_id).first()
                # TODO(Sandy): This assumes the transcript is real and we create a UserCourse even if the course_id
                # doesn't exist. It is possible for the user to spam us with fake courses on their transcript. Decide
                # whether or not we should be creating these entries
                if user_course is None:
                    user_course = m.UserCourse(user_id=user_id, course_id=course_id, term_id=term_id)
                    user_course.save()

                course_history_list.append(course_id)

        user.course_history = course_history_list
        user.save()

    except KeyError:
        # Invalid key (shouldn't be happening)
        print 'KeyError at /api/transcript.'
        return 'Error'

    return ''


@app.route('/api/user/course', methods=['POST', 'PUT'])
def user_course():
    # TODO(david) FIXME: check FB access token. Authentication + authorization!
    # TODO(david) FIXME: Use ORM, don't shove! and ensure_index
    # TODO(david): This should also update aggregate ratings table, etc.
    uc = json_util.loads(flask.request.data)

    now = datetime.now()
    def set_comment_time_if_necessary(review):
        if not review:
            return None

        # TODO(mack): add more stringent checking against user manually
        # setting time on the frontend
        if 'comment' in review and not 'comment_time':
            review['comment_time'] = now

    set_comment_time_if_necessary(uc.get('user_review'))
    set_comment_time_if_necessary(uc.get('course_review'))

    # TODO(mack): remove user_id hardcode
    user_id = m.User.objects.get(fbid='1647810326').id
    uc['user_id'] = user_id

    if 'course_review' in uc:
        uc['course_review'] = m.CourseReview(**uc['course_review'])

    if 'professor_review' in uc:
        uc['professor_review'] = m.ProfessorReview(**uc['professor_review'])

    uc = m.UserCourse(**uc)
    uc.save()

    return json_util.dumps(clean_user_course(uc))

###############################################################################
# Helper functions

def clean_user_course(user_course):
    course_review = user_course.course_review
    professor_review = user_course.professor_review

    return {
        'id': user_course.id,
        'user_id': user_course.user_id,
        'course_id': user_course.course_id,
        'professor_id': user_course.professor_id,
        'anonymous': user_course.anonymous,
        'course_review': {
            'easiness': course_review.easiness,
            'interest': course_review.interest,
            'comment': course_review.comment,
            'comment_time': course_review.comment_time,
        },
        'professor_review': {
            'clarity': professor_review.clarity,
            'passion': professor_review.passion,
            'comment': professor_review.comment,
            'comment_time': professor_review.comment_time,
        },
    }

def clean_course(course):

    def get_professors(course):
        professors = m.Professor.objects(
                id__in=course.professor_ids).only('id', 'first_name', 'last_name')
        return [{'id': p.id, 'name': p.name} for p in professors]

    def get_user_course(course):
        # XXX TODO(david) FIXME: search by user as well
        user_course = m.UserCourse.objects(course_id=course.id).first()

        if not user_course:
            return None

        return clean_user_course(user_course)

    return {
        'id': course.id,
        'code': course.code,
        'name': course.name,
        'description': course.description,
        #'availFall': bool(int(course['availFall'])),
        #'availSpring': bool(int(course['availSpring'])),
        #'availWinter': bool(int(course['availWinter'])),
        # TODO(mack): create user models for friends
        #'friends': [1647810326, 518430508, 541400376],
        'ratings': {
            'easiness': course.easiness.to_dict(),
            'interest': course.interest.to_dict(),
        },
        'overall': course.overall.to_dict(),
        'professors': get_professors(course),
        'userCourse': get_user_course(course),
    }

if __name__ == '__main__':
  app.debug = True
  app.run()

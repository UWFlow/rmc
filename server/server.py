from bson import json_util
from datetime import datetime
import bson
import flask
import functools
import itertools
import mongoengine as me
import pymongo
import re
import redis
import time

import rmc.shared.constants as c
import rmc.shared.secrets as s
import rmc.models as m

import base64
import hashlib
import hmac

app = flask.Flask(__name__)
app.config.from_envvar('FLASK_CONFIG')
me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
r = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)

flask.render_template = functools.partial(flask.render_template,
        env=app.config['ENV'])


# Jinja filters
@app.template_filter()
def tojson(obj):
    return json_util.dumps(obj)

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


# TODO(Sandy): Move this somewhere more appropraite. It is currently being called by api/transcript and /profile
def get_sorted_transcript_for_user(user):

    course_history = user.course_history
    if not course_history:
        return []

    transcript = {}
    cid_to_tid = {}
    cids = []

    ucs = m.UserCourse.objects(id__in=course_history).only(
            'course_id', 'term_id', 'program_year_id')
    for uc in ucs:
        cids.append(uc.course_id)
        cid_to_tid[uc.course_id] = (uc.term_id, uc.program_year_id)

    courses = m.Course.objects(id__in=cids)
    # TODO(mack): since this can be called for other users, need to
    # explicitly set the user to appropriate user; but should do
    # in cleaner way
    cleaned_courses = map(functools.partial(clean_course, user=user), courses)

    for course in cleaned_courses:
        transcript.setdefault(cid_to_tid[course['id']], []).append(course)

    # TODO(Sandy): Do this more cleanly?
    sorted_transcript = []
    for (term_id, program_year_id), course_models in sorted(transcript.items(), reverse=True):
        cur_term = m.Term(id=term_id)
        term_name = cur_term.name
        term_data = {
            'term_name': term_name,
            'program_year_id': program_year_id,
            'course_models': course_models,
        }

        sorted_transcript.append(term_data)

    return sorted_transcript


# TODO(mack): move this somewhere more appropriate
def get_user_obj(user):
    # fetch mutual friends from redis
    pipe = r.pipeline()
    for friend_id in user.friend_ids:
        pipe.smembers(user.mutual_courses_redis_key(friend_id))
    results = pipe.execute()

    zipped = itertools.izip(user.friend_ids, results)
    zipped = sorted(
        zipped,
        key=lambda (friend_id, mutual_course_ids): len(mutual_course_ids),
        reverse=True,
    )

    # TODO(mack): fetching and returning so much data!!!

    # find all courses we need to pass to frontend; combo of
    # your courses and friends' courses
    all_course_ids = set()
    for _, mutual_course_ids in zipped:
        all_course_ids = all_course_ids.union(set(mutual_course_ids))

    courses_map = {}
    for course in m.Course.objects(id__in=list(all_course_ids)):
        courses_map[course.id] = clean_course(course)

    # TODO(Sandy): So hacky, shouldn't need to pass in courses_map every time...
    user_obj = clean_user(user, courses_map)

    friend_map = {}
    for friend in m.User.objects(id__in=user.friend_ids):
        friend_map[friend.id] = clean_user(friend, courses_map)

    # get friend data for user
    user_obj['friends'] = []
    for friend_id, mutual_course_ids in zipped:
        friend_obj = friend_map[friend_id]
        friend_obj['mutual_courses'] = []

        # Get the list of mutual courses the user took with the friend
        for course_id in mutual_course_ids:
            if course_id in courses_map:
                friend_obj['mutual_courses'].append(
                    courses_map[course_id])

        user_obj['friends'].append(friend_obj)

    return user_obj


@app.route('/')
def index():
    return flask.render_template('index_page.html',
            page_script='index_page.js')


# TODO(mack): maybe support fbid in addition to user_id
@app.route('/profile', defaults={'user_id': None})
@app.route('/profile/<string:user_id>')
@login_required
def profile(user_id):

    user = get_current_user()

    if user_id:
        user_id = bson.ObjectId(user_id)

    if not user_id or user_id == user.id:
        sorted_transcript = get_sorted_transcript_for_user(user)
        profile_obj = get_user_obj(user)
        profile_obj['own_profile'] = True
    else:
        other_user = m.User.objects(id=user_id).first()
        if other_user is None:
            print 'other-use is None'
            return flask.redirect('/profile', 302)

        profile_obj = get_user_obj(other_user)
        profile_obj['own_profile'] = False
        sorted_transcript = get_sorted_transcript_for_user(other_user)
        # TODO(Sandy): Figure out what should and shouldn't be displayed when viewing someone else's profile

    if sorted_transcript:
        profile_obj['last_term_name'] = sorted_transcript[0]['term_name']

    return flask.render_template('profile_page.html',
        page_script='profile_page.js',
        transcript_data=json_util.dumps(sorted_transcript),
        profile_obj=profile_obj,
    )


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
    course = m.Course.objects.with_id(course_id)
    if not course:
        # TODO(david): 404 page
        flask.abort(404)

    course_cleaned = clean_course(course, expanded=True)

    # TODO(david): Protect against the </script> injection XSS hack
    return flask.render_template('course_page.html',
            page_script='course_page.js',
            course=course_cleaned,
            page_data=json_util.dumps(course_cleaned))


@app.route('/login', methods=['POST'])
def login():
    # TODO(Sandy): move this to a more appropriate place
    def base64_url_decode(inp):
        padding_factor = (4 - len(inp) % 4) % 4
        inp += "="*padding_factor
        return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

    def parse_signed_request(signed_request, secret):

        l = signed_request.split('.', 2)
        encoded_sig = l[0]
        payload = l[1]

        sig = base64_url_decode(encoded_sig)
        data = json_util.loads(base64_url_decode(payload))

        if data.get('algorithm').upper() != 'HMAC-SHA256':
            print 'Unknown algorithm during fbsr decode'
            return None

        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

        if sig != expected_sig:
            return None

        return data

    req = flask.request

    # TODO(Sandy): Use Flask Sessions instead of raw cookie

    fbid = req.cookies.get('fbid')
    # FIXME[uw](Sandy): No need to pass the fb_access_token up, we can just exchange fb_data.code for the token from FB
    # https://developers.facebook.com/docs/authentication/signed_request/
    fb_access_token = req.cookies.get('fb_access_token')
    # Compensate for network latency by subtracting 10 seconds
    fb_access_token_expiry_date = int(time.time()) + int(req.cookies.get('fb_access_token_expires_in')) - 10;
    fb_access_token_expiry_date = datetime.fromtimestamp(fb_access_token_expiry_date)
    fbsr = req.form.get('fb_signed_request')

    if (fbid is None or
        fb_access_token is None or
        fb_access_token_expiry_date is None or
        fbsr is None):
            # TODO(Sandy): redirect to landing page, or nothing
            # Shouldn't happen normally, user probably manually requested this page
            #print 'No fbid/access_token specified'
            return 'Error'

    # Validate against Facebook's signed request
    fb_data = parse_signed_request(fbsr, s.FB_APP_SECRET)
    if fb_data is None or fb_data['user_id'] != fbid:
        # Data is invalid
        return 'Error'

    # FIXME[uw](mack): Someone could pass fake fb_access_token for an fbid, need to
    # validate on facebook before creating the user. (Sandy): See the note above on using signed_request
    user = m.User.objects(fbid=fbid).first()
    if user:
        user.fb_access_token = fb_access_token
        user.fb_access_token_expiry_date = fb_access_token_expiry_date
        user.save()
        return ''

    # TODO(Sandy): Can remove the try except now becaues we're uisng form.get, same for all the other lines
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
            'fb_access_token_expiry_date': fb_access_token_expiry_date,
#TODO(Sandy): Count visits properly
            'join_date': now,
            'join_source': m.User.JoinSource.FACEBOOK,
            'num_visits': 1,
            'last_visited': now,
            'friend_fbids': friend_fbids,
#TODO(Sandy): Fetch from client side and pass here: name, email, school, program, faculty
        }
        user = m.User(**user_obj).save()
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

    def get_term_id(term_name):
        season, year = term_name.split()
        return m.Term.get_id_from_year_season(year, season)

    transcript_data = json_util.loads(req.form['transcriptData'])
    courses_by_term = transcript_data['coursesByTerm']

    for term in courses_by_term:
        term_id = get_term_id(term['name'])
        program_year_id = term['programYearId']

        for course_id in term['courseIds']:
            course_id = course_id.lower()
            # TODO(Sandy): Fill in course weight and grade info here
            user_course = m.UserCourse.objects(
                user_id=user_id, course_id=course_id, term_id=term_id).first()
            # TODO(Sandy): This assumes the transcript is real and we create a UserCourse even if the course_id
            # doesn't exist. It is possible for the user to spam us with fake courses on their transcript. Decide
            # whether or not we should be creating these entries
            if user_course is None:
                user_course = m.UserCourse(
                    user_id=user_id,
                    course_id=course_id,
                    term_id=term_id,
                    program_year_id=program_year_id,
                )
                user_course.save()

            course_history_list.append(user_course.id)

    if courses_by_term:
        last_term = courses_by_term[0]
        term_id = get_term_id(last_term['name'])
        user.last_term_id = term_id
        user.last_program_year_id = last_term['programYearId']
    user.program_name = transcript_data['programName']
    user.student_id = str(transcript_data['studentId'])
    user.course_history = course_history_list
    user.cache_mutual_courses(r)
    user.save()

    return ''


@app.route('/api/remove_transcript', methods=['POST'])
@login_required
def remove_transcript():
    user = get_current_user()
    user.course_history = []
    user.save()
    return flask.make_response(flask.redirect('/'))


# XXX[uw](Sandy): Make this not completely fail when hitting this endpoint, otherwise the user would have wasted all
# their work. We can do one of 1. a FB login on the client 2. store their data for after they login 3. don't let them
# start writing if they aren't logged in. 1 or 3 seems best
@login_required
@app.route('/api/user/course', methods=['POST', 'PUT'])
def user_course():
    # FIXME[uw](david): This should also update aggregate ratings table, etc.
    uc = json_util.loads(flask.request.data)

    now = datetime.now()
    def set_comment_date_if_necessary(review):
        if not review:
            return None

        # TODO(mack): add more stringent checking against user manually
        # setting time on the frontend
        if 'comment' in review and not 'comment_date':
            review['comment_date'] = now

    set_comment_date_if_necessary(uc.get('user_review'))
    set_comment_date_if_necessary(uc.get('course_review'))

    user = get_current_user()
    uc['user_id'] = user.id

    if 'course_review' in uc:
        uc['course_review'] = m.CourseReview(**uc['course_review'])

    if 'professor_review' in uc:
        uc['professor_review'] = m.ProfessorReview(**uc['professor_review'])

    uc = m.UserCourse(**uc)
    uc.save()

    return json_util.dumps(clean_user_course(uc))


###############################################################################
# Helper functions

# TODO(david): This fn has a weird signature
def clean_ratings(rating_dict):
    update_with_name = lambda ar, name: dict(ar.to_dict(), **{ 'name': name})
    return [update_with_name(v, k) for k, v in rating_dict.iteritems()]


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
            'comment_date': course_review.comment_date,
        },
        'professor_review': {
            'clarity': professor_review.clarity,
            'passion': professor_review.passion,
            'comment': professor_review.comment,
            'comment_date': professor_review.comment_date,
        },
    }


def clean_prof_review(review):
    prof_ratings = review.professor_review.get_ratings()
    prof_ratings.update(review.course_review.get_ratings())

    review = {
        'comment': {
            'comment': review.professor_review.comment,
            'comment_date': review.professor_review.comment_date,
        },
        'ratings': clean_ratings(prof_ratings)
    }

    if hasattr(review, 'user_id') and not review.anonymous:
        author = m.User.objects.with_id(review.user_id)
        author_name = author.only('first_name', 'last_name').name
        review.update({
            'author_id': review.user_id,
            'author_name': author_name,
        })

    return review


def clean_professor(professor, course_id=None):
    # TODO(david): Get department, contact info
    ratings_cleaned = clean_ratings(professor.get_ratings())

    # TODO(david): Generic reviews for prof? Don't need that yet
    prof = {
        'name': professor.name,
        'ratings': ratings_cleaned
    }

    if course_id:
        course_ratings = professor.get_ratings_for_course(course_id)
        prof['course_ratings'] = clean_ratings(course_ratings)

        course_reviews = m.user_course.get_reviews_for_course_prof(course_id,
                professor.id)
        prof['course_reviews'] = map(clean_prof_review, course_reviews)

    return prof


def clean_course(course, expanded=False, user=None):
    """Returns information about a course to be sent down an API.

    Args:
        course: The course object.
        expanded: Whether to fetch more information, such as professor reviews.
    """

    user = user or get_current_user()

    def get_professors(course):
        professors = m.Professor.objects(id__in=course.professor_ids)

        if expanded:
            return [clean_professor(p, course.id) for p in professors]
        else:
            professors = professors.only('id', 'first_name', 'last_name')
            return [{'id': p.id, 'name': p.name} for p in professors]

    def get_user_course(course):
        user_course = m.UserCourse.objects(
                course_id=course.id, user_id=user.id).first()

        if not user_course:
            return None

        return clean_user_course(user_course)

    def get_friend_user_courses(course):
        ucs = m.UserCourse.objects(
            course_id=course.id, user_id__in=user.friend_ids).only('user_id', 'term_id')
        friend_map = {}
        for uc in ucs:
            friend_map[uc.user_id] = {
                # FIXME(mack): should use json to convert id to objectid
                'id': str(uc.id),
                'user_id': uc.user_id,
                # TODO(mack): send term_id or term_name?
                'term_name': m.Term(id=uc.term_id).name,
            }
        for friend in m.User.objects(id__in=friend_map.keys()).only(
                'fbid', 'first_name', 'last_name'):
            # TODO(mack): should be storing in user objects
            friend_map[friend.id].update({
                'user_name': friend.name,
                'user_fbid': friend.fbid,
                'user_fb_pic_url': friend.fb_pic_url,
                'user_profile_url': friend.profile_url,
            })

        return friend_map.values()

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
        'friend_user_courses': get_friend_user_courses(course),
    }


def clean_user(user, courses_map):
    program_name = None
    if user.program_name:
        program_name = user.program_name.split(',')[0]

    last_term_name = m.Term(id=user.last_term_id).name

    courses_took = []
    for uc in m.UserCourse.objects(id__in=user.course_history).only('course_id', 'term_id'):
        # TODO(Sandy): Handle courses that we have from UserCourse, but not in Course
        # TODO(Sandy): Don't hardcore this. REMEMBER TO DO THIS BEFORE 2013_01
        if courses_map.has_key(uc.course_id) and uc.term_id == '2012_09':
            courses_took.append(courses_map[uc.course_id])

    return {
        'id': user.id,
        'fbid': user.fbid,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'name': user.name,
        'fb_pic_url': user.fb_pic_url,
        'program_name': program_name,
        'last_program_year_id': user.last_program_year_id,
        'lastTermName': last_term_name,
        'coursesTook': courses_took,
    }


if __name__ == '__main__':
  app.debug = True
  app.run()

from datetime import datetime
import bson
import flask
import functools
import itertools
import logging
import mongoengine as me
import pymongo
import re
import redis
import time

import rmc.shared.constants as c
import rmc.shared.secrets as s
import rmc.models as m
import rmc.shared.util as util

import base64
import hashlib
import hmac

VERSION = int(time.time())

# Minimum number of characters for a review to pass
# TODO(david): Have a function to do this. First, we need consistent review
#     interface
MIN_REVIEW_LENGTH = 15

app = flask.Flask(__name__)
app.config.from_envvar('FLASK_CONFIG')
me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
r = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)

flask.render_template = functools.partial(flask.render_template,
        env=app.config['ENV'],
        version=VERSION,
        js_dir=app.config['JS_DIR'])

if not app.debug:
    from logging.handlers import TimedRotatingFileHandler
    logging.basicConfig(level=logging.INFO)

    file_handler = TimedRotatingFileHandler(filename=app.config['LOG_PATH'],
            when='D')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s in'
            ' %(module)s:%(lineno)d %(message)s')
    file_handler.setFormatter(formatter)

    # TODO(david): Add email handler for critical level
    app.logger.addHandler(file_handler)
    logging.getLogger('').addHandler(file_handler)  # Root handler
else:
    logging.basicConfig(level=logging.DEBUG)


# Jinja filters
@app.template_filter()
def tojson(obj):
    return util.json_dumps(obj)

@app.template_filter()
def version(file_name):
    return '%s?v=%s' % (file_name, VERSION)

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


# TODO(Sandy): Move this somewhere more appropriate. It is currently being
# called by api/transcript and /profile

# TODO(mack): move this somewhere more appropriate
def get_js_profile_friends_obj(profile_user):

    profile_dict = clean_user(profile_user)

    # fetch mutual friends from redis
    pipe = r.pipeline()

    # Show mutual courses between the viewing user and the friends of the profile user
    viewer_user = get_current_user()
    for friend_id in profile_user.friend_ids:
        pipe.smembers(viewer_user.mutual_courses_redis_key(friend_id))
    mutual_course_ids_per_user = pipe.execute()

    zipped = itertools.izip(profile_user.friend_ids, mutual_course_ids_per_user)
    zipped = sorted(
        zipped,
        key=lambda (friend_id, mutual_course_ids): len(mutual_course_ids),
        reverse=True,
    )

    # TODO(mack): reduce amount of data we fetch for each friend
    friend_dicts = {}
    for friend in m.User.objects(id__in=profile_user.friend_ids):
        friend_dicts[friend.id] = clean_user(friend)

    # find all courses we need to pass to frontend; combo of
    # your courses and friends' courses
    # TODO(mack): control how much data we fetch based on what the course
    # is needed for
    all_course_ids = set()
    all_user_course_ids = set()
    for user_dict in friend_dicts.values() + [profile_dict]:
        all_course_ids = all_course_ids.union(user_dict['course_ids'])
        all_user_course_ids = all_user_course_ids.union(
                user_dict['course_history'])

    course_dicts = {}
    fetched_course_ids = set()
    for course in m.Course.objects(id__in=list(all_course_ids)):
        course_dicts[course.id] = clean_course(course)
        fetched_course_ids.add(course.id)

    user_course_dicts = {}
    # TODO(mack): rather than fetching all friend user course ids,
    # should just be fetching those that are for courses you have
    # also taken
    for user_course in m.UserCourse.objects(id__in=list(all_user_course_ids)):
        user_course_dict = clean_user_course(user_course)
        user_course_dicts[user_course.id] = user_course_dict

    for friend_id, mutual_course_ids in zipped:
        if friend_id not in friend_dicts:
            continue

        friend_dict = friend_dicts[friend_id]
        friend_dict['mutual_course_ids'] = mutual_course_ids.intersection(
                fetched_course_ids)

    return profile_dict, friend_dicts, user_course_dicts, course_dicts


@app.route('/')
def index():
    # Redirect logged-in users to profile
    # TODO(Sandy): If we request extra permissions from FB, we'll need to show them the landing page to let them to
    # Connect again and accept the new permissions. Alternatively, we could use other means of requesting for new perms
    if get_current_user():
        return flask.make_response(flask.redirect('profile'))

    return flask.render_template('index_page.html',
            page_script='index_page.js')


@app.route('/crash')
def crash():
    """For testing error logging"""
    logging.warn("Crashing because you want me to (hit /crash)")
    raise Exception("OH NOES we've crashed!!!!!!!!!! /crash was hit")


# TODO(mack): maybe support fbid in addition to user_id
# TODO(mack): move each api into own class
@app.route('/profile', defaults={'profile_user_id': None})
@app.route('/profile/<string:profile_user_id>')
@login_required
def profile(profile_user_id):
    # TODO(mack): for dict maps, use .update() rather than overwriting to
    # avoid subtle overwrites by data that has fields filled out

    # TODO(mack): remove hardcode of LAST_TERM_ID
    LAST_TERM_ID = '2012_09'

    # PART ONE - VALIDATION

    current_user = get_current_user()

    if profile_user_id:
        profile_user_id = bson.ObjectId(profile_user_id)

    # XXX(Sandy)[uw]: Run permission check on this user to show restricted
    # profile view if not friends. simple fbid lookup should do
    # Check if viewing own or another user's profile
    if not profile_user_id or profile_user_id == current_user.id:
        own_profile = True
        profile_user = current_user
    else:
        own_profile = False
        profile_user = m.User.objects.with_id(profile_user_id)
        if profile_user is None:
            logging.warn('other-use is None')
            return flask.redirect('/profile', 302)

    # PART TWO - DATA FETCHING

    # Get the mutual course ids of friends of profile user
    mutual_course_ids_by_friend = {}
    if own_profile:
        mutual_course_ids_by_friend = profile_user.get_mutual_course_ids(r)

    def get_friend_course_ids_in_term(friend_ids, term_id):
        user_courses = m.UserCourse.objects(
                term_id=term_id, user_id__in=friend_ids).only(
                    'user_id', 'course_id')

        last_term_course_ids_by_friend = {}
        for uc in user_courses:
            last_term_course_ids_by_friend.setdefault(
                    uc.user_id, []).append(uc.course_id)
        return last_term_course_ids_by_friend

    # Get the course ids of last term courses of friends of profile user
    last_term_course_ids_by_friend = get_friend_course_ids_in_term(
            profile_user.friend_ids, LAST_TERM_ID)

    # Get the user courses of profile user
    profile_user_courses = profile_user.get_user_courses()
    # Get a mapping from course id to user_course for profile user
    profile_course_to_user_course = {}
    for uc in profile_user_courses:
        profile_course_to_user_course[uc.course_id] = uc
    # Get the course ids of courses profile user has taken
    profile_course_ids = set(profile_course_to_user_course.keys())

    if not own_profile:
        # Get the user courses of current user
        current_user_courses = current_user.get_user_courses()
        # Get a mapping from course id to user_course for current user
        current_course_to_user_course = {}
        for uc in current_user_courses:
            current_course_to_user_course[uc.course_id] = uc
    else:
        current_user_courses = profile_user_courses
        current_course_to_user_course = profile_course_to_user_course


    # Get user courses of friends of current user for displaying in transcript
    # course cards
    friend_user_courses = m.UserCourse.objects(
            user_id__in=current_user.friend_ids,
            course_id__in=profile_course_ids).only(
                    'term_id', 'user_id', 'course_id')

    # Fetch courses for transcript, which need more detailed information
    # than other courses (such as mutual and last term courses for friends)
    transcript_courses = m.Course.objects(id__in=profile_course_ids)
    transcript_course_ids = set([c.id for c in transcript_courses])


    # Fetch remainining courses that need less data. This will be mutual
    # and last term courses for profile user's friends
    friend_course_ids = set()
    friend_courses = []
    if own_profile:
        for course_ids in mutual_course_ids_by_friend.values():
            friend_course_ids = friend_course_ids.union(course_ids)
        for course_ids in last_term_course_ids_by_friend.values():
            friend_course_ids = friend_course_ids.union(course_ids)
        friend_course_ids = friend_course_ids - profile_course_ids
        friend_courses = m.Course.objects(
                id__in=friend_course_ids).only('id', 'name')

    # Fetch simplified information for friends of profile user
    # (for friend sidebar)
    friends = m.User.objects(id__in=profile_user.friend_ids).only(
            'id', 'fbid', 'first_name', 'last_name')

    # PART THREE - TRANSFORM DATA TO DICTS

    # Convert courses to dicts
    course_dicts = {}
    for course in transcript_courses:
        course_dict = course.to_dict()
        # The user course context that should be that of the current user
        current_uc = current_course_to_user_course.get(course.id)
        course_dict['user_course_id'] = current_uc.id if current_uc else None
        profile_uc = profile_course_to_user_course.get(course.id)
        course_dict['profile_user_course_id'] = profile_uc.id
        course_dicts[course.id] = course_dict
    for course in friend_courses:
        course_dicts[course.id] = course.to_dict()

    # Store friend usercourse ids in your own usercourses of the same
    # course id for friends of current user
    friend_user_courses_by_course = {}
    for fuc in friend_user_courses:
        if fuc.course_id in transcript_course_ids:
            friend_user_courses_by_course.setdefault(
                    fuc.course_id, []).append(fuc)
    if own_profile:
        for course_id, fucs in friend_user_courses_by_course.items():
            course_dict = course_dicts[course_id]
            course_dict['friend_user_course_ids'] = [fuc.id for fuc in fucs]

    def filter_course_ids(course_ids):
        return [course_id for course_id in course_ids
                if course_id in course_dicts]

    # Convert friend users to dicts
    user_dicts = {}
    last_term = m.Term(id=LAST_TERM_ID)
    for friend in friends:
        user_dict = friend.to_dict()

        if own_profile:
            user_dict.update({
                'last_term_name': last_term.name,
                'last_term_course_ids': filter_course_ids(
                    last_term_course_ids_by_friend.get(friend.id, [])),
                'mutual_course_ids': filter_course_ids(
                    mutual_course_ids_by_friend.get(friend.id, [])),
            })

        user_dicts[friend.id] = user_dict

    # Convert profile user to dict
    # TODO(mack): This must be after friend user dicts since it can override
    # data in it. Remove this restriction
    profile_dict = profile_user.to_dict()
    profile_dict.update({
        'own_profile': own_profile
    })
    user_dicts.setdefault(profile_user.id, {}).update(profile_dict)

    # Convert current user to dict
    # TODO(mack): This must be after friend user dicts since it can override
    # data in it. Remove this restriction
    if not own_profile:
        user_dicts.setdefault(
                current_user.id, {}).update(current_user.to_dict())

    # Convert users courses to dicts
    user_course_dicts = {}
    for user_course in profile_user_courses:
        if user_course.course_id not in transcript_course_ids:
            continue

        user_course_dicts[user_course.id] = user_course.to_dict()
    if not own_profile:
        for user_course in current_user_courses:
            if user_course.course_id not in transcript_course_ids:
                continue
            user_course_dicts[user_course.id] = user_course.to_dict()
    for user_course in friend_user_courses:
        if (user_course.course_id not in course_dicts
                or user_course.id in user_course_dicts):
            continue
        user_course_dicts[user_course.id] = user_course.to_dict()

    def get_ordered_transcript(profile_user_courses):
        transcript_by_term = {}

        for uc in profile_user_courses:
            transcript_by_term.setdefault(uc.term_id, []).append(uc)

        ordered_transcript = []
        for term_id, ucs in sorted(transcript_by_term.items(), reverse=True):
            curr_term = m.Term(id=term_id)
            term_dict = {
                'id': curr_term.id,
                'name': curr_term.name,
                'program_year_id': ucs[0].program_year_id,
                'course_ids': [uc.course_id for uc in ucs
                    if uc.course_id in course_dicts],
            }
            ordered_transcript.append(term_dict)

        return ordered_transcript

    # Store courses by term as transcript using the current user's friends
    ordered_transcript = get_ordered_transcript(profile_user_courses)

    return flask.render_template('profile_page.html',
        page_script='profile_page.js',
        transcript_obj=ordered_transcript,
        user_objs=user_dicts.values(),
        user_course_objs=user_course_dicts.values(),
        course_objs=course_dicts.values(),
        # TODO(mack): currently needed by jinja to do server-side rendering
        # figure out a cleaner way to do this w/o passing another param
        profile_obj=profile_dict,
        profile_user_id=profile_user.id,
        current_user_id=current_user.id,
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

    current_user = get_current_user()

    return flask.render_template(
        'search_page.html',
        page_script='search_page.js',
        sort_modes=sort_modes,
        directions=directions,
        current_user_id=current_user.id if current_user else None,
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

    current_user = get_current_user()

    course_obj = clean_course(course, expanded=True)

    user_course_objs = []
    user_objs = []
    if current_user:
        user_course = m.UserCourse.objects(
                course_id=course_id, user_id=current_user.id).first()
        user_course_obj = clean_user_course(user_course)

        # TODO(mack): optimize this
        friend_user_courses = m.UserCourse.objects(id__in=
                course_obj['friend_user_course_ids'])

        user_course_objs = ([user_course_obj] +
                map(clean_user_course, friend_user_courses))

        friend_ids = [uc.user_id for uc in friend_user_courses]
        friends = m.User.objects(id__in=friend_ids)
        user_objs = map(clean_user, [current_user] + list(friends))

    ucs = m.UserCourse.objects(course_id=course_id)

    ## TODO(mack): refactor tips similar to other models
    #tip_objs = map(tip_from_uc, filter(course_review_exists, ucs))

    # TODO(david): Use a projection
    tip_objs = [tip_from_uc(uc) for uc in ucs if
            len(uc.course_review.comment) > MIN_REVIEW_LENGTH]

    return flask.render_template('course_page.html',
        page_script='course_page.js',
        course_obj=course_obj,
        tip_objs=tip_objs,
        user_course_objs=user_course_objs,
        user_objs=user_objs,
        current_user_id=current_user.id if current_user else None,
    )


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
        data = util.json_loads(base64_url_decode(payload))

        if data.get('algorithm').upper() != 'HMAC-SHA256':
            logging.error('Unknown algorithm during fbsr decode')
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
            logging.warn('No fbid/access_token specified')
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
        logging.error('Exception while saving user: %s' % ex)
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

    return util.json_dumps({ 'courses': course_map })

COURSES_SORT_MODES = [
    # TODO(mack): 'num_friends'
    # TODO(david): Usefulness
    { 'value': 'num_ratings', 'name': 'by popularity', 'direction': pymongo.DESCENDING, 'field': 'overall.count' },
    { 'value': 'alphabetical', 'name': 'alphabetically', 'direction': pymongo.ASCENDING, 'field': 'id' },
    { 'value': 'overall', 'name': 'by overall rating', 'direction': pymongo.DESCENDING, 'field': 'overall.rating' },
    { 'value': 'interest', 'name': 'by interest', 'direction': pymongo.DESCENDING, 'field': 'interest.rating' },
    { 'value': 'easiness', 'name': 'by easiness' , 'direction': pymongo.DESCENDING, 'field': 'easiness.rating' },
    { 'value': 'friends', 'name': 'friends taking' , 'direction': pymongo.DESCENDING, 'field': 'custom' },
]
COURSES_SORT_MODES_BY_VALUE = {}
for sort_mode in COURSES_SORT_MODES:
    COURSES_SORT_MODES_BY_VALUE[sort_mode['value']] = sort_mode


@app.route('/api/course-search', methods=['GET'])
# TODO(mack): find a better name for function
# TODO(mack): a potential problem with a bunch of the sort modes is if the
# value they are sorting by changes in the objects. this can lead to missing
# or duplicate contests being passed to front end
def search_courses():
    # TODO(mack): create enum of sort options
    # num_friends, num_ratings, overall, interest, easiness

    request = flask.request
    keywords = request.values.get('keywords')
    sort_mode = request.values.get('sort_mode', 'num_ratings')
    default_direction = COURSES_SORT_MODES_BY_VALUE[sort_mode]['direction']
    direction = int(request.values.get('direction', default_direction))
    count = int(request.values.get('count', 10))
    offset = int(request.values.get('offset', 0))

    current_user = get_current_user()

    if keywords:
        keywords = re.sub('\s+', ' ', keywords)
        keywords = keywords.split(' ')

        def regexify_keywords(keyword):
            keyword = keyword.lower()
            return re.compile('^%s' % keyword)

        keywords = map(regexify_keywords, keywords)

    if keywords:
        unsorted_courses = m.Course.objects(_keywords__all=keywords)
    else:
        unsorted_courses = m.Course.objects()

    if sort_mode == 'friends':

        # TODO(mack): should only do if user is logged in
        friends = m.User.objects(id__in=current_user.friend_ids).only(
                'course_history')
        # TODO(mack): need to majorly optimize this
        num_friends_by_course = {}
        for friend in friends:
            for course_id in friend.course_ids:
                if not course_id in num_friends_by_course:
                    num_friends_by_course[course_id] = 0
                num_friends_by_course[course_id] += 1

        existing_courses = m.Course.objects(
                id__in=num_friends_by_course.keys()).only('id')
        existing_course_ids = set(c.id for c in existing_courses)
        for course_id in num_friends_by_course.keys():
            if course_id not in existing_course_ids:
                del num_friends_by_course[course_id]

        sorted_course_count_tuples = sorted(
            num_friends_by_course.items(),
            key=lambda (_, total): total,
            reverse=direction < 0,
        )[offset:offset+count]

        sorted_course_ids = [course_id for (course_id, total)
                in sorted_course_count_tuples]

        unsorted_limited_courses = m.Course.objects(id__in=sorted_course_ids)

        limited_courses_by_id = {}
        for course in unsorted_limited_courses:
            limited_courses_by_id[course.id] = course

        limited_courses = []
        for course_id in sorted_course_ids:
            limited_courses.append(limited_courses_by_id[course_id])

    else:
        sort_options = COURSES_SORT_MODES_BY_VALUE[sort_mode]
        sort_instr = ''
        if direction < 0:
            sort_instr = '-'
        sort_instr += sort_options['field']

        sorted_courses = unsorted_courses.order_by(sort_instr)
        limited_courses = sorted_courses.skip(offset).limit(count)

    has_more = len(limited_courses) == count
    course_objs = map(clean_course, limited_courses)

    user_objs = []
    user_course_objs = []

    if current_user:
        course_ids = [c.id for c in limited_courses]
        user_courses = m.UserCourse.objects(
                user_id__in=[current_user.id] + current_user.friend_ids,
                course_id__in=course_ids)
        user_course_objs = map(clean_user_course, list(user_courses))

        users = m.User.objects(id__in=[uc.user_id for uc in user_courses])
        user_objs = map(clean_user, users)

    return util.json_dumps({
        'user_objs': user_objs,
        'course_objs': course_objs,
        'user_course_objs': user_course_objs,
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

    transcript_data = util.json_loads(req.form['transcriptData'])
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
    user.cache_mutual_course_ids(r)
    user.save()

    return ''


@app.route('/api/remove_transcript', methods=['POST'])
@login_required
def remove_transcript():
    current_user = get_current_user()
    current_user.course_history = []
    current_user.save()

    # Remove cached mutual courses
    current_user.remove_mutual_course_ids(r)

    # Remove term_id from user_courses
    # TODO(mack): Display message notifying users how many reviews they will
    # lose by removing their transcript.
    m.UserCourse.objects(user_id=current_user.id).delete()

    return ''


# XXX[uw](Sandy): Make this not completely fail when hitting this endpoint, otherwise the user would have wasted all
# their work. We can do one of 1. a FB login on the client 2. store their data for after they login 3. don't let them
# start writing if they aren't logged in. 1 or 3 seems best
@login_required
@app.route('/api/user/course', methods=['POST', 'PUT'])
def user_course():
    uc_data = util.json_loads(flask.request.data)
    user = get_current_user()

    # Validate request object
    course_id = uc_data.get('course_id')
    term_id = uc_data.get('term_id')
    if course_id is None or term_id is None:
        logging.error("/api/user/course got course_id (%s) and term_id (%s)" %
            (course_id, term_id))
        raise ApiError('No course_id or term_id set')

    # Fetch existing UserCourse
    uc = m.UserCourse.objects(
        user_id=user.id,
        course_id=uc_data['course_id'],
        term_id=uc_data['term_id']
    ).first()

    if uc is None:
        logging.error("/api/user/course User course not found for " +
            "user_id=%s course_id=%s term_id=%s" %
            (user.id, course_id, term_id))
        raise ApiError('No user course found')

    # Update privacy settings
    # TODO(Sandy): Move this when we revamp privacy
    uc.anonymous = uc_data['anonymous']

    # TODO(Sandy): Consider the case where the user picked a professor and rates
    # them, but then changes the professor. We need to remove the ratings from
    # the old prof's aggregated ratings and add them to the new prof's
    # Maybe create professor if newly added
    if uc_data.get('new_prof_added'):

        new_prof_name = uc_data['new_prof_added']

        prof_id = m.Professor.get_id_from_name(new_prof_name)
        uc.professor_id = prof_id

        # TODO(Sandy): Have some kind of sanity check for professor names.
        # Don't allow ridiculousness like "Santa Claus", "aksnlf", "swear words"
        if m.Professor.objects(id=prof_id).count() == 0:
            first_name, last_name = m.Professor.guess_names(new_prof_name)
            m.Professor(
                id=prof_id,
                first_name=first_name,
                last_name=last_name,
            ).save()

        course = m.Course.objects.with_id(uc.course_id)
        course.professor_ids = list(set(course.professor_ids) | {prof_id})
        course.save()

        logging.info("Added new course professor %s (name: %s)" % (prof_id,
                new_prof_name))
    elif uc_data.get('professor_id'):
        uc.professor_id = uc_data['professor_id']
    else:
        # TODO(Sandy): Handle professor not set
        pass

    now = datetime.now()

    if uc_data.get('course_review'):
        # New course review data
        uc.course_review.update_review_with_date_and_dict(
            now, **uc_data['course_review'])

    if uc_data.get('professor_review'):
        # New prof review data
        uc.professor_review.update_review_with_date_and_dict(
            now, **uc_data['professor_review'])

    uc.save()

    return util.json_dumps({
        'professor_review.comment_date': uc['professor_review'][
            'comment_date'],
        'course_review.comment_date': uc['course_review'][ 'comment_date'],
    })


###############################################################################
# Helper functions

def clean_user_course(user_course):

    user_course_dict = {}
    if user_course:
        user_course_dict = user_course.to_dict()
    return user_course_dict


def clean_prof_review(entity):
    review = {
        'comment': {
            'comment': entity.professor_review.comment,
            'comment_date': entity.professor_review.comment_date,
        },
        'ratings': entity.professor_review.to_array(),
    }

    # TODO(david): Maybe just pass down the entire user object
    # TODO(david) FIXME[uw](david): Should not nest comment
    if hasattr(entity, 'user_id') and not entity.anonymous:
        author = m.User.objects.only('first_name', 'last_name', 'fbid',
                'program_name').with_id(entity.user_id)
        review['comment']['author'] = clean_review_author(author)

    return review


def clean_review_author(author):
    user = get_current_user()

    if user and (author.id in user.friend_ids or user.id == author.id):
        return {
            'id': author.id,
            'name': 'You' if user.id == author.id else author.name,
            'fbid': author.fbid,
            'fb_pic_url': author.fb_pic_url,
        }
    else:
        return {
            'program_name': author.short_program_name
        }


def clean_professor(professor, course_id=None):
    # TODO(david): Get department, contact info

    # TODO(david): Generic reviews for prof? Don't need that yet
    prof = {
        'id': professor.id,
        'name': professor.name,
        'ratings': professor.get_ratings(),
    }

    if course_id:
        prof['course_ratings'] = professor.get_ratings_for_course(course_id)

        course_reviews = m.user_course.get_reviews_for_course_prof(course_id,
                professor.id)
        # TODO(david): Eventually do this in mongo query or enforce quality
        #     metrics on front-end
        course_reviews = filter(
                lambda r: len(r.professor_review.comment) >= MIN_REVIEW_LENGTH,
                course_reviews)
        prof['course_reviews'] = map(clean_prof_review, course_reviews)

    return prof


def clean_course(course, expanded=False):
    """Returns information about a course to be sent down an API.

    Args:
        course: The course object.
        expanded: Whether to fetch more information, such as professor reviews.
    """

    current_user = get_current_user()

    user_course_id = None
    friend_user_courses = []
    if current_user:
        user_course = m.UserCourse.objects(
                course_id=course.id, user_id=current_user.id).only('id').first()
        if user_course:
            user_course_id = user_course.id

        # TODO(mack): make sure this is fast or do somewhere else more
        # appropriate
        friend_user_courses = m.UserCourse.objects(
            course_id=course.id, user_id__in=current_user.friend_ids).only('id')

    course_dict = course.to_dict()
    course_dict.update({
        'user_course_id': user_course_id,
        'friend_user_course_ids': [fuc.id for fuc in friend_user_courses],
    })

    # TODO(david): Caller should expand its own professors
    if expanded:
        course_dict['professors'] = [clean_professor(p, course.id) for p in
                course.get_professors()]

    return course_dict


def clean_user(user):
    program_name = user.short_program_name

    last_term_name = None
    if user.last_term_id:
        last_term_name = m.Term(id=user.last_term_id).name

    course_ids = []
    last_term_course_ids = []
    for uc in m.UserCourse.objects(id__in=user.course_history).only('course_id', 'term_id'):
        course_ids.append(uc.course_id)
        # TODO(Sandy): Handle courses that we have from UserCourse, but not in Course
        # TODO(Sandy): Don't hardcore this. REMEMBER TO DO THIS BEFORE 2013_01
        if uc.term_id == '2012_09':
            if m.Course.objects.only('id').with_id(uc.course_id):
                last_term_course_ids.append(uc.course_id)

    return {
        'id': user.id,
        'fbid': user.fbid,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'name': user.name,
        'friend_ids': user.friend_ids,
        'fb_pic_url': user.fb_pic_url,
        'program_name': program_name,
        'last_program_year_id': user.last_program_year_id,
        'last_term_name': last_term_name,
        'last_term_course_ids': last_term_course_ids,
        'course_history': user.course_history,
        'course_ids': course_ids,
    }

def tip_from_uc(uc):
    user_id = uc.user_id
    user = m.User.objects(id=user_id).only('first_name', 'middle_name', 'last_name').first()
    names = [user.first_name, user.last_name]
    if user.middle_name is not None:
        names.insert(1, user.middle_name)

    full_name = ' '.join(names)
    return {
        'userId': user_id,
        'name': full_name,
        'comment': uc.course_review.comment,
        'comment_date': uc.course_review.comment_date,
    }

if __name__ == '__main__':
  app.debug = True
  app.run()

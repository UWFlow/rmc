from datetime import datetime
import bson
import flask
import functools
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
import rmc.shared.rmclogger as rmclogger

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

flask_render_template = flask.render_template
def render_template(*args, **kwargs):
    kwargs.update({
        'env': app.config['ENV'],
        'VERSION': VERSION,
        'js_dir': app.config['JS_DIR'],
        'ga_property_id': app.config['GA_PROPERTY_ID'],
        'current_user': get_current_user(),
    })
    return flask_render_template(*args, **kwargs)
flask.render_template = render_template

if not app.debug:
    from logging.handlers import TimedRotatingFileHandler
    logging.basicConfig(level=logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s in'
            ' %(module)s:%(lineno)d %(message)s')

    file_handler = TimedRotatingFileHandler(filename=app.config['LOG_PATH'],
            when='D')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    logging.getLogger('').addHandler(file_handler)  # Root handler

    from log_handler import HipChatHandler
    hipchat_handler = HipChatHandler(s.HIPCHAT_TOKEN, s.HIPCHAT_HACK_ROOM_ID,
            notify=True, color='red', sender='Flask')
    hipchat_handler.setLevel(logging.WARN)
    hipchat_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(hipchat_handler)
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

    if req.current_user and req.current_user.is_admin:
        oid = req.args.get('as_oid', '')
        fbid = req.args.get('as_fbid', '')
        if oid:
            try:
                as_user = m.User.objects.with_id(oid)
                req.current_user = as_user
            except:
                logging.warn("Bad as_oid (%s) in get_current_user()" % oid)
        elif fbid:
            as_user = m.User.objects(fbid=fbid).first()
            if as_user is None:
                logging.warn("Bad as_fbid (%s) in get_current_user()" % fbid)
            else:
                req.current_user = as_user

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

def redirect_to_profile(user):
    """
    Returns a flask.redirect() to a given user's profile.

    Basically redirect the request to the /profile endpoint with their ObjectId

    Args:
        user: The user's profile to redirects to. Should NOT be None.
    """
    if user is None:
        # This should only happen during development time...
        logging.error('redirect_to_profile(user) called with user=None')
        return flask.redirect('/profile', 302)

    return flask.redirect('/profile/%s' % user.id, 302)

@app.route('/')
def index():
    # Redirect logged-in users to profile
    # TODO(Sandy): If we request extra permissions from FB, we'll need to show them the landing page to let them to
    # Connect again and accept the new permissions. Alternatively, we could use other means of requesting for new perms
    # TODO(mack): checking for logout flag probably no longer necessary since
    # we are now clearing cookie before redirecting to home page, so
    # get_current_user() would return None
    logout = bool(flask.request.values.get('logout'))
    if not logout and get_current_user():
        return flask.make_response(flask.redirect('profile'))

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_LANDING,
    )

    in_pre_enroll_exp = 'k' in flask.request.values
    return flask.render_template('index_page.html',
        page_script='index_page.js',
        in_pre_enroll_exp=in_pre_enroll_exp,
    )


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
def profile_page(profile_user_id):
    # TODO(mack): for dict maps, use .update() rather than overwriting to
    # avoid subtle overwrites by data that has fields filled out

    LAST_TERM_ID = util.get_current_term_id()

    # PART ONE - VALIDATION

    current_user = get_current_user()

    try:
        if profile_user_id:
            profile_user_id = bson.ObjectId(profile_user_id)
    except:
        logging.warn('Invalid profile_user_id (%s)' % profile_user_id)
        return redirect_to_profile(current_user)

    if not profile_user_id:
        return redirect_to_profile(current_user)

    if profile_user_id == current_user.id:
        own_profile = True
        profile_user = current_user
    else:
        own_profile = False

        # Allow only friends to view profile
        if not (profile_user_id in current_user.friend_ids
                or current_user.is_admin and flask.request.values.get('admin')):
            logging.warn("User (%s) tried to access non-friend profile (%s)"
                    % (current_user.id, profile_user_id))
            return redirect_to_profile(current_user)

        profile_user = m.User.objects.with_id(profile_user_id)
        # Technically we don't need this check due to above (under normal
        # operation). Though have this anyway as a failsafe
        if profile_user is None:
            logging.warn('profile_user is None')
            return redirect_to_profile(current_user)

    # Redirect the user appropriately... to /onboarding if they have no course
    # history, and to wherever they logged in from if they just logged in
    # TODO(david): Should have frontend decide whether to take us to /profile
    #     or /onboarding and not redirect in one of these two places
    if own_profile:
        redirect_url = flask.request.values.get('next')
        if current_user.has_course_history and redirect_url:
            return flask.make_response(flask.redirect(redirect_url))
        elif not current_user.has_course_history:
            return flask.make_response(flask.redirect('onboarding'))

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

    # Get the course ids of courses profile user has taken
    profile_course_ids = set(profile_user.course_ids)

    # Fetch courses for transcript, which need more detailed information
    # than other courses (such as mutual and last term courses for friends)
    transcript_courses = m.Course.objects(id__in=profile_course_ids)

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

    # Fetch all professors for all courses
    professor_objs = m.Professor.get_reduced_professors_for_courses(
            transcript_courses)

    # PART THREE - TRANSFORM DATA TO DICTS

    # Convert professors to dicts
    professor_dicts = {}
    for professor_obj in professor_objs:
        professor_dicts[professor_obj['id']] = professor_obj

    # Convert courses to dicts
    course_dict_list, user_course_dict_list = m.Course.get_course_and_user_course_dicts(
        transcript_courses, current_user, include_friends=own_profile)
    course_dicts = {}
    for course_dict in course_dict_list:
        course_dicts[course_dict['id']] = course_dict
    user_course_dicts = {}
    for user_course_dict in user_course_dict_list:
        user_course_dicts[user_course_dict['id']] = user_course_dict

    profile_uc_dict_list = []

    # We only need to fetch usercourses for profile user if it is not the
    # current user since m.Course.get_course_and_user_course_dicts() will
    # have already fetched usercourses for the current user
    if not own_profile:
        # Get the user courses of profile user
        profile_uc_dict_list = [
                uc.to_dict() for uc in profile_user.get_user_courses()]
        # Get a mapping from course id to user_course for profile user
        profile_user_course_by_course = {}
        for uc_dict in profile_uc_dict_list:
            profile_user_course_by_course[uc_dict['course_id']] = uc_dict

    # Fill in with information about profile user
    for course in transcript_courses:
        course_dict = course_dicts[course.id]

        if not own_profile:
            # This has already been done for current user
            profile_uc_dict = profile_user_course_by_course.get(course.id)
            profile_user_course_id = profile_uc_dict['id']
            user_course_dicts[profile_user_course_id] = profile_uc_dict
        else:
            profile_user_course_id = course_dict.get('user_course_id')
            if profile_user_course_id:
                profile_uc_dict_list.append(
                        user_course_dicts[profile_user_course_id])

        course_dict['profile_user_course_id'] = profile_user_course_id

    for course in friend_courses:
        course_dicts[course.id] = course.to_dict()


    def filter_course_ids(course_ids):
        return [course_id for course_id in course_ids
                if course_id in course_dicts]

    # Convert friend users to dicts
    user_dicts = {}
    # TODO(mack): should really be named current_term
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


    def get_latest_program_year_id(uc_dict_list, user_id):
        latest_term_uc = None
        for uc_dict in uc_dict_list:
            if (uc_dict['user_id'] != user_id or
                    uc_dict['term_id'] > LAST_TERM_ID):
                continue
            elif not latest_term_uc:
                latest_term_uc = uc_dict
            elif uc_dict['term_id'] > latest_term_uc['term_id']:
                latest_term_uc = uc_dict

        if latest_term_uc:
            return latest_term_uc['program_year_id']

        return None

    # Convert profile user to dict
    # TODO(mack): This must be after friend user dicts since it can override
    # data in it. Remove this restriction
    profile_dict = profile_user.to_dict()
    profile_dict.update({
        'last_program_year_id': get_latest_program_year_id(
            user_course_dict_list, profile_user.id),
    })
    user_dicts.setdefault(profile_user.id, {}).update(profile_dict)

    # Convert current user to dict
    # TODO(mack): This must be after friend user dicts since it can override
    # data in it. Remove this restriction
    if not own_profile:
        user_dicts.setdefault(
                current_user.id, {}).update(current_user.to_dict())

    def get_ordered_transcript(profile_uc_dict_list):
        transcript_by_term = {}

        for uc_dict in profile_uc_dict_list:
            transcript_by_term.setdefault(uc_dict['term_id'], []).append(uc_dict)

        ordered_transcript = []
        for term_id, uc_dicts in sorted(transcript_by_term.items(), reverse=True):
            curr_term = m.Term(id=term_id)
            term_dict = {
                'id': curr_term.id,
                'name': curr_term.name,
                'program_year_id': uc_dicts[0].get('program_year_id'),
                'course_ids': [uc_dict['course_id'] for uc_dict in uc_dicts
                    if uc_dict['course_id'] in course_dicts],
            }
            ordered_transcript.append(term_dict)

        return ordered_transcript, transcript_by_term

    # Store courses by term as transcript using the current user's friends
    ordered_transcript, transcript_by_term = get_ordered_transcript(
            profile_uc_dict_list)

    # Fetch exam schedules
    # TODO(david): 2013
    if transcript_by_term.get('2012_09'):
        current_course_ids = [c['course_id'] for c in transcript_by_term['2012_09']]
        print current_course_ids
        exam_objs = m.Exam.objects(course_id__in=current_course_ids)
        exam_dicts = [e.to_dict() for e in exam_objs]
    else:
        exam_dicts = []


    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_PROFILE, {
            'current_user': current_user.id,
            'profile_user': profile_user.id,
        },
    )

    return flask.render_template('profile_page.html',
        page_script='profile_page.js',
        transcript_obj=ordered_transcript,
        user_objs=user_dicts.values(),
        user_course_objs=user_course_dicts.values(),
        course_objs=course_dicts.values(),
        professor_objs=professor_dicts.values(),
        # TODO(mack): currently needed by jinja to do server-side rendering
        # figure out a cleaner way to do this w/o passing another param
        profile_obj=profile_dict,
        profile_user_id=profile_user.id,
        current_user_id=current_user.id,
        own_profile=own_profile,
        has_courses=current_user.has_course_history,
        exam_objs=exam_dicts,
        has_shortlisted=current_user.has_shortlisted,
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

    terms = [
        { 'value': '', 'name': 'any term' },
        { 'value': '01', 'name': 'Winter' },
        { 'value': '05', 'name': 'Spring' },
        { 'value': '09', 'name': 'Fall' },
    ]
    sort_modes = map(clean_sort_modes, COURSES_SORT_MODES)

    current_user = get_current_user()

    return flask.render_template(
        'search_page.html',
        page_script='search_page.js',
        terms=terms,
        sort_modes=sort_modes,
        current_user_id=current_user.id if current_user else None,
        user_objs=[current_user.to_dict()] if current_user else [],
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

    course_dict_list, user_course_dict_list = m.Course.get_course_and_user_course_dicts(
            [course], current_user, include_all_users=True,
            include_friends=True, full_user_courses=True)

    professor_dict_list = m.Professor.get_full_professors_for_course(
            course, current_user)

    user_dicts = {}
    if current_user:
        friend_ids = set()
        for uc_dict in user_course_dict_list:
            user_id = uc_dict['user_id']
            if user_id == current_user.id:
                continue
            # TODO(Sandy): This is poorly named because its not only friends...
            friend_ids.add(user_id)
        friends = m.User.objects(id__in=friend_ids).only(
                'first_name', 'last_name', 'fbid')

        for friend in friends:
            user_dicts[friend.id] = friend.to_dict()
        user_dicts[current_user.id] = current_user.to_dict()

    def tip_from_uc(uc_dict):
        # TODO(david): Don't instantiate a class just to call a method on it
        return m.CourseReview(**uc_dict['course_review']).to_dict(current_user,
                uc_dict['user_id'])

    tip_dict_list = [tip_from_uc(uc_dict) for uc_dict in user_course_dict_list
            if len(uc_dict['course_review']['comment']) >= MIN_REVIEW_LENGTH]

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_SINGLE_COURSE, {
            'current_user': current_user.id if current_user else None,
            'course_id': course_id,
        },
    )

    return flask.render_template('course_page.html',
        page_script='course_page.js',
        course_obj=course_dict_list[0],
        professor_objs=professor_dict_list,
        tip_objs=tip_dict_list,
        user_course_objs=user_course_dict_list,
        user_objs=user_dicts.values(),
        current_user_id=current_user.id if current_user else None,
        current_term_id=util.get_current_term_id(),
    )


@app.route('/onboarding', methods=['GET'])
@login_required
def onboarding():
    current_user = get_current_user()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_ONBOARDING,
        current_user.id,
    )

    friends = m.User.objects(
        id__in=current_user.friend_ids
    ).only('first_name', 'last_name', 'course_history', 'fbid')

    user_objs = []
    for user in [current_user] + list(friends):
        user_objs.append(user.to_dict())

    return flask.render_template('onboarding_page.html',
        page_script='onboarding_page.js',
        current_user_id=current_user.id,
        user_objs=user_objs,
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
    if app.config['ENV'] == 'dev':
        fb_data = parse_signed_request(fbsr, s.FB_APP_SECRET_DEV)
    else:
        fb_data = parse_signed_request(fbsr, s.FB_APP_SECRET_PROD)

    if fb_data is None or fb_data['user_id'] != fbid:
        # Data is invalid
        return 'Error'

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_LOGIN, {
            'fbid': fbid,
            'token': fb_access_token,
            'expiry': fb_access_token_expiry_date,
            'fb_data': fb_data,
            'request_form': req.form,
        },
    )

    # FIXME[uw](mack): Someone could pass fake fb_access_token for an fbid, need to
    # validate on facebook before creating the user. (Sandy): See the note above on using signed_request
    user = m.User.objects(fbid=fbid).first()
    if user:
        user.fb_access_token = fb_access_token
        user.fb_access_token_expiry_date = fb_access_token_expiry_date
        user.save()
        rmclogger.log_event(
            rmclogger.LOG_CATEGORY_IMPRESSION,
            rmclogger.LOG_EVENT_LOGIN, {
                'new_user': False,
                'user_id': user.id,
            },
        )
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
        user = m.User(**user_obj)
        user.save()
        rmclogger.log_event(
            rmclogger.LOG_CATEGORY_IMPRESSION,
            rmclogger.LOG_EVENT_LOGIN, {
                'new_user': True,
                'user_id': user.id,
            },
        )
    except KeyError as ex:
        # Invalid key (shouldn't be happening)
# TODO(Sandy): redirect to landing page, or nothing
        logging.error('Exception while saving user: %s' % ex)
        return 'Error'
    return ''


@app.route('/privacy')
def privacy():
    # current_user CAN be None, but that's okay for logging
    current_user = get_current_user()
    user_id = current_user.id if current_user else None
    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_PRIVACY_POLICY,
        user_id,
    )

    return flask.render_template('privacy_page.html')


@app.route('/about', methods=['GET'])
def about_page():
    # current_user CAN be None, but that's okay for logging
    current_user = get_current_user()
    user_id = current_user.id if current_user else None
    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_ABOUT,
        user_id,
    )

    return flask.render_template('about_page.html')

@app.route('/demo')
def login_as_demo_user():

    fbid = c.DEMO_ACCOUNT_FBID
    user = m.User.objects(fbid=fbid).first()
    # To catch errors on dev. We may not all have the test account in our mongo
    if user is None:
        logging.error("Accessed non-existant test/demo account %s" % fbid)
        return flask.redirect('/profile')

    resp = flask.make_response(flask.redirect('/profile/%s' % user.id, 302))
    # Set user's cookies to mimic demo account
    resp.set_cookie('fbid', user.fbid)
    resp.set_cookie('fb_access_token', user.fb_access_token)
    return resp

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

    # TODO(mack): not currently being called, fix it when it is needed
    # course_objs = map(clean_course, courses)
    course_objs = []
    professor_objs = m.Professor.get_reduced_professor_for_courses(courses)

    return util.json_dumps({
        'course_objs': course_objs,
        'professor_objs': professor_objs,
    })

COURSES_SORT_MODES = [
    # TODO(david): Usefulness
    { 'value': 'num_ratings', 'name': 'popular', 'direction': pymongo.DESCENDING, 'field': 'interest.count' },
    { 'value': 'friends', 'name': 'friends taken' , 'direction': pymongo.DESCENDING, 'field': 'custom' },
    { 'value': 'interest', 'name': 'interesting', 'direction': pymongo.DESCENDING, 'field': 'interest.sorting_score' },
    { 'value': 'easiness', 'name': 'easy' , 'direction': pymongo.DESCENDING, 'field': 'easiness.sorting_score' },
    { 'value': 'easiness', 'name': 'hard' , 'direction': pymongo.ASCENDING, 'field': 'easiness.sorting_score' },
    { 'value': 'alphabetical', 'name': 'course code', 'direction': pymongo.ASCENDING, 'field': 'id'},
]
COURSES_SORT_MODES_BY_NAME = {}
for sort_mode in COURSES_SORT_MODES:
    COURSES_SORT_MODES_BY_NAME[sort_mode['name']] = sort_mode

# Special sort instructions are needed for these sort modes
# TODO(Sandy): deprecate overall and add usefulness
RATING_SORT_MODES = ['overall', 'interest', 'easiness']

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
    term = request.values.get('term')
    sort_mode = request.values.get('sort_mode', 'num_ratings')
    name = request.values.get('name', 'popular')
    default_direction = COURSES_SORT_MODES_BY_NAME[name]['direction']
    direction = int(request.values.get('direction', default_direction))
    count = int(request.values.get('count', 10))
    offset = int(request.values.get('offset', 0))

    current_user = get_current_user()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_COURSE_SEARCH,
        rmclogger.LOG_EVENT_SEARCH_PARAMS,
        request.values
    )

    filters = {}
    if keywords:
        # Clean keywords to just alphanumeric and space characters
        keywords = re.sub(r'[^\w ]', ' ', keywords)

        keywords = re.sub('\s+', ' ', keywords)
        keywords = keywords.split(' ')

        def regexify_keywords(keyword):
            keyword = keyword.lower()
            return re.compile('^%s' % keyword)

        keywords = map(regexify_keywords, keywords)
        filters['_keywords__all'] = keywords

    if term:
        filters['terms_offered'] = term

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

        filters['id__in'] = num_friends_by_course.keys()
        existing_courses = m.Course.objects(**filters).only('id')
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
        sort_options = COURSES_SORT_MODES_BY_NAME[name]

        if sort_mode in RATING_SORT_MODES:
            sort_instr = '-' + sort_options['field']
            sort_instr += "_positive" if direction < 0 else "_negative"
        else:
            sort_instr = ''
            if direction < 0:
                sort_instr = '-'
            sort_instr += sort_options['field']

        unsorted_courses = m.Course.objects(**filters)
        sorted_courses = unsorted_courses.order_by(sort_instr)
        limited_courses = sorted_courses.skip(offset).limit(count)

    has_more = len(limited_courses) == count

    course_dict_list, user_course_dict_list = m.Course.get_course_and_user_course_dicts(
            limited_courses, current_user, include_friends=True, full_user_courses=False)
    professor_dict_list = m.Professor.get_reduced_professors_for_courses(
            limited_courses)

    user_dict_list = []
    if current_user:
        user_ids = [uc['user_id'] for uc in user_course_dict_list
                if uc['user_id'] != current_user.id]
        users = m.User.objects(id__in=user_ids).only(
                'first_name', 'last_name', 'fbid')
        user_dict_list = [u.to_dict() for u in users]

    return util.json_dumps({
        'user_objs': user_dict_list,
        'course_objs': course_dict_list,
        'professor_objs': professor_dict_list,
        'user_course_objs': user_course_dict_list,
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
    course_history_list = user.course_history

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_TRANSCRIPT, {
            'user_id': user_id,
            'requset_form': req.form,
        },
    )

    def get_term_id(term_name):
        season, year = term_name.split()
        return m.Term.get_id_from_year_season(year, season)

    transcript_data = util.json_loads(req.form['transcriptData'])
    courses_by_term = transcript_data['coursesByTerm']

    # TODO(Sandy): Batch request fetch to mongo instead of fetch while looping
    for term in courses_by_term:
        term_id = get_term_id(term['name'])
        program_year_id = term['programYearId']

        for course_id in term['courseIds']:
            course_id = course_id.lower()
            # TODO(Sandy): Fill in course weight and grade info here
            user_course = m.UserCourse.objects(
                user_id=user_id, course_id=course_id).first()

            if user_course is None:
                if m.Course.objects.with_id(course_id) is None:
                    # Non-existant course according to our data
                    rmclogger.log_event(
                        rmclogger.LOG_CATEGORY_DATA_MODEL,
                        rmclogger.LOG_EVENT_UNKNOWN_COURSE_ID,
                        course_id
                    )
                    continue

                user_course = m.UserCourse(
                    user_id=user_id,
                    course_id=course_id,
                    term_id=term_id,
                    program_year_id=program_year_id,
                )
            else:
                # Record only the latest attempt for duplicate/failed courses
                if term_id > user_course.term_id:
                    user_course.term_id = term_id

            user_course.save()

            # We don't need to put this here and have this check, but it's more
            # robust against data corruption if/when we mess up
            if user_course.id not in course_history_list:
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

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_TRANSCRIPT,
        rmclogger.LOG_EVENT_UPLOAD,
        user_id
    )
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

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_TRANSCRIPT,
        rmclogger.LOG_EVENT_REMOVE,
        current_user.id
    )
    return ''

@app.route('/api/user/add_course_to_shortlist', methods=['POST'])
@login_required
def add_course_to_shortlist():
    current_user = get_current_user()

    user_course = m.UserCourse(
        user_id=current_user.id,
        course_id=flask.request.form.get('course_id'),
        term_id=m.Term.SHORTLIST_TERM_ID,
    )
    user_course.save()
    current_user.update(add_to_set__course_history=user_course.id)

    return util.json_dumps({
        'user_course': user_course.to_dict(),
    })

@app.route('/api/user/remove_course', methods=['POST'])
@login_required
def remove_course():
    current_user = get_current_user()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_REMOVE_COURSE, {
            'request_form': flask.request.form,
            'user_id': current_user.id,
        },
    )

    user_course = m.UserCourse.objects(
        user_id=current_user.id,
        course_id=flask.request.form.get('course_id'),
        term_id=flask.request.form.get('term_id'),
    ).first()

    if not user_course:
        logging.warn("No UserCourse found matching request values %s" %
                flask.request.values)
        # TODO(david): Use api.py:not_found in my onboarding-v2 branch
        return ''

    current_user.update(pull__course_history=user_course.id)
    user_course.delete()

    return ''

# XXX[uw](Sandy): Make this not completely fail when hitting this endpoint, otherwise the user would have wasted all
# their work. We can do one of 1. a FB login on the client 2. store their data for after they login 3. don't let them
# start writing if they aren't logged in. 1 or 3 seems best
@login_required
@app.route('/api/user/course', methods=['POST', 'PUT'])
def user_course():
    uc_data = util.json_loads(flask.request.data)
    user = get_current_user()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_USER_COURSE, {
            'uc_data': uc_data,
            'user_id': user.id,
        },
    )

    # Validate request object
    course_id = uc_data.get('course_id')
    term_id = uc_data.get('term_id')
    if course_id is None or term_id is None:
        logging.error("/api/user/course got course_id (%s) and term_id (%s)" %
            (course_id, term_id))
        # TODO(david): Perhaps we should have a request error function that
        # returns a 400
        raise ApiError('No course_id or term_id set')

    # Fetch existing UserCourse
    uc = m.UserCourse.objects(
        user_id=user.id,
        course_id=uc_data['course_id'],
        term_id=uc_data['term_id']
    ).first()

    if uc is None:
        logging.error("/api/user/course User course not found for "
            "user_id=%s course_id=%s term_id=%s" %
            (user.id, course_id, term_id))
        # TODO(david): Perhaps we should have a request error function that
        # returns a 400
        raise ApiError('No user course found')

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
        uc.professor_id = None

    now = datetime.now()

    if uc_data.get('course_review'):
        # New course review data
        uc_data['course_review']['comment_date'] = now
        uc.course_review.update(**uc_data['course_review'])

    if uc_data.get('professor_review'):
        # New prof review data
        uc_data['professor_review']['comment_date'] = now
        uc.professor_review.update(**uc_data['professor_review'])

    uc.save()

    return util.json_dumps({
        'professor_review.comment_date': uc['professor_review'][
            'comment_date'],
        'course_review.comment_date': uc['course_review'][ 'comment_date'],
    })


if __name__ == '__main__':
  app.debug = True
  app.run()

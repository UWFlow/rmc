from datetime import datetime
import bson
import flask
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile
assert line_profile  # silence pyflakes
import logging
import mongoengine as me
import pymongo
import re
import time

import rmc.shared.constants as c
import rmc.shared.secrets as s
import rmc.models as m
import rmc.shared.util as util
import rmc.shared.rmclogger as rmclogger
import rmc.server.profile as profile
import rmc.server.view_helpers as view_helpers

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

flask_render_template = flask.render_template
def render_template(*args, **kwargs):
    kwargs.update({
        'env': app.config['ENV'],
        'VERSION': VERSION,
        'js_dir': app.config['JS_DIR'],
        'ga_property_id': app.config['GA_PROPERTY_ID'],
        'current_user': view_helpers.get_current_user(),
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


@app.route('/')
def index():
    # Redirect logged-in users to profile
    # TODO(Sandy): If we request extra permissions from FB, we'll need to show them the landing page to let them to
    # Connect again and accept the new permissions. Alternatively, we could use other means of requesting for new perms
    # TODO(mack): checking for logout flag probably no longer necessary since
    # we are now clearing cookie before redirecting to home page, so
    # get_current_user() would return None
    logout = bool(flask.request.values.get('logout'))
    if not logout and view_helpers.get_current_user():
        return flask.make_response(flask.redirect('profile'))

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_LANDING,
    )

    return flask.render_template('index_page.html',
        page_script='index_page.js',
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
@view_helpers.login_required
def profile_page(profile_user_id):
    return profile.render_profile_page(profile_user_id)


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

    current_user = view_helpers.get_current_user()

    return flask.render_template(
        'search_page.html',
        page_script='search_page.js',
        terms=terms,
        sort_modes=sort_modes,
        current_user_id=current_user.id if current_user else None,
        user_objs=[current_user.to_dict(
            include_course_ids=True)] if current_user else [],
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

    current_user = view_helpers.get_current_user()

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
        user_dicts[current_user.id] = current_user.to_dict(
                include_course_ids=True)

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
@view_helpers.login_required
def onboarding():
    current_user = view_helpers.get_current_user()

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
    fb_access_token_expires_in = req.cookies.get('fb_access_token_expires_in')
    fbsr = req.form.get('fb_signed_request')

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_LOGIN, {
            'fbid': fbid,
            'token': fb_access_token,
            'expires_in': fb_access_token_expires_in,
            'fbsr': fbsr,
            'request_form': req.form,
        },
    )

    if (fbid is None or
        fb_access_token is None or
        fb_access_token_expires_in is None or
        fbsr is None):
            # TODO(Sandy): redirect to landing page, or nothing
            # Shouldn't happen normally, user probably manually requested this page
            logging.warn('No fbid/access_token specified')
            return 'Error'

    fb_access_token_expiry_date = datetime.fromtimestamp(
            int(time.time()) + int(fb_access_token_expires_in) - 10)

    # Validate against Facebook's signed request
    if app.config['ENV'] == 'dev':
        fb_data = parse_signed_request(fbsr, s.FB_APP_SECRET_DEV)
    else:
        fb_data = parse_signed_request(fbsr, s.FB_APP_SECRET_PROD)

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
    current_user = view_helpers.get_current_user()
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
    current_user = view_helpers.get_current_user()
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

@app.route('/unsubscribe', methods=['GET'])
def unsubscribe_page():
    current_user = view_helpers.get_current_user()
    req = flask.request
    unsubscribe_user_id = req.args.get('pasta')

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_UNSUBSCRIBE, {
            'current_user': current_user.id if current_user else None,
            'unsubscribe_user': unsubscribe_user_id,
            'request_args': req.args,
        },
    )

    return flask.render_template('unsubscribe_page.html',
        page_script='unsubscribe_page.js',
        unsubscribe_user=unsubscribe_user_id,
    )

# TODO(mack): move API's to separate file
# TODO(mack): add security measures (e.g. require auth, xsrf cookie)
###############################
######## API ##################
###############################

@app.route('/api/user/unsubscribe', methods=['POST'])
def unsubscribe_user():
    current_user = view_helpers.get_current_user()
    req = flask.request
    unsubscribe_user_id = req.form.get('pasta')

    if not unsubscribe_user_id:
        logging.warn('Missing user_id (%s)' % unsubscribe_user_id)
        return flask.redirect('/')

    try:
        unsubscribe_user_id = bson.ObjectId(unsubscribe_user_id)
    except:
        logging.warn('Invalid user_id (%s)' % unsubscribe_user_id)
        return flask.redirect('/')

    user = m.User.objects.with_id(unsubscribe_user_id)
    if user:
        user.email_unsubscribed = True
        user.save()

        # TODO(Sandy): Temporary until we enforce logged in unsub's or just
        # generate and send out a hash next time
        notes = "Legit unsub"
        if current_user:
            if current_user.id != unsubscribe_user_id:
                notes = "Suspicious: Non-matching logged in user_id/unsub_id"
        else:
            notes = "Suspicious: No logged in user_id"

        rmclogger.log_event(
            rmclogger.LOG_CATEGORY_API,
            rmclogger.LOG_EVENT_UNSUBSCRIBE_USER, {
                'current_user': current_user.id if current_user else None,
                'unsubscribe_user': unsubscribe_user_id,
                'request_form': req.form,
                'notes': notes,
            },
        )
    else:
        logging.warn('User object (%s) not found' % unsubscribe_user_id)
        return flask.redirect('/')

    return flask.redirect('/')

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

    current_user = view_helpers.get_current_user()

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
@view_helpers.login_required
def upload_transcript():
    req = flask.request
    # TODO(Sandy): The following two cases involve users trying to import their transcript without being logged in.
    # We have to decide how we treat those users. E.g. we might prevent this from the frontend, or maybe save it and
    # tell them to make an account, etc

    user = view_helpers.get_current_user()
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
    user.cache_mutual_course_ids(view_helpers.get_redis_instance())
    user.save()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_TRANSCRIPT,
        rmclogger.LOG_EVENT_UPLOAD,
        user_id
    )
    return ''


@app.route('/api/remove_transcript', methods=['POST'])
@view_helpers.login_required
def remove_transcript():
    current_user = view_helpers.get_current_user()
    current_user.course_history = []
    current_user.save()

    # Remove cached mutual courses
    current_user.remove_mutual_course_ids(view_helpers.get_redis_instance())

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
@view_helpers.login_required
def add_course_to_shortlist():
    current_user = view_helpers.get_current_user()

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
@view_helpers.login_required
def remove_course():
    current_user = view_helpers.get_current_user()

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
@view_helpers.login_required
@app.route('/api/user/course', methods=['POST', 'PUT'])
def user_course():
    uc_data = util.json_loads(flask.request.data)
    user = view_helpers.get_current_user()

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
    # Late import since this isn't used on production
    import flask_debugtoolbar

    app.debug = True
    app.config.update({
        'SECRET_KEY' : 'TODO(jlfwong)',
        'DEBUG_TB_INTERCEPT_REDIRECTS' : False,
        'DEBUG_TB_PROFILER_ENABLED' : True,
        'DEBUG_TB_PANELS' : [
            'flask_debugtoolbar.panels.versions.VersionDebugPanel',
            'flask_debugtoolbar.panels.timer.TimerDebugPanel',
            'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
            'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
            'flask_debugtoolbar.panels.template.TemplateDebugPanel',
            'flask_debugtoolbar.panels.logger.LoggingPanel',
            'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
            'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel'
        ]
    })

    #toolbar = flask_debugtoolbar.DebugToolbarExtension(app)
    app.run()

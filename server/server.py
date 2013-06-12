from datetime import datetime
import bson
import flask
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile
assert line_profile  # silence pyflakes
import logging
import mongoengine as me
import os
import pymongo
import re
import time
import werkzeug.exceptions as exceptions

import rmc.shared.constants as c
import rmc.shared.secrets as s
import rmc.models as m
import rmc.html_snapshots as html_snapshots
import rmc.shared.util as util
import rmc.shared.rmclogger as rmclogger
import rmc.server.profile as profile
import rmc.server.rmc_sift as rmc_sift
import rmc.server.view_helpers as view_helpers
import rmc.analytics.stats as rmc_stats

import rmc.shared.facebook as facebook

VERSION = int(time.time())

app = flask.Flask(__name__)

app.config.from_envvar('FLASK_CONFIG')
me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)

SERVER_DIR = os.path.dirname(os.path.realpath(__file__))

flask_render_template = flask.render_template
def render_template(*args, **kwargs):
    redis = view_helpers.get_redis_instance()

    current_user = view_helpers.get_current_user()
    should_renew_fb_token = False
    if (current_user and
        not current_user.is_demo_account and
        not hasattr(flask.request, 'as_user_override')):
        should_renew_fb_token = current_user.should_renew_fb_token

    kwargs.update({
        'env': app.config['ENV'],
        'VERSION': VERSION,
        'js_dir': app.config['JS_DIR'],
        'ga_property_id': app.config['GA_PROPERTY_ID'],
        'current_user': view_helpers.get_current_user(),
        'total_points': int(redis.get('total_points') or 0),
        'current_user': current_user,
        'should_renew_fb_token': should_renew_fb_token,
        'current_term_id': util.get_current_term_id(),
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

# Initialize sift stuff after logging has been initialized
sift = rmc_sift.RmcSift(api_key=c.SIFT_API_KEY)


# Jinja filters
@app.template_filter()
def tojson(obj):
    return util.json_dumps(obj)

@app.template_filter()
def version(file_name):
    return '%s?v=%s' % (file_name, VERSION)

@app.before_request
def before_request():
    if '_escaped_fragment_' not in flask.request.values:
        return

    # Remove leading '/'s to be compatible with os.path.join()
    path = flask.request.path
    if path and path[-1] == '/':
        path += 'index'
    path = re.sub('^/*', '', path)
    file_path = os.path.join(html_snapshots.HTML_DIR, path)
    try:
        with open(file_path, 'r') as f:
            # Returning something will cause this to be the response
            # for the request
            return f.read()
    except IOError:
        logging.warn('Snapshot does not exist for %s. '
            'Returning dynamic page' % path)


# TODO(Sandy): Unused right now, but remove in a separate diff for future
# reference
def after_this_request(f):
    if not hasattr(flask.g, 'after_request_callbacks'):
        flask.g.after_request_callbacks = []
    flask.g.after_request_callbacks.append(f)
    return f

@app.after_request
def call_after_request_callbacks(response):
    for callback in getattr(flask.g, 'after_request_callbacks', ()):
        response = callback(response)

    # Enable CORS for api requests
    if view_helpers.is_api_request():
        response.headers['Access-Control-Allow-Origin'] = '*'

    return response


@app.route('/')
def index():
    # Redirect logged-in users to profile
    # TODO(Sandy): If we request extra permissions from FB, we'll need to show them the landing page to let them to
    # Connect again and accept the new permissions. Alternatively, we could use other means of requesting for new perms
    # TODO(mack): checking for logout flag probably no longer necessary since
    # we are now clearing cookie before redirecting to home page, so
    # get_current_user() would return None
    request = flask.request
    logout = bool(request.values.get('logout'))
    referrer_id = request.values.get('meow') or request.values.get('referrer')
    if not logout and not referrer_id and view_helpers.get_current_user():
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


@app.route('/profile/demo')
def demo_profile():
    fbid = c.DEMO_ACCOUNT_FBID
    user = m.User.objects(fbid=fbid).first()

    # To catch errors on dev. We may not all have the test account in our mongo
    if user is None:
        logging.error("Accessed non-existant test/demo account %s" % fbid)
        return flask.redirect('/profile')

    return profile.render_profile_page(user.id, user)


# TODO(mack): maybe support fbid in addition to user_id
# TODO(mack): move each api into own class
@app.route('/profile', defaults={'profile_user_id': None})
@app.route('/profile/<string:profile_user_id>')
@view_helpers.login_required
def profile_page(profile_user_id):
    return profile.render_profile_page(profile_user_id)

@app.route('/schedule/ical/<string:profile_user_secret_id>.ics')
def schedule_page_ical(profile_user_secret_id):
    return profile.render_schedule_ical_feed(profile_user_secret_id)

@app.route('/schedule/<string:profile_user_secret_id>')
def schedule_page(profile_user_secret_id):
    profile_user = m.User.objects(secret_id=profile_user_secret_id).first()

    # TODO(jlfwong): This should be removed, but I'm not sure whether the page
    # should just 404 or whether we should redirect or what exactly the right
    # behaviour is here, so for now just let it fall back. This makes the
    # privacy problem less discoverable
    if profile_user is None:
        profile_user = m.User.objects.with_id(profile_user_secret_id)

        if profile_user:
            logging.warn("Schedule loaded via public user id %s"
                % profile_user.id)

    return profile.render_schedule_page(profile_user)

@app.route('/course')
def course():
    return flask.redirect('/courses', 301)  # Moved permanently


@app.route('/courses')
def courses():
    # TODO(mack): move into COURSES_SORT_MODES
    def clean_sort_modes(sort_mode):
        return {
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

    course_dict_list, user_course_dict_list, user_course_list = (
            m.Course.get_course_and_user_course_dicts(
                [course], current_user, include_all_users=True,
                include_friends=True, full_user_courses=True))

    professor_dict_list = m.Professor.get_full_professors_for_course(
            course, current_user)

    user_dicts = {}
    if current_user:
        # TODO(Sandy): This is poorly named because its not only friends...
        friend_ids = ({uc_dict['user_id'] for uc_dict in user_course_dict_list}
                - set([current_user.id]))
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
            if len(uc_dict['course_review']['comment']) >=
                m.review.CourseReview.MIN_REVIEW_LENGTH]

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_SINGLE_COURSE, {
            'current_user': current_user.id if current_user else None,
            'course_id': course_id,
        },
    )

    exam_objs = m.Exam.objects(course_id=course_id)
    exam_dict_list = [e.to_dict() for e in exam_objs]

    exam_updated_date = None
    if exam_objs:
        exam_updated_date = exam_objs[0].id.generation_time

    return flask.render_template('course_page.html',
        page_script='course_page.js',
        course_obj=course_dict_list[0],
        professor_objs=professor_dict_list,
        tip_objs=tip_dict_list,
        user_course_objs=user_course_dict_list,
        user_objs=user_dicts.values(),
        exam_objs=exam_dict_list,
        exam_updated_date=exam_updated_date,
        current_user_id=current_user.id if current_user else None,
    )


@app.route('/onboarding', methods=['GET'])
@view_helpers.login_required
def onboarding():
    current_user = view_helpers.get_current_user()

    current_user.last_show_onboarding = datetime.now()
    current_user.save()

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
    req = flask.request

    # TODO(Sandy): Use Flask Sessions instead of raw cookie
    # http://flask.pocoo.org/docs/quickstart/#sessions

    # TODO(Sandy): No need to send fbid either. fbsr is all we need!
    fbid = req.cookies.get('fbid')
    fbsr = req.form.get('fb_signed_request')

    # TODO(Sandy): Change log category because this isn't API?
    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_LOGIN, {
            'fbid': fbid,
            'fbsr': fbsr,
            'request_form': req.form,
        },
    )

    if (fbid is None or
        fbsr is None):
            logging.warn('No fbsr set')
            raise exceptions.ImATeapot('No fbsr set')

    fb_data = facebook.get_fb_data(fbsr, app.config)
    fbid = fb_data['fbid']
    fb_access_token= fb_data['access_token']
    fb_access_token_expiry_date = fb_data['expires_on']

    # FIXME[uw](mack): Someone could pass fake fb_access_token for an fbid, need to
    # validate on facebook before creating the user. (Sandy): See the note above on using signed_request
    user = m.User.objects(fbid=fbid).first()
    if user:
        user.fb_access_token = fb_access_token
        user.fb_access_token_expiry_date = fb_access_token_expiry_date
        user.fb_access_token_invalid = False
        user.save()

        rmclogger.log_event(
            rmclogger.LOG_CATEGORY_IMPRESSION,
            rmclogger.LOG_EVENT_LOGIN, {
                'new_user': False,
                'user_id': user.id,
            },
        )

        expiry_date_timestamp = time.mktime(
                fb_access_token_expiry_date.timetuple())
        return util.json_dumps({
            'fb_access_token_expires_on': expiry_date_timestamp,
            'fb_access_token': fb_access_token,
        })

    # Sign up the new user
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
    referrer_id = req.form.get('referrer_id')
    if referrer_id:
        try:
            user_obj['referrer_id'] = bson.ObjectId(referrer_id)
        except:
            pass

    user = m.User(**user_obj)
    user.save()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_IMPRESSION,
        rmclogger.LOG_EVENT_LOGIN, {
            'new_user': True,
            'user_id': user.id,
            'referrer_id': referrer_id,
        },
    )

    expiry_date_timestamp = time.mktime(
            fb_access_token_expiry_date.timetuple())
    return util.json_dumps({
        'fb_access_token_expires_on': expiry_date_timestamp,
        'fb_access_token': fb_access_token,
    })

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


@app.route('/admin/backfill_schedules', methods=['GET'])
@view_helpers.admin_required
def backfill_schedules():

    return flask.render_template(
        'backfill_schedules_page.html',
        page_script='backfill_schedules_page.js',
    )

@app.route('/admin/user/<string:user_id>', methods=['GET'])
@view_helpers.admin_required
def get_user_info(user_id):
    # TODO(Sandy): We could list all attr's on a user and maybe even provide
    # hyper links to it, if we ever need friendlier interface to this data.
    # Maybe non-devs will need it. Build it later if we need it
    return m.User.objects.with_id(user_id).name

@app.route('/admin/user/<string:user_id>/<string:attr>', methods=['GET'])
@view_helpers.admin_required
def get_user_attr(user_id, attr):
    return getattr(m.User.objects.with_id(user_id), attr)

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
    { 'name': 'popular', 'direction': pymongo.DESCENDING, 'field': 'interest.count' },
    { 'name': 'friends_taken' , 'direction': pymongo.DESCENDING, 'field': 'custom' },
    { 'name': 'interesting', 'direction': pymongo.DESCENDING, 'field': 'interest.sorting_score' },
    { 'name': 'easy' , 'direction': pymongo.DESCENDING, 'field': 'easiness.sorting_score' },
    { 'name': 'hard' , 'direction': pymongo.ASCENDING, 'field': 'easiness.sorting_score' },
    { 'name': 'course code', 'direction': pymongo.ASCENDING, 'field': 'id'},
]
COURSES_SORT_MODES_BY_NAME = {}
for sort_mode in COURSES_SORT_MODES:
    COURSES_SORT_MODES_BY_NAME[sort_mode['name']] = sort_mode

# Special sort instructions are needed for these sort modes
# TODO(Sandy): deprecate overall and add usefulness
RATING_SORT_MODES = ['overall', 'interesting', 'easy', 'hard']

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
    sort_mode = request.values.get('sort_mode', 'popular')
    default_direction = COURSES_SORT_MODES_BY_NAME[sort_mode]['direction']
    direction = int(request.values.get('direction', default_direction))
    count = int(request.values.get('count', 10))
    offset = int(request.values.get('offset', 0))
    exclude_taken_courses = request.values.get('exclude_taken_courses')

    current_user = view_helpers.get_current_user()

    # TODO(david): These logging things should be done asynchronously
    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_COURSE_SEARCH,
        rmclogger.LOG_EVENT_SEARCH_PARAMS,
        request.values
    )

    if current_user:
        sift.track('search', {
            '$user_id': str(current_user.id),
            '$user_email': current_user.email,
            'keywords': unicode(keywords).encode('utf8'),
            'term': term,
            'name': sort_mode,
            'direction': direction,
            'count': count,
            'offset': offset,
        })

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

    if exclude_taken_courses == "yes":
        if current_user:
            ucs = (current_user.get_user_courses().only('course_id', 'term_id'))
            filters['id__nin'] = [
                uc.course_id for uc in ucs
                if not m.term.Term.is_shortlist_term(uc.term_id)
            ]
        else:
            logging.error('Anonymous user tried excluding taken courses')

    if sort_mode == 'friends_taken':
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
        sort_options = COURSES_SORT_MODES_BY_NAME[sort_mode]

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

    course_dict_list, user_course_dict_list, user_course_list = (
            m.Course.get_course_and_user_course_dicts(
                limited_courses, current_user, include_friends=True,
                full_user_courses=False))
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

@app.route('/api/renew-fb', methods=['POST'])
@view_helpers.login_required
def renew_fb():
    '''
    Renews the current user's Facebook access token.

    Takes {'fb_signed_request': obj} from post parameters.
    '''
    req = flask.request
    current_user = view_helpers.get_current_user()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_RENEW_FB, {
            'user_id': current_user.id,
            'request_form': req.form,
        }
    )

    fbsr = req.form.get('fb_signed_request')
    if fbsr is None:
        logging.warn('No fbsr set')
        raise exceptions.ImATeapot('No fbsr set')

    fb_data = facebook.get_fb_data(fbsr, app.config)
    access_token = fb_data['access_token']
    expires_on = fb_data['expires_on']

    if expires_on > current_user.fb_access_token_expiry_date:
        # Only use the new token if it expires later. It might be the case that
        # get_fb_data failed to grab a new token
        current_user.fb_access_token_expiry_date = expires_on
        current_user.fb_access_token = access_token
        current_user.fb_access_token_invalid = False

        # Update the user's fb friend list, since it's likely outdated by now
        try:
            current_user.update_fb_friends(
                    facebook.get_friend_list(access_token))
        except:
            # Not sure why this would happen. Usually it's due to invalid
            # access_token, but we JUST got the token, so it should be valid
            logging.warn("/api/renew-fb: get_friend_list failed with token (%s)"
                    % access_token)

        current_user.save()

    expiry_date_timestamp = time.mktime(
            expires_on.timetuple())
    return util.json_dumps({
        'fb_access_token_expires_on': expiry_date_timestamp,
        'fb_access_token': access_token,
    })

@app.route('/api/schedule', methods=['POST'])
@view_helpers.login_required
def upload_schedule():
    req = flask.request
    user = view_helpers.get_current_user()

    schedule_data = util.json_loads(req.form.get('schedule_data'))
    processed_items = schedule_data['processed_items']
    failed_items = schedule_data['failed_items']
    term_name = schedule_data['term_name']
    term_id = m.Term.id_from_name(term_name)

    # FIXME TODO(david): Save these in models and display on schedule
    #failed_items = schedule_data['failed_items']

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_SCHEDULE, {
            'schedule_data': schedule_data,
            'term_id': term_id,
            'user_id': user.id,
        },
    )

    now = datetime.now()

    user.last_good_schedule_paste = req.form.get('schedule_text')
    user.last_good_schedule_paste_date = now
    user.save()

    # Remove existing schedule items for the user for the given term
    for usi in m.UserScheduleItem.objects(user_id=user.id, term_id=term_id):
        usi.delete()

    for item in processed_items:
        try:
            # Create this UserScheduleItem
            first_name, last_name = m.Professor.guess_names(item['prof_name'])
            prof_id = m.Professor.get_id_from_name(
                first_name=first_name,
                last_name=last_name,
            )
            if first_name and last_name:
                if not m.Professor.objects.with_id(prof_id):
                    m.Professor(
                        id=prof_id,
                        first_name=first_name,
                        last_name=last_name,
                    ).save()

            usi = m.UserScheduleItem(
                user_id=user.id,
                class_num=item['class_num'],
                building=item['building'],
                room=item.get('room'),
                section_type=item['section_type'],
                section_num=item['section_num'],
                start_date=datetime.fromtimestamp(item['start_date']),
                end_date=datetime.fromtimestamp(item['end_date']),
                course_id=item['course_id'],
                prof_id=prof_id,
                term_id=term_id,
            )
            try:
                usi.save()
            except me.NotUniqueError as ex:
                # Likely the case where the user pastes in two or more valid
                # schedules into the same input box
                logging.info('Duplicate error on UserScheduleItem .save(): %s'
                        % (ex))

            # Add this item to the user's course history
            # FIXME(Sandy): See if we can get program_year_id from Quest
            # Or just increment their last one
            user.add_course(usi.course_id, usi.term_id)

        except KeyError:
            logging.error("Invalid item in uploaded schedule: %s" % (item))

    # Add courses that failed to fully parse, probably due to unavailable times
    for course_id in set(failed_items):
        fsi = m.FailedScheduleItem(
            user_id=user.id,
            course_id=course_id,
            parsed_date=now,
        )

        try:
            fsi.save()
        except me.NotUniqueError as ex:
            # This should never happen since we're iterating over a set
            logging.warn('WTF this should never happen.')
            logging.warn('Duplicate error FailedScheduleItem.save(): %s' % ex)

        user.add_course(course_id, term_id)

    user.schedules_imported += 1
    user.save()

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_SCHEDULE,
        rmclogger.LOG_EVENT_UPLOAD,
        user.id
    )

    return ''

# Create the directory for storing schedules if it does not exist
SCHEDULE_DIR = os.path.join(app.config['LOG_DIR'], 'schedules')
if not os.path.exists(SCHEDULE_DIR):
    os.makedirs(SCHEDULE_DIR)

@app.route('/api/schedule/log', methods=['POST'])
@view_helpers.login_required
def schedule_log():
    user = view_helpers.get_current_user()

    file_name = '%d.txt' % int(time.time())
    file_path = os.path.join(SCHEDULE_DIR, file_name)
    with open(file_path, 'w') as f:
        f.write(flask.request.form['schedule'].encode('utf-8'))

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_SCHEDULE,
        rmclogger.LOG_EVENT_PARSE_FAILED, {
            'user_id': user.id,
            'file_path': file_path,
        },
    )

    user.last_bad_schedule_paste = flask.request.form.get('schedule')
    user.last_bad_schedule_paste_date = datetime.now()
    user.save()

    return ''

@app.route('/api/transcript', methods=['POST'])
@view_helpers.login_required
def upload_transcript():
    req = flask.request

    user = view_helpers.get_current_user()
    user_id = user.id

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
            # TODO(Sandy): Fill in course weight and grade info here
            user.add_course(course_id.lower(), term_id, program_year_id)

    if courses_by_term:
        last_term = courses_by_term[0]
        term_id = get_term_id(last_term['name'])
        user.last_term_id = term_id
        user.last_program_year_id = last_term['programYearId']
    user.program_name = transcript_data['programName']

    student_id = transcript_data.get('studentId')
    if student_id:
        user.student_id = str(student_id)

    user.cache_mutual_course_ids(view_helpers.get_redis_instance())
    user.transcripts_imported += 1
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


# Create the directory for storing transcripts if it does not exist
TRANSCRIPT_DIR = os.path.join(app.config['LOG_DIR'], 'transcripts')
if not os.path.exists(TRANSCRIPT_DIR):
    os.makedirs(TRANSCRIPT_DIR)

@app.route('/api/transcript/log', methods=['POST'])
@view_helpers.login_required
def transcript_log():
    user = view_helpers.get_current_user()

    file_name = '%d.txt' % int(time.time())
    file_path = os.path.join(TRANSCRIPT_DIR, file_name)
    with open(file_path, 'w') as f:
        f.write(flask.request.form['transcript'].encode('utf-8'))

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_TRANSCRIPT,
        rmclogger.LOG_EVENT_PARSE_FAILED, {
            'user_id': user.id,
            'file_path': file_path,
        },
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
@app.route('/api/user/course', methods=['POST', 'PUT'])
@view_helpers.login_required
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

    if user:
        sift.track('user_course', dict({
            '$user_id': str(user.id),
            '$user_email': user.email,
        }, **util.flatten_dict(uc_data)))

    # Validate request object
    course_id = uc_data.get('course_id')
    term_id = uc_data.get('term_id')
    if course_id is None or term_id is None:
        logging.error("/api/user/course got course_id (%s) and term_id (%s)" %
            (course_id, term_id))
        # TODO(david): Perhaps we should have a request error function that
        # returns a 400
        raise exceptions.ImATeapot('No course_id or term_id set')

    if not m.UserCourse.can_review(term_id):
        logging.warning("%s attempted to rate %s in future/shortlist term %s"
                % (user.id, course_id, term_id))
        raise exceptions.ImATeapot('Can\'t review a course in the future or shortlist')

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
        raise exceptions.ImATeapot('No user course found')


    orig_points = uc.num_points

    # TODO(Sandy): Consider the case where the user picked a professor and rates
    # them, but then changes the professor. We need to remove the ratings from
    # the old prof's aggregated ratings and add them to the new prof's
    # Maybe create professor if newly added
    if uc_data.get('new_prof_added'):

        new_prof_name = uc_data['new_prof_added']

        # TODO(mack): should do guess_names first, and use that to
        # generate the id
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

    points_gained = uc.num_points - orig_points
    user.award_points(points_gained, view_helpers.get_redis_instance())
    user.save()

    return util.json_dumps({
        'professor_review.comment_date': uc['professor_review'][
            'comment_date'],
        'course_review.comment_date': uc['course_review']['comment_date'],
        'points_gained': points_gained,
    })

# TODO(mack): maybe merge this api into /api/user/course/share
@app.route('/api/user/course/share', methods=['POST'])
@view_helpers.login_required
def user_course_share():
    user_course_id = flask.request.form['user_course_id']
    review_type  = flask.request.form['review_type']
    current_user = view_helpers.get_current_user()

    review = None
    points_gained = 0

    user_course = m.UserCourse.objects.get(
            id=user_course_id, user_id=current_user.id)
    if review_type == 'course':
        review = user_course.course_review
        points_gained = m.PointSource.SHARE_COURSE_REVIEW
    elif review_type == 'professor':
        review = user_course.professor_review
        points_gained = m.PointSource.SHARE_PROFESSOR_REVIEW

    # Only award points on the first share
    if not review.share_date:
        redis = view_helpers.get_redis_instance()
        current_user.award_points(points_gained, redis)
    else:
        points_gained = 0

    review.share_date = datetime.now()
    user_course.save()
    current_user.save()

    return util.json_dumps({
        'points_gained': points_gained,
    })

@app.route('/api/user/course/to_review', methods=['GET'])
@view_helpers.login_required
def next_course_to_review():
    current_user = view_helpers.get_current_user()
    uc = current_user.next_course_to_review() if current_user else None
    if not uc:
        return util.json_dumps({})

    uc.select_for_review(current_user)
    return util.json_dumps(uc.to_dict())

@app.route('/api/invite_friend', methods=['POST'])
@view_helpers.login_required
def invite_friend():
    current_user = view_helpers.get_current_user()
    orig_points  = current_user.num_points

    current_user.invite_friend(view_helpers.get_redis_instance())
    current_user.save()

    points_gained = current_user.num_points - orig_points

    return util.json_dumps({
        'num_invites': current_user.num_invites,
        'points_gained': points_gained,
    })

@app.route('/api/users/schedule_paste', methods=['GET'])
@view_helpers.admin_required
def pasted_schedule_users():
    include_good_paste = bool(flask.request.values.get('include_good_paste'))
    include_bad_paste = bool(flask.request.values.get('include_bad_paste'))

    # Start off with a query that maches no one
    query = me.Q(id__exists=False)
    if include_good_paste:
        query = query | me.Q(last_good_schedule_paste__exists=True)
    if include_bad_paste:
        query = query | me.Q(last_bad_schedule_paste__exists=True)

    users = m.User.objects.filter(query).only('id')
    user_ids = [user.id for user in users]
    print 'num_users', len(user_ids)
    return util.json_dumps({
        'user_ids': user_ids,
    })


@app.route('/api/user/last_schedule_paste', methods=['GET'])
# TODO(mack): make this work for logged in user, rather than just admins
@view_helpers.admin_required
def last_schedule_paste():

    user_id = flask.request.values.get('user_id')
    if not user_id:
        user_id = view_helpers.get_current_user().id
    else:
        user_id = bson.ObjectId(user_id)

    user = m.User.objects.with_id(user_id)
    last_schedule_paste = user.last_schedule_paste

    return util.json_dumps({
        'last_schedule_paste': last_schedule_paste,
    })

@app.route('/admin/api/generic-stats', methods=['POST'])
@view_helpers.admin_required
def dashboard_data():
    REDIS_KEY_DASHBOARD_DATA = 'dashboard_data'
    CACHE_EXPIRY_SECONDS = 3 * 60

    redis = view_helpers.get_redis_instance()
    data = redis.get(REDIS_KEY_DASHBOARD_DATA)
    if not data:
        data = rmc_stats.generic_stats(show_all=True)
        data['latest_reviews'] = rmc_stats.latest_reviews(n=5)
        data = util.json_dumps(data)

        redis.set(REDIS_KEY_DASHBOARD_DATA, data)
        redis.expire(REDIS_KEY_DASHBOARD_DATA, CACHE_EXPIRY_SECONDS)

    return data

@app.route('/dashboard', methods=['GET'])
@view_helpers.admin_required
def dashboard_page():
    data = util.json_loads(dashboard_data())
    return flask.render_template(
        'dashboard.html',
        page_script='dashboard.js',
        **data
    )

@app.route('/api/sign_up_email', methods=['POST'])
def save_sign_up_email():
    email = flask.request.values.get('email')
    logging.info('user wants to sign in with email: %s' % email)
    with open('email_sign_ups.txt', 'a') as f:
        f.write("%s\n" % email)
    return ''

# TODO(mack): Follow instructions at:
# http://stackoverflow.com/questions/4239825/static-files-in-flask-robot-txt-sitemap-xml-mod-wsgi
# to clean up how we serve up custom static path
@app.route('/google92ea789ec6f7d90c.html', methods=['GET'])
def verify_webmaster():
    # To verify site with https://www.google.com/webmasters
    file_path = os.path.join(SERVER_DIR, 'webmaster.html')
    response = flask.make_response(open(file_path).read())
    response.headers["Content-Type"] = "text/plain"
    return response


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

    toolbar = flask_debugtoolbar.DebugToolbarExtension(app)
    app.run()

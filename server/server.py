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

import rmc.shared.constants as c
import rmc.shared.secrets as s
import rmc.models as m
import rmc.shared.util as util
import rmc.shared.rmclogger as rmclogger
import rmc.server.profile as profile
import rmc.server.rmc_sift as rmc_sift
import rmc.server.view_helpers as view_helpers

import rmc.shared.facebook as facebook

VERSION = int(time.time())

app = flask.Flask(__name__)

app.config.from_envvar('FLASK_CONFIG')
me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)


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
    return response

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

@app.route('/schedule', defaults={'profile_user_id': None})
@app.route('/schedule/<string:profile_user_id>')
def schedule_page(profile_user_id):
    return profile.render_schedule_page(profile_user_id)

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

    return flask.render_template('course_page.html',
        page_script='course_page.js',
        course_obj=course_dict_list[0],
        professor_objs=professor_dict_list,
        tip_objs=tip_dict_list,
        user_course_objs=user_course_dict_list,
        user_objs=user_dicts.values(),
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
            raise ApiError('No fbsr set')

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

        expiry_date_timestamp = time.mktime(
                fb_access_token_expiry_date.timetuple())
        return util.json_dumps({
            'fb_access_token_expires_on': expiry_date_timestamp,
            'fb_access_token': fb_access_token,
        })
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
            'keywords': str(keywords),
            'term': term,
            'sort_mode': sort_mode,
            'name': name,
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
        raise ApiError('No fbsr set')

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

    user.last_good_schedule_paste = req.form.get('schedule_text')
    user.last_good_schedule_paste_date = datetime.now()
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
            usi.save()

            # Add this item to the user's course history
            # FIXME(Sandy): See if we can get program_year_id from Quest
            # Or just increment their last one
            user.add_course(usi.course_id, usi.term_id)

        except KeyError:
            logging.error("Invalid item in uploaded schedule: %s" % (item))

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
        raise ApiError('No course_id or term_id set')

    if term_id > util.get_current_term_id():
        logging.warning("%s attempted to rate %s in future/shortlist term %s"
                % (user.id, course_id, term_id))
        raise ApiError('Can\'t review a course in the future or shortlist')

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

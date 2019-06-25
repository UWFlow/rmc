from datetime import datetime
import bson
import flask
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile
assert line_profile  # silence pyflakes
import logging
import mongoengine as me
import os
import re
import time
import werkzeug.exceptions as exceptions

import rmc.shared.constants as c
import rmc.shared.secrets as s
import rmc.models as m
import rmc.html_snapshots as html_snapshots
import rmc.shared.facebook as facebook
import rmc.shared.util as util
import rmc.shared.rmclogger as rmclogger
from rmc.server.app import app
import rmc.server.api.v1 as api_v1
import rmc.server.profile as profile
import rmc.server.view_helpers as view_helpers
import rmc.analytics.stats as rmc_stats
import rmc.shared.schedule_screenshot as schedule_screenshot
import rmc.kittens.data as kitten_data


app.register_blueprint(api_v1.api)

VERSION = int(time.time())

SERVER_DIR = os.path.dirname(os.path.realpath(__file__))

flask_render_template = flask.render_template

KITTEN_DATA = kitten_data.get_kitten_data()


def render_template(*args, **kwargs):
    redis = view_helpers.get_redis_instance()

    current_user = view_helpers.get_current_user()
    should_renew_fb_token = False
    if (current_user and
        current_user.fbid and
        not current_user.is_demo_account and
        not hasattr(flask.request, 'as_user_override')):
        should_renew_fb_token = current_user.should_renew_fb_token

    kwargs.update({
        'env': app.config['ENV'],
        'VERSION': VERSION,
        'NUM_KITTENS': len(KITTEN_DATA),
        'js_dir': app.config['JS_DIR'],
        'ga_property_id': app.config['GA_PROPERTY_ID'],
        'total_points': int(redis.get('total_points') or 0),
        'current_user': current_user,
        'should_renew_fb_token': should_renew_fb_token,
        'current_term_id': util.get_current_term_id(),
        'user_agent': flask.request.headers['User-Agent'] if 'User-Agent' in flask.request.headers else 'No Info',
    })
    return flask_render_template(*args, **kwargs)
flask.render_template = render_template


# Jinja filters
@app.template_filter()
def tojson(obj):
    return util.json_dumps(obj)


@app.template_filter()
def version(file_name):
    return '%s?v=%s' % (file_name, VERSION)


@app.before_request
def render_snapshot_for_great_seo():
    """Renders static snapshots captured using phantomjs to improve SEO."""
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


@app.before_request
def csrf_protect():
    """Require a valid CSRF token for any method other than GET."""
    req = flask.request

    # TODO(sandy): Use get-csrf-token from the API instead of excluding here
    # Exclude API login from CSRF protection, because API clients will not yet
    # have a CSRF token when they hit this endpoint (eg. mobile apps).
    if req.endpoint == 'api.login_facebook':
        return

    # Based on http://flask.pocoo.org/snippets/3/, but modified to use headers
    # and generally be more Rails-like
    if req.method != 'GET':
        # We intentionally don't invalidate CSRF tokens after a single use to
        # enable multiple AJAX requests originating from the page load to all
        # work off the same CSRF token.
        token = flask.session.get(view_helpers.SESSION_COOKIE_KEY_CSRF, None)
        if not token or token != req.headers.get('X-CSRF-Token'):
            flask.abort(403)


app.jinja_env.globals['csrf_token'] = view_helpers.generate_csrf_token


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
    # TODO(Sandy): If we request extra permissions from FB, we'll need to show
    # them the landing page to let them to Connect again and accept the new
    # permissions. Alternatively, we could use other means of requesting for
    # new perms
    request = flask.request
    logout = bool(request.values.get('logout'))
    referrer_id = request.values.get('meow') or request.values.get('referrer')

    if logout:
        view_helpers.logout_current_user()

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


# TODO(david): Figure out why there's a user who's hitting
# /schedule/RIGFOY5JA.ics on regular intervals... I'm guessing user might've
# exported improperly by just pasting the "/schedule/RIGFOY5JA" URL into their
# calendar app's schedule import.
@app.route('/schedule/<string:profile_user_secret_id>.ics')
def schedule_page_ics_redirect(profile_user_secret_id):
    return flask.redirect('/schedule/ical/%s.ics' % profile_user_secret_id,
            301)


@app.route('/schedule/<string:profile_user_secret_id>')
def schedule_page(profile_user_secret_id):
    profile_user = (m.User.objects(secret_id=profile_user_secret_id.upper())
                        .first())

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

    sort_modes = map(clean_sort_modes, m.Course.SORT_MODES)

    current_user = view_helpers.get_current_user()

    # Don't show friends_taken sort mode when user has no friends
    if current_user and len(current_user.friend_ids) == 0:
        sort_modes = [sm for sm in sort_modes if sm['name'] != 'friends_taken']

    return flask.render_template(
        'search_page.html',
        page_script='search_page.js',
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
                include_friends=True, full_user_courses=True,
                include_sections=True))

    professor_dict_list = m.Professor.get_full_professors_for_course(
            course, current_user)

    user_dicts = {}
    if current_user:
        # TODO(Sandy): This is poorly named because its not only friends...
        friend_ids = ({uc_dict['user_id'] for uc_dict in user_course_dict_list}
                - set([current_user.id]))
        friends = m.User.objects(id__in=friend_ids).only(*m.User.CORE_FIELDS)

        for friend in friends:
            user_dicts[friend.id] = friend.to_dict()
        user_dicts[current_user.id] = current_user.to_dict(
                include_course_ids=True)

    tip_dict_list = course.get_reviews(current_user, user_course_list)

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


@app.route('/professor/<string:prof_id>')
def prof_page(prof_id):
    prof = m.Professor.objects.with_id(prof_id)
    if not prof:
        flask.abort(404)

    current_user = view_helpers.get_current_user()
    courses_taught = prof.get_courses_taught()
    courses = m.Course.objects(id__in=courses_taught)
    full_course_info = [c.to_dict() for c in courses]

    return flask.render_template('prof_page.html',
        page_script='prof_page.js',
        prof_name=prof.name,
        prof_ratings=prof.get_ratings_for_career(),
        prof_courses=courses_taught,
        prof_courses_full=full_course_info,
        prof_departments_list=prof.get_departments_taught(),
        tip_objs_by_course=prof.get_reviews_for_all_courses(current_user)
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
    ).only(*(m.User.CORE_FIELDS + ['course_history']))

    user_objs = []
    for user in [current_user] + list(friends):
        user_objs.append(user.to_dict())

    return flask.render_template('onboarding_page.html',
        page_script='onboarding_page.js',
        current_user_id=current_user.id,
        user_objs=user_objs,
    )


@app.route('/login/facebook', methods=['POST'])
def login_with_facebook():
    """Login or create an account using Facebook connect

    Upon successful login or account creation, returns a 'secure cookie'
    (provided by Flask) containing the session data.

    Takes a Facebook signed request in the form of:
    {
        'fb_signed_request': obj
    }
    """
    req = flask.request

    fbsr = req.form.get('fb_signed_request')

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_GENERIC,
        rmclogger.LOG_EVENT_LOGIN, {
            'fbsr': fbsr,
            'request_form': req.form,
            'type': rmclogger.LOGIN_TYPE_STRING_FACEBOOK,
        },
    )

    if (fbsr is None):
        raise exceptions.ImATeapot('No fbsr set')

    fb_data = facebook.get_fb_data(fbsr, app.config)
    fbid = fb_data['fbid']
    fb_access_token = fb_data['access_token']
    fb_access_token_expiry_date = fb_data['expires_on']
    is_invalid = fb_data['is_invalid']

    user = m.User.objects(fbid=fbid).first()
    if user:
        # Existing user. Update with their latest Facebook info
        user.fb_access_token = fb_access_token
        user.fb_access_token_expiry_date = fb_access_token_expiry_date
        user.fb_access_token_invalid = is_invalid
        user.save()

        # Authenticate
        view_helpers.login_as_user(user)

        rmclogger.log_event(
            rmclogger.LOG_CATEGORY_IMPRESSION,
            rmclogger.LOG_EVENT_LOGIN, {
                'new_user': False,
                'user_id': user.id,
                'type': rmclogger.LOGIN_TYPE_STRING_FACEBOOK,
            },
        )
    else:
        # New user, or existing email logins user.
        now = datetime.now()
        email = req.form.get('email')
        user_data = {
            'fb_access_token': fb_access_token,
            'fb_access_token_expiry_date': fb_access_token_expiry_date,
            'fbid': fbid,
            'friend_fbids': flask.json.loads(req.form.get('friend_fbids')),
            'gender': req.form.get('gender'),
            'last_visited': now,
        }

        user = m.User.objects(email=email).first() if email else None
        if user:
            # Update existing account with Facebook data
            referrer_id = None
            for k, v in user_data.iteritems():
                user[k] = v
            user.save()
        else:
            # Create an account with their Facebook data
            user_data.update({
                'email': email,
                'first_name': req.form.get('first_name'),
                'join_date': now,
                'join_source': m.User.JoinSource.FACEBOOK,
                'last_name': req.form.get('last_name'),
                'middle_name': req.form.get('middle_name'),
            })

            referrer_id = req.form.get('referrer_id')
            if referrer_id:
                try:
                    user_data['referrer_id'] = bson.ObjectId(referrer_id)
                except bson.errors.InvalidId:
                    pass

            user = m.User(**user_data)
            user.save()

        # Authenticate
        view_helpers.login_as_user(user)

        rmclogger.log_event(
            rmclogger.LOG_CATEGORY_IMPRESSION,
            rmclogger.LOG_EVENT_LOGIN, {
                'new_user': True,
                'user_id': user.id,
                'referrer_id': referrer_id,
                'type': rmclogger.LOGIN_TYPE_STRING_FACEBOOK,
            },
        )

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


@app.route('/kittens')
def kittens():
    return flask.render_template('kittens_page.html', kitten_data=KITTEN_DATA)


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

    view_helpers.login_as_user(user)
    return flask.redirect('/profile/%s' % user.id, 302)


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


# TODO(david): Doesn't seem like this is used anymore... remove.
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


@app.route('/api/course-search', methods=['GET'])
# TODO(mack): find a better name for function
# TODO(mack): a potential problem with a bunch of the sort modes is if the
# value they are sorting by changes in the objects. this can lead to missing
# or duplicate contests being passed to front end
def search_courses():
    current_user = view_helpers.get_current_user()
    courses, has_more = m.Course.search(flask.request.values, current_user)

    course_dict_list, user_course_dict_list, user_course_list = (
            m.Course.get_course_and_user_course_dicts(
                courses, current_user, include_friends=True,
                full_user_courses=False, include_sections=True))

    professor_dict_list = m.Professor.get_reduced_professors_for_courses(
            courses)

    user_dict_list = []
    if current_user:
        user_ids = [uc['user_id'] for uc in user_course_dict_list
                if uc['user_id'] != current_user.id]
        users = m.User.objects(id__in=user_ids).only(*m.User.CORE_FIELDS)
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
    '''Renew the current user's Facebook access token.

    The client should make this call periodically (once every couple months,
    see User.should_renew_fb_token) to keep the access token up to date.

    Takes a Facebook signed request object from the post params in the form of:
    {
        'fb_signed_request': obj
    }
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
    is_invalid = fb_data['is_invalid']

    if not is_invalid:
        current_user.fb_access_token_expiry_date = expires_on
        current_user.fb_access_token = access_token
        current_user.fb_access_token_invalid = is_invalid

        # Update the user's fb friend list, since it's likely outdated by now
        try:
            current_user.update_fb_friends(
                    facebook.get_friend_list(access_token))
        except:
            # Not sure why this would happen. Usually it's due to invalid
            # access_token, but we JUST got the token, so it should be valid
            logging.warn(
                    "/api/renew-fb: get_friend_list failed with token (%s)"
                    % access_token)

        current_user.save()

    return ''


@app.route('/api/schedule', methods=['POST'])
@view_helpers.login_required
def upload_schedule():
    req = flask.request
    user = view_helpers.get_current_user()

    schedule_data = util.json_loads(req.form.get('schedule_data'))
    courses = schedule_data['courses']
    failed_courses = schedule_data['failed_courses']
    term_name = schedule_data['term_name']
    term_id = m.Term.id_from_name(term_name)

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

    for course in courses:
        # Add this item to the user's course history
        # FIXME(Sandy): See if we can get program_year_id from Quest
        # Or just increment their last one
        user.add_course(course['course_id'], term_id)

        for item in course['items']:
            try:
                # Create this UserScheduleItem
                first_name, last_name = m.Professor.guess_names(
                        item['prof_name'])
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
                    section_type=item['section_type'].upper(),
                    section_num=item['section_num'],
                    start_date=datetime.utcfromtimestamp(item['start_date']),
                    end_date=datetime.utcfromtimestamp(item['end_date']),
                    course_id=course['course_id'],
                    prof_id=prof_id,
                    term_id=term_id,
                )
                try:
                    usi.save()
                except me.NotUniqueError as ex:
                    # Likely the case where the user pastes in two or more
                    # valid schedules into the same input box
                    logging.info(
                            'Duplicate error on UserScheduleItem .save(): %s'
                            % (ex))

            except KeyError:
                logging.error("Invalid item in uploaded schedule: %s" % (item))

    # Add courses that failed to fully parse, probably due to unavailable times
    for course_id in set(failed_courses):
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

    schedule_screenshot.update_screenshot_async(user)

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_SCHEDULE,
        rmclogger.LOG_EVENT_UPLOAD,
        user.id
    )

    return ''


def get_schedule_dir():
    return os.path.join(app.config['LOG_DIR'], 'schedules')


@app.route('/api/schedule/screenshot_url', methods=['GET'])
@view_helpers.login_required
def schedule_screenshot_url():
    user = view_helpers.get_current_user()

    return util.json_dumps({
        # Note that this may be None
        "url": schedule_screenshot.get_screenshot_url(user)
    })


@app.route('/api/schedule/log', methods=['POST'])
@view_helpers.login_required
def schedule_log():
    user = view_helpers.get_current_user()

    file_name = '%d.txt' % int(time.time())
    file_path = os.path.join(get_schedule_dir(), file_name)
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


def get_transcript_dir():
    return os.path.join(app.config['LOG_DIR'], 'transcripts')


@app.route('/api/transcript/log', methods=['POST'])
@view_helpers.login_required
def transcript_log():
    user = view_helpers.get_current_user()

    file_name = '%d.txt' % int(time.time())
    file_path = os.path.join(get_transcript_dir(), file_name)
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

    # Remove calendar items corresponding to the user course
    if not m.Term.is_shortlist_term(user_course.term_id):
        m.UserScheduleItem.objects(
            user_id=current_user.id,
            course_id=user_course.course_id,
            term_id=user_course.term_id,
        ).delete()

    user_course.delete()

    return ''


# XXX[uw](Sandy): Make this not completely fail when hitting this endpoint,
# otherwise the user would have wasted all their work. We can do one of 1. a FB
# login on the client 2. store their data for after they login 3. don't let
# them start writing if they aren't logged in. 1 or 3 seems best
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
        raise exceptions.ImATeapot(
                "Can't review a course in the future or shortlist")

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

    # TODO(Sandy): Consider the case where the user picked a professor and
    # rates them, but then changes the professor. We need to remove the ratings
    # from the old prof's aggregated ratings and add them to the new prof's
    # Maybe create professor if newly added
    if uc_data.get('new_prof_added'):

        new_prof_name = uc_data['new_prof_added']

        # TODO(mack): should do guess_names first, and use that to
        # generate the id
        prof_id = m.Professor.get_id_from_name(new_prof_name)
        uc.professor_id = prof_id

        # TODO(Sandy): Have some kind of sanity check for professor names.
        # Don't allow ridiculousness like "Santa Claus", "aksnlf",
        # "swear words"
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
    review_type = flask.request.form['review_type']
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
    orig_points = current_user.num_points

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


# TODO(david): Move this somewhere else.
def dashboard_data():
    data = rmc_stats.generic_stats()
    data['latest_reviews'] = rmc_stats.latest_reviews(n=5)
    return data


@app.route('/admin/api/generic-stats', methods=['POST'])
@view_helpers.admin_required
def generic_stats():
    return util.json_dumps(dashboard_data())


@app.route('/dashboard', methods=['GET'])
@view_helpers.admin_required
def dashboard_page():
    data = dashboard_data()
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


@app.route('/api/schedules/backfill_screenshots', methods=['POST'])
@view_helpers.admin_required
def backfill_screenshots():
    # We don't use a projection on user objects because update_screenshot_async
    # could call user.save().
    for user in m.User.objects:
        schedule_screenshot.update_screenshot_async(user)

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


def before_app_run():
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
    app.config.from_envvar('FLASK_CONFIG')

    if not app.debug:
        from logging.handlers import TimedRotatingFileHandler
        logging.basicConfig(level=logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s in'
                ' %(module)s:%(lineno)d %(message)s')

        file_handler = TimedRotatingFileHandler(
                            filename=app.config['LOG_PATH'],
                            when='D')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
        logging.getLogger('').addHandler(file_handler)  # Root handler

    else:
        logging.basicConfig(level=logging.DEBUG)

    # Create the directory for storing schedules if it does not exist
    schedule_dir = get_schedule_dir()
    if not os.path.exists(schedule_dir):
        os.makedirs(schedule_dir)

    # create the directory for storing transcripts if it does not exist
    transcript_dir = get_transcript_dir()
    if not os.path.exists(transcript_dir):
        os.makedirs(transcript_dir)

if __name__ == '__main__':
    before_app_run()

    # Late import since this isn't used on production
    import flask_debugtoolbar

    app.debug = True
    app.config.update({
        'DEBUG_TB_INTERCEPT_REDIRECTS': False,
        'DEBUG_TB_PROFILER_ENABLED': True,
        'DEBUG_TB_PANELS': [
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
    app.run(host='0.0.0.0')

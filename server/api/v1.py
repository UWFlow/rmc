"""Version 1 of Flow's public, officially-supported API."""

import collections
import datetime

import bson
import flask
import mongoengine as me

import rmc.models as m
import rmc.server.api.api_util as api_util
import rmc.server.view_helpers as view_helpers
import rmc.shared.schedule_screenshot as schedule_screenshot
import rmc.shared.facebook as facebook
import rmc.shared.rmclogger as rmclogger


# TODO(david): Bring in other API methods from server.py to here.
# TODO(david): Document API methods. Clarify which methods accept user auth.


api = flask.Blueprint('api', __name__, url_prefix='/api/v1')


###############################################################################
# /courses/:course_id routes: info about a specific course


@api.route('/courses/<string:course_id>', methods=['GET'])
def get_course(course_id):
    course = m.Course.objects.with_id(course_id)
    if not course:
        raise api_util.ApiNotFoundError('Course %s not found. :(' % course_id)

    current_user = view_helpers.get_current_user()
    course_reviews = course.get_reviews(current_user)

    # TODO(david): Implement HATEOAS (URLs of other course info endpoints).
    return api_util.jsonify(dict(course.to_dict(), **{
        'reviews': course_reviews,
    }))


@api.route('/courses/<string:course_id>/professors', methods=['GET'])
def get_course_professors(course_id):
    course = m.Course.objects.with_id(course_id)
    if not course:
        raise api_util.ApiNotFoundError('Course %s not found. :(' % course_id)

    current_user = view_helpers.get_current_user()
    professors = m.Professor.get_full_professors_for_course(
            course, current_user)

    return api_util.jsonify({
        'professors': professors
    })


@api.route('/courses/<string:course_id>/exams', methods=['GET'])
def get_course_exams(course_id):
    exams = m.Exam.objects(course_id=course_id)
    exam_dict_list = [e.to_dict() for e in exams]
    last_updated_date = exams[0].id.generation_time if exams else None

    return api_util.jsonify({
        'exams': exam_dict_list,
        'last_updated_date': last_updated_date,
    })


@api.route('/courses/<string:course_id>/sections', methods=['GET'])
def get_course_sections(course_id):
    sections = m.section.Section.get_for_course_and_recent_terms(course_id)
    section_dicts = [s.to_dict() for s in sections]

    return api_util.jsonify({
        'sections': section_dicts
    })


@api.route('/courses/<string:course_id>/users', methods=['GET'])
def get_course_users(course_id):
    """Get users who are taking, have taken, or plan to take the given course.

    Restricts to only users that current user is allowed to know (is FB friends
    with). Also returns which terms users took the course.

    Example:
        {
          "users": [
            {
              "num_points": 2710,
              "first_name": "David",
              "last_name": "Hu",
              "name": "David Hu",
              "course_ids": [],
              "fbid": "541400376",
              "profile_pic_urls": {
                'default':
                    'https://graph.facebook.com/541400376/picture',
                'large':
                    'https://graph.facebook.com/541400376/picture?type=large',
                'square':
                    'https://graph.facebook.com/541400376/picture?type=square'
              }
              "num_invites": 0,
              "friend_ids": [],
              "program_name": "Software Engineering",
              "course_history": [],
              "id": "50a532518aedf423ac645891"
            }
          ],
          "term_users": [
            {
              "term_id": "2013_01",
              "user_ids": [ "50a532518aedf423ac645891" ],
              "term_name": "Winter 2013"
            }
          ]
        }
    """
    course = m.Course.objects.with_id(course_id)
    if not course:
        raise api_util.ApiNotFoundError('Course %s not found. :(' % course_id)

    current_user = view_helpers.get_current_user()
    course_dict_list, user_course_dict_list, user_course_list = (
            m.Course.get_course_and_user_course_dicts(
                [course], current_user, include_friends=True))

    user_ids = set(ucd['user_id'] for ucd in user_course_dict_list)
    users = m.User.objects(id__in=list(user_ids)).only(
            *(m.User.CORE_FIELDS + ['num_points', 'num_invites',
            'program_name']))

    term_users_map = collections.defaultdict(list)
    for ucd in user_course_dict_list:
        term_users_map[ucd['term_id']].append(ucd['user_id'])

    term_users = []
    for term_id, user_ids in term_users_map.iteritems():
        term_users.append({
            'term_id': term_id,
            'term_name': m.Term.name_from_id(term_id),
            'user_ids': user_ids,
        })

    return api_util.jsonify({
        'users': [user.to_dict(extended=False) for user in users],
        'term_users': term_users,
    })


###############################################################################
# Endpoints used for authentication


@api.route('/login/email', methods=['POST'])
def login_email():
    """Attempt to log in a user with the credentials encoded in the POST body.

    Expects the following form data:
        email: E.g. 'tswift@gmail.com'
        password: E.g. 'iknewyouweretrouble'

    Responds with the session cookie via the `set-cookie` header on success.
    Send the associated cookie for all subsequent API requests that accept
    user authentication.
    """
    # Prevent a CSRF attack from replacing a logged-in user's account with the
    # attacker's.
    current_user = view_helpers.get_current_user()
    if current_user:
        return api_util.jsonify({'message': 'A user is already logged in.'})

    params = flask.request.form.copy()

    # Don't log the password
    password = params.pop('password', None)

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_LOGIN, {
            'params': params,
            'type': rmclogger.LOGIN_TYPE_STRING_EMAIL,
        },
    )

    email = params.get('email')

    if not email:
        raise api_util.ApiBadRequestError('Must provide email.')

    if not password:
        raise api_util.ApiBadRequestError('Must provide password.')

    user = m.User.auth_user(email, password)

    if not user:
        raise api_util.ApiNotFoundError('Incorrect email or password.')

    view_helpers.login_as_user(user)

    return api_util.jsonify({'message': 'Logged in user %s' % user.name})


@api.route('/login/facebook', methods=['POST'])
def login_facebook():
    """Attempt to login a user with FB credentials encoded in the POST body.

    Expects the following form data:
        fb_access_token: Facebook user access token. This is used to verify
            that the user did authenticate with Facebook and is authenticated
            to our app. The user's FB ID is also obtained from this token.

    Responds with the session cookie via the `set-cookie` header on success.
    Send the associated cookie for all subsequent API requests that accept
    user authentication.

    Also returns the CSRF token, which must be sent as the value of the
    "X-CSRF-Token" header for all non-GET requests.
    """
    # Prevent a CSRF attack from replacing a logged-in user's account with the
    # attacker's.
    current_user = view_helpers.get_current_user()
    if current_user:
        return api_util.jsonify({'message': 'A user is already logged in.'})

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_SIGNUP, {
            'type': rmclogger.LOGIN_TYPE_STRING_FACEBOOK,
        },
    )

    req = flask.request
    fb_access_token = req.form.get('fb_access_token')

    # We perform a check to confirm the fb_access_token is indeed the person
    # identified by fbid, and that it was our app that generated the token.
    token_info = facebook.get_access_token_info(fb_access_token)

    if not token_info['is_valid'] or not token_info.get('user_id'):
        raise api_util.ApiForbiddenError(
                'The given FB credentials are invalid.')

    fbid = str(token_info['user_id'])
    user = m.User.objects(fbid=fbid).first()

    if not user:
        raise api_util.ApiForbiddenError('No user with fbid %s exists. '
                'Create an account at uwflow.com.' % fbid)

    view_helpers.login_as_user(user)
    # TODO(sandy): We don't need to do this anymore, just use the endpoint
    csrf_token = view_helpers.generate_csrf_token()

    return api_util.jsonify({
        'message': 'Logged in user %s' % user.name,
        'csrf_token': csrf_token,
    })


@api.route('/signup/email', methods=['POST'])
def signup_email():
    """Create a new account using data encoded in the POST body.

    Expects the following form data:
        first_name: E.g. 'Taylor'
        last_name: E.g. 'Swift'
        email: E.g. 'tswift@gmail.com'
        password: E.g. 'iknewyouweretrouble'

    Responds with the session cookie via the `set-cookie` header on success.
    Send the associated cookie for all subsequent API requests that accept
    user authentication.
    """
    # Prevent a CSRF attack from replacing a logged-in user's account with
    # a new account with known credentials
    current_user = view_helpers.get_current_user()
    if current_user:
        return api_util.jsonify({'message': 'A user is already logged in.'})

    params = flask.request.form.copy()

    # Don't log the password
    password = params.pop('password', None)

    rmclogger.log_event(
        rmclogger.LOG_CATEGORY_API,
        rmclogger.LOG_EVENT_SIGNUP, {
            'params': params,
            'type': rmclogger.LOGIN_TYPE_STRING_EMAIL,
        },
    )

    first_name = params.get('first_name')
    last_name = params.get('last_name')
    email = params.get('email')

    if not first_name:
        raise api_util.ApiBadRequestError('Must provide first name.')

    if not last_name:
        raise api_util.ApiBadRequestError('Must provide last name.')

    if not email:
        raise api_util.ApiBadRequestError('Must provide email.')

    if not password:
        raise api_util.ApiBadRequestError('Must provide password.')

    try:
        user = m.User.create_new_user_from_email(
                first_name, last_name, email, password)
    except m.User.UserCreationError as e:
        raise api_util.ApiBadRequestError(e.message)

    view_helpers.login_as_user(user)

    return api_util.jsonify({
        'message': 'Created and logged in user %s' % user.name
    })


@api.route('/csrf-token', methods=['GET'])
def csrf_token():
    """Return the CSRF token for the current seesion.

    Responds with the session cookie via the `set-cookie` header on success.
    You should send the associated cookie for (at least) all subsequent non-GET
    requests.

    Returns the CSRF token, which must be sent as the value of the
    "X-CSRF-Token" header for all non-GET requests.
    """
    return api_util.jsonify({
        'token': view_helpers.generate_csrf_token()
    })


###############################################################################
# /users/:user_id endpoints: info about a user


def _get_user_require_auth(user_id=None):
    """Return the requested user only if authenticated and authorized.

    Defaults to the current user if no user_id given.

    Guaranteed to return a user object.
    """
    current_user = view_helpers.get_current_user()
    if not current_user:
        raise api_util.ApiBadRequestError('Must authenticate as a user.')

    if not user_id:
        return current_user

    try:
        user_id_bson = bson.ObjectId(user_id)
    except bson.errors.InvalidId:
        raise api_util.ApiBadRequestError(
                'User ID %s is not a valid BSON ObjectId.' % user_id)

    # Does the the current user have permission to get info about this user?
    if (user_id_bson == current_user.id or user_id_bson in
            current_user.friend_ids):
        user = m.User.objects.with_id(user_id_bson)
        if user:
            return user

    raise api_util.ApiForbiddenError(
            'Not authorized to get info about this user.')


@api.route('/user', defaults={'user_id': None}, methods=['GET'])
@api.route('/users/<string:user_id>', methods=['GET'])
def get_user(user_id):
    user = _get_user_require_auth(user_id)
    user_dict = user.to_dict(extended=False)
    return api_util.jsonify(user_dict)


@api.route('/user/schedule', defaults={'user_id': None}, methods=['GET'])
@api.route('/users/<string:user_id>/schedule', methods=['GET'])
def get_user_schedule(user_id):
    user = _get_user_require_auth(user_id)
    schedule_item_dict_list = user.get_schedule_item_dicts()
    screenshot_url = schedule_screenshot.get_screenshot_url(user)

    return api_util.jsonify({
        'schedule': schedule_item_dict_list,
        'screenshot_url': screenshot_url,
    })


@api.route('/user/exams', defaults={'user_id': None}, methods=['GET'])
@api.route('/users/<string:user_id>/exams', methods=['GET'])
def get_user_exams(user_id):
    user = _get_user_require_auth(user_id)
    exams = user.get_current_term_exams()
    exam_dicts = [e.to_dict() for e in exams]
    last_updated_date = exams[0].id.generation_time if exams else None

    return api_util.jsonify({
        'exams': exam_dicts,
        'last_updated_date': last_updated_date,
    })


@api.route('/user/courses', defaults={'user_id': None}, methods=['GET'])
@api.route('/users/<string:user_id>/courses', methods=['GET'])
def get_user_courses(user_id):
    """Get courses that a user took, is taking, or plan to take (shortlist).

    Also contains user-specific information about those courses, such as the
    term the user took the course in and the user's ratings and reviews (if
    any).

    Example:
        {
          "courses": [
            {
              "ratings": [
                { "count": 25, "rating": 0.08, "name": "usefulness" },
                { "count": 100, "rating": 0.47, "name": "interest" },
                { "count": 100, "rating": 0.63, "name": "easiness" }
              ],
              "code": "CHE 102",
              "name": "Chemistry for Engineers",
              "prereqs": "Open only to students in Chemical Engineering",
              "overall": { "count": 131, "rating": 0.7099236641221374 },
              "professor_ids": [ "hyuk_sang_park" ],
              "user_course_id": "50a9c41c8aedf423ac6458b1",
              "id": "che102",
              "description": "Chemical principles blah blah blah..."
            }
          ],
          "user_courses": [
            {
              "id": "50a9c41c8aedf423ac6458b1",
              "user_id": "50a532518aedf423ac645891",
              "course_id": "che102",
              "term_name": "Fall 2009",
              "term_id": "2009_09",
              "has_reviewed": true,
              "professor_id": "jao_soares",
              "course_review": {
                "comment": "Took off faster than a green light go.",
                "ratings": [
                  { "rating": 1.0, "name": "usefulness" },
                  { "rating": null, "name": "easiness" },
                  { "rating": null, "name": "interest" }
                ],
                "comment_date": 1355447961031,
                "privacy": "friends"
              },
              "professor_review": {
                "comment": "Skipped the conversation when you already know.",
                "ratings": [
                  { "rating": 1.0, "name": "clarity" },
                  { "rating": null, "name": "passion" }
                ],
                "comment_date": 1355447928463,
                "privacy": "friends"
              },
              "program_year_id": "1A"
            }
          ]
        }
    """
    user = _get_user_require_auth(user_id)

    courses = list(m.Course.objects(id__in=set(user.course_ids)))
    course_dicts, user_course_dicts, _ = (
            m.Course.get_course_and_user_course_dicts(courses, user))

    return api_util.jsonify({
        'courses': course_dicts,
        'user_courses': user_course_dicts,
    })


@api.route('/user/friends', defaults={'user_id': None}, methods=['GET'])
@api.route('/users/<string:user_id>/friends', methods=['GET'])
def get_user_friends(user_id):
    user = _get_user_require_auth(user_id)
    friends = user.get_friends()
    friend_dicts = [f.to_dict(extended=False) for f in friends]

    return api_util.jsonify({
        'friends': friend_dicts
    })


@api.route('/user/shortlist/<string:course_id>', methods=['PUT'])
def add_course_to_shortlist(course_id):
    """Adds the given course to the user's shortlist.

    Idempotent.
    """
    user = _get_user_require_auth()
    user_course = user.add_course(course_id, m.Term.SHORTLIST_TERM_ID)

    if user_course is None:
        raise api_util.ApiBadRequestError(
                'Could not add course %s to shortlist. :(' % course_id)

    return api_util.jsonify({
        'user_course': user_course.to_dict(),
    })

# TODO(david): Add corresponding remove course endpoint

@api.route('/user/rate_review_for_user', methods=['PUT'])
def rate_review_for_user():
    """Rates the review with the id in data as helpful or not
    for the given user
    """
    values = flask.request.values
    review_id = values.get('review_id')
    voted_helpful = values.get('voted_helpful')
    review_type = values.get('review_type')

    uc_review = None
    filtered_courses = m.UserCourse.objects(id=review_id)
    if len(filtered_courses) > 0:
        uc = filtered_courses[0]
        if review_type == 'course':
            uc_review = uc.course_review
        else:
            uc_review = uc.professor_review
    else:
        filtered_courses = m.MenloCourse.objects(id=review_id)
        if len(filtered_courses) > 0:
            uc = filtered_courses[0]
            uc_review = uc.professor_review

    vote_added_response = api_util.jsonify({
        'success': True
    })
    voted_already_response = api_util.jsonify({
        'already_voted': True
    })

    user = _get_user_require_auth()
    if review_type == 'course':
        if review_id in user.voted_course_review_ids:
            return voted_already_response
        user.voted_course_review_ids.append(review_id)
    elif review_type == 'prof':
        if review_id in user.voted_prof_review_ids:
            return voted_already_response
        user.voted_prof_review_ids.append(review_id)
    user.save()

    if uc_review:
        if voted_helpful == 'true':
            uc_review.num_voted_helpful += 1
        else:
            uc_review.num_voted_not_helpful += 1
        uc.save()

    return vote_added_response

@api.route('/user/scholarships/<string:scholarship_id>', methods=['DELETE'])
def remove_scholarship_from_profile(scholarship_id):
    """Removes the scholarship from the users profile so it won't show
    up on their profile page any more
    """
    successfully_removed_response = api_util.jsonify({
        'success': True
    })
    already_removed_response = api_util.jsonify({
        'already_removed': True
    })

    user = _get_user_require_auth()
    if scholarship_id in user.closed_scholarship_ids:
        return already_removed_response

    user.closed_scholarship_ids.append(scholarship_id)
    user.save()
    return successfully_removed_response

###############################################################################
# /search* endpoints: Search API


@api.route('/search/courses')
def search_courses():
    """Search courses from various criteria.

    Accepts the following query parameters:
        keywords: Keywords to search on
        sort_mode: Name of a sort mode. See Course.SORT_MODES. If this is
            'friends_taken', a user must be authenticated, otherwise, will
            default to the 'popular' sort mode.
        direction: 1 for ascending, -1 for descending
        count: Max items to return (aka. limit)
        offset: Index of first search result to return (aka. skip)
        exclude_taken_courses: "yes" to exclude courses current user has taken.

    If a user is authenticated, additional user-specific info will be returned,
    such as terms user took each course and ratings and reviews (if any).
    """
    current_user = view_helpers.get_current_user()
    courses, has_more = m.Course.search(flask.request.values, current_user)

    course_dicts, user_course_dicts, _ = (
            m.Course.get_course_and_user_course_dicts(courses, current_user))

    return api_util.jsonify({
        'courses': course_dicts,
        'user_courses': user_course_dicts,
        'has_more': has_more,
    })


@api.route('/search/unified')
def search_unified():
    """Returns an array of course objects and an array of friend objects which
    power the unified search bar.
    """
    result_types = flask.request.args.get('result_types').split(',')

    # TODO(david): Cache this.
    course_dicts = []
    if 'courses' in result_types:
        courses = sorted(list(m.Course.objects().only('id', 'name',
                '_keywords', 'department_id', 'number')), key=lambda c: c.id)
        course_dicts = [{
            'label': c.id,
            'name': c.name,
            'type': 'course',
            'tokens': c._keywords,
            'department_id': c.department_id,
            'number': c.number
        } for c in courses]

    friend_dicts = []
    if 'friends' in result_types:
        user = view_helpers.get_current_user()
        if user:
            friends = user.get_friends()
            friend_dicts = [{
                'label': f.name,
                'program': f.short_program_name,
                'type': 'friend',
                'id': f.id,
                'pic': f.profile_pic_urls['square'],
                'tokens': [f.first_name, f.last_name]
            } for f in friends]

    prof_dicts = []
    if 'professors' in result_types:
        professors = m.Professor.objects().only('id', 'first_name',
                'last_name', 'departments_taught')
        prof_dicts = [{
            'label': p.name,
            'departments_taught': p.departments_taught,
            'type': 'prof',
            'prof_id': p.id,
            'name': p.name,
            'tokens': [p.first_name, p.last_name, 'professor']
        } for p in professors]

    return api_util.jsonify({
        'friends': friend_dicts,
        'courses': course_dicts,
        'professors': prof_dicts
    })


###############################################################################
# Alerts


@api.route('/alerts/course/gcm', methods=['POST'])
def add_gcm_course_alert():
    """Adds an alert to notify when a seat opens up in a course/section via
    GCM.

    GCM is used to send push notifications to our Android app.

    Requires the following parameters:
        registration_id: Provided by GCM to identify the device-app pair
        course_id: ID of the course to alert on

    Optional parameters:
        created_date: Timestamp in millis
        expiry_date: Timestamp in millis. Defaults to 1 year later
        term_id: e.g. "2014_01"
        section_type: e.g. "LEC"
        section_num: e.g. "001"
        user_id: ID of the logged in user
    """
    params = flask.request.form

    created_date = datetime.datetime.now()

    expiry_date_param = params.get('expiry_date')
    if expiry_date_param:
        expiry_date = datetime.datetime.fromtimestamp(int(expiry_date_param))
    else:
        expiry_date = created_date + datetime.timedelta(days=365)

    try:
        alert_dict = {
            'registration_id': params['registration_id'],
            'course_id': params['course_id'],
            'created_date': created_date,
            'expiry_date': expiry_date,
            'term_id': params.get('term_id'),
            'section_type': params.get('section_type'),
            'section_num': params.get('section_num'),
            'user_id': params.get('user_id'),
        }
    except KeyError as e:
        raise api_util.ApiBadRequestError(
                'Missing required parameter: %s' % e.message)

    alert = m.GcmCourseAlert(**alert_dict)

    try:
        alert.save()
    except me.NotUniqueError as e:
        raise api_util.ApiBadRequestError(
                'Alert with the given parameters already exists.')

    return api_util.jsonify({
        'gcm_course_alert': alert.to_dict(),
    })


@api.route('/alerts/course/gcm/<string:alert_id>', methods=['DELETE'])
def delete_gcm_course_alert(alert_id):
    alert = m.GcmCourseAlert.objects.with_id(alert_id)

    if not alert:
        raise api_util.ApiNotFoundError(
                'No GCM course alert with id %s found.' % alert_id)

    alert.delete()

    return api_util.jsonify({
        'gcm_course_alert': alert.to_dict(),
    })


###############################################################################
# Misc.


@api.route('/programs', methods=['GET'])
def get_programs():
    """Get the counts of how many users belong to each program."""
    users = m.User.objects().only('program_name')
    programs_names = [user.short_program_name for user in users]

    program_frequencies = collections.Counter(programs_names)

    programs = []
    for program, count in program_frequencies.items():
        programs.append({
            'name': program,
            'count': count,
        })

    return api_util.jsonify({
        'programs': programs
    })

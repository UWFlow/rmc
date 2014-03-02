"""Version 1 of Flow's public, officially-supported API."""

import collections

import bson
import flask

import rmc.models as m
import rmc.server.api.api_util as api_util
import rmc.server.view_helpers as view_helpers
import rmc.shared.facebook as facebook


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
    """
    # Prevent a CSRF attack from replacing a logged-in user's account with the
    # attacker's.
    current_user = view_helpers.get_current_user()
    if current_user:
        return api_util.jsonify({'message': 'A user is already logged in.'})

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
    return api_util.jsonify({'message': 'Logged in user %s' % user.name})


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

    return api_util.jsonify({
        'schedule': schedule_item_dict_list
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

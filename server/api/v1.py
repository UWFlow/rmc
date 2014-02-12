"""Version 1 of Flow's public, officially-supported API."""

import collections

import flask

import rmc.models as m
from rmc.server.app import app
import rmc.server.api.api_util as api_util
import rmc.server.view_helpers as view_helpers
import rmc.shared.facebook as facebook


# TODO(david): Bring in other API methods from server.py to here.


###############################################################################
# /courses/:course_id routes: info about a specific course


@app.route('/api/v1/courses/<string:course_id>', methods=['GET'])
def get_course(course_id):
    course = m.Course.objects.with_id(course_id)
    if not course:
        return api_util.api_not_found('Course %s not found. :(' % course_id)

    current_user = view_helpers.get_current_user()
    course_reviews = course.get_reviews(current_user)

    # TODO(david): Implement HATEOAS (URLs of other course info endpoints).
    return api_util.jsonify(dict(course.to_dict(), **{
        'reviews': course_reviews,
    }))


@app.route('/api/v1/courses/<string:course_id>/professors', methods=['GET'])
def get_course_professors(course_id):
    course = m.Course.objects.with_id(course_id)
    if not course:
        return api_util.api_not_found('Course %s not found. :(' % course_id)

    current_user = view_helpers.get_current_user()
    professors = m.Professor.get_full_professors_for_course(
            course, current_user)

    return api_util.jsonify(professors)


@app.route('/api/v1/courses/<string:course_id>/exams', methods=['GET'])
def get_course_exams(course_id):
    exams = m.Exam.objects(course_id=course_id)
    exam_dict_list = [e.to_dict() for e in exams]

    last_updated_date = None
    if exams:
        last_updated_date = exams[0].id.generation_time

    return api_util.jsonify({
        'exams': exam_dict_list,
        'last_updated_date': last_updated_date,
    })


@app.route('/api/v1/courses/<string:course_id>/sections', methods=['GET'])
def get_course_sections(course_id):
    sections = m.section.Section.get_for_course_and_recent_terms(course_id)
    return api_util.jsonify(s.to_dict() for s in sections)


@app.route('/api/v1/courses/<string:course_id>/users', methods=['GET'])
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
              "fb_pic_url": "https://graph.facebook.com/541400376/picture",
              "num_invites": 0,
              "friend_ids": [],
              "program_name": "Software Engineering",
              "course_history": [],
              "id": {
                "$oid": "50a532518aedf423ac645891"
              }
            }
          ],
          "term_users": [
            {
              "term_id": "2013_01",
              "user_ids": [
                {
                  "$oid": "50a532518aedf423ac645891"
                }
              ],
              "term_name": "Winter 2013"
            }
          ]
        }
    """
    course = m.Course.objects.with_id(course_id)
    if not course:
        return api_util.api_not_found('Course %s not found. :(' % course_id)

    current_user = view_helpers.get_current_user()
    course_dict_list, user_course_dict_list, user_course_list = (
            m.Course.get_course_and_user_course_dicts(
                [course], current_user, include_friends=True))

    user_ids = set(ucd['user_id'] for ucd in user_course_dict_list)
    users = m.User.objects(id__in=list(user_ids)).only(
            'first_name', 'last_name', 'fbid', 'num_points', 'program_name')

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
        # TODO(david): Scrub keys of values that we're not returning, such as
        #     friend_ids or course_history
        'users': [user.to_dict() for user in users],
        'term_users': term_users,
    })


###############################################################################
# Endpoints used for authentication


@app.route('/api/v1/login/facebook', methods=['POST'])
def login_facebook():
    """Attempt to login a user with FB credentials encoded in the POST body.

    Expects the following form data:
        fbid: Facebook user ID
        fb_access_token: Facebook user access token. This is used to verify
            that the user did authenticate with Facebook and is authenticated
            to our app.

    Responds with the session cookie via the `set-cookie` header on success.
    Send up this cookie for all API requests that accept user authentication.
    """
    # FIXME(david): We must move Flow to HTTPS because clients will
    #     send users' access tokens in this route.

    req = flask.request
    fbid = req.form.get('fbid')
    fb_access_token = req.form.get('fb_access_token')

    # We perform a check to confirm the fb_access_token is indeed the person
    # identified by fbid, and that it was our app that generated the token.
    token_info = facebook.get_access_token_info(fb_access_token)

    if not token_info:
        return api_util.api_forbidden('Could not check FB access token.')

    if not token_info['is_valid'] or str(token_info['user_id']) != fbid:
        return api_util.api_forbidden('The given FB credentials are invalid.')

    user = m.User.objects(fbid=fbid).first()
    if not user:
        return api_util.api_forbidden('No user with fbid %s exists. '
                'Create an account at uwflow.com.' % fbid)

    view_helpers.login_as_user(user)
    return 'Logged in user %s' % user.name

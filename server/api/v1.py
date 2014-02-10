"""Version 1 of Flow's public, officially-supported API."""

import rmc.models as m
from rmc.server.app import app
import rmc.server.api.api_util as api_util
import rmc.server.view_helpers as view_helpers


# TODO(david): Bring in other API methods from server.py to here.


@app.route('/api/v1/courses/<string:course_id>', methods=['GET'])
def get_course(course_id):
    course = m.Course.objects.with_id(course_id)
    if not course:
        return api_util.api_not_found('Course %s not found. :(' % course_id)

    current_user = view_helpers.get_current_user()
    course_reviews = course.get_reviews(current_user)

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

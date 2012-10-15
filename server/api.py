import functools

import flask
from flask import current_app as app

from rmc.shared import util


# TODO(david): Move API handlers into this file, or make an api subdirectory


def jsonify(f):
    @functools.wraps(f)
    def jsonified(*args, **kwargs):
        ret = f(*args, **kwargs)

        if isinstance(ret, app.response_class):
            return ret

        response = util.json_dumps(ret)
        return app.response_class(response, mimetype='application/json')
    return jsonified


def not_found():
    response = util.json_dumps({
            'status': 404,
            'message': 'Not Found: %s' % flask.request.url,
    })

    # Allow the client to tell us to not return a 404 HTTP status, since
    # sometimes the client expects a 404 and don't want its error handler to be
    # called
    http_status = 200 if '404ok' in flask.request.values else 404

    return app.response_class(response, mimetype='application/json',
            status=http_status)


# TODO(david): This should be a function that returns a Flask response
class ApiError(Exception):
    """All errors during api calls should use this rather than Exception
    directly.
    """
    pass

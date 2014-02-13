"""Utility functions for the API."""

import flask

from rmc.server.app import app
import rmc.shared.util as util


class ApiError(Exception):
    status_code = 400

    def __init__(self, message):
        super(ApiError, self).__init__()
        self.message = message

    def to_dict(self):
        return {'error': self.message}


class ApiBadRequestError(ApiError):
    status_code = 400


class ApiForbiddenError(ApiError):
    status_code = 403


class ApiNotFoundError(ApiError):
    status_code = 404


@app.errorhandler(ApiError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# TODO(david): Actually, our existing JSON-serialized date format is a little
#     disgusting ({ "start_date": { "$date": 1354840200000 } }). It would be
#     nice to just be the timestamp, but would require updating all our JS so
#     that our web client can consume the v1 API. Also, our Mongo IDs are
#     disgusting too ({ "$oid": "507495f87903f30a4dedd202" }).
def jsonify(data):
    """Returns a flask.Response of data, JSON-stringified.

    This is basically Flask's jsonify
    (https://github.com/mitsuhiko/flask/blob/master/flask/json.py), but using
    our own JSON dumps method, which plugs an XSS hole and knows how to encode
    Mongo ObjectIds and datetimes.
    """
    indent = None if flask.request.is_xhr else 2

    return flask.current_app.response_class(
            util.json_dumps(data, indent=indent), mimetype='application/json')

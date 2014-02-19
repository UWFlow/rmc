"""Utility functions for the API."""

import calendar
import datetime
import json

from bson.objectid import ObjectId
import flask

from rmc.server.app import app


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


# TODO(david): Update the web app to use this encoder as well.
class ApiJsonEncoder(json.JSONEncoder):
    """A custom JSON encoder for types that Python's json doesn't know about.

    This includes datetimes and BSON object IDs.

    We don't use PyMongo's bson.json_util for our API, because it obnoxiously
    encodes types nested in an object, eg. ObjectId as
    { "$oid": "deadbeef1337" } and dates as { "$date": 1354840200000 }. Our API
    should be agnostic of the underlying datastore and clients should not have
    to deal with ugliness like { "start_date": { "$date": 1354840200000 } }.

    Note that this means that our API JSON serialization is different from the
    JSON format we send down to our web app, unfortunately.

    See for how this class works:
    http://docs.python.org/2/library/json.html#json.JSONEncoder
    """

    def default(self, obj):
        # Implementation adapted from
        # github.com/mongodb/mongo-python-driver/blob/master/bson/json_util.py
        # and docs.python.org/2/library/json.html#json.JSONEncoder.default

        # Encode a datetime as milliseconds since epoch
        if isinstance(obj, datetime.datetime):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
            millis = int(calendar.timegm(obj.timetuple()) * 1000 +
                obj.microsecond / 1000)
            return millis

        # Encode BSON ObjectId as just a string
        if isinstance(obj, ObjectId):
            return str(obj)

        # Resolve iterables (eg. generators)
        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)

        # We don't know how to encode this value type -- give up.
        return super(ApiJsonEncoder, self).default(obj)


def jsonify(data):
    """Returns a flask.Response of data, JSON-stringified.

    This is basically Flask's jsonify
    (https://github.com/mitsuhiko/flask/blob/master/flask/json.py), but plugs
    an XSS hole and knows how to encode Mongo ObjectIds and datetimes.
    """
    indent = None if flask.request.is_xhr else 2

    jsonified = json.dumps(data, indent=indent, cls=ApiJsonEncoder)
    jsonified_safe = jsonified.replace('</', '<\\/')

    return flask.current_app.response_class(jsonified_safe,
            mimetype='application/json')

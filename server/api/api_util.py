"""Utility functions for the API."""

import flask

import rmc.shared.util as util


# TODO(david): Errors should return JSON similar to success message. Refactor
#     to use http://flask.pocoo.org/docs/patterns/apierrors/


def api_bad_request(message):
    return (message, 404)


def api_forbidden(message):
    return (message, 403)


def api_not_found(message):
    return (message, 404)


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

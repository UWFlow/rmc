"""Utility functions for the API."""

import flask

import rmc.shared.util as util


def api_not_found(message):
    return (message, 404)


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

"""Initializes a Flask app so that multiple modules can register routes."""

# TODO(david): Should refactor to use Blueprints instead:
#     http://flask.pocoo.org/docs/blueprints/#blueprints

import flask


app = flask.Flask(__name__)

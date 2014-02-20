import functools
import logging
import werkzeug.exceptions as exceptions

import flask
import mongoengine as me
import redis
import urllib

import rmc.models as m
import rmc.shared.constants as c


SESSION_COOKIE_KEY_USER_ID = 'user_id'


_redis_instance = redis.StrictRedis(host=c.REDIS_HOST,
                                    port=c.REDIS_PORT,
                                    db=c.REDIS_DB)


def get_redis_instance():
    return _redis_instance


# TODO(mack): checking that path starts with '/api/' seems brittle
def is_api_request():
    return flask.request.path.find('/api/') == 0


def logout_current_user():
    flask.session.pop(SESSION_COOKIE_KEY_USER_ID, None)


def login_as_user(user):
    flask.session[SESSION_COOKIE_KEY_USER_ID] = user.id


def get_current_user():
    """Get the current user using Flask sessions.

    Also allows admins to become another user based on oid or fbid.

    Returns a User object if the user is logged in, or None otherwise.
    """
    req = flask.request

    if hasattr(req, 'current_user'):
        return req.current_user

    api_key = req.values.get('api_key')
    if api_key and is_api_request():
        req.current_user = m.User.objects(api_key=api_key).first()
        if not req.current_user:
            # TODO(mack): change exceptions to not return html, but just the
            # error text
            raise exceptions.ImATeapot('Invalid api key %s' % api_key)
    elif SESSION_COOKIE_KEY_USER_ID in flask.session:
        user_id = flask.session[SESSION_COOKIE_KEY_USER_ID]
        req.current_user = m.User.objects.with_id(user_id)
    else:
        req.current_user = None

    if req.current_user and req.current_user.is_admin:
        oid = req.values.get('as_oid', '')
        fbid = req.values.get('as_fbid', '')
        if oid:
            try:
                as_user = m.User.objects.with_id(oid)
                req.current_user = as_user
                req.as_user_override = True
            except me.base.ValidationError:
                logging.warn("Bad as_oid (%s) in get_current_user()" % oid)
        elif fbid:
            as_user = m.User.objects(fbid=fbid).first()
            if as_user is None:
                logging.warn("Bad as_fbid (%s) in get_current_user()" % fbid)
            else:
                req.current_user = as_user
                req.as_user_override = True

    return req.current_user


def login_required_func():
    current_user = get_current_user()

    user_logging = current_user.id if current_user else None
    logging.info("login_required: current_user (%s)" % user_logging)
    if not current_user:
        next_url = urllib.quote_plus(flask.request.url)
        return flask.redirect('/?next=%s' % next_url)


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        resp = login_required_func()
        if resp is not None:
            return resp

        return f(*args, **kwargs)

    return wrapper


# TODO(mack): figure out how to do properly by wrapping in @login_required
def admin_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        resp = login_required_func()
        if resp is not None:
            return resp

        current_user = get_current_user()
        logging.info("admin_required: current_user (%s)" % current_user)
        if not current_user.is_admin:
            resp = flask.make_response(flask.redirect('/'))
            return resp

        return f(*args, **kwargs)

    return wrapper


def redirect_to_profile(user):
    """
    Returns a flask.redirect() to a given user's profile.

    Basically redirect the request to the /profile endpoint with their ObjectId

    Args:
        user: The user's profile to redirects to. Should NOT be None.
    """
    if user is None:
        # This should only happen during development time...
        logging.error('redirect_to_profile(user) called with user=None')
        return flask.redirect('/profile', 302)

    if flask.request.query_string:
        return flask.redirect('/profile/%s?%s' % (
            user.id, flask.request.query_string), 302)
    else:
        return flask.redirect('/profile/%s' % user.id, 302)

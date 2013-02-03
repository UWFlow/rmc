import functools
import logging
import werkzeug.exceptions as exceptions

import flask
import redis
import urllib

import rmc.models as m
import rmc.shared.constants as c

_redis_instance = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)


def get_redis_instance():
    return _redis_instance

# TODO(mack): checking that path starts with '/api/' seems brittle
def is_api_request():
    return flask.request.path.find('/api/') == 0

def get_current_user():
    """
        Get the logged in user (if it exists) based on fbid and fb_access_token.
        Cache the user across multiple calls during the same request.
    """
    req = flask.request

    if hasattr(req, 'current_user'):
        return req.current_user

    # TODO(Sandy): Eventually support non-fb users?
    fbid = req.cookies.get('fbid')
    fb_access_token = req.cookies.get('fb_access_token')

    api_key = req.values.get('api_key')
    if api_key and is_api_request():
        req.current_user = m.User.objects(api_key=api_key).first()
        if not req.current_user:
            # TODO(mack): change exceptions to not return html, but just the
            # error text
            raise exceptions.ImATeapot('Invalid api key %s' % api_key)

    elif fbid is None or fb_access_token is None:
        req.current_user = None
    else:
        req.current_user = m.User.objects(
                fbid=fbid, fb_access_token=fb_access_token).first()

    if req.current_user and req.current_user.is_admin:
        oid = req.args.get('as_oid', '')
        fbid = req.args.get('as_fbid', '')
        if oid:
            try:
                as_user = m.User.objects.with_id(oid)
                req.current_user = as_user
                req.as_user_override = True
            except:
                logging.warn("Bad as_oid (%s) in get_current_user()" % oid)
        elif fbid:
            as_user = m.User.objects(fbid=fbid).first()
            if as_user is None:
                logging.warn("Bad as_fbid (%s) in get_current_user()" % fbid)
            else:
                req.current_user = as_user
                req.as_user_override = True

    return req.current_user

def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        current_user = get_current_user()
        logging.info("login_required: current_user (%s)" % current_user)

        if not current_user:
            next_url = urllib.quote_plus(flask.request.url)
            resp = flask.make_response(flask.redirect('/?next=%s' % next_url))
            resp.set_cookie('fbid', None)
            resp.set_cookie('fb_access_token', None)
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

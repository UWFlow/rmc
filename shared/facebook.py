from datetime import datetime
import base64
import hashlib
import hmac
import logging
import requests
import time
import urlparse

from rmc.server.app import app
import rmc.server.api.api_util as api_util
import rmc.shared.util as util

# A long token normally lasts for 60 days
FB_FORCE_TOKEN_EXPIRATION_DAYS = 57

USED_AUTH_CODE_MSG = 'This authorization code has been used.'


def code_for_token(code, config, cmd_line_debug=False):
    """Returns a dictionary containing the user's Facebook access token and
    seconds until it expires from now

    See https://developers.facebook.com/blog/post/2011/05/13/how-to--handle-expired-access-tokens/

    Right now, the resulting token is a short-lived token (~2 hours). But it's
    possible that this is wrong and that it should be a long-term token
    instead.  See https://developers.facebook.com/bugs/341793929223330/

    Args:
        code: The code we get from their fb_signed_request

    Returns {
        'access_token': 'token-here-blarg',
        'expires': 6200,
    }
    """
    # Since we're exchanging a client-side token, redirect_uri should be ''
    params = {
        'client_id': config['FB_APP_ID'],
        'redirect_uri': '',
        'client_secret': config['FB_APP_SECRET'],
        'code': code,
    }
    resp = requests.get('https://graph.facebook.com/oauth/access_token',
            params=params)

    if resp.status_code != 200:
        err = util.json_loads(resp.text)
        if (err.get('error').get('message') == USED_AUTH_CODE_MSG and
            err.get('error').get('code') == 100):
            logging.info('code_for_token failed (%d) with text:\n%s' % (
                    resp.status_code, resp.text))
        else:
            logging.warn('code_for_token failed (%d) with text:\n%s' % (
                    resp.status_code, resp.text))

    result = dict(urlparse.parse_qsl(resp.text))

    if cmd_line_debug:
        print "result dict:"
        print result
        return resp

    return result


def get_access_token_info(access_token):
    """Returns info about the given Facebook access token.

    Verifies that the access token was issued for Flow. This prevents an
    attacker from hijacking a user's Flow account by providing a valid access
    token issued for another FB app.

    For return data, see (https://developers.facebook.com/docs/facebook-login
            /manually-build-a-login-flow/#confirm)
    """
    res = requests.get('https://graph.facebook.com/debug_token'
            '?input_token=%s&access_token=%s|%s' % (
                access_token,
                app.config['FB_APP_ID'],
                app.config['FB_APP_SECRET']))

    if not res.ok or not res.json.get('data'):
        logging.error('Failed verifying FB access token. FB response: %s' %
                res.json)
        raise api_util.ApiBadRequestError('Failed verifying FB access token.')

    return res.json['data']


# TODO(Sandy): Find out how often a new token is issued
def token_for_long_token(short_token, config, cmd_line_debug=False):
    """
    Returns a dictionary containing the user's long Facebook access token and
    seconds until it expires from now

    The resulting tokens should last 60 days. Though making the same request
    within a short period of time (eg. minutes) won't result in a new token.

    Args:
        short_token: The short-lived token we're exchanging

    Returns {
        'access_token': 'token-here-blarg',
        'expires': 5184000,
    }
    """
    # Since we're exchanging a client-side token, redirect_uri should be ''
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': config['FB_APP_ID'],
        'client_secret': config['FB_APP_SECRET'],
        'fb_exchange_token': short_token,
    }
    resp = requests.get('https://graph.facebook.com/oauth/access_token',
            params=params)

    if resp.status_code != 200:
        # TODO(Sandy): See if this is too verbose
        logging.warn('token_for_long_token failed (%d) with text:\n%s' % (
                resp.status_code, resp.text))

    result = dict(urlparse.parse_qsl(resp.text))

    if cmd_line_debug:
        print "result dict:"
        print result
        return resp

    return result


def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += '=' * padding_factor
    return base64.b64decode(unicode(inp)
                            .translate(dict(zip(map(ord, u'-_'), u'+/'))))


def parse_signed_request(signed_request, secret):
    """
    Returns a dict of the the Facebook signed request object
    See https://developers.facebook.com/docs/authentication/signed_request/
    """
    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = util.json_loads(base64_url_decode(payload))

    if data.get('algorithm').upper() != 'HMAC-SHA256':
        logging.error('Unknown algorithm during signed request decode')
        return None

    expected_sig = (hmac.new(secret, msg=payload, digestmod=hashlib.sha256)
                        .digest())

    if sig != expected_sig:
        return None

    return data


# TODO(Sandy): Remove config parameter when Flask re-factoring is done
def get_fb_data(signed_request, config):
    """
    Get FB access token and expiry information from the Facebook signed request

    A long-lived token should be returned (60 days expiration), if everything
    went smoothly.

    Returns {
        'access_token': 'token-here-blarg',
        'expires_on': 5184000,
        'fbid': 123456789,
    }
    """
    # Validate against Facebook's signed request
    fbsr_data = parse_signed_request(signed_request, config['FB_APP_SECRET'])

    # TODO(Sandy): Maybe move the validation somewhere else since it can raise
    # an Exception
    if fbsr_data is None or not fbsr_data.get('user_id'):
        logging.warn('Could not parse Facebook signed request (%s)'
                % signed_request)
        raise Exception('Could not parse Facebook signed request (%s)'
                % signed_request)

    # Fetch long token from Facebook
    # TODO(Sandy): Migrate to Flask sessions so null tokens won't be a problem
    fb_access_token = None
    fb_access_token_expiry_date = None
    is_invalid = True

    code = fbsr_data.get('code')
    if code:
        result_dict = code_for_token(code, config)

        short_access_token = result_dict.get('access_token')
        if short_access_token:
            result_dict = token_for_long_token(short_access_token, config)

            long_access_token = result_dict.get('access_token')
            token_expires_in = result_dict.get('expires')
            if long_access_token and token_expires_in:
                fb_access_token = long_access_token
                fb_access_token_expiry_date = datetime.fromtimestamp(
                        int(time.time()) + int(token_expires_in) - 10)
                is_invalid = False
            else:
                logging.warn('Failed to exchange (%s) for long access token'
                        % short_access_token)
        else:
            logging.info('Failed to exchange code (%s) for token' % code)
    else:
        # Shouldn't happen, Facebook messed up
        logging.warn('No "code" field in fbsr. Blame FB')

    return {
        'access_token': fb_access_token,
        'expires_on': fb_access_token_expiry_date,
        'fbid': fbsr_data['user_id'],
        'is_invalid': is_invalid,
    }


class FacebookOAuthException(Exception):
    '''
        Invalid Facebook token (expired or just plain invalid):
        https://developers.facebook.com/blog/post/2011/05/13/how-to--handle-expired-access-tokens/
    '''
    pass


def get_friend_list(token):
    '''
    Return a list of fbids for the Facebook user associated with token
    '''
    params = {
        'access_token': token,
    }
    resp = requests.get('https://graph.facebook.com/me/friends', params=params)
    resp_dict = util.json_loads(resp.text)

    if 'error' in resp_dict:
        if resp_dict.get('error').get('type') == 'OAuthException':
            raise FacebookOAuthException()
        raise Exception(resp.text)

    fbid_list = []
    if 'data' in resp_dict:
        for entry in resp_dict['data']:
            fbid_list.append(entry['id'])
    else:
        raise Exception('"data" not in dict (%s)' % resp_dict)

    return fbid_list

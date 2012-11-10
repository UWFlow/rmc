from datetime import datetime
import base64
import hashlib
import hmac
import logging
import requests
import time
import urlparse

import rmc.shared.constants as c
import rmc.shared.util as util

def code_for_token(code, app):
    """
    Returns a dictionary containing the user's Facebook access token and seconds
    until it expires from now

    See https://developers.facebook.com/blog/post/2011/05/13/how-to--handle-expired-access-tokens/

    Right now, the resulting token is a short-lived token (~2 hours). But it's
    possible that this is wrong and that it should be a long-term token instead.
    See https://developers.facebook.com/bugs/341793929223330/

    Args:
        code: The code we get from their fb_signed_request

    Returns {
        'access_token': 'token-here-blarg',
        'expires': 6200,
    }
    """
    # Since we're exchanging a client-side token, redirect_uri should be ''
    token_url = ("https://graph.facebook.com/oauth/access_token?"
            "client_id=%s&"
            "redirect_uri=%s&"
            "client_secret=%s&"
            "code=%s"
            % (app.config['FB_APP_ID'], '', app.config['FB_APP_SECRET'], code))
    resp = requests.get(token_url)
    result = dict(urlparse.parse_qsl(resp.text))
    return result

# TODO(Sandy): Find out how often a new token is issued
def token_for_long_token(short_token, app):
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
    exchange_url = ("https://graph.facebook.com/oauth/access_token?"
            "grant_type=fb_exchange_token&"
            "client_id=%s&"
            "client_secret=%s&"
            "fb_exchange_token=%s"
            % (app.config['FB_APP_ID'], app.config['FB_APP_SECRET'], short_token))
    resp = requests.get(exchange_url)
    result = dict(urlparse.parse_qsl(resp.text))
    return result

# TODO(Sandy): Remove app parameter when Flask re-factoring is done
def get_fb_data(signed_request, app):
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
    def base64_url_decode(inp):
        padding_factor = (4 - len(inp) % 4) % 4
        inp += "="*padding_factor
        return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

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

        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

        if sig != expected_sig:
            return None

        return data

    # Validate against Facebook's signed request
    fbsr_data = parse_signed_request(signed_request, app.config['FB_APP_SECRET'])

    # TODO(Sandy): Maybe move the validation somewhere else since it can raise
    # an Exception
    if fbsr_data is None or not fbsr_data.get('user_id'):
        logging.warn("Could not parse Facebook signed request (%s)"
                % signed_request)
        raise Exception("Could not parse Facebook signed request (%s)"
                % signed_request)

    # Fetch long token from Facebook
    # TODO(Sandy): Migrate to Flask sessions so null tokens won't be a problem
    fb_access_token = c.FB_NO_ACCESS_TOKEN
    fb_access_token_expiry_date = datetime.now()
    code = fbsr_data.get('code')
    if code:
        result_dict = code_for_token(code, app)

        short_access_token = result_dict.get('access_token')
        if short_access_token:
            result_dict = token_for_long_token(short_access_token, app)

            long_access_token = result_dict.get('access_token')
            token_expires_in = result_dict.get('expires')
            if long_access_token and token_expires_in:
                fb_access_token = long_access_token
                fb_access_token_expiry_date = datetime.fromtimestamp(
                        int(time.time()) + int(token_expires_in) - 10)
            else:
                logging.warn('Failed to exchange (%s) for long access token'
                        % short_access_token)
        else:
            logging.warn('Failed to exchange code (%s) for token' % code)
    else:
        # Shouldn't happen, Facebook messed up
        logging.warn('No "code" field in fbsr. Blame FB')

    return {
        'access_token': fb_access_token,
        'expires_on': fb_access_token_expiry_date,
        'fbid': fbsr_data['user_id'],
    }

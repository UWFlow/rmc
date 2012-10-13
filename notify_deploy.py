"""Sends a message to HipChat that we just deployed.

Args:
    $1: whoami
"""

import sys

import requests

from rmc.shared import secrets


HIPCHAT_API_URL = 'https://api.hipchat.com/v1/rooms/message'


if __name__ == '__main__':
    deployer = sys.argv[1] if len(sys.argv) >= 2 else "rmc"
    msg = "%s just deployed to uwflow.com" % deployer

    payload = {
        'auth_token': secrets.HIPCHAT_TOKEN,
        'notify': 0,
        'color': 'purple',
        'from': 'Mr Monkey',
        'room_id': secrets.HIPCHAT_HACK_ROOM_ID,
        'message': msg,
        'message_format': 'text',
    }

    return requests.post(HIPCHAT_API_URL, msg, params=payload)

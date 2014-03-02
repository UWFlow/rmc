"""Sends a message to HipChat that we just deployed.

Args:
    $1: whoami
"""

import sys

import requests

from rmc.shared import secrets


HIPCHAT_API_URL = 'https://api.hipchat.com/v1/rooms/message'


def notify_hipchat(deployer, room_id):
    message = '%s just deployed to uwflow.com' % deployer

    payload = {
        'auth_token': secrets.HIPCHAT_TOKEN,
        'notify': 0,
        'color': 'purple',
        'from': 'Mr Monkey',
        'room_id': room_id,
        'message': message,
        'message_format': 'text',
    }

    try:
        r = requests.post(HIPCHAT_API_URL, message, params=payload)
        print 'Message sent to HipChat: %s\nResponse: %s' % (message, r.text)
    except Exception:
        print sys.exc_info()[1]


if __name__ == '__main__':
    deployer = sys.argv[1] if len(sys.argv) >= 2 else "rmc"

    notify_hipchat(deployer, secrets.HIPCHAT_HACK_ROOM_ID)
    notify_hipchat(deployer, secrets.HIPCHAT_PUBLIC_ROOM_ID)

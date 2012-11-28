import sys
import traceback

import boto
import mongoengine as me

import rmc.models as m
import rmc.shared.constants as c
import rmc.shared.secrets as secrets

EMAIL_SENDER = 'UW Flow <flow@uwflow.com>'

me.connect(c.MONGO_DB_RMC)

conn = boto.connect_ses(
    aws_access_key_id=secrets.AWS_KEY_ID,
    aws_secret_access_key=secrets.AWS_SECRET_KEY)

def batch_send(title_renderer, body_renderer,
        html_body_renderer=None, pre_send=None, post_send=None):

    # TODO(mack): filter out users we've already sent to here
    users = m.User.objects(
        email__exists=True,
    )

    num_sent = 0
    for user in users:
        try:
            if not (user.fbid == '1647810326'):
                continue

            if not (user.fbid == '1647810326' or user.fbid == '541400376'
                    or user.fbid == '518430508' or user.fbid == '1643490055'
                    or user.fbid == '504457208' or user.fbid == '1652790284'):
                continue

            #if pre_send:
            #    include_user = pre_send(user)
            #    if not include_user:
            #        continue

            html_body = None
            if html_body_renderer:
                html_body = html_body_renderer(user)

            conn.send_email(
                EMAIL_SENDER,
                title_renderer(user),
                body_renderer(user),
                [user.email],
                html_body=html_body,
            )

            if post_send:
                post_send(user)

            num_sent += 1
            print 'Sent email to: %s' % user.email
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print 'Could not send email to user: %s' % user.id

    print 'Sent email to %d users' % num_sent

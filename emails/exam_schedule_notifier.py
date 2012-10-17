import sys
import traceback

import boto
import mongoengine as me
#import jinja2 as jinja

import rmc.models as m
import rmc.shared.constants as c
import rmc.shared.secrets as secrets

me.connect(c.MONGO_DB_RMC)

def send_exam_schedule_email():

    conn = boto.connect_ses(
        aws_access_key_id=secrets.AWS_KEY_ID,
        aws_secret_access_key=secrets.AWS_SECRET_KEY)

    # TODO(mack): come up with name for email
    EMAIL_TITLE = 'See your exam schedule on Flow'

    # TODO(mack): should not show num_friends if it's 0
    friend_email_body = \
"""Welcome to Flow, %(first_name)s! %(num_friends)d of your friends have signed up.

Flow now lets you see your final exam schedule for this term! Check it out on your profile at:

http://uwflow.com/profile

We're working hard to bring you more awesome features! Like us on on Facebook (http://www.facebook.com/planyourflow) and follow us on Twitter (https://twitter.com/useflow) to stay updated.

Good luck flowing through your midterms!

Flow Developers"""

    no_friend_email_body = \
"""Welcome to Flow, %(first_name)s!

Flow now lets you see your final exam schedule for this term! Check it out on your profile at:

http://uwflow.com/profile

We're working hard to bring you more awesome features! Like us on on Facebook (http://www.facebook.com/planyourflow) and follow us on Twitter (https://twitter.com/useflow) to stay updated.

Good luck flowing through your midterms!

Flow Developers"""

    # TODO(mack): .only()
    # TODO(mack): Inspect why sent_exam_schedule_notifier_email=False doesn't work
    #users = m.User.objects(
    #    email__exists=True,
    #)
    users = m.User.objects(
        fbid__in=['1647810326', '541400376', '1643490055', '504457208', '518430508'],
        email__exists=True,
    )

    num_sent = 0
    for user in users:
        if user.sent_exam_schedule_notifier_email:
            continue

        try:
            if user.friend_ids:
                params = {
                    'first_name': user.first_name,
                    'num_friends': len(user.friend_ids),
                }
                conn.send_email(
                    c.EMAIL_SENDER,
                    EMAIL_TITLE,
                    friend_email_body % params,
                    [user.email],
                )
            else:
                params = {
                    'first_name': user.first_name,
                }
                conn.send_email(
                    c.EMAIL_SENDER,
                    EMAIL_TITLE,
                    no_friend_email_body % params,
                    [user.email],
                )

            user.sent_exam_schedule_notifier_email = True
            user.save()
            num_sent += 1
            print 'Sent email to: %s' % user.email
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print 'Could not send email to user: %s' % user.id

    print 'Sent email to %d users' % num_sent

if __name__ == '__main__':
    send_exam_schedule_email()

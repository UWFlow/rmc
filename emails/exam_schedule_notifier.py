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
    EMAIL_TITLE = 'Welcome to Flow'

    # TODO(mack): should not show num_friends if it's 0
    email_body = \
"""%(first_name), welcome to Flow!
%(friends_joined_line)
Flow now lets you see your final exam schedule for this term! Check it out on your profile at http://uwflow.com/profile

We’ll continue working hard to bring you more awesome features! Like us on on Facebook (http://www.facebook.com/planyourflow) and follow us on Twitter (https://twitter.com/useflow) to stay updated.

Good luck with the incoming storm of midterms!
-The Flow Team"""

    friends_joined_line = \
"""
%(num_friends)d of your friends started using Flow since last week.
"""

    # TODO(mack): .only()
    # TODO(mack): Inspect why sent_exam_schedule_notifier_email=False doesn't work
    #users = m.User.objects(
    #    email__exists=True,
    #)
    users = m.User.objects(
        fbid='1647810326',
        email__exists=True,
    )

    num_sent = 0
    for user in users:
        if user.sent_exam_schedule_notifier_email:
            continue

        try:
            params = {
                'first_name': user.first_name,
                'friends_joined_line': '',
            }
            if (user.friend_ids):
                params['friends_joined_line'] = friends_joined_line % {
                        'num_friends': len(user.friend_ids) }
            conn.send_email(
                c.EMAIL_SENDER,
                EMAIL_TITLE,
                email_body % params,
                [user.email],
            )
            user.sent_exam_schedule_notifier_email = True
            user.save()
            num_sent += 1
        except:
            print 'Could not send email to user: %s' % user.id

    print 'Sent email to %d users' % num_sent

if __name__ == '__main__':
    send_exam_schedule_email()

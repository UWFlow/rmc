import sys
import traceback

import boto
import mongoengine as me
#import jinja2 as jinja

import rmc.models as m
import rmc.shared.constants as c
import rmc.shared.secrets as secrets

me.connect(c.MONGO_DB_RMC)

# TODO(mack): refactor out common code in exam_schedule_notifier.py
def send_velocity_demo_email():

    conn = boto.connect_ses(
        aws_access_key_id=secrets.AWS_KEY_ID,
        aws_secret_access_key=secrets.AWS_SECRET_KEY)

    # TODO(mack): come up with name for email
    EMAIL_TITLE = 'Come say Hi at VeloCity Demo Day today and win a pair of Dr. Dre Headphones!'

    text_email_body = \
"""Hey %(first_name)s!

UW Flow is going to be pitching at VeloCity's Demo Day:

http://velocity.uwaterloo.ca/velocity-demo-day/finals-velocity-demo-day

today in the DC foyer from 12 - 1 pm! We'd love to meet you at our booth from 1 - 3 pm!

In a few days, we'll be starting a contest to reward you for using Flow and just being awesome.

Come by our booth today and get a head start by telling us what you think of Flow. You're the reason we're doing this, so we'd love to meet you in person and hear your feedback!

See you there!

The Flow Team
www.uwflow.com

P.S. We're working on getting some amazing prizes to give out. Stay updated by...
Liking us on Facebook: www.fb.com/planyourflow
Following us on Twitter: www.twitter.com/useflow

P.P.S. Come out for a chance to win a pair of Dr. Dre headphones! Just tweet with #UWDemoDay and @uwVeloCity (oh and @useflow wouldn't hurt either).

Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    # TODO(mack): should not show num_friends if it's 0
    html_email_body = \
"""<p>Hey %(first_name)s!</p>

<p><a href="http://uwflow.com">UW Flow</a> is going to be pitching at <a href="http://velocity.uwaterloo.ca/velocity-demo-day/finals-velocity-demo-day">VeloCity Demo Day</a> today in the <b>DC foyer from 12 - 1 pm!</b> We'd love to meet you at our <b>booth from 1 - 3 pm!</b></p>

<p>In a few days, we'll be starting a contest to reward you for using Flow and just being awesome.</p>

<p>Come by our booth today and get a head start by telling us what you think of Flow. You're the reason we're doing this, so we'd love to meet you in person and hear your feedback!</p>

<p>See you there!</p>

<p><a href="http://uwflow.com/about">The Flow Team</a></p>

<p>P.S. We're working on getting some amazing prizes to give out. Stay updated by
<a href="http://www.fb.com/planyourflow">liking us on Facebook</a> and <a href="http://www.twitter.com/useflow">following us on Twitter</a>.
</p>

<p>P.P.S. Come out for a chance to <b>win a pair of Dr. Dre headphones!</b> Just tweet with #UWDemoDay and @uwVeloCity (oh and <a href="http://twitter.com/useflow">@useflow</a> wouldn't hurt either).</p>

<p style="border-top: 1px solid #CCC; padding-top: 10px; margin-top: 50px;"><small style="color:#999">Are we annoying you? Sorry :( Feel free to <a style="color:#999" href="http://uwflow.com/unsubscribe?pasta=%(user_id)s">unsubscribe</a>.</small></p>"""

    # TODO(mack): .only()
    # TODO(mack): Inspect why sent_exam_schedule_notifier_email=False doesn't work
    #users = m.User.objects(
    #    email__exists=True,
    #)
    users = m.User.objects(
        fbid__in=['1647810326'],
        email__exists=True,
    )

    num_sent = 0
    for user in users:
        if user.sent_velocity_demo_notifier_email:
            continue

        try:
            params = {
                'first_name': user.first_name,
                'user_id': user.id,
            }
            conn.send_email(
                c.EMAIL_SENDER,
                EMAIL_TITLE,
                text_email_body % params,
                [user.email],
                html_body=html_email_body % params,
            )

            user.sent_velocity_demo_notifier_email = True
            user.save()
            num_sent += 1
            print 'Sent email to: %s' % user.email
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print 'Could not send email to user: %s' % user.id

    print 'Sent email to %d users' % num_sent

if __name__ == '__main__':
    send_velocity_demo_email()

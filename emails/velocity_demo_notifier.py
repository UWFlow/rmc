import rmc.emails.sender as sender


def title_renderer(user):
    return 'Come say Hi at VeloCity Demo Day today and win a pair of Dr. Dre Headphones!'

def body_renderer(user):
    email_body = \
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

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
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

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


# TODO(mack): generalize checking if email of this type has been set in
# pre_send() and marking as sent in post_send() into sender.batch_send()

def pre_send(user):
    return user.fbid == '1647810326'
    #return user.sent_velocity_demo_notifier_email

def post_send(user):
    user.sent_velocity_demo_notifier_email = True
    user.save()

def send_velocity_demo_email():
    sender.batch_send(
        title_renderer,
        body_renderer,
        html_body_renderer=html_body_renderer,
        pre_send=pre_send,
        post_send=post_send,
    )

if __name__ == '__main__':
    send_velocity_demo_email()

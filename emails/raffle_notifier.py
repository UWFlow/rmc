import rmc.emails.sender as sender


def title_renderer(user):
    return 'Review courses and win a Nexus 7'

def body_renderer(user):
    email_body = \
    """Hey %(first_name)s!

    We're running a contest rewarding you for using Flow! In two 2 weeks, we'll be raffling off a $50 food gift card, Kindle, and Nexus 7 depending on the total points earned by everyone. The more points everyone earns, the more prizes will be unlocked!

    Each point you earn gives you a chance to win, but you'll need at least 300 points to qualify.

    Here's how you get points:

       - Rate a course you've taken (10 points)
       - Write reviews (50 points)
       - Share your review on Facebook (50 points)
       - Invite your friends to use Flow (100 points)

    Get started: www.uwflow.com

    Enjoy your last week of class,

    The Flow Team


    P.S. We'll be posting contest updates on Twitter (http://twitter.com/useflow) and Facebook (http://facebook.com/planyourflow), so make sure to follow us to stay updated!



    Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
    """<p>Hey %(first_name)s!</p>

    <p>We're running a contest rewarding you for using Flow! In two 2 weeks, we'll be raffling off a <b>$50 food gift card</b>, <b>Kindle</b>, and <b>Nexus 7</b> depending on the total points earned by everyone. The more points everyone earns, the more prizes will be unlocked!</p>

    <p>Each point you earn gives you a chance to win, but you'll need at least 300 points to qualify.</p>

    <p>Here's how you get points:</p>
    <ul>
      <li>Rate a course you've taken (10 points)</li>
      <li>Write reviews (50 points)</li>
      <li>Share your review on Facebook (50 points)</li>
      <li>Invite your friends to use Flow (100 points)</li>
    </ul>

    Get started: <a href="http://uwflow.com">www.uwflow.com</a>

    <p>Enjoy your last week of class,</p>

    <p><a href="http://uwflow.com/about">The Flow Team</a></p>

    <br>

    <p>P.S. We'll be posting contest updates on <a href="http://twitter.com/useflow">Twitter</a> and <a href="http://facebook.com/planyourflow">Facebook</a>, so make sure to follow us to stay updated!</p>

    <p style="border-top: 1px solid #CCC; padding-top: 10px; margin-top: 50px;"><small style="color:#999">Are we annoying you? Sorry :( Feel free to <a style="color:#999" href="http://uwflow.com/unsubscribe?pasta=%(user_id)s">unsubscribe</a>.</small></p>"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


# TODO(mack): generalize checking if email of this type has been set in
# pre_send() and marking as sent in post_send() into sender.batch_send()

def pre_send(user):
    return user.sent_raffle_notifier_email

def post_send(user):
    user.sent_raffle_notifier_email = True
    user.save()

def send_raffle_email():
    sender.batch_send(
        title_renderer,
        body_renderer,
        html_body_renderer=html_body_renderer,
        pre_send=pre_send,
        post_send=post_send,
    )

if __name__ == '__main__':
    send_raffle_email()

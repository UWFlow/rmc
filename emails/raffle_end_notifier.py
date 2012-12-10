import rmc.emails.sender as sender


def title_renderer(user):
    return 'Win a Kindle or Nexus 7 - Contest ends on 12/12/12 at 12:12:12 pm'

def body_renderer(user):
    email_body = \
    """Hey %(first_name)s,

    Hope exams are going well.

    Just a reminder, you can win a $50 gift card, Kindle, or potentially a Nexus 7 by reviewing courses and profs on Flow! You'll need 300 points to qualify, and each point is another chance to win. Check your profile at www.uwflow.com/profile?points=1 to see your current points.

    There's only 2 days left until the contest ends this Wednesday, 12/12/12 at 12:12:12 pm. So take a quick study break by reviewing some courses on www.uwflow.com.

    Good luck with exams!



    Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
    """<p>Hey %(first_name)s,</p>

    <p>Hope exams are going well.</p>

    <p>Just a reminder, you can win a <b>$50 gift card</b>, <b>Kindle</b>, or potentially a <b>Nexus 7</b> by reviewing courses and profs on Flow! You'll need 300 points to qualify, and each point is another chance to win. Check your <a href="www.uwflow.com/profile?points=1">profile</a> to see your current points.</p>

    <p>There's only <b>2 days left</b> until the contest ends this <b>Wednesday, 12/12/12 at 12:12:12 pm</b>. So take a quick study break by reviewing some courses on <a href="www.uwflow.com">www.uwflow.com</a>.</p>

    <p>Good luck with exams!</p>


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
    #return not user.sent_raffle_end_notifier_email

def post_send(user):
    user.sent_raffle_end_notifier_email = True
    user.save()

def send_raffle_end_email():
    sender.batch_send(
        title_renderer,
        body_renderer,
        html_body_renderer=html_body_renderer,
        pre_send=pre_send,
        post_send=post_send,
    )

if __name__ == '__main__':
    send_raffle_end_email()

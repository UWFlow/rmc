import rmc.emails.sender as sender


def title_renderer(user):
    return 'Review some courses on Flow to win prizes!'

def body_renderer(user):
    email_body = \
    """Hey %(first_name)s!

    Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
    """<p>Hey %(first_name)s!</p>

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
    #return user.sent_raffle_notifier_email

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

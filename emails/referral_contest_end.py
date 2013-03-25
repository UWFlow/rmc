import rmc.emails.sender as sender


def title_renderer(user):
    return 'Less than 24 hours to win your box of Amazon!'

def body_renderer(user):
    email_body = \
    """Hey %(first_name)s!

    We hope you've found Flow useful so far! We've been trying to grow our community to make Flow even more useful for everyone, and we'd love it if you could help out by referring your friends. To thank you, we're giving out four $25 Amazon gift cards!

    Just get your friends to sign up at uwflow.com through this link:

    http://uwflow.com/?meow=%(user_id)s

    You'll get a chance to win for each friend who signs up. Also, for signing up through your link, your friend gets a chance to win too!

    Thanks, and good luck.

    PS. This contest ends at noon tomorrow (11:59 am) and just 18 people have participated so far!



    Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
    """<p>Hey %(first_name)s!</p>

    <p>We hope you've found Flow useful so far! We've been trying to grow our community to make Flow even more useful for everyone, and we'd love it if you could help out by referring your friends. To thank you, we're giving out four $25 Amazon gift cards!</p>

    <p>Just get your friends to sign up at uwflow.com through this link:</p>

    <p><a href="http://uwflow.com?meow=%(user_id)s">http://uwflow.com?meow=%(user_id)s</a></p>

    <p>You'll get a chance to win for each friend who signs up. Also, for signing up through your link, your friend gets a chance to win too!</p>

    <p>Thanks, and good luck.</p>

    <p>PS. This contest ends at noon tomorrow (11:59 am) and just <strong>18 people</strong> have participated so far!</p>


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
    #return not user.sent_referral_contest_end_email

def post_send(user):
    user.sent_referral_contest_end_email = True
    user.save()

def send_email():
    sender.batch_send(
        title_renderer,
        body_renderer,
        html_body_renderer=html_body_renderer,
        pre_send=pre_send,
        post_send=post_send,
    )

if __name__ == '__main__':
    send_email()

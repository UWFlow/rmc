import rmc.emails.sender as sender


def title_renderer(user):
    return 'Refer friends, win prizes!'

def body_renderer(user):
    email_body = \
    """Hey %(first_name)s!

    The end of the term is near! Don't forget that you can check your exam schedules on UW Flow.

    We're running a raffle for four $25 Amazon gift cards, and all you have to do is spread the love of using Flow! You get one entry into the raffle for each user that signs up for Flow using your referral link:

    http://uwflow.com/?meow=%(user_id)s

    We'll be drawing the winners at on Monday, March 25th, which is in 6 days!

    Follow @useflow and like us on Facebook to stay updated!



    Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
    """<p>Hey %(first_name)s!</p>

    <p>The end of the term is near! Don't forget that you can check your <a href="http://uwflow.com/profile">exam schedules on UW Flow</a>.</p>

    <p>We're running a raffle for four $25 Amazon gift cards, and all you have to do is spread the love of using Flow! You get one entry into the raffle for each user that signs up for Flow using your referral link:</p>

    <p><a href="http://uwflow.com?meow=%(user_id)s">http://uwflow.com?meow=%(user_id)s</a></p>

    <p>We'll be drawing the winners at on Monday, March 25<sup>th</sup>, which is in 6 days!</p>

    <p>Follow <a href="http://www.twitter.com/useflow">@useflow</a> and like us on <a href="http://www.fb.com/planyourflow">Facebook</a> to stay updated!</p>


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
    #return not user.sent_referral_contest_email

def post_send(user):
    user.sent_referral_contest_email = True
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

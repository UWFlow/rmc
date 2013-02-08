import rmc.emails.sender as sender


def title_renderer(user):
    return 'Don\'t forget to enroll in courses!'

def body_renderer(user):
    email_body = \
    """If you're on co-op:

        Class enrollment appointments for Spring 2013 is happening this week: February 4th - 9th
        Open class enrollment begins next week on February 11th.


    If you're on campus:

        Pre-enrollment for Fall 2013 will be in 2 weeks: February 25th - March 3rd


    As always, we invite you to use Flow to help with planning courses. Let us know how we can make this process even simpler!

    Your friends at Flow

    PS. You can now search by courses your friends have taken that you haven't.



    Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
    """
    <p>If you're on co-op:</p>
    <ul>
        <li>Class enrollment appointments for Spring 2013 is happening this week: February 4th - 9th</li>
        <li>Open class enrollment begins next week on February 11th</li>
    </ul>

    <p>If you're on campus:</p>
    <ul>
      <li>Pre-enrollment for Fall 2013 will be in 2 weeks: February 25th - March 3rd</li>
    </ul>

    <p>As always, we invite you to <a href="http://uwflow.com/profile?next=/courses">use Flow</a> to help with planning courses. Let us know how we can make this process even simpler!</p>

    <br>

    <p>Your friends at Flow</p>

    <br>

    <p>PS. You can now search by courses your friends have taken that you haven't.</p>

    <p style="border-top: 1px solid #CCC; padding-top: 10px; margin-top: 50px;"><small style="color:#999">Are we annoying you? Sorry :( Feel free to <a style="color:#999" href="http://uwflow.com/unsubscribe?pasta=%(user_id)s">unsubscribe</a>.</small></p>"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


# TODO(mack): generalize checking if email of this type has been set in
# pre_send() and marking as sent in post_send() into sender.batch_send()

def pre_send(user):
    #return user.fbid == '1647810326'
    return not user.sent_course_enrollment_feb_8_email

def post_send(user):
    user.sent_course_enrollment_feb_8_email = True
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

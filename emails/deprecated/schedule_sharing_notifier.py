import rmc.emails.sender as sender


def title_renderer(user):
    return 'Share your Winter 2013 class schedule on Flow!'

def body_renderer(user):
    email_body = \
    """Hey %(first_name)s!

    Hope you enjoyed your winter break.

    So the world didn't end, and that means school's starting again! (If you're not on co-op.)

    Wondering who's in your class? Well, we're excited to launch schedule sharing!

    Just copy-and-paste your schedule from Quest, and you'll be able to share and print your timetable. Browse your friends' schedules and see what they're taking!

    Get started: http://uwflow.com/profile?import-schedule=1

    Have a great term!



    Are we annoying you? Sorry :( Feel free to unsubscribe at http://uwflow.com/unsubscribe?pasta=%(user_id)s"""

    params = {
        'first_name': user.first_name,
        'user_id': user.id,
    }
    return email_body % params


def html_body_renderer(user):
    email_body = \
    """<p>Hey %(first_name)s!</p>

    <p>Hope you enjoyed your winter break.</p>

    <p>So the world didn't end, and that means school's starting again! (If you're not on co-op.)</p>

    <p>Wondering who's in your class? Well, we're excited to launch <b>schedule sharing</b>!</p>

    <img src="http://uwflow.com/static/img/class-schedule-screenshot-small.png">

    <p>Just copy-and-paste your schedule from Quest, and you'll be able to <b>share and print your timetable</b>. Browse your friends' schedules and see what they're taking!</p>

    <p><b>Get started:</b> <a href="http://uwflow.com/profile?import-schedule=1">http://uwflow.com/profile?import-schedule=1</a></p>

    <p>Have a great term!</p>


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
    #return not user.sent_schedule_sharing_notifier_email

def post_send(user):
    user.sent_schedule_sharing_notifier_email = True
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

import rmc.emails.sender as sender
from datetime import datetime

def description():
    return 'Email that is sent out 2 days after the user has signed up,' \
            ' prompting them to import schedule, transcript, review courses,' \
            ' etc...'

def title_renderer(user):
    return 'Welcome to Flow!!'

def html_body_renderer(user):

    welcome_email_body = \
    """<p>Hey %(first_name)s!</p>

    <p>We noticed that you recently signed up for <a href="http://uwflow.com">UW Flow</a>!</p>"""

    if not user.has_schedule:
        welcome_email_body += \
        """<p>Did you know that you can <a href="http://uwflow.com/profile?import-schedule=1">upload your class schedule</a>? This gives easy access to your course schedule for you and your friends.</p>

        <img src="http://uwflow.com/static/img/class-schedule-screenshot-small.png">"""

    if not user.has_course_history:
        welcome_email_body += \
        """<p>If you <a href="http://uwflow.com/onboarding">upload your Quest transcript</a>, you'll be able to track courses you've taken, rate and review them, and let your friends see what you've taken!</p>"""
    else:
        welcome_email_body += \
        """<p>We'd love it if you could <a href="http://uwflow.com/profile?review_modal=1">review some courses</a>. Taking just 10 minutes to share your opinion can really help out your friends and fellow UW students!</p>"""

    welcome_email_body += \
    """<br/>
    <p>Have a Flow-tastic day,</p>
    <p>The Flow team</p>"""


    return welcome_email_body % {
        'first_name': user.first_name,
    }


def pre_send(user):
    time_delta = datetime.now() - user.join_date
    # Send to users who signed up 2 or 3 days. Send for both days to handle
    # possible corner cases, since cron to sends email just once a day
    return not user.sent_welcome_email and 2 <= time_delta.days <= 3

def post_send(user):
    user.sent_welcome_email = True
    user.save()

def send_welcome_email():
    sender.batch_send(
        title_renderer,
        html_body_renderer=html_body_renderer,
        pre_send=pre_send,
        post_send=post_send,
    )

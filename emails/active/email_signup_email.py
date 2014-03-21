import sys
import traceback

import boto
import mongoengine as me

import rmc.models as m
import rmc.shared.constants as c
import rmc.shared.secrets as secrets

EMAIL_SENDER = 'UW Flow <flow@uwflow.com>'

me.connect(c.MONGO_DB_RMC)

conn = boto.connect_ses(
    aws_access_key_id=secrets.AWS_KEY_ID,
    aws_secret_access_key=secrets.AWS_SECRET_KEY)


def title_renderer():
    return 'We\'re Excited to Announce Email Signup!'


def html_body_renderer():

    email_body = \
    """<p>Hey there,</p>

    <p>A while back, you expressed interest in using email to sign up for <a href="https://uwflow.com">Flow</a>. We've received a lot of interest from users like you, and we've finally added email sign-up!

    <p>By signing up, you will be able to:</p>
    <ul>
        <li>Export your class and exam schedule from Quest to Google Calendar, iCal, or Outlook</li>
        <li>Track courses you've taken</li>
        <li>Shortlist courses you want to take</li>
        <li>Rate and review courses and professors</li>
    </ul>

    <p>So, why not try it out? Visit <a href="https://uwflow.com">Flow</a> and click the "sign up with email" link to sign up now!</p>

    <img src="https://uwflow.com/static/img/email_signup.png" width="450px">

    <p>- The Flow Team</p>
    <br>
    <p>P.S. We're presenting at the SE design symposium today in the Davis Centre until 5 pm. Come swing by if you have time!</p>"""

    return email_body


def get_interested_emails():
    with file('/home/rmc/email_sign_ups.txt') as f:
        emails = set()
        for email in f:
            email = email.strip()
            if email in emails:
                continue
            if not m.User.objects(email=email):
                continue
            emails.add(email)
    return list(emails)


def send_email():
    interested_emails = get_interested_emails()
    print 'Will send to %d users:' % len(interested_emails)
    num_emails_to_print = 20
    for email in interested_emails[:num_emails_to_print]:
        print email
    remaining_emails = max(0, len(interested_emails) - num_emails_to_print)
    if remaining_emails > 0:
        print '  ...'
        print '  %d other users' % remaining_emails
    choice_str = raw_input('Are you sure you want to send [y/n]: ')
    if choice_str != 'y':
        print 'Aborting send'
        return

    for email in interested_emails:
        try:
            conn.send_email(
                EMAIL_SENDER,
                title_renderer(),
                '',  # text_body
                [email],
                html_body=html_body_renderer(),
            )
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print 'Could not send email to %s' % email


if __name__ == '__main__':
    send_email()

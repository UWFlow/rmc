import sys
import traceback

import boto
import mongoengine as me

import rmc.models as m
import rmc.shared.constants as c
import rmc.shared.secrets as secrets

# TODO(mack): A/B test with sender being actual person
EMAIL_SENDER = 'UW Flow <flow@uwflow.com>'

me.connect(c.MONGO_DB_RMC)

conn = boto.connect_ses(
    aws_access_key_id=secrets.AWS_KEY_ID,
    aws_secret_access_key=secrets.AWS_SECRET_KEY)


def get_to_send_users(pre_send=None):
    # TODO(mack): filter out users we've already sent to here
    users = m.User.objects(
        email__exists=True,
    )

    to_send_users = []
    for user in users:
        if user.email_unsubscribed:
            continue

        if pre_send:
            include_user = pre_send(user)
            if not include_user:
                continue

        to_send_users.append(user)

    return to_send_users


# TODO(mack): Attach email id to links in email so we can track click through
# rate from emails
def batch_send(to_send_users, title_renderer, body_renderer=None,
        html_body_renderer=None, pre_send=None, post_send=None):

    assert body_renderer or html_body_renderer, \
            'Cannot render email because no renderer provided. Aborting.'

    num_sent = 0
    for user in to_send_users:
        try:
            html_body = None
            if html_body_renderer:
                html_body = html_body_renderer(user)
                html_body += \
                """<p style="border-top: 1px solid #CCC; padding-top: 10px; margin-top: 50px;"><small style="color:#999">Are we annoying you? Sorry :( Feel free to <a style="color:#999" href="https://uwflow.com/unsubscribe?pasta=%(user_id)s">unsubscribe</a>.</small></p>""" % { 'user_id': user.id }

            text_body = ''
            if body_renderer:
                text_body = body_renderer(user)
                text_body += \
                """\n\n\nAre we annoying you? Sorry :( Feel free to unsubscribe at https://uwflow.com/unsubscribe?pasta=%(user_id)s""" % { 'user_id': user.id }

            conn.send_email(
                EMAIL_SENDER,
                title_renderer(user),
                text_body,
                [user.email],
                html_body=html_body,
            )

            if post_send:
                post_send(user)

            num_sent += 1
            print 'Sent email to: %s' % user.email
        except Exception:
            traceback.print_exc(file=sys.stdout)
            print 'Could not send email to user: %s' % user.id

    print 'Sent email to %d users' % num_sent

def main():
    import argparse
    import rmc.emails.active.welcome_email as welcome_email
    email_id_to_module = {
        'welcome': welcome_email,
    }

    description = 'Send the specific email.\n\nSupported email ids:'
    for email_id, email_module in email_id_to_module.items():
        description += '\n\'%s\': %s' % (email_id, email_module.description())

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('email_id', metavar='EMAIL_ID', type=str,
            help='id of the email to send')
    parser.add_argument('-f', '--force', dest='force', action='store_true',
            help='send the email without confirmations')
    args = parser.parse_args()

    email_module = email_id_to_module[args.email_id]

    to_send_users = get_to_send_users(
        pre_send=getattr(email_module, 'pre_send'),
    )

    if not args.force:
        print 'Will send to %d users:' % len(to_send_users)
        num_names_to_print = 20
        for user in to_send_users[:num_names_to_print]:
            print '  %s %s: %s' % (user.first_name, user.last_name, user.email)
        remaining_users = max(0, len(to_send_users) - num_names_to_print)
        if remaining_users > 0:
            print '  ...'
            print '  %d other users' % remaining_users
        choice_str = raw_input('Are you sure you want to send [y/n]: ')
        if choice_str != 'y':
            print 'Aborting send'
            return

    batch_send(
        to_send_users,
        email_module.title_renderer,
        body_renderer=getattr(email_module, 'body_renderer', None),
        html_body_renderer=getattr(email_module, 'html_body_renderer', None),
        pre_send=getattr(email_module, 'pre_send', None),
        post_send=getattr(email_module, 'post_send', None),
    )


if __name__ == '__main__':
    main()

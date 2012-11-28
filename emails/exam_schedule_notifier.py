import rmc.emails.sender as sender


def title_renderer(user):
    return 'See your exam schedule on Flow'

def body_renderer(user):
    # TODO(mack): should not show num_friends if it's 0
    friend_email_body = \
    """Welcome to Flow, %(first_name)s! %(num_friends)d of your friends have signed up.

    Flow now lets you see your final exam schedule for this term! Check it out on your profile at:

    http://uwflow.com/profile

    We're working hard to bring you more awesome features! Like us on on Facebook (http://www.facebook.com/planyourflow) and follow us on Twitter (https://twitter.com/useflow) to stay updated.

    Good luck flowing through your midterms!

    Flow Developers"""

    no_friend_email_body = \
    """Welcome to Flow, %(first_name)s!

    Flow now lets you see your final exam schedule for this term! Check it out on your profile at:

    http://uwflow.com/profile

    We're working hard to bring you more awesome features! Like us on on Facebook (http://www.facebook.com/planyourflow) and follow us on Twitter (https://twitter.com/useflow) to stay updated.

    Good luck flowing through your midterms!

    Flow Developers"""

    if user.friend_ids:
        params = {
            'first_name': user.first_name,
            'num_friends': len(user.friend_ids),
        }
        return friend_email_body % params
    else:
        params = {
            'first_name': user.first_name,
        }
        return no_friend_email_body % params

def pre_send(user):
    return not user.sent_exam_schedule_notifier_email

def post_send(user):
    user.sent_exam_schedule_notifier_email = True
    user.save()

def send_exam_schedule_email():
    sender.batch_send(
        title_renderer,
        body_renderer,
        pre_send=pre_send,
        post_send=post_send,
    )

if __name__ == '__main__':
    send_exam_schedule_email()

import boto

import datetime
import json

import mongoengine as me
import requests

import course
import rmc.shared.secrets as s
import section
import user

from rmc.shared import util

class BaseCourseAlert(me.Document):
    """An abstract base class for notifying when a seat opens in a course.

    Subclasses must define the behaviour for sending the alert to the desired
    audience. See GcmCourseAlert for an example subclass.

    Can optionally specify a single section of a course.
    """

    BASE_INDEXES = [
        'course_id',
        ('course_id', 'term_id', 'section_type', 'section_num'),
    ]

    # These set of fields form a partial key; together with an audience
    # identifier from the subclass, forms a complete key.
    BASE_UNIQUE_FIELDS = ['course_id', 'term_id', 'section_type',
            'section_num']

    meta = {
        'indexes': BASE_INDEXES,
        'abstract': True,
    }

    # eg. earth121l
    course_id = me.StringField(required=True)

    # eg. datetime.datetime(2013, 1, 7, 22, 30)
    created_date = me.DateTimeField(required=True)

    # eg. datetime.datetime(2013, 1, 7, 22, 30)
    expiry_date = me.DateTimeField(required=True)

    # Optional fields to specify section to alert on

    # eg. 2013_09. Note that this is our term ID, not Quest's 4-digit ID.
    term_id = me.StringField(default='')

    # eg. LEC, TUT, EXAM. Note uppercase.
    section_type = me.StringField(default='')

    # eg. 001
    section_num = me.StringField(default='')

    TO_DICT_FIELDS = ['id', 'course_id', 'created_date', 'expiry_date',
            'term_id', 'section_type', 'section_num']

    def to_dict(self):
        return util.to_dict(self, self.TO_DICT_FIELDS)

    def send_alert(self, sections):
        """Sends an alert about a seat opening.

        Args:
            sections: Sections that have spots available.

        Returns whether this alert was successfully sent.
        """
        raise Exception('Sublasses must implement this method.')

    @classmethod
    def send_eligible_alerts(cls):
        """Checks if any alerts can be sent, and if so, sends them.

        Deletes alerts that were successfully sent.

        Returns how many alerts were successfully sent.
        """
        alerts_sent = 0

        for alert in cls.objects():
            query = {'course_id': alert.course_id}

            if alert.term_id:
                query['term_id'] = alert.term_id

            if alert.section_type:
                query['section_type'] = alert.section_type

            if alert.section_num:
                query['section_num'] = alert.section_num

            sections = section.Section.objects(**query)
            open_sections = filter(
                    lambda s: s.enrollment_capacity > s.enrollment_total,
                    sections)

            # TODO(david): Also log to Mixpanel or something.
            if open_sections and alert.send_alert(open_sections):
                alert.delete()
                alerts_sent += 1

        return alerts_sent

    @classmethod
    def delete_expired(cls):
        cls.objects(expiry_date__lt=datetime.datetime.now()).delete()

class GcmCourseAlert(BaseCourseAlert):
    """Course alert using Google Cloud Messaging (GCM) push notifications.

    GCM is Android's main push notification mechanism.
    """

    meta = {
        'indexes': BaseCourseAlert.BASE_INDEXES + [
            'registration_id',
        ]
    }

    # An ID issued by GCM that uniquely identifies a device-app pair.
    registration_id = me.StringField(required=True,
            unique_with=BaseCourseAlert.BASE_UNIQUE_FIELDS)

    # Optional user ID associated with this alert.
    user_id = me.ObjectIdField()

    TO_DICT_FIELDS = BaseCourseAlert.TO_DICT_FIELDS + [
            'registration_id', 'user_id']

    def __repr__(self):
        return "<GcmCourseAlert: %s, %s, %s %s>" % (
            self.course_id,
            self.term_id,
            self.section_type,
            self.section_num,
        )

    def send_alert(self, sections):
        """Sends a push notification using GCM's HTTP method.

        See http://developer.android.com/google/gcm/server.html and
        http://developer.android.com/google/gcm/http.html.

        Overrides base class method.
        """
        course_obj = course.Course.objects.with_id(self.course_id)

        # GCM has a limit on payload data size, so be conservative with the
        # amount of data we're serializing.
        data = {
            'registration_ids': [self.registration_id],
            'data': {
                'type': 'course_alert',
                'sections_open_count': len(sections),
                'course': course_obj.to_dict(),
            },
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'key=%s' % s.GOOGLE_SERVER_PROJECT_API_KEY,
        }

        res = requests.post('https://android.googleapis.com/gcm/send',
                data=json.dumps(data), headers=headers)

        # TODO(david): Implement exponential backoff for retries
        return res.ok

class EmailCourseAlert(BaseCourseAlert):
    """Course alert using email notifications."""

    user_id = me.ObjectIdField(
        unique_with=BaseCourseAlert.BASE_UNIQUE_FIELDS)

    def __repr__(self):
        return "<EmailCourseAlert: %s, %s, %s %s>" % (
            self.course_id,
            self.term_id,
            self.section_type,
            self.section_num,
        )

    def send_alert(self, sections):

        _conn = boto.connect_ses(
            aws_access_key_id=s.AWS_KEY_ID,
            aws_secret_access_key=s.AWS_SECRET_KEY)

        email_body = \
        """<p>Hey %(first_name)s!</p>

        <p>It looks like you're waiting for %(course_name)s %(section_name)s to
        open up. Good news, because a seat is available right now! Go check it
        out on Quest!</p>
        <br/>
        <p>Have a Flow-tastic day,</p>
        <p>The Flow team</p>"""

        _conn.send_email(
            'UW Flow <flow@uwflow.com>',
            '%s open spot notification' % (self.course_id.capitalize()),
            email_body % {
                'first_name': user.User.objects(id=self.user_id),
                'course_name': self.course_id.capitalize(),
                'section_name': self.section_type + ' ' + self.section_num
            },
            user.User.objects.get(id=self.user_id).email
        )
        return True

import datetime
import json

import mongoengine as me
import requests

import course
import rmc.shared.secrets as s
import section


class BaseCourseAlert(me.Document):
    """An abstract base class for notifying when a seat opens in a course.

    Subclasses must define the behaviour for sending the alert to the desired
    audience.

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

    def send_alert(self, sections):
        """Sends an alert about a seat opening.

        Args:
            sections: Sections that have spots available.

        Returns whether this alert was successfully sent.
        """
        raise Exception('Sublasses must implement this method.')

    @classmethod
    def try_send_alerts(cls):
        """Checks if any alerts can be sent, and if so, sends them.

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

            if open_sections and alert.send_alert(open_sections):
                alert.delete()
                alerts_sent += 1

        return alerts_sent

    @classmethod
    def delete_expired(cls):
        cls.objects(expiry_date__gt=datetime.datetime.now()).delete()


class GcmCourseAlert(BaseCourseAlert):
    """Course alert using Google Cloud Messaging (GCM) push notifications.

    GCM is Android's main push notification mechanism.
    """

    meta = {
        'indexes': BaseCourseAlert.BASE_INDEXES + [
            'registration_id',
        ]
    }

    # A GCM-issued ID that uniquely identifies a device-app pair.
    registration_id = me.StringField(required=True,
            unique_with=BaseCourseAlert.BASE_UNIQUE_FIELDS)

    # Optional user ID associated with this device.
    user_id = me.ObjectIdField()

    def __repr__(self):
        return "<GcmCourseAlert: %s, %s, %s %s>" % (
            self.course_id,
            self.term_id,
            self.section_type,
            self.section_num,
        )

    # Override
    def send_alert(self, sections):
        course_obj = course.Course.objects.with_id(self.course_id)

        data = {
            'registration_ids': [self.registration_id],
            'data': {
                'type': 'course_alert',
                'course_id': self.course_id,
                'sections_available': len(sections),
                'course': course_obj.to_dict(),
            },
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'key=%s' % s.GOOGLE_SERVER_PROJECT_API_KEY,
        }

        # See http://developer.android.com/google/gcm/http.html
        res = requests.post('https://android.googleapis.com/gcm/send',
                data=json.dumps(data), headers=headers)

        # TODO(david): Implement exponential backoff retries
        return res.ok

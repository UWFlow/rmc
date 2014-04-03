import datetime

import mongoengine as me

import section


class BaseCourseAlert(me.Document):
    """An abstract base class for notifying when a seat opens in a course.

    Subclasses must define the behaviour for sending the alert to the desired
    audience.

    Can optionally specify a single section of a course.
    """

    meta = {
        'indexes': [
            'course_id',
            ('course_id', 'term_id', 'section_type', 'section_num'),
        ],
        'abstract': True,
    }

    # eg. earth121l
    course_id = me.StringField(required=True,
            unique_with=['term_id', 'section_type', 'section_num'])

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

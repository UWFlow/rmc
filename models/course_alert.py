import mongoengine as me

from rmc.shared import util


class CourseAlert(me.Document):
    """A request to be notified for when a seat opens in a course.

    Can optionally specify a specific section of a course.
    """

    meta = {
        'indexes': [
            'course_id',
            'user_id',
            ('course_id', 'term_id', 'section_type', 'section_num'),
        ],
    }

    # The user to send this alert to
    user_id = me.ObjectIdField(required=True,
            unique_with=['course_id', 'term_id', 'section_type',
                'section_num'])

    # eg. earth121l
    course_id = me.StringField(required=True)

    # eg. datetime.datetime(2013, 1, 7, 22, 30)
    created_date = me.DateTimeField(required=True)

    # eg. datetime.datetime(2013, 1, 7, 22, 30)
    expiry_date = me.DateTimeField(required=True)

    # Optional fields to specify section to alert on

    # eg. 2013_09. Note that this is our term ID, not Quest's 4-digit ID.
    term_id = me.StringField()

    # eg. LEC, TUT, EXAM. Note uppercase.
    section_type = me.StringField()

    # eg. 001
    section_num = me.StringField()

    TO_DICT_FIELDS = ['id', 'user_id', 'course_id', 'created_date',
            'expiry_date', 'term_id', 'section_type', 'section_num']

    def to_dict(self):
        return util.to_dict(self, CourseAlert.TO_DICT_FIELDS)

    def __repr__(self):
        return '<CourseAlert: %s, %s, %s, %s %s>' % (
            self.user_id,
            self.course_id,
            self.term_id,
            self.section_type,
            self.section_num,
        )

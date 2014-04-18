import mongoengine as me

from rmc.shared import util


class UserScheduleItem(me.Document):
    meta = {
        'indexes': [
            # TODO(Sandy): Stole Mack's TODO from UserCourse
            # TODO(mack): this index on user_id is probably not necessary
            # since it duplicates the unique_with on user_id
            'user_id',
            'start_date',
            'end_date',
        ],
    }

    # The user with this schedule item in their schedule
    user_id = me.ObjectIdField(unique_with=['course_id', 'term_id',
                                            'section_type', 'section_num',
                                            'start_date'])

    # eg. 3359
    class_num = me.StringField()

    # eg. MC
    building = me.StringField()

    # eg. 4020
    room = me.StringField()

    # eg. LEC, TUT, EXAM
    section_type = me.StringField(required=True)

    # eg. 001
    section_num = me.StringField(required=True)

    # eg. datetime.datetime(2013, 1, 7, 22, 30)
    start_date = me.DateTimeField(required=True)

    # eg. datetime.datetime(2013, 1, 7, 23, 50)
    end_date = me.DateTimeField()

    # eg. earth121l
    course_id = me.StringField(required=True)

    # eg. byron_weber_becker
    prof_id = me.StringField()

    # eg. 2012_09
    term_id = me.StringField(required=True)

    def to_dict(self):
        return {
            'id': self.id,
            'class_num': self.class_num,
            'building': self.building,
            'room': self.room,
            'section_type': self.section_type,
            'section_num': self.section_num,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'course_id': self.course_id,
            'prof_id': self.prof_id,
            'term_id': self.term_id,
        }

    def __repr__(self):
        return "<UserScheduleItem: %s, %s, %s, %s %s, %s-%s>" % (
            self.user_id,
            self.course_id,
            self.term_id,
            self.section_type,
            self.section_num,
            self.start_date,
            self.end_date,
        )


class FailedScheduleItem(me.Document):
    meta = {
        'indexes': [
            'user_id',
            'parsed_date',
        ],
    }

    user_id = me.ObjectIdField(unique_with=['course_id', 'parsed_date'])
    course_id = me.StringField(required=True)
    parsed_date = me.DateTimeField(required=True)

    TO_DICT_FIELDS = ['id', 'user_id', 'course_id', 'parsed_date']

    def to_dict(self):
        return util.to_dict(self, FailedScheduleItem.TO_DICT_FIELDS)

    def __repr__(self):
        return "<FailedScheduleItem: %s, %s, %s, %s %s, %s-%s>" % (
            self.user_id, self.course_id, self.parsed_date)

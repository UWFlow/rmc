import mongoengine as me

class UserScheduleItem(me.Document):

    meta = {
        'indexes': [
            # TODO(Sandy): Stole Mack's TODO from UserCourse
            # TODO(mack): this index on user_id is probably not necessary
            # since it duplicates the unique_with on user_id
            'user_id',
        ],
    }

    # The user with this schedule item in their schedule
    user_id = me.ObjectIdField(unique_with=['class_num'])

    # eg. 3359
    class_num = me.StringField(required=True)

    # eg. MC
    building = me.StringField()

    # eg. 4020
    room = me.StringField()

    # eg. LEC 001
    section = me.StringField(required=True)

    # eg. 14:30
    start_time = me.StringField()

    # eg. 15:20
    end_time = me.StringField()

    # eg. earth121l
    course_id = me.StringField(required=True)

    # eg. byron_weber_becker
    prof_id = me.StringField()

    # eg. 2012_09
    term_id = me.StringField(required=True)

    # eg. ['T', 'Th']
    days = me.ListField(me.StringField())

    def to_dict(self):
        return {
            'id': self.id,
            'class_num': self.class_num,
            'building': self.building,
            'room': self.room,
            'section': self.section,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'course_id': self.course_id,
            'prof_id': self.prof_id,
            'term_id': self.term_id,
            'days': self.days
        }

    def __repr__(self):
        return "<UserScheduleItem: %s, %s, %s, %s-%s, %s>" % (
            self.user_id,
            self.course_id,
            self.term_id,
            self.start_time,
            self.end_time,
            ''.join(self.days)
        )

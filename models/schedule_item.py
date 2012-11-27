import mongoengine as me

class ScheduleItem(me.Document):

    # eg. 3359 - taken from opendata
    id = me.StringField(primary_key=True)

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

    def __repr__(self):
        return "<ScheduleItem: %s, %s, %s-%s, %s>" % (
            self.course_id,
            self.term_id,
            self.start_time,
            self.end_time,
            ''.join(self.days)
        )

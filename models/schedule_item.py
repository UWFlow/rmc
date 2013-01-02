import re

import mongoengine as me

class ScheduleItem(me.Document):

    # FIXME(Sandy): Find out if this changes every term, impacts term changes
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

    @staticmethod
    def days_str_to_list(date_str):
        return re.findall(r'[A-Z][a-z]?', date_str)

    @staticmethod
    def time_from_ampm_time(time_str):
        '''
        Transforms 11:00AM -> 11:00, 3:00PM -> 15:00
        '''
        # FIXME(Sandy): Do something here
        return time_str

    def to_dict(self):
        return {
            'id': self.id,
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
        return "<ScheduleItem: %s, %s, %s-%s, %s>" % (
            self.course_id,
            self.term_id,
            self.start_time,
            self.end_time,
            ''.join(self.days)
        )

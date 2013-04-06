import mongoengine as me

from rmc.shared import util
import user_schedule_item as _user_schedule_item

class Exam(me.Document):
    meta = {
        'indexes': [
            'course_id',
        ],
    }

    course_id = me.StringField(required=True)

    # A string listing the sections. E.g. '001', '001, 003', '002 to 004'
    # Is not guaranteed to exist
    sections = me.StringField()

    start_date = me.DateTimeField()
    end_date = me.DateTimeField()

    # E.g. 'RCH 301', 'DC 1350,1351,MC 1056', "See Prof", 'WLU' and more
    location = me.StringField()

    # Whether or not we have info on the course. Set during parse time. Right
    # now this applies to WLU courses that we don't have info on and that one
    # MSCI course...
    info_known = me.BooleanField()

    # Instead of having start_date and end_date, we can have url instead
    # So far this only applies to WLU courses on the UW schedule. Same URL
    url = me.StringField()

    @property
    def location_known(self):
        return (self.location != 'See prof' and self.location != 'Check Quest')

    def to_schedule_obj(self, term_id=None):
        """Converts to a UserScheduleItem."""
        return _user_schedule_item.UserScheduleItem(
            id=self.id,
            class_num='',
            building=self.location,
            room='',
            section_type='EXAM',  # TODO(david): Make this a constant
            section_num=self.sections,
            start_date=self.start_date,
            end_date=self.end_date,
            course_id=self.course_id,
            term_id=term_id or util.get_current_term_id(),
        )

    def to_dict(self):
        return {
            'course_id': self.course_id,
            'sections': self.sections,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'location': self.location,
            'location_known': self.location_known,
            'info_known': self.info_known,
            'url': self.url,
        }

import mongoengine as me

# TODO(sandy): rename
class ExamSlot(me.Document):
    course_id = me.StringField(required=True)
    # A string listing the sections. E.g. '001', '001, 003', '002 to 004'
    # Is not guaranteed to exist
    section = me.StringField()
    start_date = me.DateTimeField()
    end_date = me.DateTimeField()
# E.g. 'RCH 301', 'DC 1350,1351,MC 1056', "See Prof", 'WLU' and more
    location = me.StringField()
    @property
    def is_location_see_prof():
        return location == 'See prof'

    # Instead of having start_date and end_date, we can have url instead
    # So far this only applies to WLU courses on the UW schedule. Same URL
    url = me.StringField()

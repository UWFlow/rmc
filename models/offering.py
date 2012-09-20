import mongoengine as me

class CourseOffering(me.Document):
    # id = me.ObjectIdField(primary_key=True)

    course_id = me.StringField(required=True, unique_with=['term_id', 'section_id'])
    term_id = me.StringField(required=True)

    # TODO(mack): maybe should be list with LEC, TUT, LAB options?
    # eg. LEC001 or just 001?
    section_id = me.IntField(required=True)

    # eg. mc2045, distance_ed
    location_id = me.StringField()

    # TODO(mack): should be some kind of list of (day_of_week, time)?
    # class_times = me.ListField(me.DateTimeField(), required=True)


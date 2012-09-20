from mongoengine import Document
import _field as f

class CourseOffering(Document):
    # id = f.ObjectIdField(primary_key=True)

    course_id = f.StringField(required=True, unique_with=['term_id', 'section_id'])
    term_id = f.StringField(required=True)

    # TODO(mack): maybe should be list with LEC, TUT, LAB options?
    # eg. LEC001 or just 001?
    section_id = f.IntField(required=True)

    # eg. mc2045, distance_ed
    location_id = f.StringField()

    # TODO(mack): should be some kind of list of (day_of_week, time)?
    # class_times = f.ListField(f.DateTimeField(), required=True)


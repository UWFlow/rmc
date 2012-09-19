from mongoengine import Document
from mongoengine import StringField, URLField

class Department(Document):

    # e.g. earth
    id = StringField(primary_key=True)

    # Earth Sciences
    name = StringField(required=True)

    # e.g. sci
    faculty_id = StringField(required=True)

    # e.g. http://ugradcalendar.uwaterloo.ca/courses/EARTH
    url = URLField(required=True)

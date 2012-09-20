from mongoengine import Document
import _field as f

class Department(Document):

    # eg. earth
    id = f.StringField(primary_key=True)

    # eg. Earth Sciences
    name = f.StringField(required=True)

    # eg. sci
    faculty_id = f.StringField(required=True)

    # eg. http://ugradcalendar.uwaterloo.ca/courses/EARTH
    url = f.URLField(required=True)

import mongoengine as me

class Department(me.Document):

    # eg. earth
    id = me.StringField(primary_key=True)

    # eg. Earth Sciences
    name = me.StringField(required=True)

    # eg. sci
    faculty_id = me.StringField(required=True)

    # eg. http://ugradcalendar.uwaterloo.ca/courses/EARTH
    url = me.URLField(required=True)

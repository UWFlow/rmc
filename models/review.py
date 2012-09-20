import mongoengine as me

class CourseReview(me.EmbeddedDocument):
    clarity = me.FloatField(min_value=0.0, max_value=1.0)
    easiness = me.FloatField(min_value=0.0, max_value=1.0)
    comment = me.StringField(max_length=4096)
    comment_time = me.DateTimeField()

class ProfessorReview(me.EmbeddedDocument):
    clarity = me.FloatField(min_value=0.0, max_value=1.0)
    passion = me.FloatField(min_value=0.0, max_value=1.0)
    comment = me.StringField(max_length=4096)
    comment_time = me.DateTimeField()

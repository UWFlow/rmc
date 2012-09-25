import mongoengine as me

from rmc.models.rating import AggregateRating

class CourseReview(me.EmbeddedDocument):
    interest = me.FloatField(min_value=0.0, max_value=1.0)
    easiness = me.FloatField(min_value=0.0, max_value=1.0)
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()

    def get_ratings(self):
        return {
            # FIXME(david): Uncomment. This is just for prof review display
            #'interest': AggregateRating.from_single_rating(self.interest),
            'easiness': AggregateRating.from_single_rating(self.easiness),
        }

class ProfessorReview(me.EmbeddedDocument):
    clarity = me.FloatField(min_value=0.0, max_value=1.0)
    passion = me.FloatField(min_value=0.0, max_value=1.0)
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()

    def get_ratings(self):
        return {
            'clarity': AggregateRating.from_single_rating(self.clarity),
            # FIXME(david): Uncomment. Don't have any passion data yet...
            #'passion': AggregateRating.from_single_rating(self.passion),
        }

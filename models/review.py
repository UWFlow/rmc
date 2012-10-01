import mongoengine as me


def update_kwargs_from_ratings(kwargs):
    if 'ratings' in kwargs:
        kwargs.update({ d['name']: d['rating'] for d in kwargs['ratings'] })
        del kwargs['ratings']


class CourseReview(me.EmbeddedDocument):
    interest = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    easiness = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()

    def __init__(self, **kwargs):
        update_kwargs_from_ratings(kwargs)
        super(CourseReview, self).__init__(**kwargs)

    # TODO(david): This should be renamed to get_ratings() and return a dict
    def to_array(self):
        return [{
            'name': 'interest',
            'rating': self.interest,
        }, {
            'name': 'easiness',
            'rating': self.easiness,
        }]


class ProfessorReview(me.EmbeddedDocument):
    clarity = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    passion = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()

    def __init__(self, **kwargs):
        update_kwargs_from_ratings(kwargs)
        super(ProfessorReview, self).__init__(**kwargs)

    def to_array(self):
        return [{
            'name': 'clarity',
            'rating': self.clarity,
        }, {
            'name': 'passion',
            'rating': self.passion,
        }]

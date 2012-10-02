import mongoengine as me
import logging

import rmc.shared.constants as c

def update_kwargs_from_ratings(kwargs):
    if 'ratings' in kwargs:
        kwargs.update({ d['name']: d['rating'] for d in kwargs['ratings'] })
        del kwargs['ratings']

def update_comment_and_date(review_obj, comment, date):
    if comment is not None and comment != review_obj.comment:
        review_obj.comment = comment
        review_obj.comment_date = date

class CourseReview(me.EmbeddedDocument):
    interest = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    easiness = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    usefulness = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()

    def __init__(self, **kwargs):
        update_kwargs_from_ratings(kwargs)
        super(CourseReview, self).__init__(**kwargs)

    # TODO(david): This should be renamed to get_ratings() and return a dict
    def to_array(self):
        return [{
            'name': c.COURSE_REVIEW_FIELD_USEFULNESS,
            'rating': self.usefulness,
        }, {
            'name': c.COURSE_REVIEW_FIELD_EASINESS,
            'rating': self.easiness,
        }, {
            'name': c.COURSE_REVIEW_FIELD_INTEREST,
            'rating': self.interest,
        }]

    def update_ratings_with_dict(self, **kwargs):
        if 'ratings' in kwargs:
            new_values = { d['name']: d['rating'] for d in kwargs['ratings'] }

            self.easiness = new_values.get(c.COURSE_REVIEW_FIELD_EASINESS)
            self.interest = new_values.get(c.COURSE_REVIEW_FIELD_INTEREST)
            self.usefulness = new_values.get(c.COURSE_REVIEW_FIELD_USEFULNESS)
        else:
            logging.warn("Trying to update CourseReview rating with empty dict")

    # TODO(Sandy): Remove duplicate code with ProfessorReview?
    def update_review_with_date_and_dict(self, date, **kwargs):
        self.update_ratings_with_dict(**kwargs)
        update_comment_and_date(self, kwargs.get('comment'), date)

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
            'name': c.PROFESSOR_REVIEW_FIELD_CLARITY,
            'rating': self.clarity,
        }, {
            'name': c.PROFESSOR_REVIEW_FIELD_PASSION,
            'rating': self.passion,
        }]

    def update_ratings_with_dict(self, **kwargs):
        if 'ratings' in kwargs:
            new_values = { d['name']: d['rating'] for d in kwargs['ratings'] }

            self.clarity = new_values.get(c.PROFESSOR_REVIEW_FIELD_CLARITY)
            self.passion = new_values.get(c.PROFESSOR_REVIEW_FIELD_PASSION)
        else:
            logging.warn("Trying to update CourseReview rating with empty dict")

    def update_review_with_date_and_dict(self, date, **kwargs):
        self.update_ratings_with_dict(**kwargs)
        update_comment_and_date(self, kwargs.get('comment'), date)

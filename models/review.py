from datetime import datetime
import mongoengine as me
import logging

import rmc.shared.constants as c

def update_kwargs_from_ratings(kwargs):
    if 'ratings' in kwargs:
        kwargs.update({ d['name']: d['rating'] for d in kwargs['ratings'] })
        del kwargs['ratings']

def update_comment_and_date(review_obj, **kwargs):
    comment = kwargs.get('comment')
    if comment is not None and comment != review_obj.comment:
        review_obj.comment = comment

        date = kwargs.get('comment_date')
        if date is None:
            logging.warn("CourseReview: update_comment_and_date comment_date"
                "not set. Defaulting to current time")
            date = datetime.now()
        review_obj.comment_date = date

class CourseReview(me.EmbeddedDocument):
    interest = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    easiness = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    usefulness = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()

    # Minimum number of characters for a review to pass
    # TODO(david): Have a function to do this. First, we need consistent review
    #     interface
    MIN_REVIEW_LENGTH = 15

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

    def update_ratings(self, **kwargs):
        if 'ratings' in kwargs:
            new_values = { d['name']: d['rating'] for d in kwargs['ratings'] }
            self.old_interest = self.interest
            self.old_easiness = self.easiness
            self.old_usefulness = self.usefulness

            self.easiness = new_values.get(c.COURSE_REVIEW_FIELD_EASINESS)
            self.interest = new_values.get(c.COURSE_REVIEW_FIELD_INTEREST)
            self.usefulness = new_values.get(c.COURSE_REVIEW_FIELD_USEFULNESS)
        else:
            logging.warn("CourseReview: update_ratings without ratings in "
                "dict");

    # TODO(Sandy): Remove duplicate code with ProfessorReview?
    def update_review(self, **kwargs):
        self.update_ratings(**kwargs)
        update_comment_and_date(self, **kwargs)

    def update_course_aggregate_ratings(self, cur_course):
        # Update associated aggregate ratings
        if hasattr(self, 'old_easiness'):
            cur_course.easiness.update_aggregate_after_replacement(
                self.old_easiness, self.easiness)
        if hasattr(self, 'old_interest'):
            cur_course.interest.update_aggregate_after_replacement(
                self.old_interest, self.interest)
        if hasattr(self, 'old_usefulness'):
            cur_course.usefulness.update_aggregate_after_replacement(
                self.old_usefulness, self.usefulness)



class ProfessorReview(me.EmbeddedDocument):
    clarity = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    passion = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()

    # Minimum number of characters for a review to pass
    # TODO(david): Have a function to do this. First, we need consistent review
    #     interface
    MIN_REVIEW_LENGTH = 15

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

    def update_ratings(self, **kwargs):
        if 'ratings' in kwargs:
            new_values = { d['name']: d['rating'] for d in kwargs['ratings'] }
            self.old_clarity = self.clarity
            self.old_passion = self.passion

            self.clarity = new_values.get(c.PROFESSOR_REVIEW_FIELD_CLARITY)
            self.passion = new_values.get(c.PROFESSOR_REVIEW_FIELD_PASSION)
        else:
            logging.warn("ProfessorReview: update_ratings without ratings in"
                "dict");

    def update_review(self, **kwargs):
        self.update_ratings(**kwargs)
        update_comment_and_date(self, **kwargs)

    def update_professor_aggregate_ratings(self, cur_professor):
        # Update associated aggregate ratings
        if hasattr(self, 'old_clarity'):
            cur_professor.clarity.update_aggregate_after_replacement(
                self.old_clarity, self.clarity)
        if hasattr(self, 'old_passion'):
            cur_professor.passion.update_aggregate_after_replacement(
                self.old_passion, self.passion)

    def to_dict(self, current_user, user_course):
        # TODO(mack): this should somehow be done from UserCourse rather than
        # here since it currently requires passing through user_course which is
        # stupid

        dict_ = {
            'comment': {
                'comment': self.comment,
                'comment_date': self.comment_date,
            },
            'ratings': self.to_array(),
        }

        # TODO(david): Maybe just pass down the entire user object
        # TODO(david) FIXME[uw](david): Should not nest comment
        if hasattr(user_course, 'user_id') and not user_course.anonymous:
            # TODO(mack): fix circular dependency
            import user as _user
            author = _user.User.objects.only('first_name', 'last_name', 'fbid',
                    'program_name').with_id(user_course.user_id)
            dict_['comment']['author'] = author.to_review_author_dict(
                    current_user)

        return dict_

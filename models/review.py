from datetime import datetime
import mongoengine as me
import logging


class Privacy(object):
    ME = 0
    FRIENDS = 1
    EVERYONE = 2

    @staticmethod
    def choices():
        return [Privacy.ME, Privacy.FRIENDS, Privacy.EVERYONE]

    # TODO(david): Make this class more magical and not require calling these
    @staticmethod
    def to_int(str_privacy, default=1):
        return {
            'me': Privacy.ME,
            'friends': Privacy.FRIENDS,
            'everyone': Privacy.EVERYONE,
        }.get(str_privacy, default)

    @staticmethod
    def to_str(int_privacy, default='friends'):
        return {
            Privacy.ME: 'me',
            Privacy.FRIENDS: 'friends',
            Privacy.EVERYONE: 'everyone',
        }.get(int_privacy, default)


class BaseReview(me.EmbeddedDocument):
    comment = me.StringField(default='', max_length=4096)
    comment_date = me.DateTimeField()
    share_date = me.DateTimeField()
    # The time that any rating for this review was changed
    # (either created, modified, or deleted)
    rating_change_date = me.DateTimeField()
    privacy = me.IntField(choices=Privacy.choices(), default=Privacy.FRIENDS)

    # Minimum number of characters for a review to pass
    # TODO(david): Have a function to do this. First, we need consistent review
    #     interface
    MIN_REVIEW_LENGTH = 11

    def __init__(self, **kwargs):
        if 'ratings' in kwargs:
            kwargs.update({d['name']: d['rating'] for d in kwargs['ratings']})
            del kwargs['ratings']

        if isinstance(kwargs.get('privacy'), basestring):
            kwargs['privacy'] = Privacy.to_int(kwargs['privacy'])

        super(BaseReview, self).__init__(**kwargs)

    def rating_fields(self):
        raise NotImplementedError("return a list of rating field names")

    @property
    # Has this review ever been rated in the past?
    def has_been_rated(self):
        if self.rating_change_date:
            return True

        for rating_name in self.rating_fields():
            if getattr(self, rating_name) is not None:
                return True

        return False

    @property
    def has_commented(self):
        return self.comment_date and self.comment

    @property
    def has_shared(self):
        return self.share_date

    def get_ratings_array(self):
        return [{'name': r, 'rating': getattr(self, r)}
                for r in self.rating_fields()]

    def update_ratings(self, ratings_dict):
        for rating_name in self.rating_fields():
            old_rating = getattr(self, rating_name)
            new_rating = ratings_dict.get(rating_name)
            setattr(self, 'old_%s' % rating_name, old_rating)
            setattr(self, rating_name, new_rating)

            if new_rating != old_rating:
                self.rating_change_date = datetime.now()

    def update(self, **kwargs):
        if 'ratings' in kwargs:
            new_values = {d['name']: d['rating'] for d in kwargs['ratings']}
            self.update_ratings(new_values)

        comment = kwargs.get('comment')
        if comment is not None and comment != self.comment:
            self.comment = comment

            date = kwargs.get('comment_date')
            if date is None:
                logging.warn("Review.update() comment_date "
                    "not set. Defaulting to current time")
                date = datetime.now()
            self.comment_date = date

        if 'privacy' in kwargs:
            self.privacy = Privacy.to_int(kwargs['privacy'])

    def to_dict(self, current_user=None, author_id=None):
        dict_ = {
            'comment': self.comment,
            'comment_date': self.comment_date,
            'privacy': Privacy.to_str(self.privacy),
            'ratings': self.get_ratings_array(),
        }

        if author_id:
            # TODO(david): Remove circular dependency
            import user as _user
            author = _user.User.objects.only(*(_user.User.CORE_FIELDS +
                    ['program_name'])).with_id(author_id)
            show_author = self.should_show_author(current_user, author_id)
            dict_['author'] = author.to_review_author_dict(current_user,
                    show_author)

        return dict_

    def should_show_author(self, current_user, author_id):
        if self.privacy == Privacy.ME:
            return False
        elif self.privacy == Privacy.FRIENDS:
            return current_user and (author_id in current_user.friend_ids or
                    current_user.id == author_id)
        elif self.privacy == Privacy.EVERYONE:
            return True
        else:
            logging.error('Unrecognized privacy setting %s' % self.privacy)
            return False


class CourseReview(BaseReview):
    interest = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    easiness = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    usefulness = me.FloatField(min_value=0.0, max_value=1.0, default=None)

    def rating_fields(self):
        return ['usefulness', 'easiness', 'interest']

    # TODO(david): Refactor into base class
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


class ProfessorReview(BaseReview):
    clarity = me.FloatField(min_value=0.0, max_value=1.0, default=None)
    passion = me.FloatField(min_value=0.0, max_value=1.0, default=None)

    def rating_fields(self):
        return ['clarity', 'passion']

    # TODO(david): Refactor into base class
    # TODO(mack): tidy up interface so we don't have to pass in course,
    # course_review
    # TODO(mack): handle the case you change the professor
    def update_professor_aggregate_ratings(self, cur_professor,
            cur_course, course_review):

        redis_changes = []

        if hasattr(course_review, 'old_easiness'):
            redis_changes.append({
                'name': 'easiness',
                'old': course_review.old_easiness,
                'new': course_review.easiness,
            })

        if hasattr(course_review, 'old_interest'):
            redis_changes.append({
                'name': 'interest',
                'old': course_review.old_interest,
                'new': course_review.interest,
            })

        # Update associated aggregate ratings
        if hasattr(self, 'old_clarity'):
            cur_professor.clarity.update_aggregate_after_replacement(
                self.old_clarity, self.clarity)
            redis_changes.append({
                'name': 'clarity',
                'old': self.old_clarity,
                'new': self.clarity,
            })

        if hasattr(self, 'old_passion'):
            cur_professor.passion.update_aggregate_after_replacement(
                self.old_passion, self.passion)
            redis_changes.append({
                'name': 'passion',
                'old': self.old_passion,
                'new': self.passion,
            })

        cur_professor.update_redis_ratings_for_course(
                cur_course.id, redis_changes)

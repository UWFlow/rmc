from bson import json_util
import mongoengine as me
import re
import redis

import rating as _rating
import review as _review
import rmc.shared.constants as c
from rmc.shared import util
import user_course

# TODO(mack): remove this from here?
r = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)


class Professor(me.Document):

    meta = {
        'indexes': [
            'clarity.rating',
            'clarity.count',
            'easiness.rating',
            'easiness.count',
            'passion.rating',
            'passion.count',
        ],
    }

    #FIXME(Sandy): Becker actually shows up as byron_becker
    # eg. byron_weber_becker
    id = me.StringField(primary_key=True)

    # TODO(mack): available in menlo data
    # department_id = me.StringField()

    # eg. Byron Weber
    first_name = me.StringField(required=True)

    # eg. Becker
    last_name = me.StringField(required=True)

    clarity = me.EmbeddedDocumentField(_rating.AggregateRating, default=_rating.AggregateRating())
    easiness = me.EmbeddedDocumentField(_rating.AggregateRating, default=_rating.AggregateRating())
    passion = me.EmbeddedDocumentField(_rating.AggregateRating, default=_rating.AggregateRating())

    @classmethod
    def get_id_from_name(cls, first_name, last_name=None):
        if not last_name:
            return re.sub(r'\s+', '_', first_name.lower())

        first_name = first_name.lower()
        last_name = last_name.lower()
        return re.sub(r'\s+', '_', '%s %s' % (first_name, last_name))

    @staticmethod
    def guess_names(combined_name):
        """Returns first, last name given a string."""
        names = re.split(r'\s+', combined_name)
        return (' '.join(names[:-1]), names[-1])

    @property
    def name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = Professor.get_id_from_name(self.first_name, self.last_name)

        super(Professor, self).save(*args, **kwargs)

    def get_ratings(self):
        ratings_dict = {
            'clarity': self.clarity.to_dict(),
            'easiness': self.easiness.to_dict(),
            'passion': self.passion.to_dict(),
        }
        ratings_dict['overall'] = _rating.get_overall_rating(
                ratings_dict.values()).to_dict()
        return util.dict_to_list(ratings_dict)

    # TODO(mack): redis key should be namespaced under course_professor
    # or something....
    # TODO(mack): store all ratings under single hash which is
    # supposed to be more memory efficient (and probably faster
    # fetching as well)
    def get_professor_course_redis_key(self, course_id, rating_name):
        return ':'.join([course_id, self.id, rating_name])

    def set_course_rating_in_redis(self, course_id, rating_name, aggregate_rating):
        redis_key = self.get_professor_course_redis_key(
                    course_id, rating_name)
        r.set(redis_key, aggregate_rating.to_json())

    def get_course_rating_from_redis(self, course_id, rating_name):
        rating_json = r.get(self.get_professor_course_redis_key(
            course_id, rating_name))

        if rating_json:
            rating_loaded = json_util.loads(rating_json)

            return _rating.AggregateRating(
                rating=rating_loaded['rating'],
                count=rating_loaded['count'],
            )

        return None

    def update_redis_ratings_for_course(self, course_id, changes):
        # TOOO(mack): use redis pipeline for this
        for change in changes:
            rating_name = change['name']
            agg_rating = self.get_course_rating_from_redis(
                    course_id, rating_name)
            if not agg_rating:
                agg_rating = _rating.AggregateRating()

            agg_rating.update_aggregate_after_replacement(
                    change['old'], change['new'])

            self.set_course_rating_in_redis(course_id, rating_name, agg_rating)


    # TODO(david): This should go on ProfCourse
    def get_ratings_for_course(self, course_id):
        rating_dict = {}
        for name in ['clarity', 'easiness', 'passion']:
            agg_rating = self.get_course_rating_from_redis(course_id, name)
            if agg_rating:
                rating_dict[name] = agg_rating.to_dict()

        rating_dict['overall'] = _rating.get_overall_rating(
                rating_dict.values()).to_dict()

        return util.dict_to_list(rating_dict)


    @classmethod
    def get_reduced_professors_for_courses(cls, courses):
        professor_ids = set()
        for course in courses:
            professor_ids = professor_ids.union(course.professor_ids)

        professors = cls.objects(id__in=professor_ids).only(
                'first_name', 'last_name')

        return [p.to_dict() for p in professors]

    @classmethod
    def get_full_professors_for_course(cls, course, current_user):
        professors = cls.objects(id__in=course.professor_ids)
        return [p.to_dict(course_id=course.id, current_user=current_user)
                for p in professors]


    def to_dict(self, course_id=None, current_user=None):
        dict_ = {
            'id': self.id,
            #'first_name': self.first_name,
            #'last_name': self.last_name,
            #'ratings': self.get_ratings(),
            'name': self.name,
        }

        if course_id:

            ucs = user_course.get_reviews_for_course_prof(
                    course_id, self.id)

            # TODO(david): Eventually do this in mongo query or enforce quality
            #     metrics on front-end
            ucs = filter(
                    lambda uc: len(uc.professor_review.comment)
                        >= _review.ProfessorReview.MIN_REVIEW_LENGTH,
                    ucs)

            course_review_dicts = [uc.professor_review.to_dict(current_user,
                getattr(uc, 'user_id', None)) for uc in ucs]

            # Don't show older reviews
            course_review_dicts = util.freshness_filter(
                    course_review_dicts, lambda review: review['comment_date'])

            dict_.update({
                'course_ratings': self.get_ratings_for_course(course_id),
                'course_reviews': course_review_dicts,
            })

        return dict_

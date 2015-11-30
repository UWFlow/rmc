from bson import json_util
import mongoengine as me
import re
import redis

import rating as _rating
import review as _review
import rmc.shared.constants as c
from rmc.shared import util
import user_course
import itertools

# TODO(mack): remove this from here?
r = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)

_COURSE_NAME_REGEX = re.compile(r'([a-z]+)([0-9]+)')


def safe_division(a, b):
    return (0.0 if b == 0.0 else float(a) / b)


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

    # eg. ['MATH', 'CS']
    departments_taught = me.ListField(me.StringField())

    clarity = me.EmbeddedDocumentField(_rating.AggregateRating,
                                       default=_rating.AggregateRating())
    easiness = me.EmbeddedDocumentField(_rating.AggregateRating,
                                        default=_rating.AggregateRating())
    passion = me.EmbeddedDocumentField(_rating.AggregateRating,
                                       default=_rating.AggregateRating())

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
            self.id = Professor.get_id_from_name(self.first_name,
                                                 self.last_name)

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
    # example course_id is math117
    def get_professor_course_redis_key(self, course_id, rating_name):
        return ':'.join([course_id, self.id, rating_name])

    def set_course_rating_in_redis(self, course_id, rating_name,
                                   aggregate_rating):
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

    def get_ratings_for_career(self):
        """Returns an aggregate of all the ratings for a prof"""
        courses_taught = self.get_courses_taught()
        clarity = 0
        clarity_count = 0
        passion = 0
        passion_count = 0

        for c in courses_taught:
            ratings = self.get_ratings_for_course(c)
            for r in ratings:
                if r.get('name') == 'clarity':
                    clarity += round(r.get('count') * r.get('rating'))
                    clarity_count += r.get('count')
                elif r.get('name') == 'passion':
                    passion += round(r.get('count') * r.get('rating'))
                    passion_count += r.get('count')

        overall_count = clarity_count + passion_count
        overall = clarity + passion

        return [{
            'count': clarity_count,
            'name': 'clarity',
            'rating': safe_division(clarity, clarity_count)
        }, {
            'count': passion_count,
            'name': 'passion',
            'rating': safe_division(passion, passion_count)
        }, {
            'count': overall_count,
            'name': 'overall',
            'rating': safe_division(overall, overall_count)
        }]

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

    def get_reviews_for_course(self, course_id, current_user=None):
        ucs = user_course.get_reviews_for_course_prof(course_id, self.id)

        # Quality filter.
        # TODO(david): Eventually do this in mongo query or enforce quality
        #     metrics on front-end
        ucs = filter(
                lambda uc: len(uc.professor_review.comment)
                    >= _review.ProfessorReview.MIN_REVIEW_LENGTH,
                ucs)

        prof_review_dicts = [uc.professor_review.to_dict(current_user,
            getattr(uc, 'user_id', None)) for uc in ucs]

        # Try to not show older reviews, if we have enough results
        date_getter = lambda review: review['comment_date']
        prof_review_dicts = util.publicly_visible_ratings_and_reviews_filter(
                prof_review_dicts, date_getter, util.MIN_NUM_REVIEWS)

        return prof_review_dicts

    def get_reviews_for_self(self):
        """Returns all reviews for a prof, over all courses taught"""
        menlo_reviews = user_course.MenloCourse.objects(
            professor_id=self.id,
        ).only('professor_review', 'course_id')

        user_reviews = user_course.UserCourse.objects(
            professor_id=self.id,
        ).only('professor_review', 'user_id', 'term_id', 'course_id')

        return itertools.chain(menlo_reviews, user_reviews)

    def get_reviews_for_all_courses(self, current_user):
        """Returns all reviews for a prof as a dict, organized by course id"""
        courses_taught = self.get_courses_taught()
        course_reviews = []
        for course in courses_taught:
            course_reviews.append({
                'course_id': course,
                'reviews': self.get_reviews_for_course(course,
                        current_user)
            })
        return course_reviews

    def get_courses_taught(self):
        """Returns an array of course_id's for each course the prof taught"""
        ucs = self.get_reviews_for_self()

        ucs = filter(
                lambda uc: len(uc.professor_review.comment)
                    >= _review.ProfessorReview.MIN_REVIEW_LENGTH,
                ucs)

        courses_taught = set(uc['course_id'] for uc in ucs)
        return sorted(courses_taught)

    def get_departments_taught(self):
        """Returns an array of the departments the prof has taught in"""
        ucs = self.get_reviews_for_self()
        ucs = filter(
                lambda uc: len(uc.professor_review.comment)
                    >= _review.ProfessorReview.MIN_REVIEW_LENGTH,
                ucs)
        departments_taught = set(_COURSE_NAME_REGEX.match(uc['course_id']).
                group(1).upper() for uc in ucs)
        return sorted(departments_taught)

    def transfer_reviews_from_prof(self, prof, delete_dupe_prof=False):
        mcs = user_course.MenloCourse.objects(professor_id=prof.id)
        ucs = user_course.UserCourse.objects(professor_id=prof.id)
        for mc in mcs:
            mc.professor_id = self.id
            mc.save()
        for uc in ucs:
            uc.professor_id = self.id
            uc.save()

        if delete_dupe_prof:
            prof.delete()

    def to_dict(self, course_id=None, current_user=None):
        dict_ = {
            'id': self.id,
            #'first_name': self.first_name,
            #'last_name': self.last_name,
            #'ratings': self.get_ratings(),
            'name': self.name,
        }

        if course_id:
            ratings = self.get_ratings_for_course(course_id)
            reviews = self.get_reviews_for_course(course_id, current_user)
            dict_.update({
                'course_ratings': ratings,
                'course_reviews': reviews,
            })

        return dict_

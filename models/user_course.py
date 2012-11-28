import itertools

import mongoengine as me

import course
import points as _points
import professor
import rating
import review
import term


class CritiqueCourse(me.Document):
    meta = {
        'indexes': [
            'course_id',
            'professor_id',
        ],
    }

    # id = me.ObjectIdField(primary_key=True)

    course_id = me.StringField(required=True)
    # TODO(mack): need section_id or equiv
    # course_id = me.StringField(required=True, unique_with='section_id')
    # section_id = me.IntField(required=True)
    professor_id = me.StringField(required=True)
    term_id = me.StringField(required=True)

    interest = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    easiness = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    overall_course = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    clarity = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    passion = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    overall_prof = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())


class MenloCourse(me.Document):
    meta = {
        'indexes': [
            'course_id',
            'professor_id',
        ],
    }

    # id = me.ObjectIdField(primary_key=True)

    course_id = me.StringField(required=True)
    professor_id = me.StringField()

    course_review = me.EmbeddedDocumentField(review.CourseReview)
    professor_review = me.EmbeddedDocumentField(review.ProfessorReview)


# TODO(mack): should be UserCourseOffering?
class UserCourse(me.Document):

    meta = {
        'indexes': [
            # TODO(mack): this index on user_id is probably not necessary
            # since it duplicates the unique_with on user_id
            'user_id',
            'course_id',
            'professor_id',
            # TODO(mack): check if below indices are necessary
            #('course_id', 'professor_id'),
            #('professor_id', 'course_id'),
        ],
    }

    # date review created implictly stored here
    # id = me.ObjectIdField(primary_key=True)

    # TODO(mack): verify this works when user_id is not required
    # TODO(mack): might be better to just enforce uniqueness on
    # ['course_id', 'offering_id']?
    user_id = me.ObjectIdField(unique_with=['course_id', 'term_id'])
    course_id = me.StringField(required=True)
    term_id = me.StringField(required=True)
    # TODO(mack): might not appropriate to store here, maybe should be
    # calculated using combination of info about when user started
    # school and term this course was taken
    # eg. 3A
    program_year_id = me.StringField()

    # TODO(mack): add fields for grade tracking; eg. grades on assignments

    # TODO(mack): should range be 0..1 or 0..100 ?
    grade = me.FloatField(min_value=0.0, max_value=1.0)

    professor_id = me.StringField()

    course_review = me.EmbeddedDocumentField(review.CourseReview, default=review.CourseReview())
    professor_review = me.EmbeddedDocumentField(review.ProfessorReview, default=review.ProfessorReview())

    DEFAULT_TO_DICT_FIELDS = [
        'id',
        'user_id',
        'term_id',
        'term_name',
        'course_id',
        'professor_id',
        'course_review',
        'professor_review',
        'has_reviewed',
        'program_year_id',
    ]

    # TODO(mack): add section_id
    # section_id = StringField()

    # TODO(mack): should we have update_time?
    # update_date = me.DateTimeField()

    @property
    def term_name(self):
        return term.Term.name_from_id(self.term_id)

    @property
    def has_reviewed(self):
        return (self.course_review.comment_date is not None
            or self.course_review.easiness is not None
            or self.course_review.usefulness is not None
            or self.professor_review.comment_date is not None
            or self.professor_review.clarity is not None
            or self.professor_review.passion is not None
        )

    @property
    def num_points(self):
        points = 0

        if self.course_review.has_commented:
            points += _points.PointSource.COURSE_COMMENT
        if self.course_review.has_been_rated:
            points += _points.PointSource.COURSE_RATING
        if self.professor_review.has_commented:
            points += _points.PointSource.PROFESSOR_COMMENT
        if self.professor_review.has_been_rated:
            points += _points.PointSource.PROFESSOR_RATING

        return points

    def to_dict(self, fields=DEFAULT_TO_DICT_FIELDS):
        # NOTE: DO NOT MODIFY parameter `fields` in this fn, because it's
        #     statically initialized with a non-primitive default.

        # TODO(david): Reuse code below for other to_dict() methods
        def map_field(prop):
            val = getattr(self, prop)
            return val.to_dict() if hasattr(val, 'to_dict') else val

        return { f: map_field(f) for f in fields }

    def save(self, *args, **kwargs):
        # TODO(Sandy): Use transactions
        # http://docs.mongodb.org/manual/tutorial/perform-two-phase-commits/
        # or run nightly ratings aggregation script to fix race condtions
        cur_course = course.Course.objects.with_id(self.course_id)
        if cur_course:
            self.course_review.update_course_aggregate_ratings(cur_course)
            cur_course.save()

        if self.professor_id:
            cur_professor = professor.Professor.objects.with_id(
                self.professor_id)
            self.professor_review.update_professor_aggregate_ratings(
                cur_professor, cur_course, self.course_review)
            cur_professor.save()

        super(UserCourse, self).save(*args, **kwargs)


# TODO(david): Should be static method of ProfCourse
def get_reviews_for_course_prof(course_id, prof_id):
    menlo_reviews = MenloCourse.objects(
        course_id=course_id,
        professor_id=prof_id,
    ).only('professor_review', 'course_review')

    user_reviews = UserCourse.objects(
        course_id=course_id,
        professor_id=prof_id,
    ).only('professor_review', 'course_review', 'user_id', 'term_id')

    return itertools.chain(menlo_reviews, user_reviews)

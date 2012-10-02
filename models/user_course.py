import itertools

import mongoengine as me

import rating
import review
import term
import user

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

    # is the review posted anonymously?
    anonymous = me.BooleanField(default=False)
    course_review = me.EmbeddedDocumentField(review.CourseReview, default=review.CourseReview())
    professor_review = me.EmbeddedDocumentField(review.ProfessorReview, default=review.ProfessorReview())

    # TODO(mack): add section_id
    # section_id = StringField()

    # TODO(mack): should we have update_time?
    # update_date = me.DateTimeField()

    @property
    def term_name(self):
        return term.Term(self.term_id).name

    @property
    def has_reviewed(self):
        return (self.course_review.comment_date is not None
            or self.course_review.easiness is not None
            or self.course_review.usefulness is not None
            or self.professor_review.comment_date is not None
            or self.professor_review.clarity is not None
            or self.professor_review.passion is not None
        )

    def to_dict(self):
        course_review = self.course_review
        professor_review = self.professor_review

        return {
            'id': self.id,
            'user_id': self.user_id,
            # TODO(Sandy): We probably don't need to pass down term_id
            'term_id': self.term_id,
            'term_name': term.Term(id=self.term_id).name,
            'course_id': self.course_id,
            'professor_id': self.professor_id,
            'anonymous': self.anonymous,
            'course_review': {
                'ratings': course_review.to_array(),
                'comment': course_review.comment,
                'comment_date': course_review.comment_date,
            },
            'professor_review': {
                'ratings': professor_review.to_array(),
                'comment': professor_review.comment,
                'comment_date': professor_review.comment_date,
            },
            'has_reviewed': self.has_reviewed,
        }


# TODO(david): Should be static method of ProfCourse
def get_reviews_for_course_prof(course_id, prof_id):
    menlo_reviews = MenloCourse.objects(
        course_id=course_id,
        professor_id=prof_id,
    ).only('professor_review', 'course_review')

    user_reviews = UserCourse.objects(
        course_id=course_id,
        professor_id=prof_id,
    ).only('professor_review', 'course_review', 'user_id', 'term_id',
            'anonymous')

    return itertools.chain(menlo_reviews, user_reviews)

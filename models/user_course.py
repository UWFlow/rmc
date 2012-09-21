import mongoengine as me

import rating
import review

class CritiqueCourse(me.Document):
    meta = {
        'indexes': [
            'course_id',
            'professor_id',
        ],
    }

    # id = me.ObjectIdField(primary_key=True)

    course_id = me.StringField(primary_key=True, required=True)
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
    user_id = me.StringField(unique_with=['course_id', 'term_id'])
    course_id = me.StringField(required=True)
    term_id = me.StringField(required=True)

    # TODO(mack): add fields for grade tracking; eg. grades on assignments

    # TODO(mack): should range be 0..1 or 0..100 ?
    grade = me.FloatField(min_value=0.0, max_value=1.0)

    professor_id = me.StringField()

    # is the review posted anonymously?
    anonymous = me.BooleanField(default=False)
    course_review = me.EmbeddedDocumentField(review.CourseReview)
    professor_review = me.EmbeddedDocumentField(review.ProfessorReview)

    # TODO(mack): add section_id
    # section_id = StringField()

    # TODO(mack): should we have update_time?
    # update_time = me.DateTimeField()

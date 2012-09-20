from mongoengine import EmbeddedDocument, Document
import _field as f

import rating

class CritiqueCourseReview(Document):
    meta = {
        'indexes': [
            'course_id',
            'professor_id',
        ],
    }

    # id = f.ObjectIdField(primary_key=True)

    course_id = f.StringField(required=True)
    # TODO(mack): need section_id or equiv
    # course_id = f.StringField(required=True, unique_with='section_id')
    # section_id = f.IntField(required=True)
    professor_id = f.ObjectIdField(required=True)

    clarity = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    easiness = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    passion = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())


class CourseReview(EmbeddedDocument):
    clarity = f.FloatField(min_value=0.0, max_value=1.0)
    easiness = f.FloatField(min_value=0.0, max_value=1.0)
    comment = f.StringField(max_length=4096)
    comment_time = f.DateTimeField()

class ProfessorReview(EmbeddedDocument):
    clarity = f.FloatField(min_value=0.0, max_value=1.0)
    passion = f.FloatField(min_value=0.0, max_value=1.0)
    comment = f.StringField(max_length=4096)
    comment_time = f.DateTimeField()


class MenloCourseReview(Document):
    meta = {
        'indexes': [
            'course_id',
            'professor_id',
        ],
    }

    # id = f.ObjectIdField(primary_key=True)

    course_id = f.StringField(required=True)
    professor_id = f.StringField()

    course_review = f.EmbeddedDocumentField(CourseReview)
    professor_review = f.EmbeddedDocumentField(ProfessorReview)


# TODO(mack): should be UserCourseOffering?
class UserCourseReview(Document):

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
    # id = f.ObjectIdField(primary_key=True)

    # TODO(mack): verify this works when user_id is not required
    # TODO(mack): might be better to just enforce uniqueness on
    # ['course_id', 'offering_id']?
    user_id = f.StringField(unique_with=['course_id', 'term_id'])
    course_id = f.StringField(required=True)
    term_id = f.StringField(required=True)

    # TODO(mack): add fields for grade tracking; eg. grades on assignments

    # TODO(mack): should range be 0..1 or 0..100 ?
    grade = f.FloatField(min_value=0.0, max_value=1.0)

    professor_id = f.StringField()

    # is the review posted anonymously?
    anonymous = f.BooleanField(default=False)
    course_review = f.EmbeddedDocumentField(CourseReview)
    professor_review = f.EmbeddedDocumentField(ProfessorReview)

    # TODO(mack): add section_id
    # section_id = StringField()

    # TODO(mack): should we have update_time?
    # update_time = f.DateTimeField()

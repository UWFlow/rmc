from mongoengine import Document
from mongoengine import StringField, EmbeddedDocumentField, ListField

import rmc.models.rating.Rating as Rating

class CourseRating(Document):
    meta = {
        'abstract': True
    }

    # e.g. earth121l
    id = StringField(primary_key=True)

    interest = EmbeddedDocumentField(Rating, required=True)
    easiness = EmbeddedDocumentField(Rating, required=True)

class MenloCourseRating(CourseRating):
    pass

class CritiqueCourseRating(CourseRating):
    pass

class FlowCourseRating(CourseRating):
    pass

class Course(Document):
    meta = {
        'indexes': [
            '_keywords',
            'interest.rating',
            'interest.count',
            'easiness.rating',
            'easiness.count',
            'overall.rating',
            'overall.count',
        ],
    }

    # e.g. earth121l
    id = StringField(primary_key=True)

    # e.g. earth
    department_id = StringField(required=True)

    # e.g. 121l
    number = StringField(required=True)

    # Introductory Earth Sciences Laboratory 1
    name = StringField(required=True)

    # Description about the course
    description = StringField(required=True)

    # aggregate of Menlo/Critique/Flow CourseRating
    interest = EmbeddedDocumentField(Rating, default=Rating())
    easiness = EmbeddedDocumentField(Rating, default=Rating())
    overall = EmbeddedDocumentField(Rating, default=Rating())

    # e.g. ['earth', '121l', 'earth121l', 'Introductory', 'Earth' 'Sciences', 'Laboratory', '1']
    _keywords = ListField(StringField(), required=True)

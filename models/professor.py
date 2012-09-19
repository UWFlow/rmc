from mongoengine import Document
from mongoengine import ObjectIdField, StringField, EmbeddedDocumentField

import rmc.models.rating.Rating as Rating

class ProfessorRating(Document):
    meta = {
        'abstract': True
    }

    # eg. professor_id => ObjectId()
    id = ObjectIdField(primary_key=True)

    clarity = EmbeddedDocumentField(Rating, required=True)
    easiness = EmbeddedDocumentField(Rating, required=True)
    passion = EmbeddedDocumentField(Rating, required=True)


class MenloProfessorRating(ProfessorRating):
    pass

class CritiqueProfessorRating(ProfessorRating):
    pass

class FlowProfessorRating(ProfessorRating):
    pass

class Professor(Document):
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

    # eg. ObjectId()
    id = ObjectIdField(primary_key=True)

    # eg. Byron
    first_name = StringField(required=True)

    # eg. Weber
    middle_name = StringField(required=False)

    # eg. Becker
    last_name = StringField(required=True)

    # aggregate from Menlo/Critique/Flow ProfessorRating
    easiness = EmbeddedDocumentField(Rating, default=Rating())
    clarity = EmbeddedDocumentField(Rating, default=Rating())
    passion = EmbeddedDocumentField(Rating, default=Rating())

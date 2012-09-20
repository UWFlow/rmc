from mongoengine import Document
import _field as f

import rating


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

    # eg. earth121l
    id = f.StringField(primary_key=True)

    # eg. earth
    department_id = f.StringField(required=True)

    # eg. 121l
    number = f.StringField(required=True)

    # eg. Introductory Earth Sciences Laboratory 1
    name = f.StringField(required=True)

    # Description about the course
    description = f.StringField(required=True)

    # eg. ['earth', '121l', 'earth121l', 'Introductory', 'Earth' 'Sciences', 'Laboratory', '1']
    _keywords = f.ListField(f.StringField(), required=True)

    easiness = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    interest = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    overall = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())

    def save(self, *args, **kwargs):
        self.id = self.department_id + self.number
        super(Course, self).save(*args, **kwargs)

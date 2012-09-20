from mongoengine import Document
import _field as f

import rating

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

    # eg. byron_weber_becker
    id = f.StringField(primary_key=True)

    # TODO(mack): available in menlo data
    # department_id = f.StringField()

    # eg. Byron Weber
    first_name = f.StringField(required=True)

    # eg. Becker
    last_name = f.StringField(required=True)

    clarity = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    easiness = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    passion = f.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())

    @classmethod
    def get_id_from_name(cls, first_name, last_name):
        first_name = first_name.lower()
        last_name = last_name.lower()
        return ('%s %s' % (first_name, last_name)).replace(' ', '_')

    def save(self, *args, **kwargs):
        self.id = Professor.get_id_from_name(self.first_name, self.last_name)
        super(Professor, self).save(*args, **kwargs)

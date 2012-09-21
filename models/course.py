import mongoengine as me

import rating

class Course(me.Document):
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
    id = me.StringField(primary_key=True)

    # eg. earth
    department_id = me.StringField(required=True)

    # eg. 121l
    number = me.StringField(required=True)

    # eg. Introductory Earth Sciences Laboratory 1
    name = me.StringField(required=True)

    # Description about the course
    description = me.StringField(required=True)

    easiness = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    interest = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    overall = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())

    # eg. ['earth', '121l', 'earth121l', 'Introductory', 'Earth' 'Sciences', 'Laboratory', '1']
    _keywords = me.ListField(me.StringField(), required=True)

    def save(self, *args, **kwargs):
        self.id = self.department_id + self.number
        super(Course, self).save(*args, **kwargs)

import mongoengine as me

import rating

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

    clarity = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    easiness = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    passion = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())

    @classmethod
    def get_id_from_name(cls, first_name, last_name):
        first_name = first_name.lower()
        last_name = last_name.lower()
        return ('%s %s' % (first_name, last_name)).replace(' ', '_')

    @property
    def name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = Professor.get_id_from_name(self.first_name, self.last_name)

        super(Professor, self).save(*args, **kwargs)

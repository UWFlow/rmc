import mongoengine as me


class AggregateRating(me.EmbeddedDocument):
    rating = me.FloatField(min_value=0.0, max_value=1.0)
    count = me.IntField(min_value=0, default=0)

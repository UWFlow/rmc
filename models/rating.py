from mongoengine import EmbeddedDocument
import _field as f


class AggregateRating(EmbeddedDocument):
    rating = f.FloatField(min_value=0.0, max_value=1.0)
    count = f.IntField(min_value=0, default=0)

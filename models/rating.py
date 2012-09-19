from mongoengine import EmbeddedDocument
from mongoengine import IntField, FloatField

class Rating(EmbeddedDocument):
    count = IntField(min_value=0, default=0)
    rating = FloatField(min_value=0.0, max_value=1.0, default=None)

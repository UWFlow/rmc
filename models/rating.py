import mongoengine as me
# TODO(mack): use ujson
import json

class AggregateRating(me.EmbeddedDocument):
    rating = me.FloatField(min_value=0.0, max_value=1.0)
    count = me.IntField(min_value=0, default=0)

    def add_rating(self, rating):
        if self.rating is None:
            self.rating = 0.0
        self.rating = ((self.rating * self.count) + rating) / (self.count + 1)
        self.count += 1

    def add_aggregate_rating(self, ar):
        if ar.count == 0:
            return
        if self.rating is None:
            self.rating = 0.0
        total = ar.rating * ar.count
        self.rating = ((self.rating * self.count) + total) / (self.count + ar.count)
        self.count += ar.count

    def to_json(self):
        return json.dumps({
            'rating': self.rating,
            'count': self.count,
        })

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        return cls(**obj)

import mongoengine as me
# TODO(mack): use ujson
import json

class AggregateRating(me.EmbeddedDocument):
    rating = me.FloatField(min_value=0.0, max_value=1.0, default=0.0)
    count = me.IntField(min_value=0, default=0)

    def add_rating(self, rating):
        self.rating = ((self.rating * self.count) + rating) / (self.count + 1)
        self.count += 1

    def add_aggregate_rating(self, ar):
        if ar.count == 0:
            return
        total = ar.rating * ar.count
        self.rating = ((self.rating * self.count) + total) / (self.count + ar.count)
        self.count += ar.count

    def to_dict(self):
        return {
            'rating': self.rating,
            'count': self.count,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        return cls(**obj)

    @classmethod
    def from_single_rating(cls, value):
        return cls(rating=value, count=1)


def get_overall_rating(ar_ratings):
    sum_ratings = sum(r['rating'] * r['count'] for r in ar_ratings)
    num_ratings = sum(r['count'] for r in ar_ratings)
    return AggregateRating(
        count=max(r['count'] for r in ar_ratings) if ar_ratings else 0,
        rating=sum_ratings / max(num_ratings, 1),
    )

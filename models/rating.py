import logging
import mongoengine as me
# TODO(mack): use ujson
import json

import rmc.shared.util as util

class AggregateRating(me.EmbeddedDocument):
    rating = me.FloatField(min_value=0.0, max_value=1.0, default=0.0)
    count = me.IntField(min_value=0, default=0)
    sorting_score_positive = me.FloatField(
        min_value=0.0, max_value=1.0, default=0.0)
    sorting_score_negative = me.FloatField(
        min_value=0.0, max_value=1.0, default=0.0)

    def update_sorting_score(self):
        self.sorting_score_positive = util.get_sorting_score(
            self.rating, self.count)
        self.sorting_score_negative = util.get_sorting_score(
            1 - self.rating, self.count)


    def add_rating(self, rating):
        self.rating = ((self.rating * self.count) + rating) / (self.count + 1)
        self.count += 1
        self.update_sorting_score()

    def remove_rating(self, rating):
        if self.count == 0:
            logging.warn("AggregateRating: called remove_rating with count = 0")
            return

        if self.count == 1:
            self.rating = 0
        else:
            self.rating = (((self.rating * self.count) - rating) /
                (self.count - 1))

        self.count -= 1
        self.update_sorting_score()

    def add_aggregate_rating(self, ar):
        if ar.count == 0:
            return
        total = ar.rating * ar.count
        self.rating = ((self.rating * self.count) + total) / (self.count + ar.count)
        self.count += ar.count
        self.update_sorting_score()

    def to_dict(self):
        return {
            'rating': self.rating,
            'count': self.count,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def update_aggregate_after_replacement(self, old_value, new_value):
        if old_value is None and new_value is None:
            # Rating not changed
            pass
        elif old_value is None:
            # New rating, add new_value to the aggregate
            self.add_rating(new_value)
        elif new_value is None:
            # Removed a rating, remove old_value from the aggregate
            self.remove_rating(old_value)
        elif old_value != new_value:
            # Modified a rating, removing old_value and add new_value to the
            # aggregate
            self.remove_rating(old_value)
            self.add_rating(new_value)

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        return cls(**obj)

    # TODO(david): Does not make sense to make aggregate rating from one rating
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

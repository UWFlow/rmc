import rmc.models as m
import rmc.test.lib as testlib


class RatingTest(testlib.ModelTestCase):
    def assertRating(self, aggregate_rating, expected_rating, expected_count):
        self.assertEqual(aggregate_rating.rating, expected_rating)
        self.assertEqual(aggregate_rating.count, expected_count)

        # Ensure model field constraints are satisfied.
        self.assertTrue(0.0 <= aggregate_rating.rating <= 1.0)
        self.assertTrue(0 <= aggregate_rating.count)
        self.assertTrue(0.0 <= aggregate_rating.sorting_score_positive <= 1.0)
        self.assertTrue(0.0 <= aggregate_rating.sorting_score_negative <= 1.0)

    def test_add_remove_ratings(self):
        # This sequence of add/remove ratings reproduces a long-standing bug we
        # used to have: sometimes when users saved ratings for a professor, the
        # rating would be negative (and the save wouldn't validate due to model
        # constraints): https://github.com/UWFlow/rmc/issues/116

        # Professor Meredith is a cute kitten. Let's see if she's passionate.
        passion = m.AggregateRating()
        self.assertRating(passion, expected_rating=0.0, expected_count=0)

        # She's adopted by a girl named Taylor. They become happy roommates.
        passion.add_rating(1)
        self.assertRating(passion, expected_rating=1.0, expected_count=1)

        # But Meredith exhibits bad posture. Taylor isn't excited about that,
        # so she retracts her old rating for now.
        passion.remove_rating(1)
        self.assertRating(passion, expected_rating=0.0, expected_count=0)

        # Meredith learns how to moves her ears on command and Taylor is happy.
        passion.add_rating(1)
        self.assertRating(passion, expected_rating=1.0, expected_count=1)

        # But Ed is dejected after Meredith gives him a look of disapproval.
        passion.add_rating(0)
        self.assertRating(passion, expected_rating=0.5, expected_count=2)

        # Meredith meowed on about how Taylor can't sing, which Taylor thought
        # was Mean, so she changed her old approval to a disapproval.
        passion.remove_rating(1)
        passion.add_rating(0)
        self.assertRating(passion, expected_rating=0.0, expected_count=2)

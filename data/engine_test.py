import unittest

from pyspark import SparkContext
from engine import RecommendationEngine

sc = SparkContext()
rcmd_engine = RecommendationEngine(sc)


class EngineTest(unittest.TestCase):
    def test_recommendations_user_not_in_db(self):
        fake_user_id = 'notarealuserid'
        rcmd_engine.user_lookup = {"realuserid": 1}
        with self.assertRaises(Exception) as ex:
            rcmd_engine.recommend_user(fake_user_id, 5)
        self.assertEqual(str(ex.exception),
                         'User ' + fake_user_id + ' is not in the database')

    def test_recommendations_no_user_provided(self):
        user_id = None
        with self.assertRaises(Exception) as ex:
            rcmd_engine.recommend_user(user_id, 5)
        self.assertEqual(str(ex.exception), 'Please provide a user id')

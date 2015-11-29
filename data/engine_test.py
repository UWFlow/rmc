import unittest

from rmc.server.api.v1 import engine


class EngineTest(unittest.TestCase):
    def test_recommendations_user_not_in_db(self):
        fake_user_id = 'notarealuserid'
        with self.assertRaises(Exception) as ex:
            engine.recommend_user(fake_user_id, 5)
        self.assertEqual(str(ex.exception),
                         'User ' + fake_user_id + ' is not in the database')

    def test_recommendations_no_user_provided(self):
        user_id = None
        with self.assertRaises(Exception) as ex:
            engine.recommend_user(user_id, 5)
        self.assertEqual(str(ex.exception), 'Please provide a user id')

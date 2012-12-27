import datetime
import unittest2 as unittest

import util


class TestUtils(unittest.TestCase):

    def test_get_term_id(self):
        def assert_term_equals(expected_term_id, year, month, day):
            the_date = datetime.datetime(year=year, month=month, day=day)
            term_id = util.get_term_id_for_date(the_date)
            self.assertEqual(expected_term_id, term_id)

        # Test first day of terms
        assert_term_equals('2345_01', year=2345, month=1, day=1)
        assert_term_equals('2345_05', year=2345, month=5, day=1)
        assert_term_equals('2345_09', year=2345, month=9, day=1)

        # Test middle of terms
        assert_term_equals('2345_05', year=2345, month=7, day=1)
        assert_term_equals('2345_09', year=2345, month=10, day=3)

        # Test last day of terms
        assert_term_equals('2345_01', year=2345, month=4, day=30)
        assert_term_equals('2345_05', year=2345, month=8, day=31)
        assert_term_equals('2345_09', year=2345, month=12, day=31)


# TODO(david): Use a test runner to run all *_test.py files
if __name__ == '__main__':
    unittest.main()

import datetime
import unittest

import bson
import freezegun

import rmc.shared.util as util


class UtilTest(unittest.TestCase):
    def test_json_loads(self):
        self.assertEquals({'foo': 1}, util.json_loads('{"foo":1}'))

    def test_json_dumps_prevents_xss(self):
        self.assertEquals('["<\\/script>"]', util.json_dumps(["</script>"]))

    def test_dict_to_list(self):
        self.assertEquals(
            [{'name': 'a', 'aprop': 1}, {'name': 'b', 'bprop': 2}],
            util.dict_to_list({'a': {'aprop': 1}, 'b': {'bprop': 2}})
        )

    def test_get_current_term_id(self):
        def assert_term_equals(expected_term_id, year, month, day):
            the_date = datetime.datetime(year=year, month=month, day=day)
            with freezegun.freeze_time(the_date.strftime("%c")):
                self.assertEqual(expected_term_id, util.get_current_term_id())

        assert_term_equals('2345_09', year=2345, month=9, day=1)

    def test_get_term_id_for_date(self):
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

    @unittest.skip("TODO")
    def test_pnormaldist(self):
        pass

    @unittest.skip("TODO")
    def test_get_sorting_score(self):
        pass

    def test_flatten_dict(self):
        self.assertEquals(
            {'foo': '{"bar": {"baz": 1}}', 'obj': '519cf517943a41529299831c'},
            util.flatten_dict({
                'foo': {
                    'bar': {
                        'baz': 1
                    }
                },
                'obj': bson.ObjectId('519cf517943a41529299831c')
            })
        )

    @unittest.skip("TODO")
    def test_eastern_to_utc(self):
        pass

    @unittest.skip("TODO")
    def test_utc_date(self):
        pass

    def test_to_dict(self):
        class Bar(object):
            def to_dict(self):
                return {
                    'prop': 'val'
                }

        class Foo(object):
            x = 1
            y = 2
            z = 7
            bar = Bar()
            bar_list = [Bar(), Bar()]

        self.assertEqual(
            {
                'x': 1,
                'y': 2,
                'bar': {'prop': 'val'},
                'bar_list': [{'prop': 'val'}, {'prop': 'val'}]
            },
            util.to_dict(Foo(), ['x', 'y', 'bar', 'bar_list'])
        )

import datetime

import freezegun

import rmc.models as m
import rmc.test.lib as testlib


class TermTest(testlib.ModelTestCase):
    def test_get_next_term_id(self):
        get_next = m.Term.get_next_term_id_from_term_id
        self.assertEquals('2009_05', get_next('2009_01'))
        self.assertEquals('2009_09', get_next('2009_05'))
        self.assertEquals('2010_01', get_next('2009_09'))

        # And just for this term... I need this to work :P
        self.assertEquals('2014_01', get_next('2013_09'))

    def test_convert_between_quest_id_and_term_id(self):
        def assertConverts(term_id, quest_id):
            self.assertEquals(quest_id,
                    m.Term.get_quest_id_from_term_id(term_id))
            self.assertEquals(term_id,
                    m.Term.get_term_id_from_quest_id(quest_id))

        assertConverts('1999_09', '0999')
        assertConverts('2012_09', '1129')
        assertConverts('2013_01', '1131')
        assertConverts('2013_05', '1135')
        assertConverts('2013_09', '1139')
        assertConverts('2014_01', '1141')
        assertConverts('2100_01', '2001')

    def test_convert_between_id_and_year_season(self):
        def assertConverts(term_id, year, season):
            self.assertEquals(term_id, m.Term.get_id_from_year_season(year,
                    season))
            self.assertEquals(year, m.Term.get_year_from_id(term_id))
            self.assertEquals(season, m.Term.get_season_from_id(term_id))

        assertConverts('1999_09', 1999, 'Fall')
        assertConverts('2012_09', 2012, 'Fall')
        assertConverts('2013_01', 2013, 'Winter')
        assertConverts('2013_05', 2013, 'Spring')
        assertConverts('2013_09', 2013, 'Fall')
        assertConverts('2014_01', 2014, 'Winter')
        assertConverts('2100_01', 2100, 'Winter')

    def test_get_date_from_term_id(self):
        get_date = m.Term.get_date_from_term_id

        def make_date(year, month):
            return datetime.datetime(year=year, month=month, day=1)

        self.assertEquals(make_date(1991, 1), get_date('1991_01'))
        self.assertEquals(make_date(2014, 1), get_date('2014_01'))
        self.assertEquals(make_date(2014, 5), get_date('2014_05'))
        self.assertEquals(make_date(2014, 9), get_date('2014_09'))

    def test_get_current_term_finished_fraction(self):
        def assert_correct_fraction(expected_fraction, date_tuple):
            year, month, day = date_tuple
            the_date = datetime.datetime(year=year, month=month, day=day)
            with freezegun.freeze_time(the_date.strftime('%c')):
                self.assertAlmostEquals(expected_fraction,
                    m.Term.get_current_term_finished_fraction(), 3)

        # There are 120 days between term 2014_01 and 2014_05
        assert_correct_fraction(0, (2014, 1, 1))
        assert_correct_fraction(7.0 / 120, (2014, 1, 8))
        assert_correct_fraction(30.0 / 120, (2014, 1, 31))
        assert_correct_fraction(44.0 / 120, (2014, 2, 14))
        assert_correct_fraction(72.0 / 120, (2014, 3, 14))
        assert_correct_fraction(119.0 / 120, (2014, 4, 30))

    # TODO(david): Moar tests

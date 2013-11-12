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

    # TODO(david): Moar tests

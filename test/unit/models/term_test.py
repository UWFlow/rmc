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

    def test_get_quest_id_from_term_id(self):
        self.assertEquals('1129', m.Term.get_quest_id_from_term_id('2012_09'))
        self.assertEquals('1131', m.Term.get_quest_id_from_term_id('2013_01'))
        self.assertEquals('1135', m.Term.get_quest_id_from_term_id('2013_05'))
        self.assertEquals('1139', m.Term.get_quest_id_from_term_id('2013_09'))
        self.assertEquals('1141', m.Term.get_quest_id_from_term_id('2014_01'))

    # TODO(david): Moar tests

"""Basically, this is currently just a class of static utility methods to deal
with term identifiers.

Assume everything in this file is Waterloo-specific.
"""

import datetime
import logging

import mongoengine as me

import rmc.shared.util as util

# TODO(david): Make naming consistent... prefix all methods with a verb (eg.
#     get).
# TODO(david): Lots of easy unit tests for methods here.

# TODO(jlfwong): From what I can tell, this isn't being used as an actual model
# any more - it's just being used as a collection of static methods
class Term(me.Document):

    SHORTLIST_TERM_ID = '9999_99'

    SEASONS = ['Winter', 'Spring', 'Fall']
    INVALID_TERM_MONTH = 13

    # TODO(mack): should month be 0 or 1 offset?
    # eg. 2011_05 => term that began May, 2011 => Spring 2011
    id = me.StringField(primary_key=True)

    @staticmethod
    def get_year_from_id(tid):
        return int(tid[:4])

    @property
    def year(self):
        return Term.get_year_from_id(self.id)

    @staticmethod
    def get_month_from_id(term_id):
        return int(term_id[5:])

    @staticmethod
    def get_season_from_id(tid):
        # currently specific to waterloo
        month = Term.get_month_from_id(tid)
        if (month == Term.INVALID_TERM_MONTH):
            return ''
        return Term.SEASONS[(month-1) / 4]

    @property
    def season(self):
        return Term.get_season_from_id(self.id)

    @staticmethod
    def name_from_id(tid):
        if tid == Term.SHORTLIST_TERM_ID:
            return 'Shortlist'
        else:
            return '%s %d' % (Term.get_season_from_id(tid),
                    Term.get_year_from_id(tid))

    @property
    def name(self):
        return Term.name_from_id(self.id)

    @staticmethod
    def get_id_from_year_month(year, month):
        if month not in [1, 5, 9, Term.INVALID_TERM_MONTH]:
            raise "Invalid month: %s" % month

        return '%s_%02d' % (year, month)

    @staticmethod
    def get_id_from_year_season(year, season):
        season = season.lower()
        month = Term.INVALID_TERM_MONTH
        for idx, ssn in enumerate(Term.SEASONS):
            if ssn.lower() == season:
                month = idx * 4 + 1

        if month == Term.INVALID_TERM_MONTH:
            logging.warn("Term: Invalid seasons '%s'. Using month %d in term id" % (season, Term.INVALID_TERM_MONTH))

        return Term.get_id_from_year_month(year, month)

    @staticmethod
    def id_from_name(name):
        try:
            season, year = name.split()
        except ValueError:
            logging.error("term.py: id_from_name(cls, '%s'). Fix me!" % (name))
            # Special place holder so we can correct it later
            return '8888_88'

        return Term.get_id_from_year_season(year, season)

    @classmethod
    def is_shortlist_term(cls, term_id):
        return term_id == Term.SHORTLIST_TERM_ID

    @staticmethod
    def get_current_term_id():
        return util.get_current_term_id()

    @staticmethod
    def get_next_term_id():
        return Term.get_next_term_id_from_term_id(Term.get_current_term_id())

    @staticmethod
    def get_next_term_id_from_year_month(year, month):
        year = int(year)
        month = int(month)

        if month == 9:
            year += 1
            month = 1
        else:
            month += 4

        return Term.get_id_from_year_month(year, month)

    @staticmethod
    def get_date_from_term_id(term_id):
        """Return a datetime from the term_id, using starting from the first day
        of the month.
        """
        year, month = map(lambda x: int(x), term_id.split('_'))
        return datetime.datetime(year=year, month=month, day=1)

    @staticmethod
    def get_current_term_percent_finished():
        """Return a percent indicating how much time has passed in the current
        term.
        """
        term_id = Term.get_current_term_id()
        next_term_id = Term.get_next_term_id_from_term_id(term_id)

        current_term = Term.get_date_from_term_id(term_id)
        next_term = Term.get_date_from_term_id(next_term_id)
        now = datetime.datetime.now()

        term_length = next_term - current_term
        elapsed_length = now - current_term

        return 1.0 * elapsed_length.days / term_length.days

    @staticmethod
    def get_next_term_id_from_term_id(term_id):
        year = Term.get_year_from_id(term_id)
        month = Term.get_month_from_id(term_id)
        return Term.get_next_term_id_from_year_month(year, month)

    @staticmethod
    def get_quest_id_from_term_id(term_id):
        """Convert a term ID from our format to Quest's funky 4-digit code. Eg.
        2013_09 => 1139, 2014_01 => 1141.
        """
        year = Term.get_year_from_id(term_id)
        month = Term.get_month_from_id(term_id)
        return '%03d%d' % (year - 1900, month)

    @staticmethod
    def get_term_id_from_quest_id(quest_term_id):
        """Convert Quest's funky 4-digit term code to our term ID.
        Eg. 1139 => 2013_09, 1141 => 2014_01.
        """
        quest_term_id = int(quest_term_id)
        return '%04d_%02d' % (1900 + (quest_term_id / 10), quest_term_id % 10)

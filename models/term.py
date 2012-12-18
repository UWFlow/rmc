import mongoengine as me
import logging

class Term(me.Document):

    SHORTLIST_TERM_ID = '9999_99'

    SEASONS = ['Winter', 'Spring', 'Fall']
    INVALID_TERM_MONTH = 13

    # TODO(mack): should month be 0 or 1 offset?
    # eg. 2011_05 => term that began May, 2011 => Spring 2011
    id = me.StringField(primary_key=True)

    @staticmethod
    def year_from_id(tid):
        return int(tid[:4])

    @property
    def year(self):
        return Term.year_from_id(self.id)

    @staticmethod
    def season_from_id(tid):
        # currently specific to waterloo
        month = int(tid[5:])
        if (month == Term.INVALID_TERM_MONTH):
            return ''
        return Term.SEASONS[(month-1) / 4]

    @property
    def season(self):
        return Term.season_from_id(self.id)

    @staticmethod
    def name_from_id(tid):
        if tid == Term.SHORTLIST_TERM_ID:
            return 'Shortlist'
        else:
            return '%s %d' % (Term.season_from_id(tid), Term.year_from_id(tid))

    @property
    def name(self):
        return Term.name_from_id(self.id)

    @staticmethod
    def id_from_year_season(year, season):
        season = season.lower()
        month = Term.INVALID_TERM_MONTH
        for idx, ssn in enumerate(Term.SEASONS):
            if ssn.lower() == season:
                month = idx * 4 + 1

        if month == Term.INVALID_TERM_MONTH:
            logging.warn("Term: Invalid seasons '%s'. Using month %d in term id" % (season, Term.INVALID_TERM_MONTH))

        return ('%s %02d' % (year, month)).replace(' ', '_')

    # TODO(Sandy): Deprecate this
    @classmethod
    def get_id_from_year_season(cls, year, season):
        return Term.id_from_year_season(year, season)

    @staticmethod
    def id_from_name(name):
        try:
            season, year = name.split()
        except ValueError:
            logging.error("term.py: id_from_name(cls, '%s'). Fix me!" % (name))
            # Special place holder so we can correct it later
            return '8888_88'

        return Term.id_from_year_season(year, season)

    @classmethod
    def is_shortlist_term(cls, term_id):
        if term_id == Term.SHORTLIST_TERM_ID:
            return True
        return False

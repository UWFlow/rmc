import mongoengine as me

class Term(me.Document):

    SHORTLIST_TERM_ID = '9999_99'
    PAST_TERM_ID = '0000_00'

    SEASONS = ['Winter', 'Spring', 'Fall']
    INVALID_TERM_MONTH = 13

    # TODO(mack): should month be 0 or 1 offset?
    # eg. 2011_05 => term that began May, 2011 => Spring 2011
    id = me.StringField(primary_key=True)

    @property
    def year(self):
        return int(self.id[:4])

    @property
    def season(self):
        # currently specific to waterloo
        month = int(self.id[5:])
        if (month == Term.INVALID_TERM_MONTH):
            return ''
        return Term.SEASONS[(month-1) / 4]

    @property
    def name(self):
        if self.id == self.SHORTLIST_TERM_ID:
            return 'My Shortlist'
        elif self.id == self.PAST_TERM_ID:
            return ''
        else:
            return '%s %d' % (self.season, self.year)

    @classmethod
    def get_id_from_year_season(cls, year, season):
        season = season.lower()
        month = Term.INVALID_TERM_MONTH
        for idx, ssn in enumerate(Term.SEASONS):
            if ssn.lower() == season:
                month = idx * 4 + 1

        if month == Term.INVALID_TERM_MONTH:
            print "Term: Invalid seasons '%s'. Using month %d in term id" % (season, Term.INVALID_TERM_MONTH)

        return ('%s %02d' % (year, month)).replace(' ', '_')

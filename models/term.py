import mongoengine as me

class Term(me.Document):

    SEASONS = ['Winter', 'Spring', 'Fall']

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
        return Term.SEASONS[(month-1) / 4]

    @property
    def name(self):
        return '%s %d' % (self.season, self.year)

    @classmethod
    def get_id_from_year_season(cls, year, season):
        season = season.lower()
        month = 13
        for idx, ssn in enumerate(Term.SEASONS):
            if ssn.lower() == season:
                month = idx * 4 + 1

        if month == 13:
            print "Term: Invalid seasons '%s'. Using month 13 in term id" % season

        return ('%s %s' % (year, month)).replace(' ', '_')

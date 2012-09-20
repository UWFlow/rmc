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





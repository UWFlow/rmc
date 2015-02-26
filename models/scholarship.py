import mongoengine as me

class Scholarship(me.Document):
    id = me.StringField(primary_key=True)

    # eg. Geoffrey F. Butler Award
    title = me.StringField()

    description = me.StringField()

    # e.g. ["Canadian citizen", "Permanent resident"]
    citizenship = me.ListField(me.StringField())

    # e.g. ["Arts", "Drama and Speech Communication", "Fine Arts", "Music"]
    programs = me.ListField(me.StringField())

    # e.g. ["Minimum average above 80%", "Involvment in extracurriculars"]
    eligibility = me.ListField(me.StringField())

    # e.g. ["Complete the General Undergraduate Award Application form.",
    #       "Attach a letter explaining how you meet the award criteria."]
    instructions = me.ListField(me.StringField())

    # e.g. ["Year One, Year Two]
    enrollment_year = me.ListField(me.StringField())

    # e.g. "Please contact the Undergraduate Awards Assistant if you have
    #       questions about this award."
    contact = me.StringField()

    # e.g. "https://uwaterloo.ca/student-awards-financial-aid/undergraduate-
    #       awards/crosslink-technology-inc-scholarship"
    link = me.StringField()

    def to_dict(self):
        """Serialize data to be sent to the client"""

        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'eligibility': self.eligibility,
            'enrollment_year': self.enrollment_year,
            'link': self.link,
        }

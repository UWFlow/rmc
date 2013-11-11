import mongoengine as me


class SectionMeeting(me.EmbeddedDocument):
    """A set of consistent weekly times and a location that a section will meet
    at.

    Each section has one or more of these meetings.
    """

    # eg. 14:30
    # TODO(david): Change this to be a numerical integer value to support
    #     querying
    start_time = me.StringField()
    end_time = me.StringField()

    # eg. ['T', 'Th']
    days = me.ListField(me.StringField(
            choices=['M', 'T', 'W', 'Th', 'F', 'S', 'Su']))

    # eg. 9/20 or null (meaning this class is held for the entire term)
    # Note that granularity for this field is a day; {start,end}_time has
    # time-of-day granularity.
    # TODO(david): Using None to denote entire term is really stupid and
    #     requires special-casing (and makes querying harder). Ask Kartik to
    #     scrape term begin/end dates so we can actually fill these out with
    #     something sensible.
    start_date = me.DateTimeField()
    end_date = me.DateTimeField()

    # eg. MC
    building = me.StringField()

    # eg. 4020
    room = me.StringField()

    # eg. byron_weber_becker or null
    # TODO(david): This should actually be a list in case of multiple
    #     instructors. This is just a single ID to match the format of
    #     UserScheduleItem, which should be changed consistently.
    prof_id = me.StringField()

    is_tba = me.BooleanField()
    is_cancelled = me.BooleanField()
    is_closed = me.BooleanField()


class Section(me.Document):
    """An offering of a course for a given term.

    See https://uwaterloo.ca/quest/undergraduate-students/schedule-of-classes-definitions
    for Waterloo's definition of some of these fields.
    """

    meta = {
        'indexes': [
            ('course_id', 'term_id')
        ],
    }

    # eg. earth121l
    course_id = me.StringField(required=True,
            unique_with=['term_id', 'section_type', 'section_num'])

    # eg. 2013_09. Note that this is our term ID, not Quest's 4-digit ID.
    term_id = me.StringField(required=True)

    # eg. LEC, TUT, EXAM. Note uppercase.
    section_type = me.StringField(required=True)

    # eg. 001
    section_num = me.StringField(required=True)

    # eg. UW U
    campus = me.StringField()

    # eg. 350
    enrollment_capacity = me.IntField(min_value=0)

    # eg. 157
    enrollment_total = me.IntField(min_value=0)

    # eg. 0
    waiting_capacity = me.IntField(min_value=0)

    # eg. 0
    waiting_total = me.IntField(min_value=0)

    # Meeting times (usually there's just one... eg. TTh @ RCH 101 8:30 - 9:50)
    meetings = me.ListField(me.EmbeddedDocumentField(SectionMeeting))

    # eg. "4779" (Quest-specific)
    class_num = me.StringField()

    # eg. 0.5
    units = me.FloatField(min_value=0.0)

    # eg. "Lecture can be taken without Lab."
    note = me.StringField()

    last_updated = me.DateTimeField()

    # TODO(david): Reserves info (we don't show this at the moment).

    # TODO(david): Do we want associated class crap
    # https://uwaterloo.ca/quest/undergraduate-students/glossary-of-terms#associated class (assoc. class)

    def __repr__(self):
        return "<Section: %s, %s, %s %s>" % (
            self.course_id,
            self.term_id,
            self.section_type,
            self.section_num,
        )

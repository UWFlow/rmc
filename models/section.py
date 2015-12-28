import mongoengine as me

import term
from rmc.shared import util


class SectionMeeting(me.EmbeddedDocument):
    """A set of consistent weekly times and a location that a section will meet
    at.

    Each section has one or more of these meetings.
    """

    # Seconds since 0:00:00. eg. 52200 (2:30 pm)
    start_seconds = me.IntField(min_value=0, max_value=60 * 60 * 24)
    end_seconds = me.IntField(min_value=0, max_value=60 * 60 * 24)

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

    TO_DICT_FIELDS = ['start_seconds', 'end_seconds', 'days', 'start_date',
            'end_date', 'building', 'room', 'prof_id', 'is_tba',
            'is_cancelled', 'is_closed']

    def to_dict(self):
        return util.to_dict(self, SectionMeeting.TO_DICT_FIELDS)


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

    # Uuid used to keep track of which sections were updated
    # See https://github.com/UWFlow/rmc/issues/255 for more details
    update_id = me.StringField()

    # TODO(david): Reserves info (we don't show this at the moment).

    # TODO(david): Do we want associated class crap
    # https://uwaterloo.ca/quest/undergraduate-students/glossary-of-terms#associated class (assoc. class)

    TO_DICT_FIELDS = ['id', 'course_id', 'term_id', 'section_type',
            'section_num', 'campus', 'enrollment_capacity', 'enrollment_total',
            'waiting_capacity', 'waiting_total', 'meetings', 'class_num',
            'units', 'note', 'last_updated']

    def to_dict(self):
        return util.to_dict(self, Section.TO_DICT_FIELDS)

    def __repr__(self):
        return "<Section: %s, %s, %s %s>" % (
            self.course_id,
            self.term_id,
            self.section_type,
            self.section_num,
        )

    @staticmethod
    def get_for_course_and_terms(course_id, term_ids):
        """Get all sections for a given course and the given term IDs."""
        return Section.objects(course_id=course_id, term_id__in=term_ids)

    @staticmethod
    def get_for_course_and_recent_terms(course_id):
        """Get all sections for a given course for this current term and the
        next term.
        """
        term_ids = [term.Term.get_current_term_id(),
                    term.Term.get_next_term_id()]
        return Section.get_for_course_and_terms(course_id, term_ids)

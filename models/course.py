import mongoengine as me
import re

import professor
import rating
from rmc.shared import util

class Course(me.Document):
    meta = {
        'indexes': [
            '_keywords',
            'interest.rating',
            'interest.count',
            'easiness.rating',
            'easiness.count',
            'usefulness.rating',
            'usefulness.count',
            'overall.rating',
            'overall.count',
        ],
    }

    # eg. earth121l
    id = me.StringField(primary_key=True)

    # eg. earth
    department_id = me.StringField(required=True)

    # eg. 121l
    number = me.StringField(required=True)

    # eg. Introductory Earth Sciences Laboratory 1
    name = me.StringField(required=True)

    # Description about the course
    description = me.StringField(required=True)

    easiness = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    interest = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    usefulness = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())
    overall = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())

    professor_ids = me.ListField(me.StringField())

    # eg. ['earth', '121l', 'earth121l', 'Introductory', 'Earth' 'Sciences', 'Laboratory', '1']
    _keywords = me.ListField(me.StringField(), required=True)

    @property
    def code(self):
        matches = re.findall(r'^([a-z]+)(.*)$', self.id)[0]
        department = matches[0]
        number = matches[1]
        return '%s %s' % (department.upper(), number.upper())

    def save(self, *args, **kwargs):
        if not self.id:
            # id should not be set during first save
            self.id = self.department_id + self.number

        super(Course, self).save(*args, **kwargs)

    def get_ratings(self):
        return {
            'interest': self.interest.to_dict(),
            'usefulness': self.usefulness.to_dict(),
            'easiness': self.easiness.to_dict(),
        }

    # TODO(david): Cache function result
    def get_professors(course, expanded=False):
        professors = professor.Professor.objects(
                id__in=course.professor_ids)

        if expanded:
            return professors.all()
        else:
            return professors.only('id', 'first_name', 'last_name')

    def to_dict(self):
        """Returns information about a course to be sent down an API.

        Args:
            course: The course object.
        """

        # TODO(mack): to not nest Professor in Course
        professors = [{'id': p.id, 'name': p.name} for p in
                self.get_professors()]

        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            #'availFall': bool(int(course['availFall'])),
            #'availSpring': bool(int(course['availSpring'])),
            #'availWinter': bool(int(course['availWinter'])),
            # TODO(mack): create user models for friends
            #'friends': [1647810326, 518430508, 541400376],
            'ratings': util.dict_to_list(self.get_ratings()),
            'overall': self.overall.to_dict(),
            'professors': professors,
        }

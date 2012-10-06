import mongoengine as me
import re

import professor
import rating
from rmc.shared import util
import user_course as _user_course

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
    # TODO(mack): deprecated
    def get_professors(course, expanded=False):
        professors = professor.Professor.objects(
                id__in=course.professor_ids)

        if expanded:
            return professors.all()
        else:
            return professors.only('id', 'first_name', 'last_name')

    @classmethod
    def get_course_and_user_course_dicts(cls, courses, current_user,
            include_friends=False, full_user_courses=False):

        course_dicts = []
        for course in courses:
            course_dicts.append(course.to_dict())

        if not current_user:
            return course_dicts, []


        friend_ids = []
        if include_friends:
            friend_ids = current_user.friend_ids

        course_ids = [c.id for c in courses]
        if full_user_courses:
            ucs = _user_course.UserCourse.objects(
                user_id__in=[current_user.id] + friend_ids,
                course_id__in=course_ids,
            )
            ucs = list(ucs)
        else:
            ucs = _user_course.UserCourse.objects(
                user_id__in=friend_ids,
                course_id__in=course_ids,
            ).only('term_id', 'user_id', 'course_id')

            # TODO(mack): optimize to not always get full user course
            # for current_user
            current_uc = _user_course.UserCourse.objects(
                user_id=current_user.id,
                course_id__in=course_ids,
            )
            ucs = list(ucs) + list(current_uc)

        current_user_course_ids = set(current_user.course_history)

        current_user_course_by_course = {}
        friend_user_courses_by_course = {}
        for uc in ucs:
            if uc.id in current_user_course_ids:
                current_user_course_by_course[uc.course_id] = uc.to_dict()
            elif include_friends:
                friend_user_courses_by_course.setdefault(
                        uc.course_id, []).append(uc.to_dict())

        for course_dict in course_dicts:
            current_uc = current_user_course_by_course.get(
                    course_dict['id'])
            current_uc_id = current_uc['id'] if current_uc else None
            course_dict['user_course_id'] = current_uc_id

            if include_friends:
                friend_ucs = friend_user_courses_by_course.get(
                        course_dict['id'], [])
                friend_uc_ids = [uc['id'] for uc in friend_ucs]
                course_dict['friend_user_course_ids'] = friend_uc_ids

        all_user_courses = current_user_course_by_course.values()
        if include_friends:
            for user_courses in friend_user_courses_by_course.values():
                all_user_courses.extend(user_courses)

        return course_dicts, all_user_courses



    def to_dict(self):
        """Returns information about a course to be sent down an API.

        Args:
            course: The course object.
        """

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
            'professor_ids': self.professor_ids,
        }

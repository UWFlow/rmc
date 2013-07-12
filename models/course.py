import re
import collections

import mongoengine as me

import professor
import rating
from rmc.shared import util
import user_course as _user_course
import user as _user

class GenderStats(me.EmbeddedDocument):
    male_count = me.IntField(default=0)
    female_count = me.IntField(default=0)
    other_count = me.IntField(default=0)

    def to_dict(self):
        return {
            'male': self.male_count,
            'female': self.female_count,
            'other': self.other_count
        }

    def __repr__(self):
        return "GenderStats(male_count=%r, female_count=%r, other_count=%r)" % (
            self.male_count, self.female_count, self.other_count
        )

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
    # TODO(mack): deprecate overall rating
    overall = me.EmbeddedDocumentField(rating.AggregateRating, default=rating.AggregateRating())

    gender_stats = me.EmbeddedDocumentField(GenderStats, default=GenderStats())

    professor_ids = me.ListField(me.StringField())

    antireqs = me.StringField()
    coreqs = me.StringField()
    prereqs = me.StringField()

    # NOTE: The word term is overloaded based on where it's used. Here, it mean
    # which terms of the year is the course being offered?
    # e.g. ['01', '05', '09']
    terms_offered = me.ListField(me.StringField())

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
            'easiness': self.easiness.to_dict()
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

    def get_all_user_courses(self):
        return _user_course.UserCourse.objects(course_id=self.id)

    def get_all_users(self):
        ucs = self.get_all_user_courses().only('user_id')
        user_course_ids = [uc.user_id for uc in ucs]

        return _user.User.objects(id__in=user_course_ids)

    def get_current_gender_stats(self):
        """Find the exact current gender stats for the course.

        This information is based exclusively on UserCourses.

        For performance reasons, use the cached Course.gender_info instead.
        """
        users = self.get_all_users().only('gender')
        histogram = collections.Counter([u.gender for u in users])

        return GenderStats(
            male_count=histogram.get('male', 0),
            female_count=histogram.get('female', 0),
            other_count=histogram.get(None, 0)
        )

    # TODO(mack): this function is way too overloaded, even to separate into
    # multiple functions based on usage
    @classmethod
    def get_course_and_user_course_dicts(cls, courses, current_user,
            include_friends=False, include_all_users=False,
            full_user_courses=False):

        limited_user_course_fields = [
                'program_year_id', 'term_id', 'user_id', 'course_id']

        course_dicts = [course.to_dict() for course in courses]
        course_ids = [c['id'] for c in course_dicts]

        ucs = []
        if not current_user:
            if include_all_users:
                ucs = _user_course.UserCourse.objects(
                        course_id__in=course_ids)
                if not full_user_courses:
                    ucs.only(**limited_user_course_fields)

                ucs = list(ucs)
                uc_dicts = [uc.to_dict() for uc in ucs]
                return course_dicts, uc_dicts, ucs
            else:
                return course_dicts, [], []

        uc_dicts = []
        if include_all_users or include_friends:
            query = {
                'course_id__in': course_ids,
            }

            # If we're just including friends
            if not include_all_users:
                query['user_id__in'] = current_user.friend_ids

            if full_user_courses:
                if not include_all_users:
                    query.setdefault('user_id__in', []).append(current_user.id)
                ucs = list(_user_course.UserCourse.objects(**query))
                uc_dicts = [uc.to_dict() for uc in ucs]
            else:
                ucs = list(_user_course.UserCourse.objects(**query).only(
                        *limited_user_course_fields))
                friend_uc_fields = ['id', 'user_id', 'course_id', 'term_name']
                uc_dicts = [uc.to_dict(friend_uc_fields) for uc in ucs]

        # TODO(mack): optimize to not always get full user course
        # for current_user
        current_ucs = list(_user_course.UserCourse.objects(
            user_id=current_user.id,
            course_id__in=course_ids,
            id__nin=[uc_dict['id'] for uc_dict in uc_dicts],
        ))
        ucs += current_ucs
        uc_dicts += [uc.to_dict() for uc in current_ucs]

        current_user_course_by_course = {}
        friend_user_courses_by_course = {}
        current_friends_set = set(current_user.friend_ids)
        current_user_course_ids = set(current_user.course_history)

        for uc_dict in uc_dicts:
            if uc_dict['id'] in current_user_course_ids:
                current_user_course_by_course[uc_dict['course_id']] = uc_dict
            elif include_friends:
                if uc_dict['user_id'] in current_friends_set:
                    friend_user_courses_by_course.setdefault(
                            uc_dict['course_id'], []).append(uc_dict)

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

        return course_dicts, uc_dicts, ucs

    @classmethod
    def code_to_id(cls, course_code):
        return "".join(course_code.split()).lower()

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
            'terms_offered': self.terms_offered,
            'gender_stats': self.gender_stats.to_dict(),
            # TODO(mack): create user models for friends
            #'friends': [1647810326, 518430508, 541400376],
            'ratings': util.dict_to_list(self.get_ratings()),
            'overall': self.overall.to_dict(),
            'professor_ids': self.professor_ids,
            'prereqs': self.prereqs,
        }

    def __repr__(self):
        return "<Course: %s>" % self.code

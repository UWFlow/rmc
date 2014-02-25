import collections
import logging
import re

import mongoengine as me
import pymongo

import review
import rating
import section
import term
from rmc.shared import rmclogger
from rmc.shared import util
import user_course as _user_course


# TODO(david): Add usefulness
_SORT_MODES = [
    {
        'name': 'popular',
        'direction': pymongo.DESCENDING,
        'field': 'interest.count'
    },
    {
        'name': 'friends_taken',
        'direction': pymongo.DESCENDING,
        'field': 'custom'
    },
    {
        'name': 'interesting',
        'direction': pymongo.DESCENDING,
        'field': 'interest.sorting_score'
    },
    {
        'name': 'easy',
        'direction': pymongo.DESCENDING,
        'field': 'easiness.sorting_score'
    },
    {
        'name': 'hard',
        'direction': pymongo.ASCENDING,
        'field': 'easiness.sorting_score'
    },
    {
        'name': 'course code',
        'direction': pymongo.ASCENDING,
        'field': 'id'
    },
]

_SORT_MODES_BY_NAME = {sm['name']: sm for sm in _SORT_MODES}

# Special sort instructions are needed for these sort modes
# TODO(Sandy): deprecate overall and add usefulness
_RATING_SORT_MODES = ['overall', 'interesting', 'easy', 'hard']


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

    easiness = me.EmbeddedDocumentField(rating.AggregateRating,
                                        default=rating.AggregateRating())
    interest = me.EmbeddedDocumentField(rating.AggregateRating,
                                        default=rating.AggregateRating())
    usefulness = me.EmbeddedDocumentField(rating.AggregateRating,
                                          default=rating.AggregateRating())
    # TODO(mack): deprecate overall rating
    overall = me.EmbeddedDocumentField(rating.AggregateRating,
                                       default=rating.AggregateRating())

    professor_ids = me.ListField(me.StringField())

    antireqs = me.StringField()
    coreqs = me.StringField()
    prereqs = me.StringField()

    # NOTE: The word term is overloaded based on where it's used. Here, it mean
    # which terms of the year is the course being offered?
    # NOTE: THIS FIELD IS ***DEPRECATED***, because the data source we get
    #     info about this is not reliable. There may not exist such reliable
    #     data at all -- course offerings are decided on an annual basis.
    # TODO(david): Remove this field and replace it with info from sections.
    # e.g. ['01', '05', '09']
    terms_offered = me.ListField(me.StringField())

    # eg. ['earth', '121l', 'earth121l', 'Introductory',
    #      'Earth' 'Sciences', 'Laboratory', '1']
    _keywords = me.ListField(me.StringField(), required=True)

    SORT_MODES = _SORT_MODES

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
        # Ordered for consistency with CourseReview.rating_fields; see #109.
        return collections.OrderedDict([
            ('usefulness', self.usefulness.to_dict()),
            ('easiness', self.easiness.to_dict()),
            ('interest', self.interest.to_dict()),
        ])

    def get_reviews(self, current_user=None, user_courses=None):
        """Return a list of all user reviews ("tips") about this course.

        Does not include professor reviews.

        Arguments:
            current_user: The current user. Used for revealing more author
                information if possible (eg. reviews written by friends who
                allow their friends to know that they wrote it).
            user_courses: An optional list of all user_courses that's
                associated with this course to speed up this function.
        """
        if not user_courses:
            limit_fields = ['course_id', 'user_id', 'course_review']
            user_courses = _user_course.UserCourse.objects(
                    course_id=self.id).only(*limit_fields)

        reviews = []
        for uc in user_courses:
            if (len(uc.course_review.comment) <
                    review.CourseReview.MIN_REVIEW_LENGTH):
                continue

            reviews.append(uc.course_review.to_dict(current_user, uc.user_id))

        # Filter out old reviews if we have enough results.
        date_getter = lambda review: review['comment_date']
        reviews = util.publicly_visible_ratings_and_reviews_filter(
                reviews, date_getter, util.MIN_NUM_REVIEWS)

        return reviews

    # TODO(mack): this function is way too overloaded, even to separate into
    # multiple functions based on usage
    @classmethod
    def get_course_and_user_course_dicts(cls, courses, current_user,
            include_friends=False, include_all_users=False,
            full_user_courses=False, include_sections=False):

        limited_user_course_fields = [
                'program_year_id', 'term_id', 'user_id', 'course_id']

        course_dicts = [course.to_dict() for course in courses]
        course_ids = [c['id'] for c in course_dicts]

        if include_sections:
            for course_dict in course_dicts:
                # By default, we'll send down section info for current and next
                # term for each course we return.
                sections = section.Section.get_for_course_and_recent_terms(
                        course_dict['id'])
                course_dict['sections'] = [s.to_dict() for s in sections]

        ucs = []
        if not current_user:
            if include_all_users:
                ucs = _user_course.UserCourse.objects(
                        course_id__in=course_ids)
                if not full_user_courses:
                    ucs.only(*limited_user_course_fields)

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
                friend_uc_fields = ['id', 'user_id', 'course_id', 'term_id',
                        'term_name']
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

    @staticmethod
    def code_to_id(course_code):
        return "".join(course_code.split()).lower()

    @staticmethod
    def search(params, current_user):
        """Search for courses based on various parameters.

        Arguments:
            params: Dict of search parameters (all optional):
                keywords: Keywords to search on
                sort_mode: Name of a sort mode. See Course.SORT_MODES.
                direction: 1 for ascending, -1 for descending
                count: Max items to return (aka. limit)
                offset: Index of first search result to return (aka. skip)
                exclude_taken_courses: "yes" to exclude courses current_user
                    has taken.
            current_user: The user making the request.

        Returns:
            A tuple (courses, has_more):
                courses: Search results
                has_more: Whether there could be more search results
        """
        keywords = params.get('keywords')
        sort_mode = params.get('sort_mode', 'popular')
        default_direction = _SORT_MODES_BY_NAME[sort_mode]['direction']
        direction = int(params.get('direction', default_direction))
        count = int(params.get('count', 10))
        offset = int(params.get('offset', 0))
        exclude_taken_courses = params.get('exclude_taken_courses')

        # TODO(david): These logging things should be done asynchronously
        rmclogger.log_event(
            rmclogger.LOG_CATEGORY_COURSE_SEARCH,
            rmclogger.LOG_EVENT_SEARCH_PARAMS,
            params
        )

        # XXX clean up all code beneath

        filters = {}
        if keywords:
            # Clean keywords to just alphanumeric and space characters
            keywords = re.sub(r'[^\w ]', ' ', keywords)

            keywords = re.sub('\s+', ' ', keywords)
            keywords = keywords.split(' ')

            def regexify_keywords(keyword):
                keyword = keyword.lower()
                return re.compile('^%s' % keyword)

            keywords = map(regexify_keywords, keywords)
            filters['_keywords__all'] = keywords

        if exclude_taken_courses == "yes":
            if current_user:
                ucs = (current_user.get_user_courses()
                        .only('course_id', 'term_id'))
                filters['id__nin'] = [
                    uc.course_id for uc in ucs
                    if not term.Term.is_shortlist_term(uc.term_id)
                ]
            else:
                logging.error('Anonymous user tried excluding taken courses')

        # TODO(david): Move this to another fn
        if sort_mode == 'friends_taken':
            # TODO(david): Resolve circular dependency in a better way
            import user

            # TODO(mack): should only do if user is logged in
            friends = user.User.objects(id__in=current_user.friend_ids).only(
                    'course_history')
            # TODO(mack): need to majorly optimize this
            num_friends_by_course = {}
            for friend in friends:
                for course_id in friend.course_ids:
                    if not course_id in num_friends_by_course:
                        num_friends_by_course[course_id] = 0
                    num_friends_by_course[course_id] += 1

            filters['id__in'] = num_friends_by_course.keys()
            existing_courses = Course.objects(**filters).only('id')
            existing_course_ids = set(c.id for c in existing_courses)
            for course_id in num_friends_by_course.keys():
                if course_id not in existing_course_ids:
                    del num_friends_by_course[course_id]

            sorted_course_count_tuples = sorted(
                num_friends_by_course.items(),
                key=lambda (_, total): total,
                reverse=direction < 0,
            )[offset:offset + count]

            sorted_course_ids = [course_id for (course_id, total)
                    in sorted_course_count_tuples]

            unsorted_limited_courses = Course.objects(id__in=sorted_course_ids)

            limited_courses_by_id = {}
            for course in unsorted_limited_courses:
                limited_courses_by_id[course.id] = course

            limited_courses = []
            for course_id in sorted_course_ids:
                limited_courses.append(limited_courses_by_id[course_id])

        else:
            sort_options = _SORT_MODES_BY_NAME[sort_mode]

            if sort_mode in _RATING_SORT_MODES:
                sort_instr = '-' + sort_options['field']
                sort_instr += "_positive" if direction < 0 else "_negative"
            else:
                sort_instr = ''
                if direction < 0:
                    sort_instr = '-'
                sort_instr += sort_options['field']

            unsorted_courses = Course.objects(**filters)
            sorted_courses = unsorted_courses.order_by(sort_instr)
            limited_courses = sorted_courses.skip(offset).limit(count)

        has_more = len(limited_courses) == count

        return limited_courses, has_more

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
            # TODO(mack): create user models for friends
            #'friends': [1647810326, 518430508, 541400376],
            'ratings': util.dict_to_list(self.get_ratings()),
            'overall': self.overall.to_dict(),
            'professor_ids': self.professor_ids,
            'prereqs': self.prereqs,
        }

    def __repr__(self):
        return "<Course: %s>" % self.code

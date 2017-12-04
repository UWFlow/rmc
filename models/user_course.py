import datetime
import itertools

import mongoengine as me

import course
import points as _points
import professor
import review
import rmc.shared.util as util
import term


def get_user_course_modified_date(uc):
    """Return the latest modified date, or None for an empty UserCourse."""
    dates = [
        uc.course_review.comment_date,
        uc.course_review.rating_change_date,
        uc.professor_review.comment_date,
        uc.professor_review.rating_change_date,
    ]

    valid_dates = sorted(filter(None, dates), reverse=True)

    date = None
    if len(valid_dates) > 0:
        date = valid_dates[0]

    return date


class MenloCourse(me.Document):
    '''MenloCourse objects are sourced from another website

    As such, they only have professor reviews. The course review
    EmbeddedDocument will always be the default CourseReview
    '''

    meta = {
        'indexes': [
            'course_id',
            'professor_id',
        ],
    }

    # id = me.ObjectIdField(primary_key=True)

    course_id = me.StringField(required=True)
    professor_id = me.StringField()

    course_review = me.EmbeddedDocumentField(review.CourseReview)
    professor_review = me.EmbeddedDocumentField(review.ProfessorReview)

    @classmethod
    def get_publicly_visible(cls, min_num_ucs=0, num_days=None):
        """Filter out stale MenloCourses that we don't want to display."""
        return util.publicly_visible_ratings_and_reviews_filter(
            cls.objects, get_user_course_modified_date, min_num_ucs, num_days)


class UserCourse(me.Document):

    meta = {
        'indexes': [
            # TODO(mack): this index on user_id is probably not necessary
            # since it duplicates the unique_with on user_id
            'user_id',
            'course_id',
            'professor_id',
            # TODO(mack): check if below indices are necessary
            #('course_id', 'professor_id'),
            #('professor_id', 'course_id'),
        ],
    }

    # date review created implictly stored here
    # id = me.ObjectIdField(primary_key=True)

    # TODO(mack): verify this works when user_id is not required
    # TODO(mack): might be better to just enforce uniqueness on
    # ['course_id', 'offering_id']?
    user_id = me.ObjectIdField(unique_with=['course_id', 'term_id'])
    course_id = me.StringField(required=True)
    term_id = me.StringField(required=True)
    # TODO(mack): might not appropriate to store here, maybe should be
    # calculated using combination of info about when user started
    # school and term this course was taken
    # eg. 3A
    program_year_id = me.StringField()

    # TODO(mack): add fields for grade tracking; eg. grades on assignments

    # TODO(mack): should range be 0..1 or 0..100 ?
    grade = me.FloatField(min_value=0.0, max_value=1.0)

    professor_id = me.StringField()

    course_review = me.EmbeddedDocumentField(review.CourseReview,
                                             default=review.CourseReview())
    professor_review = me.EmbeddedDocumentField(
                            review.ProfessorReview,
                            default=review.ProfessorReview())

    # Whether we've prompted the user to review this course before
    review_prompted = me.BooleanField(default=False)

    DEFAULT_TO_DICT_FIELDS = [
        'id',
        'user_id',
        'term_id',
        'term_name',
        'course_id',
        'professor_id',
        'course_review',
        'professor_review',
        'has_reviewed',
        'program_year_id',
    ]

    # TODO(mack): add section_id
    # section_id = StringField()

    # TODO(mack): should we have update_time?
    # update_date = me.DateTimeField()

    @property
    def term_name(self):
        return term.Term.name_from_id(self.term_id)

    @staticmethod
    def can_review(term_id):
        return (not term.Term.is_shortlist_term(term_id) and
                term_id <= util.get_current_term_id())

    @property
    def reviewable(self):
        return UserCourse.can_review(self.term_id)

    @property
    def has_reviewed(self):
        return (self.course_review.comment_date is not None
            or self.course_review.easiness is not None
            or self.course_review.usefulness is not None
            or self.professor_review.comment_date is not None
            or self.professor_review.clarity is not None
            or self.professor_review.passion is not None
        )

    @property
    def num_points(self):
        points = 0

        if self.course_review.has_commented:
            points += _points.PointSource.COURSE_COMMENT
        if self.course_review.has_been_rated:
            points += _points.PointSource.COURSE_RATING
        if self.course_review.has_shared:
            points += _points.PointSource.SHARE_COURSE_REVIEW

        if self.professor_review.has_commented:
            points += _points.PointSource.PROFESSOR_COMMENT
        if self.professor_review.has_been_rated:
            points += _points.PointSource.PROFESSOR_RATING
        if self.professor_review.has_shared:
            points += _points.PointSource.SHARE_PROFESSOR_REVIEW

        return points

    @classmethod
    def get_publicly_visible(cls, min_num_ucs=0, num_days=None):
        """Filter out stale UserCourses that we don't want to display."""
        return util.publicly_visible_ratings_and_reviews_filter(
            cls.objects, get_user_course_modified_date, min_num_ucs, num_days)

    def to_dict(self, fields=DEFAULT_TO_DICT_FIELDS):
        # NOTE: DO NOT MODIFY parameter `fields` in this fn, because it's
        #     statically initialized with a non-primitive default.

        # TODO(david): Reuse code below for other to_dict() methods
        def map_field(prop):
            val = getattr(self, prop)
            if hasattr(val, 'to_dict'):
                if prop == 'course_review' or prop == 'professor_review':
                    return val.to_dict(user_course_id=self.id)
                else:
                    return val.to_dict()
            else:
                return val

        return {f: map_field(f) for f in fields}

    def save(self, *args, **kwargs):
        # TODO(Sandy): Use transactions
        # http://docs.mongodb.org/manual/tutorial/perform-two-phase-commits/
        # or run nightly ratings aggregation script to fix race condtions
        cur_course = course.Course.objects.with_id(self.course_id)
        if cur_course:
            self.course_review.update_course_aggregate_ratings(cur_course)
            cur_course.save()

        if self.professor_id:
            cur_professor = professor.Professor.objects.with_id(
                self.professor_id)
            self.professor_review.update_professor_aggregate_ratings(
                cur_professor, cur_course, self.course_review)
            cur_professor.save()

        super(UserCourse, self).save(*args, **kwargs)

    def __repr__(self):
        return "<UserCourse: %s, %s>" % (self.user_id, self.course_id)

    @classmethod
    def num_course_reviews(cls, course_id):
        return UserCourse.objects(course_id=course_id,
                course_review__comment_date__exists=True)

    def select_for_review(self, current_user):
        """Mark this course as having been selected for the given user."""
        # Don't mark at all if admin user spoofing
        if current_user.id != self.user_id:
            return

        current_user.last_prompted_for_review = datetime.datetime.now()
        # TODO(david): Is there a way to auto-save changed models at end of
        #     request?
        current_user.save()

        self.review_prompted = True
        self.save()

    # TODO(david): This would be a good function to unit test
    @classmethod
    def select_course_to_review(cls, user_courses):
        """Selects the optimal next course out of a given list to review.

        The algorithm works as follows:

        Filter courses that...
            - the user can review
            - we have never prompted the user to review before
            - the user has not written a course review for
            - are in the current term only if the term is almost over

        Then sort by...
            - least # of other reviews written
            - user has taken course recently
        """
        finished_fraction = term.Term.get_current_term_finished_fraction()

        def can_select(user_course):
            # Filter out courses user can't review yet (eg. shortlist, future)
            if not user_course.reviewable:
                return False

            # Filter out courses that we've prompted before
            # TODO(david): Just weigh such courses less instead of fitler out
            if user_course.review_prompted:
                return False

            # Filter out courses that user has written a course review
            if user_course.course_review.comment_date:
                return False

            # Filter out current term courses if it's still early on in the
            # term At ~120 days/term, 60% = 72 days = ~10.3 weeks. Allow
            # students to review in the last few weeks
            if (user_course.term_id == term.Term.get_current_term_id() and
                    finished_fraction <= 0.6):
                return False

            return True

        user_courses = filter(can_select, user_courses)

        # Sort by least reviews we have for that course
        user_courses.sort(key=lambda uc: cls.num_course_reviews(uc.course_id))

        # Finally, pick the most recent course of the bunch
        user_courses.sort(key=lambda uc: uc.term_id, reverse=True)
        return user_courses[0] if user_courses else None


# TODO(david): Should be static method of ProfCourse
def get_reviews_for_course_prof(course_id, prof_id):
    menlo_reviews = MenloCourse.objects(
        course_id=course_id,
        professor_id=prof_id,
    ).only('professor_review', 'course_review')

    user_reviews = UserCourse.objects(
        course_id=course_id,
        professor_id=prof_id,
    ).only('professor_review', 'course_review', 'user_id', 'term_id')

    return itertools.chain(menlo_reviews, user_reviews)

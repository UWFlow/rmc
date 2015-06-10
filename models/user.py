import base64
import datetime
import hashlib
import itertools
import logging
import time
import uuid

import mongoengine as me
import flask.ext.bcrypt as bcrypt

import course as _course
import exam as _exam
import points as _points
import term as _term
import user_course as _user_course
import user_schedule_item as _user_schedule_item
from rmc.shared import constants
from rmc.shared import facebook
from rmc.shared import rmclogger
from rmc.shared import util


PROMPT_TO_REVIEW_DELAY_DAYS = 60
PASSWORD_MIN_LENGTH = 6
BCRYPT_ROUNDS = 12


class User(me.Document):
    # The fields needed to display a user's name and profile picture.
    CORE_FIELDS = ['first_name', 'last_name', 'fbid', 'email']

    class JoinSource(object):
        FACEBOOK = 1
        EMAIL = 2

    class UserCreationError(Exception):
        pass

    meta = {
        'indexes': [
            'fb_access_token',
            'fbid',
            # TODO(mack): need to create the 'api_key' index on prod
            'api_key',
            # Allow users with email=None, but non-None emails must be unique
            {
                'fields': ['email'],
                'unique': True,
                'sparse': True,
            },
            'referrer_id',
        ],
    }

    # Randomly generated ID used to access some subset of user's information
    # without going through any ACL. Used for e.g. sharing schedules with non
    # flow users.
    #
    # e.g. A8RLLZTMX
    secret_id = me.StringField()

    # TODO(mack): join_date should be encapsulate in _id, but store it
    # for now, just in case; can remove it when sure that info is in _id
    join_date = me.DateTimeField(required=True)
    join_source = me.IntField(required=True,
            choices=[JoinSource.FACEBOOK, JoinSource.EMAIL])
    referrer_id = me.ObjectIdField(required=False)

    # eg. Mack
    first_name = me.StringField(required=True)

    middle_name = me.StringField()

    # eg. Duan
    last_name = me.StringField(required=True)

    # TODO(mack): check if facebook always returns gender field
    gender = me.StringField(choices=['male', 'female'])

    # eg. 1647810326
    fbid = me.StringField()

    # http://stackoverflow.com/questions/4408945/what-is-the-length-of-the-access-token-in-facebook-oauth2
    fb_access_token = me.StringField(max_length=255)
    fb_access_token_expiry_date = me.DateTimeField()
    # The token expired due to de-auth, logging out, etc (ie. not time expired)
    fb_access_token_invalid = me.BooleanField(default=False)

    email = me.EmailField()

    password = me.StringField()

    # eg. list of user objectids, could be friends from sources besides
    # facebook
    friend_ids = me.ListField(me.ObjectIdField())
    # eg. list of fbids of friends from facebook, not necessarily all of whom
    # use the site
    friend_fbids = me.ListField(me.StringField())

    birth_date = me.DateTimeField()

    last_visited = me.DateTimeField()
    # TODO(mack): consider using SequenceField()
    num_visits = me.IntField(min_value=0, default=0)

    # The last time the user visited the onboarding page
    last_show_onboarding = me.DateTimeField()
    # The last time the user was shown the import schedule view
    last_show_import_schedule = me.DateTimeField()

    # eg. mduan or 20345619 ?
    student_id = me.StringField()
    # eg. university_of_waterloo ?
    school_id = me.StringField()
    # eg. software_engineering ?
    # TODO(mack): should store program_id, not program_name
    # program_id = me.StringField()
    program_name = me.StringField()

    # List of UserCourse.id's
    course_history = me.ListField(me.ObjectIdField())

    # TODO(mack): figure out why last_term_id was commented out in
    # a prior diff: #260f174
    # Deprecated
    last_term_id = me.StringField()
    # Deprecated
    last_program_year_id = me.StringField()

    # Track the number of times the user has invited friends
    # (So we can award points if they have)
    num_invites = me.IntField(min_value=0, default=0)

    # The number of points this user has. Point are awarded for a number of
    # actions such as reviewing courses, inviting friends. This is a cached
    # point total. It will be calculated once a day with aggregator.py
    num_points = me.IntField(min_value=0, default=0)

    is_admin = me.BooleanField(default=False)

    # TODO(mack): refactor this into something maintainable
    sent_exam_schedule_notifier_email = me.BooleanField(default=False)
    sent_velocity_demo_notifier_email = me.BooleanField(default=False)
    sent_raffle_notifier_email = me.BooleanField(default=False)
    sent_raffle_end_notifier_email = me.BooleanField(default=False)
    sent_schedule_sharing_notifier_email = me.BooleanField(default=False)
    sent_course_enrollment_feb_8_email = me.BooleanField(default=False)
    sent_referral_contest_email = me.BooleanField(default=False)
    sent_referral_contest_end_email = me.BooleanField(default=False)
    sent_welcome_email = me.BooleanField(default=False)

    email_unsubscribed = me.BooleanField(default=False)

    # Note: Backfilled on night of Nov. 29th, 2012
    transcripts_imported = me.IntField(min_value=0, default=0)

    schedules_imported = me.IntField(min_value=0, default=0)

    last_bad_schedule_paste = me.StringField()
    last_good_schedule_paste = me.StringField()
    last_bad_schedule_paste_date = me.DateTimeField()
    last_good_schedule_paste_date = me.DateTimeField()

    # Whether this user imported a schedule when it was still broken and we
    # should email them to apologize
    schedule_sorry = me.BooleanField(default=False)

    # API key that grants user to login_required APIs
    api_key = me.StringField()

    last_prompted_for_review = me.DateTimeField(default=datetime.datetime.min)

    voted_course_review_ids = me.ListField(me.StringField())
    voted_prof_review_ids = me.ListField(me.StringField())

    # Scholarships where a user has clicked: "Remove from profile"
    closed_scholarship_ids = me.ListField(me.StringField())

    @property
    def name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):

        # TODO(mack): If _changed_fields attribute does not exist, it mean
        # document has been saved yet. Just need to verify. In this case,
        # we could just check if id has been set
        first_save = not hasattr(self, '_changed_fields')

        if first_save:
            # TODO(Sandy): We're assuming people won't unfriend anyone.
            # Fix this later?

            # TODO(mack): this isn't safe against race condition of both
            # friends signing up at same time
            #print 'friend_fbids', self.friend_fbids
            friends = (User.objects(fbid__in=self.friend_fbids)
                        .only('id', 'friend_ids'))
            self.friend_ids = [f.id for f in friends]

        super(User, self).save(*args, **kwargs)

        if first_save:
            # TODO(mack): should do this asynchronously
            # Using update rather than save because it should be more efficient
            friends.update(add_to_set__friend_ids=self.id)

    # TODO(mack): think of better way to cache value
    @property
    def course_ids(self):
        if not hasattr(self, '_course_ids'):
            user_courses = _user_course.UserCourse.objects(
                id__in=self.course_history).only('course_id')
            self._course_ids = [uc.course_id for uc in user_courses]
        return self._course_ids

    @property
    def profile_pic_urls(self):
        if self.fbid is not None:
            urls = self._get_fb_pic_urls()
        else:
            urls = self._get_gravatar_pic_urls()
        return urls

    def _get_fb_pic_urls(self):
        base_pic = "https://graph.facebook.com/%s/picture" % (self.fbid)

        return {
            'default': base_pic,
            'large': '%s?type=large' % (base_pic),
            'square': '%s?type=square' % (base_pic),
        }

    def _get_gravatar_pic_urls(self):
        # Gravatar API: https://en.gravatar.com/site/implement/images/
        # TODO(sandy): Serve our own default image instead of the mystery man
        email_hash = hashlib.md5(self.email.strip().lower()).hexdigest()
        base_pic = "https://secure.gravatar.com/avatar/%s?d=mm" % (
                email_hash)

        return {
            'default': "%s&size=%s" % (base_pic, "50"),
            'large': "%s&size=%s" % (base_pic, "190"),
            'square': "%s&size=%s" % (base_pic, "50"),
        }

    @property
    def profile_url(self):
        return '/profile/%s' % self.id

    @property
    def absolute_profile_url(self):
        return '%s%s?admin=1' % (constants.RMC_HOST, self.profile_url)

    @property
    def short_program_name(self):
        if self.program_name:
            return self.program_name.split(',')[0]
        return ''

    @property
    def has_course_history(self):
        # TODO(Sandy): Using this to backfill transcripts imported,
        # remove later
        if len(self.course_history) == 0:
            return False

        for uc in self.get_user_courses():
            if not _term.Term.is_shortlist_term(uc.term_id):
                return True
        return False

    @property
    def has_shortlisted(self):
        for uc in self.get_user_courses():
            if _term.Term.is_shortlist_term(uc.term_id):
                return True
        return False

    @property
    def has_schedule(self):
        # TODO(Sandy): Actually this only works assuming users never remove
        # their schedule and we'll have to do actual queries when 2013_05 comes
        return self.schedules_imported > 0

    @property
    def should_renew_fb_token(self):
        # Should renew FB token if it expired or will expire "soon".
        future_date = datetime.datetime.now() + datetime.timedelta(
                days=facebook.FB_FORCE_TOKEN_EXPIRATION_DAYS)
        return (self.fb_access_token_expiry_date is None or
                self.fb_access_token_expiry_date < future_date or
                self.fb_access_token_invalid)

    @property
    def is_fb_token_expired(self):
        return (self.fb_access_token_expiry_date is None or
                self.fb_access_token_expiry_date < datetime.datetime.now() or
                self.fb_access_token_invalid)

    @property
    def is_demo_account(self):
        return self.fbid == constants.DEMO_ACCOUNT_FBID

    @property
    def last_schedule_paste(self):
        return self.last_good_schedule_paste or self.last_bad_schedule_paste

    def get_user_courses(self):
        return _user_course.UserCourse.objects(id__in=self.course_history)

    @classmethod
    def cls_mutual_courses_redis_key(cls, user_id_one, user_id_two):
        if user_id_one < user_id_two:
            first_id = user_id_one
            second_id = user_id_two
        else:
            first_id = user_id_two
            second_id = user_id_one
        return 'mutual_courses:%s:%s' % (first_id, second_id)

    def mutual_courses_redis_key(self, other_user_id):
        return User.cls_mutual_courses_redis_key(self.id, other_user_id)

    def get_mutual_course_ids(self, redis):
        # fetch mutual friends from redis
        pipe = redis.pipeline()

        # Show mutual courses between the viewing user and the friends of the
        # profile user
        for friend_id in self.friend_ids:
            pipe.smembers(self.mutual_courses_redis_key(friend_id))
        mutual_course_ids_per_user = pipe.execute()

        zipped = itertools.izip(
                self.friend_ids, mutual_course_ids_per_user)

        mutual_course_ids_by_friend = {}
        for friend_id, mutual_course_ids in zipped:
            mutual_course_ids_by_friend[friend_id] = mutual_course_ids

        return mutual_course_ids_by_friend

    def cache_mutual_course_ids(self, redis):
        friends = User.objects(id__in=self.friend_ids).only('course_history')
        friend_map = {}
        for friend in friends:
            friend_map[friend.id] = friend

        my_course_ids = set(self.course_ids)
        for friend in friends:
            mutual_course_ids = my_course_ids.intersection(friend.course_ids)
            if mutual_course_ids:
                redis_key = self.mutual_courses_redis_key(friend.id)
                redis.sadd(redis_key, *list(mutual_course_ids))

    def remove_mutual_course_ids(self, redis):
        pipe = redis.pipeline()

        for friend_id in self.friend_ids:
            pipe.delete(self.mutual_courses_redis_key(friend_id))

        return pipe.execute()

    def get_latest_program_year_id(self):
        latest_term_uc = None
        for uc_dict in self.get_user_courses():

            # Ignore untaken courses or shortlisted courses
            if uc_dict['term_id'] > util.get_current_term_id():
                continue

            if not latest_term_uc:
                latest_term_uc = uc_dict
            elif uc_dict['term_id'] > latest_term_uc['term_id']:
                latest_term_uc = uc_dict

        if latest_term_uc:
            return latest_term_uc['program_year_id']

        return None

    def get_friends(self):
        """Gets basic info for each of this user's friends."""
        return User.objects(id__in=self.friend_ids).only(
                *(User.CORE_FIELDS + ['id', 'num_points', 'num_invites',
                'program_name']))

    def rated_review(self, review_id, review_type):
        if review_type == 'course':
            return review_id in self.voted_course_review_ids
        else:
            return review_id in self.voted_prof_review_ids

    def to_dict(self, extended=True, include_course_ids=False):
        user_dict = {
            'id': self.id,
            'fbid': self.fbid,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'name': self.name,
            'profile_pic_urls': self.profile_pic_urls,
            'program_name': self.short_program_name,
            'num_invites': self.num_invites,
            'num_points': self.num_points,
        }

        if extended:
            user_dict.update({
                'friend_ids': self.friend_ids,
                'course_history': self.course_history,
            })

        if include_course_ids:
            user_dict['course_ids'] = self.course_ids

        return user_dict

    # TODO(mack): make race condition safe?
    def delete(self, *args, **kwargs):
        # Remove this user from the friend lists of all friends
        friends = User.objects(id__in=self.friend_ids)
        friends.update(pull__friend_ids=self.id)

        # Delete all their user course objects
        _user_course.UserCourse.objects(user_id=self.id).delete()

        # Delete all their UserScheduleItem objects
        _user_schedule_item.UserScheduleItem.objects(user_id=self.id).delete()

        # TODO(mack): delete mutual course information from redis?
        # should be fine for now since we are removing this user from their
        # friends' friend_ids, and redis cache will be regenerated daily
        # from aggregator.py

        return super(User, self).delete(*args, **kwargs)

    def to_review_author_dict(self, current_user, reveal_identity):
        is_current_user = current_user and current_user.id == self.id

        if reveal_identity:
            return {
                'id': self.id,
                'name': 'You' if is_current_user else self.name,
                'profile_pic_url': self.profile_pic_urls['square'],
            }

        else:
            return {
                'program_name': self.short_program_name
            }

    def invite_friend(self, redis):
        self.num_invites += 1
        if self.num_invites == 1:
            self.award_points(_points.PointSource.FIRST_INVITE, redis)

    def award_points(self, points, redis):
        self.num_points += points
        redis.incr('total_points', points)

    def update_fb_friends(self, fbids):
        self.friend_fbids = fbids
        fb_friends = (User.objects(fbid__in=self.friend_fbids)
                        .only('id', 'friend_ids'))
        # We have friends from only Facebook right now, so just set it
        self.friend_ids = [f.id for f in fb_friends]

    def get_schedule_item_dicts(self, exam_objs=None):
        """Gets all schedule items for this user starting no later than a year
        ago.

        Args:
            exam_objs: Optional exam objects to convert to UserScheduleItem and
                add to return list.
        Returns: a list of UserScheduleItem models as dicts.
        """
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
        schedule_item_objs = _user_schedule_item.UserScheduleItem.objects(
                user_id=self.id, start_date__gte=one_year_ago)
        dicts = [si.to_dict() for si in schedule_item_objs]

        if exam_objs:
            dicts.extend(e.to_schedule_obj().to_dict() for e in exam_objs)

        return dicts

    def get_failed_schedule_item_dicts(self):
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
        schedule_item_objs = _user_schedule_item.FailedScheduleItem.objects(
                user_id=self.id, parsed_date__gte=one_year_ago)
        return [si.to_dict() for si in schedule_item_objs]

    def get_all_schedule_items(self):
        return _user_schedule_item.UserScheduleItem.objects(user_id=self.id)

    def get_current_term_exams(self, current_term_course_ids=None):
        if not current_term_course_ids:
            ucs = (self.get_user_courses()
                    .filter(term_id=util.get_current_term_id())
                    .only('course_id'))
            current_term_course_ids = [uc.course_id for uc in ucs]

        return _exam.Exam.objects(course_id__in=current_term_course_ids)

    def get_secret_id(self):
        # TODO(jlfwong): This is possibly a race condition...
        if self.secret_id is None:
            self.secret_id = util.generate_secret_id()
            self.save()

        return self.secret_id

    def add_course(self, course_id, term_id, program_year_id=None):
        """Creates a UserCourse and adds it to the user's course_history.

        Idempotent.

        Returns the resulting UserCourse.
        """
        user_course = _user_course.UserCourse.objects(
            user_id=self.id, course_id=course_id).first()

        if user_course is None:
            if _course.Course.objects.with_id(course_id) is None:
                # Non-existant course according to our data
                rmclogger.log_event(
                    rmclogger.LOG_CATEGORY_DATA_MODEL,
                    rmclogger.LOG_EVENT_UNKNOWN_COURSE_ID,
                    course_id
                )
                return None

            user_course = _user_course.UserCourse(
                user_id=self.id,
                course_id=course_id,
                term_id=term_id,
                program_year_id=program_year_id,
            )
        else:
            # Record only the latest attempt for duplicate/failed courses
            if (term_id > user_course.term_id or
                user_course.term_id == _term.Term.SHORTLIST_TERM_ID):
                user_course.term_id = term_id
                user_course.program_year_id = program_year_id

        user_course.save()

        if user_course.id not in self.course_history:
            self.course_history.append(user_course.id)
            self.save()

        return user_course

    # Generate a random api key granting this user to access '/api/' routes
    def grant_api_key(self):
        uuid_ = uuid.uuid4()
        md5 = hashlib.md5()
        md5.update(str(uuid_))
        microsecs = int(time.time() * 1000000)
        raw_api_key = str(microsecs) + md5.hexdigest()
        self.api_key = base64.b64encode(raw_api_key)
        self.save()
        return self.api_key

    def next_course_to_review(self):
        user_courses = _user_course.UserCourse.objects(user_id=self.id)
        return _user_course.UserCourse.select_course_to_review(user_courses)

    def should_prompt_review(self):
        now = datetime.datetime.now()
        elapsed = min(now - self.last_prompted_for_review,
                now - self.join_date)
        return elapsed.days > PROMPT_TO_REVIEW_DELAY_DAYS

    @staticmethod
    def auth_user(email, password):
        """Returns the authenticated user or None."""
        user = User.objects(email=email)

        if not user:
            return None

        # TODO(sandy): Since we added a unique index on email, this shouldn't
        # happen anymore. But keep this around for a bit, in case something
        # messes up [Apr 8, 2014]
        if user.count() > 1:
            logging.error('Multiple email addressed matched: %s' % email)
            return None

        user = user.first()

        # TODO(sandy): Provide more helpful errors for users signed up with fb
        if (not user.password or
            not bcrypt.check_password_hash(user.password, password)):
            return None

        return user

    @staticmethod
    def create_new_user_from_email(first_name, last_name, email, password):
        if len(password) < PASSWORD_MIN_LENGTH:
            raise User.UserCreationError(
                    'Passwords must be at least 8 characters long.')

        user = User(
            email=email,
            first_name=first_name,
            join_date=datetime.datetime.now(),
            join_source=User.JoinSource.EMAIL,
            last_name=last_name,
            password=bcrypt.generate_password_hash(
                    password, rounds=BCRYPT_ROUNDS),
        )

        try:
            user.save()
        except me.base.ValidationError as e:
            if 'email' in e.errors:
                raise User.UserCreationError('Oops, that email is invalid.')
            raise
        except me.queryset.NotUniqueError as e:
            raise User.UserCreationError('That email is already signed up.'
                    ' (Maybe you already signed up with Facebook?)')

        return user

    def __repr__(self):
        return "<User: %s>" % self.name.encode('utf-8')

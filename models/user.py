import itertools

import mongoengine as me

import term as _term
import user_course as _user_course
from rmc.shared import constants

class User(me.Document):

    class JoinSource(object):
        FACEBOOK = 1

    meta = {
        'indexes': [
            'fb_access_token',
            'fbid',
        ],
    }

    # id = me.ObjectIdField(primary_key=True)

    # TODO(mack): join_date should be encapsulate in _id, but store it
    # for now, just in case; can remove it when sure that info is in _id
    join_date = me.DateTimeField(required=True)
    join_source = me.IntField(required=True, choices=[JoinSource.FACEBOOK])

    # eg. Mack
    first_name = me.StringField(required=True)

    middle_name = me.StringField()

    # eg. Duan
    last_name = me.StringField(required=True)

    # TODO(mack): check if facebook always returns gender field
    gender = me.StringField(choices=['male', 'female'])

    # eg. 1647810326
    fbid = me.StringField(required=True, unique=True)

    # http://stackoverflow.com/questions/4408945/what-is-the-length-of-the-access-token-in-facebook-oauth2
    fb_access_token = me.StringField(max_length=255, required=True, unique=True)
    fb_access_token_expiry_date = me.DateTimeField(required=True)

    email = me.EmailField()

    # eg. list of user objectids, could be friends from sources besides facebook
    friend_ids = me.ListField(me.ObjectIdField())
    # eg. list of fbids of friends from facebook, not necessarily all of whom
    # use the site
    friend_fbids = me.ListField(me.StringField())

    birth_date = me.DateTimeField( )

    last_visited = me.DateTimeField()
    # TODO(mack): consider using SequenceField()
    num_visits = me.IntField(min_value=0, default=0)

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

    is_admin = me.BooleanField(default=False)

    # TODO(mack): refactor this into something maintainable
    sent_exam_schedule_notifier_email = me.BooleanField(default=False)

    @property
    def name(self):
        return '%s %s' % (self.first_name , self.last_name)

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
            friends = User.objects(fbid__in=self.friend_fbids).only('id', 'friend_ids')
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
    # TODO(mack): support different sized pictures
    def fb_pic_url(self):
        return 'https://graph.facebook.com/%s/picture' % self.fbid

    @property
    def profile_url(self):
        return '/profile/%s' % self.id

    @property
    def absolute_profile_url(self):
        return '%s%s?admin=1' % (constants.PROD_HOST, self.profile_url)

    @property
    def short_program_name(self):
        if self.program_name:
            return self.program_name.split(',')[0]
        return ''

    @property
    def has_course_history(self):
        # TODO(Sandy): This is only a heuristic right now. Have flags for
        # importing courses and/or manually adding courses later
        return (self.course_history and len(self.course_history) > 3)

    @property
    def has_shortlisted(self):
        print _term
        for uc in self.get_user_courses():
            if _term.Term.is_shortlist_term(uc.term_id):
                return True
        return False

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
        return 'mutual_courses:%s:%s' %  (first_id, second_id)

    def mutual_courses_redis_key(self, other_user_id):
        return User.cls_mutual_courses_redis_key(self.id, other_user_id)

    def get_mutual_course_ids(self, redis):
        # fetch mutual friends from redis
        pipe = redis.pipeline()

        # Show mutual courses between the viewing user and the friends of the profile user
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
        courses_by_user = {}
        for user in User.objects.only('friend_ids', 'course_history'):
            friend_ids = [str(friend_id) for friend_id in user.friend_ids]
            ucs = _user_course.UserCourse.objects(
                    id__in=user.course_history).only('course_id')
            course_ids = [uc.course_id for uc in ucs]
            courses_by_user[str(user.id)] = [friend_ids, set(course_ids)]

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


    def to_dict(self, include_course_ids=False):
        program_name = self.short_program_name
        if include_course_ids:
            course_ids = self.course_ids
        else:
            course_ids = []

        return {
            'id': self.id,
            'fbid': self.fbid,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'name': self.name,
            'friend_ids': self.friend_ids,
            'fb_pic_url': self.fb_pic_url,
            'program_name': program_name,
            #'last_term_name': last_term_name,
            #'last_program_year_id': self.last_program_year_id,
            'course_history': self.course_history,
            'course_ids': course_ids,
        }

    # TODO(mack): make race condition safe?
    def delete(self, *args, **kwargs):
        # Remove this user from the friend lists of all friends
        friends = User.objects(id__in=self.friend_ids)
        friends.update(pull__friend_ids=self.id)

        # Delete all their user course objects
        _user_course.UserCourse.objects(user_id=self.id).delete()

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
                'fb_pic_url': self.fb_pic_url,
            }

        else:
            return {
                'program_name': self.short_program_name
            }

    def __repr__(self):
        return "<User: %s>" % self.name

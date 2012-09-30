import argparse
import mongoengine
import redis
import sys

import rmc.models as m
import rmc.shared.constants as c


r = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)
mongoengine.connect(c.MONGO_DB_RMC)

# TODO(mack): store 'overall' in professor
PROFESSOR_RATING_FIELDS = [
    'easiness',
    'clarity',
    'passion',
]

COURSE_RATING_FIELDS = [
    'easiness',
    'interest',
    'overall',
]

def increment_ratings(courses, get_rating_fn, get_fields_fn, ucs):
    for uc in ucs:
        ratings = get_rating_fn(courses, uc)
        if not ratings:
            continue
        for field_key, field_value in get_fields_fn(uc):
            if field_value is not None:
                ratings[field_key].add_rating(field_value)


def increment_aggregate_ratings(courses, get_rating_fn, get_fields_fn, ucs):
    for uc in ucs:
        ratings = get_rating_fn(courses, uc)
        if not ratings:
            continue
        for field_key, field_value in get_fields_fn(uc):
            if field_value is not None:
                ratings[field_key].add_aggregate_rating(field_value)


def import_mongo_course_rating():
    # course => ratings
    def get_rating_fn(courses, uc):
        if uc.course_id not in courses:
            obj = {}
            for field in COURSE_RATING_FIELDS:
                obj[field] = m.AggregateRating()
            courses[uc.course_id] = obj
        return courses[uc.course_id]

    def get_fields_fn(uc):
        easiness = uc.course_review.easiness
        interest = uc.course_review.interest
        if easiness and interest:
            overall = (easiness + interest) / 2
        elif easiness:
            overall = easiness
        else:
            overall = interest

        return [
            ('easiness', easiness),
            ('interest', interest),
            ('overall', overall),
        ]

    def get_aggregate_fields_fn(uc):
        easiness = uc.easiness
        interest = uc.interest

        def calculate_overall_rating(e, i):
            return (e.count * e.rating + i.count * i.rating) / max(1, (e.count + i.count))

        # heuristic for getting the overall rating:
        # 1. the count will max of the count for each attribute
        # 2. the rating will be average
        overall = m.AggregateRating(
            count=max(easiness.count, interest.count),
            rating=calculate_overall_rating(easiness, interest),
        )

        return [
            ('easiness', easiness),
            ('interest', interest),
            ('overall', overall),
        ]

    courses = {}
    args = [courses, get_rating_fn]
    increment_ratings(*(args + [get_fields_fn, m.MenloCourse.objects]))
    increment_ratings(*(args + [get_fields_fn, m.UserCourse.objects]))
    increment_aggregate_ratings(*(args + [get_aggregate_fields_fn, m.CritiqueCourse.objects]))

    count = [0]
    def set_course_ratings_in_mongo(courses):
        for course_id, ratings in courses.items():
            course = m.Course.objects.with_id(course_id)
            if not course:
                print 'could not find course %s in mongo' % course_id
                continue

            course.easiness = ratings['easiness']
            course.interest = ratings['interest']
            course.overall = ratings['overall']

            course.save()
            count[0] += 1

    set_course_ratings_in_mongo(courses)
    print 'saved ratings for %d courses in mongodb' % count[0]


def import_mongo_course_professors():

    count = 0
    for course in m.Course.objects.only('professor_ids'):
        def get_professor_ids(course, coll):
            return set(
                [x.professor_id for x in coll.objects(course_id=course.id).only('professor_id') if x.professor_id]
            )
        professor_ids = get_professor_ids(course, m.UserCourse).union(
                get_professor_ids(course, m.MenloCourse))
        # TODO(mack): Looks like add_to_set doesn't validate that each item
        # in the list meets the schema since it seemed to be letting me
        # writing lists that contained None. Investigate if this is what it
        # is doing.
        course.update(add_to_set__professor_ids=list(professor_ids))
        count += 1

    print 'added professors for %d courses in mongodb' % count


def import_redis_course_professor_rating():
    # course => professors => ratings
    def get_rating_fn(courses, uc):
        if uc.professor_id is None:
            return None

        if uc.course_id not in courses:
            courses[uc.course_id] = {}
        professors = courses[uc.course_id]

        if uc.professor_id not in professors:
            obj = {}
            for field in PROFESSOR_RATING_FIELDS:
                obj[field] = m.AggregateRating()
            professors[uc.professor_id] = obj
        return professors[uc.professor_id]

    def get_fields_fn(uc):
        return [
            ('easiness', uc.course_review.easiness),
            ('clarity', uc.professor_review.clarity),
            ('passion', uc.professor_review.passion),
        ]

    def get_aggregate_fields_fn(uc):
        return [
            ('easiness', uc.easiness),
            ('clarity', uc.clarity),
            ('passion', uc.passion),
        ]

    courses = {}
    args = [courses, get_rating_fn]
    increment_ratings(*(args + [get_fields_fn, m.MenloCourse.objects]))
    increment_ratings(*(args + [get_fields_fn, m.UserCourse.objects]))
    increment_aggregate_ratings(*(args + [get_aggregate_fields_fn, m.CritiqueCourse.objects]))

    count = [0]
    def set_course_professor_ratings_in_redis(courses):
        for course_id, professors in courses.items():
            for professor_id, ratings in professors.items():
                if professor_id is None:
                    continue
                for rating_type, aggregate_rating in ratings.items():
                    # TODO(mack): store all ratings under single hash which is
                    # supposed to be more memory efficient (and probably faster
                    # fetching as well)
                    # TODO(mack): redis key should be namespaced under
                    # course_professor or something....
                    redis_key = ':'.join([course_id, professor_id, rating_type])
                    r.set(redis_key, aggregate_rating.to_json())
                    count[0] += 1

    set_course_professor_ratings_in_redis(courses)
    print 'set %d course professor rating keys in redis' % count[0]


# TODO(mack): test it when we get data to test with
# TODO(mack): currently sort of duplicate logic in User.cache_mutual_course_ids()
def import_redis_friend_mutual_courses():

    courses_by_user = {}
    for user in m.User.objects.only('friend_ids', 'course_history'):
        friend_ids = [str(friend_id) for friend_id in user.friend_ids]
        ucs = m.UserCourse.objects(id__in=user.course_history).only('course_id')
        course_ids = [uc.course_id for uc in ucs]
        courses_by_user[str(user.id)] = [friend_ids, set(course_ids)]

    count = 0
    user_pair = set()
    for user_id, (friend_ids, courses) in courses_by_user.iteritems():
        for friend_id in friend_ids:
            if user_id < friend_id:
                first_id = user_id
                second_id = friend_id
            else:
                first_id = friend_id
                second_id = user_id
            if (first_id, second_id) in user_pair:
                continue

            friend_courses = courses_by_user[friend_id][1]
            mutual_courses = courses.intersection(friend_courses)
            if mutual_courses:
                count += 1
                redis_key = m.User.cls_mutual_courses_redis_key(
                    first_id, second_id)
                r.sadd(redis_key, *list(mutual_courses))
            user_pair.add((first_id, second_id))

    print 'set %d friend pair keys in redis' % count

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    'all',
    mode_mapping = {
        'redis_course_professor_rating': import_redis_course_professor_rating,
        'redis_friend_mutual_courses': import_redis_friend_mutual_courses,
        'mongo_course_rating': import_mongo_course_rating,
        'mongo_course_professors': import_mongo_course_professors,
    }
    parser.add_argument('mode',
            help='one of %s' % ','.join(mode_mapping.keys() + ['all']))
    args = parser.parse_args()

    if args.mode == 'all':
        for func in mode_mapping.values():
            func()
    elif args.mode in mode_mapping:
        func = mode_mapping[args.mode]
        func()
    else:
        sys.exit('The mode %s is not supported' % args.mode)

import argparse
import mongoengine
import redis
import sys

import rmc.models as m
import rmc.shared.constants as c


r = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)
mongoengine.connect(c.MONGO_DB_RMC)

PROFESSOR_RATING_FIELDS = [
    'easiness',
    'clarity',
    'passion',
]

COURSE_RATING_FIELDS = [
    'easiness',
    'interest',
]

def increment_ratings(courses, get_ratings_fn, get_fields_fn, ucs):
    for uc in ucs:
        ratings = get_ratings_fn(courses, uc)
        for field_key, field_value in get_fields_fn(uc):
            if field_value is not None:
                ratings[field_key].add_rating(field_value)


def increment_aggregate_ratings(courses, get_ratings_fn, get_fields_fn, ucs):
    for uc in ucs:
        ratings = get_ratings_fn(courses, uc)
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
        return [
            ('easiness', uc.course_review.easiness),
            ('interest', uc.course_review.interest),
        ]

    def get_aggregate_fields_fn(uc):
        return [
            ('easiness', uc.easiness),
            ('interest', uc.interest), ]

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


            def calculate_overall_rating(e, i):
                return (e.count * e.rating + i.count * i.rating) / (e.count + i.count)

            course.easiness = ratings['easiness']
            course.interest = ratings['interest']
            course.overall = m.AggregateRating(
                rating=calculate_overall_rating(course.easiness, course.interest),
                count = course.easiness.count + course.interest.count)

            course.save()
            count[0] += 1

    set_course_ratings_in_mongo(courses)
    print 'saved ratings for %d courses in mongodb' % count[0]


def import_redis_course_professor_rating():
    # course => professors => ratings
    def get_rating_fn(courses, uc):
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
                for rating_type, aggregate_rating in ratings.items():
                    redis_key = ':'.join([course_id, professor_id, rating_type])
                    r.set(redis_key, aggregate_rating.to_json())
                    count[0] += 1

    set_course_professor_ratings_in_redis(courses)
    print 'set %d keys in redis' % count[0]

# TODO(mack): store mutual courses between friends in redis
def import_friend_mutual_courses():
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    supported_modes = [
        'all',
        'redis_course_professor_rating',
        'mongo_course_rating',
    ]
    parser.add_argument('mode', help='one of %s' % ','.join(supported_modes))
    args = parser.parse_args()

    if args.mode == 'all':
        import_redis_course_professor_rating()
        import_mongo_course_rating()
    elif args.mode == 'redis_course_professor_rating':
        import_redis_course_professor_rating()
    elif args.mode == 'mongo_course_rating':
        import_mongo_course_rating()
    else:
        sys.exit('The mode %s is not supported' % args.mode)

import rmc.models as m
import rmc.shared.constants as c
import redis
import mongoengine

r = redis.StrictRedis(host=c.REDIS_HOST, port=c.REDIS_PORT, db=c.REDIS_DB)
mongoengine.connect(c.MONGO_DB_RMC)

def import_course_professor_rating():
    # course => professors => ratings
    def get_ratings_from_user_course(courses, uc):
        if uc.course_id not in courses:
            courses[uc.course_id] = {}
        professors = courses[uc.course_id]

        if uc.professor_id not in professors:
            professors[uc.professor_id] = {
                'easiness': m.AggregateRating(),
                'clarity': m.AggregateRating(),
                'passion': m.AggregateRating(),
            }
        return professors[uc.professor_id]

    courses = {}

    def increment_ratings(courses, ucs):
        for uc in ucs:
            ratings = get_ratings_from_user_course(courses, uc)
            if uc.course_review.easiness is not None:
                ratings['easiness'].add_rating(uc.course_review.easiness)
            if uc.professor_review.clarity is not None:
                ratings['clarity'].add_rating(uc.professor_review.clarity)
            if uc.professor_review.passion is not None:
                ratings['passion'].add_rating(uc.professor_review.passion)

    def increment_aggregate_ratings(courses, ucs):
        for uc in ucs:
            ratings = get_ratings_from_user_course(courses, uc)
            if uc.course_review.easiness is not None:
                ratings['easiness'].add_aggregate_rating(uc.easiness)
            if uc.professor_review.clarity is not None:
                ratings['clarity'].add_aggregate_rating(uc.clarity)
            if uc.professor_review.passion is not None:
                ratings['passion'].add_aggregate_rating(uc.passion)

    increment_ratings(courses, m.MenloCourse.objects)
    increment_ratings(courses, m.UserCourse.objects)
    increment_aggregate_ratings(courses, m.CritiqueCourse.objects)

    count = [0]
    def set_keys_in_redis(courses):
        for course_id, professors in courses.items():
            for professor_id, ratings in professors.items():
                for rating_type, aggregate_rating in ratings.items():
                    redis_key = ':'.join([course_id, professor_id, rating_type])
                    r.set(redis_key, aggregate_rating.to_json())
                    count[0] += 1

    set_keys_in_redis(courses)
    print 'set %d keys in redis' % count[0]

# TODO(mack): store mutual courses between friends in redis
def import_friend_mutual_courses():
    pass

if __name__ == '__main__':
    import_course_professor_rating()

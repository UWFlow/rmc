# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# There's some code in this file that checks for whether a field has been rated
# incorrectly (eg. `if course_review.interest`). Also, there's very slow code
# that loads all records in a collection into memory that should be converted
# to Mongo queries.
# TODO(david): Clean up this file and fix all the issues. Until then, please be
#     wary of what you use.
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


from collections import defaultdict
from datetime import datetime, timedelta
from mongoengine import Q
import csv
import mongoengine as me
import rmc.models as m
import rmc.shared.constants as c
import rmc.shared.util as _util
import sys


def truncate_datetime(dt):
    return dt - timedelta(
            hours=dt.hour,
            minutes=dt.minute,
            seconds=dt.second,
            microseconds=dt.microsecond)


def generic_stats(show_all=False):
    num_ucs = m.UserCourse.objects().count()

    num_users = m.User.objects.count()
    num_users_with_transcript = m.User.objects(
            transcripts_imported__gt=0).count()
    num_users_with_schedule = m.User.objects(
            schedules_imported__gt=0).count()

    num_course_reviews = m.UserCourse.objects(
            course_review__comment__ne='').count()
    num_professor_reviews = m.UserCourse.objects(
            professor_review__comment__ne='').count()

    # TODO(david): Make rating_fields a class method
    num_course_ratings = 0
    for rating in m.CourseReview().rating_fields():
        query = {'course_review__%s__ne' % rating: None}
        num_course_ratings += m.UserCourse.objects(**query).count()

    num_professor_ratings = 0
    for rating in m.ProfessorReview().rating_fields():
        query = {'professor_review__%s__ne' % rating: None}
        num_professor_ratings += m.UserCourse.objects(**query).count()

    q = Q()
    for rating in m.CourseReview().rating_fields():
        q |= Q(**{'course_review__%s__ne' % rating: None})
    for rating in m.ProfessorReview().rating_fields():
        q |= Q(**{'professor_review__%s__ne' % rating: None})
    q |= Q(course_review__comment__ne='')
    q |= Q(professor_review__comment__ne='')
    num_ucs_rated_reviewed = m.UserCourse.objects.filter(q).count()

    yesterday = datetime.now() - timedelta(hours=24)
    signups = users_joined_after(yesterday)

    result = {
        'num_users': num_users,
        'num_users_with_transcript': num_users_with_transcript,
        'num_users_with_schedule': num_users_with_schedule,
        'num_ucs': num_ucs,
        'num_signups_today': signups,
        'num_signups_start_time': yesterday,
        'epoch': datetime.now(),
    }
    if show_all:
        result.update({
            'num_reviews': num_course_reviews + num_professor_reviews,
            'num_ratings': num_course_ratings + num_professor_ratings,
            'num_course_reviews': num_course_reviews,
            'num_professor_reviews': num_professor_reviews,
            'num_course_ratings': num_course_ratings,
            'num_professor_ratings': num_professor_ratings,
            'num_ucs_rated_reviewed': num_ucs_rated_reviewed,
        })

    return result


def print_generic_stats():
    data = generic_stats(show_all=True)

    print """
Total User
%s
User with transcripts imported
%s
Total UserCourse
%s
Total UserCourse Course review
%s
Total UserCourse Prof reviews
%s
Total UserCourse Course ratings
%s
Total UserCourse Prof ratings
%s
Users signed up since a day ago (%s)
%s""" % (
        data['num_users'],
        data['num_users_with_transcript'],
        data['num_ucs'],
        data['num_course_reviews'],
        data['num_professor_reviews'],
        data['num_course_ratings'],
        data['num_professor_ratings'],
        data['num_signups_start_time'],
        data['num_signups_today'],
    )


# Inclusive
def users_joined_after(date=None):
    if date is None:
        date = datetime.now() - timedelta(hours=24)
    return m.User.objects(join_date__gte=date).count()


# Exclusive
def users_joined_before(date=None):
    if date is None:
        date = datetime.now() - timedelta(hours=24)
    return m.User.objects(join_date__lt=date).count()


def latest_reviews(n=5):
    tups = []

    recent_ucs_by_course = m.UserCourse.objects().order_by(
            '-course_review__comment_date').limit(n)
    recent_ucs_by_prof = m.UserCourse.objects().order_by(
            '-prof_review__comment_date').limit(n)

    for uc in (set(recent_ucs_by_course) | set(recent_ucs_by_prof)):
        cr_date = uc.course_review.comment_date
        pr_date = uc.professor_review.comment_date
        if cr_date:
            tups.append((cr_date, 'course_review', uc))
        if pr_date:
            tups.append((pr_date, 'professor_review', uc))

    tups.sort(reverse=True)

    result = []
    for tup in tups:
        date, rev_type, uc = tup
        result.append({
            'user_id': uc.user_id,
            'course_id': uc.course_id,
            'professor_id': uc.professor_id,
            'text': getattr(uc, rev_type).comment,
            'date': date,
            'type': rev_type,
        })
        if len(result) == n:
            break

    return result


def reviews_given(user):
    ucs = m.UserCourse.objects(user_id=user.id)
    review_count = 0
    for uc in ucs:
        if uc.course_review.comment:
            review_count += 1
        if uc.professor_review.comment:
            review_count += 1
    return review_count


def ratings_given(user):
    ucs = m.UserCourse.objects(user_id=user.id)
    rating_count = 0
    for uc in ucs:
        cr = uc.course_review
        if cr.interest:
            rating_count += 1
        if cr.easiness:
            rating_count += 1
        if cr.usefulness:
            rating_count += 1
        pr = uc.professor_review
        if pr.clarity:
            rating_count += 1
        if pr.passion:
            rating_count += 1
    return rating_count


def print_users_rr_counts():
    users = m.User.objects()
    user_review_count = 0
    user_rating_count = 0
    total_reviews = 0
    total_ratings = 0
    for user in users:
        num_review = reviews_given(user)
        num_rating = ratings_given(user)
        total_reviews += num_review
        total_ratings += num_rating
        if num_review > 0:
            user_review_count += 1
        if num_rating > 0:
            user_rating_count += 1
    print "Users who reviewed"
    print user_review_count
    print "Total reviews (course + prof)"
    print total_reviews
    print "Users who rated"
    print user_rating_count
    print "Total ratings (of any kind)"
    print total_ratings


def print_all_user_names():
    users = m.User.objects()
    for user in users:
        # TODO(Sandy): Add a get full name method on user
        output = user.first_name + " " + user.last_name
        print output.encode('UTF-8')


def print_courses_in_exam_but_not_course():
    ecs = [e.course_id for e in m.Exam.objects()]
    for c in ecs:
        if len(m.Course.objects(id=c)) == 0:
            print c


def print_exam_collection():
    ecs = m.Exam.objects()
    for e in sorted(ecs, key=lambda exam: exam.course_id):
        e_dict = e.to_dict()
        print e_dict


def print_program_names(users):
    for user in users:
        if user.program_name:
            print user.program_name


def print_ratings_count_histogram():
    '''
    Print the count of ratings for each UserCourse for course/prof reviews
    '''
    ucs = m.UserCourse.objects()
    cr_hist = []
    pr_hist = []
    for i in range(0, 4):
        cr_hist.append(0)
    for i in range(0, 3):
        pr_hist.append(0)
    for uc in ucs:
        cr_count = 0
        pr_count = 0
        cr = uc.course_review
        pr = uc.professor_review
        if cr.interest:
            cr_count += 1
        if cr.easiness:
            cr_count += 1
        if cr.usefulness:
            cr_count += 1
        if pr.clarity:
            pr_count += 1
        if pr.passion:
            pr_count += 1
        cr_hist[cr_count] += 1
        pr_hist[pr_count] += 1
    print "UserCourse (Course Review) Rating Count Histogram"
    print cr_hist
    sanity_check_count = 0
    for i in range(0, 4):
        sanity_check_count += cr_hist[i]
    print "Sum of indices for Course Reviews:"
    print sanity_check_count

    print "(Sanity) UserCourse (Prof Review) Rating Count Histogram"
    print pr_hist
    sanity_check_count = 0
    for i in range(0, 3):
        sanity_check_count += pr_hist[i]
    print "(Sanity) Sum of indices for Prof Reviews:"
    print sanity_check_count


def print_ratings_histogram():
    '''
    Prints a historgram of each rating.
    TODO(Sandy): Don't hardcode rating names and indices. headache right now.
    want sleep
    '''
    hist = {}
    hist['i'] = 0
    hist['e'] = 0
    hist['u'] = 0
    hist['c'] = 0
    hist['p'] = 0
    total_ratings_count = 0
    ucs = m.UserCourse.objects()
    for uc in ucs:
        cr = uc.course_review
        pr = uc.professor_review
        if cr.interest:
            hist['i'] += 1
            total_ratings_count += 1
        if cr.easiness:
            hist['e'] += 1
            total_ratings_count += 1
        if cr.usefulness:
            hist['u'] += 1
            total_ratings_count += 1
        if pr.clarity:
            hist['c'] += 1
            total_ratings_count += 1
        if pr.passion:
            hist['p'] += 1
            total_ratings_count += 1
    print "Ratings histogram"
    print "Interest: %d" % hist['i']
    print "Easiness: %d" % hist['e']
    print "Usefulness: %d" % hist['u']
    print "Clarity: %d" % hist['c']
    print "Passion: %d" % hist['p']
    print "(Sanity) Rating count"
    print total_ratings_count


def has_user_taken_cid(user, course_id):
    return course_id in user.course_ids


def users_who_took(course_id):
    users = m.User.objects()
    users_taken = []
    for user in users:
        if has_user_taken_cid(user, course_id):
            users_taken.append(user)
    return users_taken


def print_users_gender_count():
    users = m.User.objects()
    print users[0].gender
    gender_counts = {
        'male': 0,
        'female': 0,
        'none': 0,
    }
    for u in users:
        if u.gender:
            gender_counts[u.gender] += 1
        else:
            gender_counts['none'] += 1
    print gender_counts


def reviews_after_date(day=truncate_datetime(datetime.now()),
        print_result=False):
    reviews = []
    for uc in m.UserCourse.objects():
        cr = uc.course_review
        pr = uc.professor_review
        if cr and cr.comment and cr.comment_date >= day:
            reviews.append(cr.comment)
            if print_result:
                print cr.comment
        if pr and pr.comment and pr.comment_date >= day:
            reviews.append(pr.comment)
            if print_result:
                print pr.comment
    return reviews


def review_length_hist(reviews, trunc=0, print_result=False):
    hist = defaultdict(int)
    for review in reviews:
        length = len(review) % trunc if trunc else len(review)
        hist[length] += 1
    if print_result:
        for key, val in iter(sorted(hist.items())):
            length = (key + 1) * trunc if trunc else key
            print "%d: %d" % (key, val)
    return hist


def latest_review_date(user):
    latest_date = None
    for uc in user.get_user_courses():
        crd = uc.course_review.comment_date
        prd = uc.professor_review.comment_date
        if not latest_date:
            latest_date = crd
        if crd and latest_date < crd:
            latest_date = crd
        if prd and latest_date < prd:
            latest_date = prd
    return latest_date


def unsafe_clear_schedule(user, term_id=_util.get_current_term_id()):
    for usi in m.UserScheduleItem.objects(user_id=user.id, term_id=term_id):
        usi.delete()

    for uc in m.UserCourse.objects(user_id=user.id, term_id=term_id):
        try:
            user.course_history.remove(uc.id)
        except ValueError:
            print "Weird problem: UC (%s) doesn't exist" % (uc.id)
        uc.delete()

    user.schedules_imported = 0
    user.save()


# Shorthands for common query operations
def ucs_for_cid(course_id):
    return m.UserCourse.objects(course_id=course_id)


def cid(course_id):
    return m.Course.objects.with_id(course_id)


def uid(user_id):
    return m.User.objects.with_id(user_id)


# CSV dumps
# TODO(Sandy): Use dialect functionality of csv?
def ga_date(date_val):
    return date_val.strftime('%Y-%m-%d')


def csv_user_growth(file_name='stats.tmp'):
    signups = defaultdict(int)
    transcripts = defaultdict(int)
    for u in m.User.objects():
        jd = u.join_date
        jd = truncate_datetime(jd)

        if u.has_course_history:
            transcripts[jd] += 1

        signups[jd] += 1

    with open(file_name, 'w+') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([
            'Date',
            'Users signed up',
            'Users imported transcript',
        ])
        for key, s_count in iter(sorted(signups.items())):
            t_count = transcripts[key] if key in transcripts else 0
            writer.writerow([ga_date(key), s_count, t_count])

        csv_file.seek(0)
        return csv_file.read()


def csv_review_growth(file_name='stats.tmp'):
    reviews = defaultdict(int)
    for uc in m.UserCourse.objects():
        cr = uc.course_review
        pr = uc.professor_review
        if cr and cr.comment:
            rd = cr.comment_date
            rd = truncate_datetime(rd)
            reviews[rd] += 1
        if pr and pr.comment:
            rd = pr.comment_date
            rd = truncate_datetime(rd)
            reviews[rd] += 1

    with open(file_name, 'w+') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(['Date', 'Reviews'])
        for key, r_count in iter(sorted(reviews.items())):
            writer.writerow([ga_date(key), r_count])

        csv_file.seek(0)
        return csv_file.read()


def csv_user_points(file_name='user_points.tmp'):
    with open(file_name, 'w+') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([
            'User ID',
            'Name',
            'Program',
            'Year',
            'Points',
            'Reviews written',
            'Ratings given',
            'Link',
        ])
        for user in m.User.objects():
            writer.writerow([
                user.id,
                user.name.encode('utf8'),
                user.program_name,
                user.get_latest_program_year_id(),
                user.num_points,
                reviews_given(user),
                ratings_given(user),
                "https://uwflow.com/profile/%s?as_oid=%s" % (user.id, user.id),
            ])

        csv_file.seek(0)
        return csv_file.read()


def generate_csvs():
    csv_user_growth('user_growth.csv')
    csv_review_growth('review_growth.csv')


# TODO(Sandy): Move to test/debugging file
def print_user_schedule_debug():
    """
    A very light sanity check for backfilling schedule imports
    Diff the results before and after parsing changes
    """
    for user in m.User.objects():
        items = user.get_all_schedule_items()

        courses = set()
        for i in items:
            courses.add(i.course_id)

        safe_name = user.name.encode('utf-8')
        print "%s, %s, %d USIs, %d courses" % (
                str(user.id), safe_name, len(items), len(courses))


# TODO(Sandy): More help info
def stats_help():
    '''
    Print help for stats module
    '''
    for val in dir(sys.modules[__name__]):
        print val

# TODO(Sandy): cleanup this file overtime
# The basic idea is to add queries to this file whenever we want to know
# something, we should never directly do it in ipython. This way, we can reuse
# existing queries and avoid mistakes
if __name__ == '__main__':
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)

    users = m.User.objects()
    courses = m.User.objects()
    ucs = m.User.objects()

    # CSV Dumps
    #csv = csv_user_growth()
    #print csv

    # Ratings/Reviews histograms
    #print_ratings_histogram()
    #print_ratings_count_histogram()
    print_generic_stats()
    print_users_rr_counts()
    #print_program_names(users)
    #print_exam_collection()
    #print users_joined_before(datetime(2012, 10, 19))

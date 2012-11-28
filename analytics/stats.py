from collections import defaultdict
from datetime import datetime
from datetime import timedelta
import csv
import mongoengine as me
import rmc.models as m
import rmc.shared.constants as c
import sys
import time

def print_generic_stats():
    #today = datetime.now() - timedelta(hours=4)
    #today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today = datetime.now() - timedelta(hours=24)
    print "Setting time frame ('Today') to be any time after %s" % today

    users = m.User.objects()
    ucs = m.UserCourse.objects()

    print "Total User"
    print len(users)

    print "User with course_history"
    print sum([1 if user.has_course_history else 0 for user in users])

    print "Total UserCourse"
    print len(ucs)

    uc_cr = 0
    uc_pr = 0
    uc_crat = 0
    uc_prat = 0
    for uc in ucs:
        cr = uc.course_review
        pr = uc.professor_review
        if cr.comment:
            uc_cr += 1
        if cr.interest:
            uc_crat += 1
        if cr.easiness:
            uc_crat += 1
        if cr.usefulness:
            uc_crat += 1
        if pr.comment:
            uc_pr += 1
        if pr.clarity:
            uc_prat += 1
        if pr.passion:
            uc_prat += 1

    print "Total UserCourse Course reviews"
    print uc_cr
    print "Total UserCourse Prof reviews"
    print uc_pr
    print "Total UserCourse Course ratings"
    print uc_crat
    print "Total UserCourse Prof ratings"
    print uc_prat


    print "Users signed up Today"
    join_count = 0
    for user in users:
        join_date = user.join_date
        if join_date >= today:
            join_count += 1
    print join_count

def users_as_of(date):
    users = m.User.objects()
    join_count = 0
    for user in users:
        join_date = user.join_date
        if join_date <= date:
            join_count += 1
    return join_count

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
            #print user.first_name + " " + user.last_name + " " + str(num_review)
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
        #output.encode('UTF-8')
        #print user.fbid
        #output = unicode(user.first_name + " " + user.last_name).decode('UTF-8')
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
    users = m.User.objects()
    signups = defaultdict(int)
    transcripts = defaultdict(int)
    for u in users:
        jd = u.join_date
        jd -= timedelta(
                hours=jd.hour,
                minutes=jd.minute,
                seconds=jd.second,
                microseconds=jd.microsecond)

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

        csv_file.seek(0);
        return csv_file.read()

def csv_review_growth(file_name='stats.tmp'):
    reviews = defaultdict(int)
    for uc in m.UserCourse.objects():
        cr = uc.course_review
        pr = uc.professor_review
        if cr and cr.comment:
            rd = cr.comment_date
            rd -= timedelta(
                    hours=rd.hour,
                    minutes=rd.minute,
                    seconds=rd.second,
                    microseconds=rd.microsecond)
            reviews[rd] += 1
        if pr and pr.comment:
            rd = pr.comment_date
            rd -= timedelta(
                    hours=rd.hour,
                    minutes=rd.minute,
                    seconds=rd.second,
                    microseconds=rd.microsecond)
            reviews[rd] += 1

    with open(file_name, 'w+') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(['Date', 'Reviews'])
        for key, r_count in iter(sorted(reviews.items())):
            writer.writerow([ga_date(key), r_count])

        csv_file.seek(0);
        return csv_file.read()

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
    #print users_as_of(datetime(2012, 10, 19))

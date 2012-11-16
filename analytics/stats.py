import mongoengine as me
import rmc.models as m
from datetime import datetime
from datetime import timedelta

me.connect('rmc', host='localhost', port=27017)

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

def has_user_taken_cid(user, course_id):
    return course_id in user.course_ids

def users_who_took(course_id):
    users = m.User.objects()
    users_taken = []
    for user in users:
        if has_user_taken_cid(user, course_id):
            users_taken.append(user)
    return users_taken

# Shorthands for common query operations
def ucs_for_cid(course_id):
    return m.UserCourse.objects(course_id=course_id)

def cid(course_id):
    return m.Course.objects.with_id(course_id)

def uid(user_id):
    return m.User.objects.with_id(get_user)

# TODO(Sandy): cleanup this file overtime
# The basic idea is to add queries to this file whenever we want to know
# something, we should never directly do it in ipython. This way, we can reuse
# existing queries and avoid mistakes
if __name__ == '__main__':
    users = m.User.objects()
    courses = m.User.objects()
    ucs = m.User.objects()

    print_generic_stats()
    print_users_rr_counts()
    #print_program_names(users)
    #print_exam_collection()
    #print users_as_of(datetime(2012, 10, 19))

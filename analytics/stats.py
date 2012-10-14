import mongoengine as me
import rmc.models as m
from datetime import datetime
from datetime import timedelta

me.connect('rmc', host='localhost', port=27017)

today = datetime.now() - timedelta(hours=24)
today = today.replace(hour=0, minute=0, second=0, microsecond=0)
print "Today is %s" % today

users = m.User.objects()
ucs = m.UserCourse.objects()

print "Total User"
print len(users)

print "User with course_history"
print sum([1 if (user.course_history and len(user.course_history) > 4) else 0 for user in users])

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
    if cr.interest or cr.easiness or cr.usefulness:
        uc_crat += 1
    if pr.comment:
        uc_pr += 1
    if pr.clarity or pr.passion:
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


for user in users:
    #output.encode('UTF-8')
    #print user.fbid
    #output = unicode(user.first_name + " " + user.last_name).decode('UTF-8')
    output = user.first_name + " " + user.last_name
    print output.encode('UTF-8')

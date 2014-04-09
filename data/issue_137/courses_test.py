import json
import urllib2
# This is to test whether we can retrieve all the courses in a department
# using the OpenData API, and get the relevent info

department = "MATH"
KEY = "5db83c33d8d9ce35909f85db2cff487f"

department_file = open("ucalendar_courses/{0}.txt".format(department.lower()))
department_json = json.load(department_file)
department_ids = []

for i in range (len(department_json)):
	department_ids.append (department_json[i]['id'].split(": ")[1])

open_data_json = json.loads (urllib2.urlopen("https://api.uwaterloo.ca/v2/courses/{0}.json?key={1}".format(department.upper(), KEY)).read())
open_data_ids = []

for j in range (len(open_data_json['data'])):
	open_data_ids.append(open_data_json['data'][j]['course_id'])

missing = [c for c in department_ids if c not in open_data_ids]

print "Crawling the calendar found {0} courses".format(len(department_ids))
print "Using the OpenData API found {0} courses".format(len(open_data_ids))
print "There were {0} courses missed by the OpenData API".format(len(missing))

# The condition we're testing for
assert(len(missing) == 0)
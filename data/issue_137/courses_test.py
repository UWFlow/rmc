"""
This is to test whether we can retrieve all the courses in a department
using the OpenData API, and get the relevent info
"""

import json
import requests
from rmc.shared import secrets

department = "MATH"

with open("data/ucalendar_courses/{0}.txt".format(department.lower())) as calendar_file:
	calendar_json = json.load(calendar_file)
calendar_ids = []

for course in calendar_json:
	calendar_ids.append (course['id'].split(": ")[1])

open_data_json = json.loads (requests.get("https://api.uwaterloo.ca/v2/courses/{0}.json?key={1}".format(
	department.upper(), secrets.OPEN_DATA_API_KEY)).text)
open_data_ids = []

for course in open_data_json['data']:
	open_data_ids.append(course['course_id'])

missing_open_data_ids = set(calendar_ids) - set(open_data_ids)
print "Crawling the calendar found {0} courses".format(len(calendar_ids))
print "Using the OpenData API found {0} courses".format(len(open_data_ids))
print "There were {0} courses missed by the OpenData API".format(len(missing_open_data_ids))

# The condition we're testing for
assert(len(missing_open_data_ids) == 0)
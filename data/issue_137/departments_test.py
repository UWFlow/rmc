"""	
A test to ensure that getting departments through the OpenData API will cover all the courses 
we currently get by scraping the course calendar.

Example departments are: AFM, AHS and MATH

Note that for the OpenData API, subjects are equivelant to departments
"""

import json
import requests
from rmc.shared import secrets

# First get the OpenData list of departments
open_data_deps_json =  json.loads (requests.get("https://api.uwaterloo.ca/v2/codes/subjects.json?key={0}".format(
    secrets.OPEN_DATA_API_KEY)).text)
open_data_deps = []

# Add every department to the list, turning them in to all upper case letters
for department in open_data_deps_json['data']:
    open_data_deps.append (department['subject'].upper())

# Load the data we scraped from the calendar, and compare the two lists
with open("data/departments/ucalendar_departments.txt") as calendar_file:
    calendar_json = json.load (calendar_file)
calendar_deps = []

for department in calendar_json:
    calendar_deps.append(department['id'].upper())

# Find the missing departments, if any
missing_open_data_ids = set(calendar_deps) - set(open_data_deps)
print "OpenData found {0} departments".format(len(open_data_deps))
print "Calendar scraping found {0} departments".format(len(calendar_deps)) 
print "There were {0} courses that the OpenData API missed".format(len(missing_open_data_ids))

# The condition we're testing for
assert(len(missing_open_data_ids) == 0)
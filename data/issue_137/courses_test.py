"""
This is to test whether we can retrieve all the courses in a department
using the OpenData API, and get the relevent info
"""

import json
import requests
from rmc.shared import secrets
import os

# We need to load and check we have all the courses for every department
# departments_test.py will run first and store the departments it finds 
# at 'data/departments/opendata2_departments.txt'

with open("data/departments/opendata2_departments.txt") as departments_file:
    departments = json.load(departments_file)
    for d in departments:
        department = d['subject']
        if os.path.isfile("data/ucalendar_courses/{0}.txt".format(department.lower())):
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
            # print "Department is {0}".format(department)
            # print "Crawling the calendar found {0} courses".format(len(calendar_ids))
            # print "Using the OpenData API found {0} courses".format(len(open_data_ids))
            # print "There were {0} courses missed by the OpenData API".format(len(missing_open_data_ids))

            # The condition we're testing for, allow user input to override
            if (len(missing_open_data_ids) != 0):
                print "{0} has an error".format(department)
                cont = raw_input ("Do you want to continue the test? Enter y to continue\n")
                if cont[0] not in "Yy":
                    assert(False)
            else:
                print "{0} is complete".format(department)
        else:
            print "Department found with OpenData that was missed by scraping"
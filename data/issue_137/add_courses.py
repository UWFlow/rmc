"""
Actually add the courses to a text file for loading in to MongoDB
"""

import json
import requests
from rmc.shared import secrets
import os

# We need to run departments_test.py first so that we have an updated list of departments
# This should only be run if the test files run without showing any missing departments or courses

with open("data/departments/opendata2_departments.txt") as departments_file:
    departments = json.load(departments_file)
    # Create a text file for every department
    for d in departments:
        department = d['subject']
        current_dep_json = []

        open_data_json = json.loads (requests.get("https://api.uwaterloo.ca/v2/courses/{0}.json?key={1}".format(
        	department.upper(), secrets.OPEN_DATA_API_KEY)).text)
        open_data_catalog_numbers = []

        for course in open_data_json['data']:
        	open_data_catalog_numbers.append(course['catalog_number'])

        # We now poll the individual endpoints of each course for the data
        with open ("data/opendata2_courses/{0}.json".format(department.lower()), 'w') as courses_out:
            for c in open_data_catalog_numbers:
                print "{0} {1}".format(department, c)
                json_data = json.loads (requests.get("https://api.uwaterloo.ca/v2/courses/{0}/{1}.json?key={2}".format(
                    department.upper(), c, secrets.OPEN_DATA_API_KEY)).text)
                current_dep_json.append(json_data['data'])
            json.dump(current_dep_json, courses_out)

        print "{0} is complete".format(department)
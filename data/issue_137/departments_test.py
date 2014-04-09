import json
import urllib2

# A test to ensure that getting departments through the OpenData API will cover all the courses 
# we currently get by scraping the course calendar.
#
# Example departments are: AFM, AHS and MATH
#
# Note that for the OpenData API, subjects are equivelant to departments

KEY = "5db83c33d8d9ce35909f85db2cff487f"

# First get the OpenData list of departments
open_data_deps_json =  json.loads (urllib2.urlopen("https://api.uwaterloo.ca/v2/codes/subjects.json?key="+KEY).read())
open_data_deps = []

# Add every department to the list, turning them in to all upper case letters
for i in range (len(open_data_deps_json['data'])):
	open_data_deps.append (open_data_deps_json['data'][i]['subject'].upper())

# Load the data we scraped from the calendar, and compare the two lists
calendar_file = open("ucalendar_departments.txt")
calendar_json = json.load (calendar_file)
calendar_deps = []

for j in range (len(calendar_json)):
	calendar_deps.append(calendar_json[j]['id'].upper())

# Find the missing departments, if any
missing = [d for d in calendar_deps if d not in open_data_deps]
print "OpenData found {0} departments".format(len(open_data_deps))
print "Calendar scraping found {0} departments".format(len(calendar_deps)) 
print "There were {0} courses that the OpenData API missed".format(len(missing))

calendar_file.close()

# The condition we're testing for
assert(len(missing) == 0)
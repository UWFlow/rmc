# TODO(Sandy): add beautifulsoup to requirements.txt. Has to be 3.x not 4.x for
# the import statement to work
from BeautifulSoup import BeautifulSoup
import time;
import pickle
import urllib
import urllib2
import sys

# Supply your own credentials here
username = ""
password = ""
if username == "" or password == "":
	print "Please supply your credentials in the code!"
	sys.exit();

cur_time = str(int(time.time()))
output_dir = "output/"
output_file_name = output_dir + "results_" + cur_time + ".txt"
error_file_name = output_dir + "error_" + cur_time + ".txt"

# Add on password stuff
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
top_level_url = "https://www.eng.uwaterloo.ca/critiques/index.php"
password_mgr.add_password(None, top_level_url, username, password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)
opener.open(top_level_url)
urllib2.install_opener(opener)

# Grab local file for request data and list of all possible courses
url = "https://www.eng.uwaterloo.ca/critiques/index.php"
file = open("post_headers.txt","r")
post_headers = pickle.load(file)
file.close()
file = open("course_list.txt","r")
courses = file.read().split("|")
file.close()
file = open(output_file_name,"w")
err_file = open(error_file_name,"w")

for course in courses:
	post_headers["course"] = course

	print course;
	last_space = course.rfind(" ")
	course_code = course[:last_space]
	course_num = course[last_space + 1:]

	data = urllib.urlencode(post_headers)
	req = urllib2.Request(url, data)
	response = urllib2.urlopen(req)
	the_page = response.read()

	doc = the_page
	soup = BeautifulSoup(doc)
	litmus = soup.findAll(attrs={"id":"primarycontent"})

	if not litmus[0].contents[1].contents[0] == "No results were found.":
		result = soup.findAll("tr")
		course_dict = {
			"code": course_code,
			"num": course_num,
			"critiques": []
		}

		critique = {}
		data = {}

		result_length = len(result);
		if result_length >= 230:
# TODO(Sandy): Remember to scrape individual terms for courses with > 10 results
			print "More than 10 results"
			err_file.write(course + " got more than 10 results (" + str(result_length) + ")\n")

		for i in range(0, result_length):
			if (i % 23) == 0:
				times = result[i].contents[1].contents[0].lstrip("Term: ").rstrip().split();
				prof = result[i].contents[3].contents[0].lstrip("Instructor: ").rstrip();
				critique = {
					"prof": prof,
					"term": times[0],
					"year": times[1]
				}
				data = {}
			elif (i % 23) == 22:
				critique["class_size"] = int(result[22].contents[5].contents[0].lstrip("Class Size: "))
				critique["total_replies"] = int(result[22].contents[3].contents[0].lstrip("Total replies: "))
				critique["data"] = data

				course_dict["critiques"].append(data)
			elif len(result[i]) == 20:
				q = int(result[i].contents[0].contents[0].contents[0])
				data[q] = {}
				data[q]["replies"] = int(result[i].contents[2].contents[0])

				data[q]["A"] = int(result[i].contents[6].contents[0])
				data[q]["B"] = int(result[i].contents[8].contents[0])
				data[q]["C"] = int(result[i].contents[10].contents[0])
				data[q]["D"] = int(result[i].contents[12].contents[0])
				data[q]["E"] = int(result[i].contents[14].contents[0])

				data[q]["average"] = int(result[i].contents[18].contents[0])

		file.write(str(course_dict)+"\n")
		print "Data fetched and saved!"
	else:
		print "No results"

	
file.close()


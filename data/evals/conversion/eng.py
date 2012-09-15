from pymongo import Connection
import sys
import ast

def get_db():
  connection = Connection("localhost", 27017)
  return connection.rmc

def ensure_course_evals_indices(coll):
	coll.ensure_index("course")
	coll.ensure_index("comm")
	coll.ensure_index("passion")
	coll.ensure_index("overall_course")
	coll.ensure_index("term")
	coll.ensure_index("year")
	coll.ensure_index("prof")
	coll.ensure_index("interest")
	coll.ensure_index("ease")
	coll.ensure_index("overall_prof")

# Normalize critique scores to be in [0, 1]
def normalize_score(score):
	return (score["A"] * 4 + score["B"] * 3 + score["C"] * 2 + score["D"]) / 400.0

if (len(sys.argv) < 2):
	print "Please pass the Eng data filename as the first Argument"
	sys.exit()

db = get_db()
course_evals = db.course_evals

# TODO(Sandy): Write a script that will fetch raw data and feed it into this
input_file = open(sys.argv[1], "r")

line = input_file.readline()
while line:
	data = ast.literal_eval(line);

	course_name = data["code"] + " " + data["num"]

	for critique in data["critiques"]:
		prof_name = critique["prof"]
		term = critique["term"]
		year = critique["year"]

		scores = critique["scores"]
# Prof directed ratings
# COMMUNICATION
# presentation in lectures (organization and clarity)
		c1 = normalize_score(scores[1])
# response to questions
		c2 = normalize_score(scores[2])
# oral presentation (audibility, articulation, english)
		c3 = normalize_score(scores[3])
# visual presentation (organization, legibility, effective use of materials)
		c4 = normalize_score(scores[4])
# PASSION
# attitude towards teachings the course
		p1 = normalize_score(scores[8])
# OVERALL
# overall appraisal of quality of teaching
		op1 = normalize_score(scores[10])

# Course directed ratings
# INTEREST
# XXX(Sandy): Revise the use of this question-metric before launch
# how many classes attended
		i1 = normalize_score(scores[18])
# EASINESS
		e1 = normalize_score(scores[11])
		e2 = normalize_score(scores[12])
# OVERALL
		oc1 = normalize_score(scores[17])

# TODO(Sandy): Try different weightings to see if we can get better data
		rating = {
			"course": course_name,
			"comm": c1 * 0.2 + c2 * 0.2 + c3 * 0.4 + c4 * 0.2,
			"passion": p1,
			"overall_course": oc1,
			"term": term,
			"year": year,
			"prof": critique["prof"],
			"interest": i1,
			"ease": e1 * 0.5 + e2 * 0.5,
			"overall_prof": op1
		}
		course_evals.insert(rating)

	line = input_file.readline()

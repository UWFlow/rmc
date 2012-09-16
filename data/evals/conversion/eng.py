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

    course_name = data["code"] + data["num"]

    for critique in data["critiques"]:
        prof_name = critique["prof"]
        term = critique["term"]
        year = critique["year"]

        scores = critique["scores"]
# Prof directed ratings
# COMMUNICATION
# presentation in lectures (organization and clarity)
        c1 = normalize_score(scores[1])
        c1r = scores[1]['num_replies']
# response to questions
        c2 = normalize_score(scores[2])
        c2r = scores[2]['num_replies']
# oral presentation (audibility, articulation, english)
        c3 = normalize_score(scores[3])
        c3r = scores[3]['num_replies']
# visual presentation (organization, legibility, effective use of materials)
        c4 = normalize_score(scores[4])
        c4r = scores[4]['num_replies']
        c_total = c1 * 0.2 + c2 * 0.2 + c3 * 0.4 + c4 * 0.2
        c_count = int(round(c1r * 0.2 + c2r * 0.2 + c3r * 0.4 + c4r * 0.2))
# PASSION
# attitude towards teachings the course
        p1 = normalize_score(scores[8])
        p1r = scores[8]['num_replies']
# OVERALL
# overall appraisal of quality of teaching
        op1 = normalize_score(scores[10])
        op1r = scores[10]['num_replies']

# Course directed ratings
# INTEREST
# TODO(Sandy): Revise the use of this question-metric
# how many classes attended
        i1 = normalize_score(scores[17])
        i1r = scores[17]['num_replies']
# EASINESS
# difficulty of concepts
        e1 = normalize_score(scores[11])
        e1r = scores[11]['num_replies']
# workload
        e2 = normalize_score(scores[12])
        e2r = scores[12]['num_replies']
        e_total = e1 * 0.5 + e2 * 0.5
        e_count = int(round(e1r * 0.5 + e2r * 0.5))
# OVERALL
        oc1 = i1 * 0.5 + e1 * 0.25 + e2 * 0.25
        oc_count = int(round(i1r * 0.5 + e1r * 0.25 + e2r * 0.25))

# TODO(Sandy): Try different weightings to see if we can get better data
        rating = {
            "course": course_name,
            "term": term,
            "year": year,
            "comm": c_total,
            "comm_count": c_count,
            "passion": p1,
            "passion_count": p1r,
            "overall_course": oc1,
            "overall_course_count": oc_count,
            "prof": critique["prof"],
            "interest": i1,
            "interest_count": i1r,
            "easiness": e_total,
            "easiness_count": e_count,
            "overall_prof": op1,
            "overall_prof_count": op1r
        }
        course_evals.insert(rating)

    line = input_file.readline()

from pymongo import Connection
import sys
import ast
import re
import mongoengine as me

import rmc.shared.constants as c
import rmc.models as m

# Normalize critique scores to be in [0, 1]
def normalize_score(score):
    return (score["A"] * 4 + score["B"] * 3 + score["C"] * 2 + score["D"]) / 400.0

def clean_name(name):
    return re.sub(r'\s+', ' ', name.strip())

# Stolen from processor.py
def get_prof_names(prof_name):
    matches = re.findall(r'^(.+?), (.+)$', prof_name)[0]
    return {
        'first_name': clean_name(matches[1]),
        'last_name': clean_name(matches[0]),
    }

def import_critiques(input_file):
    line = input_file.readline()
    while line:
        data = ast.literal_eval(line);

        course_id = (data["code"] + data["num"]).lower()

        for critique in data["critiques"]:

            # arch247 and math212 are dumb. Has 'n/a' or '' for prof, which becomes '/a' or '' after parsing
            prof_name = critique['prof']
            if prof_name == '/a' or prof_name == '':
                continue

            # Eg. Morton, Andrew OR Morton, A
            # FIXME(Sandy): Normalize prof names
            prof_names = get_prof_names(prof_name)
            prof = m.Professor(**prof_names)
            # Note: Manually verified that .save() will not erase existing fields that are not set on save (ie. ratings)
            prof.save()
            professor_id = prof.id

            season = critique["term"]
            year = critique["year"]
            term_id = m.Term.get_id_from_year_season(year, season)

            # The score index correspond directly to the question numbers (ie. arrays are 1-indexed)
            scores = critique["scores"]

            def clarity_from_scores(scores):
                Q1_WEIGHT = 0.2
                Q2_WEIGHT = 0.2
                Q3_WEIGHT = 0.4
                Q4_WEIGHT = 0.2
                # CLARITY
                # presentation in lectures (organization and clarity)
                c1 = normalize_score(scores[1]) * Q1_WEIGHT
                c1r = scores[1]['num_replies'] * Q1_WEIGHT
                # response to questions
                c2 = normalize_score(scores[2]) * Q2_WEIGHT
                c2r = scores[2]['num_replies'] * Q2_WEIGHT
                # oral presentation (audibility, articulation, english)
                c3 = normalize_score(scores[3]) * Q3_WEIGHT
                c3r = scores[3]['num_replies'] * Q3_WEIGHT
                # visual presentation (organization, legibility, effective use of materials)
                c4 = normalize_score(scores[4]) * Q4_WEIGHT
                c4r = scores[4]['num_replies'] * Q4_WEIGHT
                c_count = int(round(c1r + c2r + c3r + c4r))
                c_rating = (c1 + c2 + c3 + c4) / max(1, c_count)
                return m.AggregateRating(rating=c_rating, count=c_count)

            def passion_from_scores(scores):
                # PASSION
                # attitude towards teachings the course
                p_count = scores[8]['num_replies']
                p_rating = normalize_score(scores[8]) / max(1, p_count)
                return m.AggregateRating(rating=p_rating, count=p_count)

            def overall_prof_from_scores(scores):
                # OVERALL
                # overall appraisal of quality of teaching
                op_count = scores[10]['num_replies']
                op_rating = normalize_score(scores[10]) / max(1, op_count)
                return m.AggregateRating(rating=op_rating, count=op_count)

            def interest_from_scores(scores):
                # Course directed ratings
                # INTEREST
                # TODO(Sandy): Revise the use of this question-metric
                # how many classes attended
                i_count = scores[17]['num_replies']
                i_rating = normalize_score(scores[17]) / max(1, i_count)
                return m.AggregateRating(rating=i_rating, count=i_count)

            def easiness_from_scores(scores):
                Q11_WEIGHT = 0.5
                Q12_WEIGHT = 0.5
                # EASINESS
                # difficulty of concepts
                e1 = normalize_score(scores[11]) * Q11_WEIGHT
                e1r = scores[11]['num_replies'] * Q11_WEIGHT
                # workload
                e2 = normalize_score(scores[12]) * Q12_WEIGHT
                e2r = scores[12]['num_replies'] * Q12_WEIGHT
                e_count = int(round(e1r + e2r))
                e_rating = (e1 + e2) / max(1, e_count)
                return m.AggregateRating(rating=e_rating, count=e_count)

            def overall_course_from_interest_easiness(i, e):
                INTEREST_WEIGHT = 0.5
                EASINESS_WEIGHT = 0.5
                # OVERALL
                oc_count = int(round(i.count * INTEREST_WEIGHT + e.count * EASINESS_WEIGHT))
                oc_rating = (i.rating * INTEREST_WEIGHT + e.rating * EASINESS_WEIGHT) / max(1, oc_count)
                return m.AggregateRating(rating=oc_rating, count=oc_count)

# TODO(Sandy): Try different weightings to see if we can get better data
            interest = interest_from_scores(scores)
            easiness = easiness_from_scores(scores)
            overall_course = overall_course_from_interest_easiness(interest, easiness)
            clarity = clarity_from_scores(scores)
            passion = passion_from_scores(scores)
            overall_prof = overall_prof_from_scores(scores)

            critique_course = {
                'course_id': course_id,
                'professor_id': professor_id,
                'term_id': term_id,
                'interest': interest,
                'easiness': easiness,
                'overall_course': overall_course,
                'clarity': clarity,
                'passion': passion,
                'overall_prof': overall_prof,
            }
            m.CritiqueCourse(**critique_course).save()

        line = input_file.readline()

    print 'imported %d course critiques' % m.CritiqueCourse.objects.count()


# TODO(Sandy): Write a script that will fetch raw data and feed it into this
if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print "Please pass the Eng data filename as the first Argument"
        sys.exit()
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)

    input_file = open(sys.argv[1], "r")
    import_critiques(input_file)

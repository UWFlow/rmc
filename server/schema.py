"""Really really ghetto rough schema definition checked in locally so we don't need to depend on Google Docs.
"""

# TODO(david): Use an ORM or define this in some real format that can be used
#     by automated tools or w/e... I'm a mongo noob

"""
users
- implicit ObjectId
- first_name
- last_name
- fb_access_token
- fbid
- join_date
- last_login_date
- visits
- school
- email
- faculty
- program
- birth_date?

user_courses
- user_id
- course_id
- prof_id
- section_id
- course_review
    - interest: {count, rating}
    - easiness: {count, rating}
    - review
    - review_date
- prof_review
    - passion: {count, rating}
    - clarity: {count, rating}
    - review
    - review_date

sections
- prof_id
- term (2011 Winter => 2011_01)
- section_number (or section_code, or designation)
- course_id


prof_course
- prof_id
- course_id
- aggregate_rating_id
- user_review_ids
- menlo_ids

aggregate_ratings
- course_id
- prof_id
- course
    - interest: {count, rating}
    - easiness: {count, rating}
    - overall: {count, rating}
- prof
    - passion: {count, rating}
    - clarity: {count, rating}
    - overall: {count, rating}


REUSE OLD MENLO
menlo (TODO(Sandy): get Mack to revise this collection, migrate courses over)
- course
- prof
- course
    - interest: {count, rating}
    - easiness: {count, rating}
- prof
    - passion: {count, rating}
    - clarity: {count, rating}
"""

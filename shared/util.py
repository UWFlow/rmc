import datetime
import logging
import math
import traceback

import pytz

from bson import json_util, ObjectId

import rmc.shared.constants as c


def json_loads(json_str):
    return json_util.loads(json_str)

def json_dumps(obj):
    return json_util.dumps(obj).replace('</', '<\\/')

def dict_to_list(dikt):
    # TODO(jlfwong): This function's name is horribly misleading about what it
    # does - rename and document
    update_with_name = lambda key, val: dict(val, **{ 'name': key })
    return [update_with_name(k, v) for k, v in dikt.iteritems()]

def get_term_id_for_date(the_date):
    # From http://ugradcalendar.uwaterloo.ca/page/uWaterloo-Calendar-Events-and-Academic-Deadlines
    # Seems should be usually right; just not sure of Spring term always
    # starting on May...
    # TODO(david): uWaterloo specific
    term_start_months = [9, 5, 1]

    # Find the month this term started
    for month in term_start_months:
        if the_date.month >= month:
            start_month = month
            break

    return "%d_%02d" % (the_date.year, start_month)

def get_current_term_id():
    return get_term_id_for_date(datetime.datetime.now())

# Ported Ruby's Statistics2.pnormaldist(qn) to Python
# http://stackoverflow.com/questions/6116770/whats-the-equivalent-of-rubys-pnormaldist-statistics-function-in-haskell
# inverse of normal distribution ([2])
# Pr( (-\infty, x] ) = qn -> x
def pnormaldist(qn):
    b = [1.570796288, 0.03706987906, -0.8364353589e-3,
        -0.2250947176e-3, 0.6841218299e-5, 0.5824238515e-5,
        -0.104527497e-5, 0.8360937017e-7, -0.3231081277e-8,
        0.3657763036e-10, 0.6936233982e-12]

    if qn < 0.0 or 1.0 < qn:
        logging.error("Error : qn <= 0 or qn >= 1  in pnorm()!")
        return 0.0;

    if qn == 0.5:
        return 0.0

    w1 = qn
    if qn > 0.5:
        w1 = 1.0 - w1
    w3 = -math.log(4.0 * w1 * (1.0 - w1))
    w1 = b[0]
    for i in range(1, 11):
        w1 += b[i] * w3**i;

    if qn > 0.5:
        return math.sqrt(w1 * w3)

    return -math.sqrt(w1 * w3)

def get_sorting_score(phat, n, confidence=c.RATINGS_CONFIDENCE):
    """
    Get the score used for sorting by ratings

    Returns the lower bound on Wilson Score. See
    http://evanmiller.org/how-not-to-sort-by-average-rating.html

    Args:
        phat: The observed proportion of positive ratings (0 <= phat <= 1)
        n: The total number of ratings
        confidence: How much confidences we want for this to be the lower bound?
    """
    if n == 0:
        return 0

    try:
        if confidence == c.RATINGS_CONFIDENCE:
            z = 1.9599639715843482
        else:
            z = pnormaldist(1-(1-confidence)/2)
        # Modified to optimize for our data model
        #phat = 1.0*pos/n
        retVal = (phat + z*z/(2*n) -
                z * math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)
    except:
        # This should never happen, so we should debug this case as soon as we
        # get the error.
        # Returning phat should be the same as calling the function with n=INF.
        # While this is bad, it's better than nothing and we can fix it
        # with the re-aggregator.
        logging.error('get_sorting_score(%s, %s, %s) threw an exception'
                % (phat, n, confidence))
        logging.error(' '.join(traceback.format_stack()))
        retVal = max(0, min(1, phat))
    return retVal

def flatten_dict(dikt):
    """Flatten dict into 1 level by JSON-encoding all non-primitive values."""
    flattened = {}
    for k, v in dikt.iteritems():
        if isinstance(v, dict) or isinstance(v, list):
            flattened[k] = json_util.dumps(v)
        elif isinstance(v, ObjectId):
            flattened[k] = str(v)
        else:
            flattened[k] = v
    return flattened

def eastern_to_utc(date):
    tz = pytz.timezone('US/Eastern')
    return utc_date(date, tz)

def utc_date(date, tz):
    return tz.normalize(tz.localize(date)).astimezone(pytz.utc)

def to_dict(doc, fields):
    # TODO(jlfwong): This looks like it's only used in one place and should
    # be killed off
    """Warning: Using this convenience fn is probably not as efficient as the
    plain old manually building up a dict."""
    def map_field(prop):
        val = getattr(doc, prop)
        return val.to_dict() if hasattr(val, 'to_dict') else val

    return { f: map_field(f) for f in fields }

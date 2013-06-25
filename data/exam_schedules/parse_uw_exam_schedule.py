from time import mktime
from datetime import datetime
from datetime import timedelta

import argparse
import mongoengine
import os
import re
import sys
import time

import rmc.models as m
import rmc.shared.constants as c
import rmc.shared.util as rmc_util

# TODO(Sandy): move into better place
def safe_list_get(l, idx, default=''):
    try:
        return l[idx]
    except IndexError:
        print "failed to get %s-th term of '%s'" % (idx, ' '.join(l))
        return default

days_of_week = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
];

# TODO(sandy): Figure out how to match multple words in regex. |'s didn't work
def is_day_of_week(token):
    for day in days_of_week:
        if re.match(day, token):
            return True

    return False

def parse_exam_schedule(exam_file_name):

    m.Exam.objects._collection.drop()

    exam_file = open(exam_file_name)


    for line in exam_file:
        index = 0
        tokens = re.split('\s+', line)

        # Get the course ID
        course_id = safe_list_get(tokens, 0) + safe_list_get(tokens, 1)
        course_id = course_id.lower()

        if not course_id:
            print "Skipping line '%s'" % ' '.join(tokens)
            continue

        # Get the sections
        # day_of_week_pattern = re.compile(
        index = 2
        section_string = ''
        while not is_day_of_week(safe_list_get(tokens, index)):
            section_string += safe_list_get(tokens, index) + ' '
            index += 1

        section_string = section_string.strip()

        # Get the date. Next 4 tokens is Tuesday December 11, 2012
        exam_date_string = ''
        for i in range(index, index + 4):
            exam_date_string += safe_list_get(tokens, i) + ' '

        index += 4

        start_date_string = (exam_date_string + safe_list_get(tokens, index) +
            safe_list_get(tokens, index + 1))
        index += 2

        end_date_string = (exam_date_string + safe_list_get(tokens, index) +
            safe_list_get(tokens, index + 1))
        index += 2

        # E.g. Tuesday December 11, 2012 7:30PM
        #      Tuesday December 11, 2012 10:00PM
        date_format = "%A %B %d, %Y %I:%M%p"

        # TODO(sandy): do timezones better
        try:
            start_date = rmc_util.eastern_to_utc(
                    datetime.fromtimestamp(
                        mktime(time.strptime(start_date_string, date_format))))
            end_date = rmc_util.eastern_to_utc(
                    datetime.fromtimestamp(
                        mktime(time.strptime(end_date_string, date_format))))
        except Exception as exp:
            print "Could not get date for line '%s'" % ' '.join(tokens)
            # Don't remmeber exactly what exception I was trying to catch...
            print exp
            start_date = None
            end_date = None

        # Get the location
        location = ''
        while index < len(tokens):
            location += tokens[index] + ' '
            index += 1

        location = location.strip()

        exam_slot = m.Exam()
        exam_slot.course_id = course_id
        exam_slot.sections = section_string
        exam_slot.start_date = start_date
        exam_slot.end_date = end_date
        exam_slot.location = location

        if (start_date and end_date):
            exam_slot.info_known = True;
        else:
            exam_slot.info_known = False;

        exam_slot.save()

        # TODO(Sandy): Set URL


if __name__ == '__main__':
    mongoengine.connect(c.MONGO_DB_RMC)

    parser = argparse.ArgumentParser()
    parser.add_argument('exam_file', help='Processed exam file (see notes)')
    args = parser.parse_args()

    parse_exam_schedule(args.exam_file)

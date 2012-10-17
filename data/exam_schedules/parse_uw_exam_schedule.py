from time import mktime
from datetime import datetime

import mongoengine
import os
import re
import sys
import time

import rmc.models as m
import rmc.shared.constants as c

mongoengine.connect(c.MONGO_DB_RMC)

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
    print 'given token'
    print token
    for day in days_of_week:
        if re.match(day, token):
            return True

    return False

def parse_exam_schedule():
    reg = re.compile(r'^(.*?)\s+\((\w+)\).*$')

    # TODO(Sandy): Don't hardcode path. Look at example from crawler.py
    exam_file = open('uw_oct_16_2012_good.txt')


    for line in exam_file:
        index = 0
        tokens = re.split('\s+', line)

        for token in tokens:
            print "%s" % token
        print ' '

        # Get the course ID
        course_id = safe_list_get(tokens, 0) + safe_list_get(tokens, 1)
        course_id.lower()

        if not course_id:
            print "Skipping line '%s'" % ' '.join(tokens)
            continue

        # Get the sections
        # day_of_week_pattern = re.compile(
        index = 2
        print 'sections'
        section_string = ''
        while not is_day_of_week(safe_list_get(tokens, index)):
            print "section: %s" % safe_list_get(tokens, index)
            section_string = safe_list_get(tokens, index) + ' '
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
        # TODO(sandy): See if timezone matters

        try:
            start_date = datetime.fromtimestamp(mktime(
                    time.strptime(start_date_string, date_format)))
            end_date = datetime.fromtimestamp(mktime(
                    time.strptime(end_date_string, date_format)))
        except:
            print "Could not get date for line '%s'" % ' '.join(tokens)
            start_date = None
            end_date = None

        print "my dates"
        print start_date
        print end_date

        # Get the location
        location = ''
        while index < len(tokens):
            location += tokens[index] + ' '
            index += 1

        location = location.strip()
        print "my location=%s" % location

        exam_slot = m.Exam()
        exam_slot.course_id = course_id
        exam_slot.sections = section_string
        exam_slot.start_date = start_date
        exam_slot.end_date = end_date
        exam_slot.location = location

        if (start_date and end_date):
            exam_slot.info_known = True;

        exam_slot.save()

        # TODO(Sandy): Set URL


if __name__ == '__main__':
    parse_exam_schedule()

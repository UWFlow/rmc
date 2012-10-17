import re
import os
import sys

import rmc.models as m

# TODO(Sandy): move into better place
def safe_list_get(l, idx, default=''):
    try:
        return l[idx]
    except IndexError:
        print "failed to get %s-th term of '%s'" % (idx, l.join())
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
    exam_file = open('uw_oct_16_2012.txt')


    for line in exam_file:
        tokens = re.split('\s+', line)

        exam_slot = m.ExamSlot()

        for token in tokens:
            print "%s" % token
        print ' '

        # Get the course ID
        course_id = safe_list_get(tokens, 0) + safe_list_get(tokens, 1)
        course_id.lower()

        if not course_id:
            print "Skipping line '%s'" % l.join()
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

        exam_date_string = exam_date_string.strip()
        index += 4

        start_time_string = safe_list_get(tokens, index) +
            safe_list_get(tokens, index + 1)
        index += 2

        end_time_string = safe_list_get(tokens, index) +
            safe_list_get(tokens, index + 1)
        index += 2





        break;


if __name__ == '__main__':
    parse_exam_schedule()

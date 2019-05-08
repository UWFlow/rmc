import pdftotext

import re

COURSE_REGEXP = re.compile(r'([A-Z]{2,})\s+(\d{1,3}\w?)\s')
LEVEL_REGEXP = re.compile(r'Level:\s+(\d\w)')
TERM_REGEXP = re.compile(r'(Fall|Winter|Spring)\s+(\d{4})')

STUDENT_ID_REGEXP = re.compile(r'Student ID:\s+(\d+)')
PROGRAM_NAME_REGEXP = re.compile(r'Program:\s+(.*?)\n')


def _partition(courses, levels):
    partitions = [[] for _ in range(len(levels))]
    i, j = 0, 0

    for j in range(len(levels) - 1):
        while i < len(courses) and levels[j].start() < courses[i].start() < levels[j + 1].start():
            partitions[j].append(courses[i])
            i += 1

    partitions[j] = levels[i:]

    return partitions


def _assemble_schedule(terms, levels, courses):
    course_partition = _partition(courses, levels)
    return [
        {
            'name': terms[i].group(0),
            'programYearId': levels[i].group(1),
            'courseIds': [(c.group(1) + c.group(2)).lower() for c in course_partition[i]],
        }
        for i in range(len(levels)) if course_partition[i]
    ]


def parse_text(text):
    student_id = STUDENT_ID_REGEXP.search(text).group(1)
    program_name = PROGRAM_NAME_REGEXP.search(text).group(1)

    # .finditer() returns a Match, so this is not equivalent to .findall()
    courses = list(COURSE_REGEXP.finditer(text))
    levels = list(LEVEL_REGEXP.finditer(text))
    terms = list(TERM_REGEXP.finditer(text))

    return {
        'coursesByTerm': _assemble_schedule(terms, levels, courses),
        'studentId': student_id,
        'programName': program_name,
    }


def parse_file(data):
    parsed = pdftotext.PDF(data)
    text = ''.join(str(page) for page in parsed)
    return parse_text(text)

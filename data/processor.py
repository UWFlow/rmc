import rmc.shared.constants as c

import copy
from datetime import datetime
import glob
import json
import os
from pymongo import Connection
import re
import sys

COURSES_DATA_DIR = 'courses'
RATINGS_DATA_DIR = 'ratings'
DEPARTMENTS_DATA_DIR = 'departments'

def get_db():
  connection = Connection(c.MONGO_HOST, c.MONGO_PORT)
  return connection.rmc

def import_departments():
  db = get_db()
  departments = db.departments

  departments.remove()
  departments.ensure_index('name', unique=True)
  for file_name in glob.glob(os.path.join(sys.path[0], DEPARTMENTS_DATA_DIR, '*.txt')):
    f = open(file_name, 'r')
    data = json.load(f)
    f.close()
    for department in data:
      department['name'] = department['Acronym']
      departments.insert(department)
  print 'imported departments:', departments.count()

def ensure_rating_indices(collection):
  collection.ensure_index('ratings.aggregate.average')
  collection.ensure_index('ratings.clarity.average')
  collection.ensure_index('ratings.easy.average')
  collection.ensure_index('ratings.helpful.average')
  collection.ensure_index('ratings.interest.average')
  collection.ensure_index('ratings.aggregate.count')
  collection.ensure_index('ratings.clarity.count')
  collection.ensure_index('ratings.easy.count')
  collection.ensure_index('ratings.helpful.count')
  collection.ensure_index('ratings.interest.count')

def import_courses():
  db = get_db()
  courses = db.courses
  departments = db.departments

  courses.remove()
  courses.ensure_index('name', unique=True)
  courses.ensure_index('title', unique=True)
  ensure_rating_indices(courses)
  for file_name in glob.glob(os.path.join(sys.path[0], COURSES_DATA_DIR, '*.txt')):
    f = open(file_name, 'r')
    data = json.load(f)
    f.close()
    for course_code in data:
      course = data[course_code]
      course_name = course['DeptAcronym'] + course['Number']
      if departments.find({'name': course['DeptAcronym']}).count() == 0:
        print 'skipping ' + course_name
        continue
      course['name'] = course_name
      course['title'] = course['Title']
      del course['Title']
      course['description'] = course['Description']
      del course['Description']
      courses.insert(course)
  print 'imported courses:', courses.count()

def import_professors():
  db = get_db()
  professors = db.professors

  professors.remove()
  professors.ensure_index('department')
  professors.ensure_index('name', unique=True)
  professors.ensure_index('first_name')
  professors.ensure_index('last_name')
  professors.ensure_index('prof_id', unique=True)
  ensure_rating_indices(professors)
  file_names = glob.glob(os.path.join(sys.path[0], RATINGS_DATA_DIR, '*.txt'))
  for file_name in file_names:
    f = open(file_name, 'r')
    data = json.load(f)
    f.close()
    prof_name = data['prof_name']
    matches = re.findall(r'^(.+?), (.+)$', prof_name)[0]
    professor = {
      'name': prof_name,
      'last_name': matches[0],
      'first_name': matches[1],
      'prof_id': data['prof_id'],
    }
    professor['department'] = None
    if 'info' in data and 'Department' in data['info']:
      professor['department'] = data['info']['Department'].strip()
    professors.insert(professor)
  print 'imported professors:', professors.count()

def import_ratings():
  db = get_db()
  ratings = db.ratings
  courses = db.courses
  departments = db.departments
  rating_mappings = {
    'r_clarity': 'clarity',
    'r_easy': 'easy',
    'r_helpful': 'helpful',
    'r_interest': 'interest',
  }

  ratings.remove()
  ratings.ensure_index('course_name')
  ratings.ensure_index('professor_name')
  ratings.ensure_index('rating_id', unique=True)
  ratings.ensure_index('time')
  file_names = glob.glob(os.path.join(sys.path[0], RATINGS_DATA_DIR, '*.txt'))
  for file_name in file_names:
    f = open(file_name, 'r')
    data = json.load(f)
    f.close()
    for rating in data['ratings']:
      course = rating['class']
      if course is None:
        #print 'skipping rating because course is None'
        continue
      course = course.upper()
      matches = re.findall(r'([A-Z]+).*?([0-9]{3}[A-Z]?)(?:[^0-9]|$)', course)
      if len(matches) != 1 or len(matches[0]) != 2:
        #print 'skipping rating because bad course'
        continue
      department = matches[0][0]
      course = matches[0][1]
      if departments.find({'name': department}).count() == 0:
        #print 'skipping rating because invalid department ' + matches[0][0]
        continue
      course_name = department + course
      if courses.find({'name': course_name}).count() == 0:
        #print 'skipping rating because invalid course ' + course_name
        continue
      rating['course_name'] = course_name
      rating['professor_name'] = data['prof_name']
      rating['rating'] = {}
      for rating_key in rating_mappings:
        if rating_key in rating:
          try:
            r = rating[rating_key]
            del rating[rating_key]
            rating['rating'][rating_mappings[rating_key]] = int(r)
          except:
            pass
      #print 'adding rating for course ' + course_name
      rating['time'] = int(datetime.strptime(rating['date'], '%m/%d/%y').strftime('%s'))
      ratings.insert(rating)
  print 'imported ratings:', ratings.count()

def update_ratings(category):
  db = get_db()
  category_mapping = {
    'course': {
      'collection': db.courses,
      'key': 'course_name',
      'list': 'professors',
      'other': 'professor_name',
    }, 'professor': {
      'collection': db.professors,
      'key': 'professor_name',
      'list': 'courses',
      'other': 'course_name',
    },
  }
  category_data = category_mapping[category]
  collection = category_data['collection']
  rating_defaults = {
    'count': 0,
    'aggregate': {'count': 0, 'total': 0, 'average': 0.0},
    'clarity': {'count': 0, 'total': 0, 'average': 0.0},
    'easy': {'count': 0, 'total': 0, 'average': 0.0},
    'helpful': {'count': 0, 'total': 0, 'average': 0.0},
    'interest': {'count': 0, 'total': 0, 'average': 0.0},
  }
  rating_types = ['clarity', 'easy', 'helpful', 'interest']
  category_names = collection.distinct('name')
  counter = 0
  for category_name in category_names:
    category_ratings = copy.deepcopy(rating_defaults)
    others = []
    other_names = db.ratings.find({category_data['key']: category_name}).distinct(category_data['other'])
    for other_name in other_names:
      other = {
        'name': other_name,
        'ratings': copy.deepcopy(rating_defaults),
      }
      ratings_data = db.ratings.find({category_data['key']: category_name, category_data['other']: other_name})
      for rating_data in ratings_data:
        other['ratings']['count'] += 1
        for rating_type in rating_data['rating']:
          other['ratings'][rating_type]['count'] += 1
          other['ratings'][rating_type]['total'] += rating_data['rating'][rating_type]
      count = 0
      total = 0
      category_ratings['count'] += other['ratings']['count']
      for rating_type in rating_types:
        tmp_count = other['ratings'][rating_type]['count']
        tmp_total = other['ratings'][rating_type]['total']
        count += tmp_count
        total += tmp_total
        category_ratings[rating_type]['count'] += tmp_count
        category_ratings[rating_type]['total'] += tmp_total
        if tmp_count > 0:
          other['ratings'][rating_type]['average'] = float(tmp_total) / tmp_count
      if count > 0:
        other['ratings']['aggregate']['count'] = count
        other['ratings']['aggregate']['total'] = total
        other['ratings']['aggregate']['average'] = float(total) / count
      others.append(other)
    count = 0
    total = 0
    for rating_type in rating_types:
      tmp_count = category_ratings[rating_type]['count']
      tmp_total = category_ratings[rating_type]['total']
      count += tmp_count
      total += tmp_total
      if tmp_count > 0:
        category_ratings[rating_type]['average'] = float(tmp_total) / tmp_count
    if count > 0:
      category_ratings['aggregate']['count'] = count
      category_ratings['aggregate']['total'] = total
      category_ratings['aggregate']['average'] = float(total) / count
    collection.update({'name': category_name}, {'$set': {category_data['list']: others, 'ratings': category_ratings}} )
    counter += 1
  print 'updated', category, ':', counter

def update_aggr_courses():
  update_ratings('course')

def update_aggr_professors():
  update_ratings('professor')

if __name__ == '__main__':
  import_departments()
  import_courses() # must be after departments
  import_professors()
  import_ratings() # must be after departments, courses
  update_aggr_courses()
  update_aggr_professors()


import os

import mongoengine as me

import rmc.shared.constants as c
import rmc.models as m

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
HTML_DIR = os.path.join(c.SHARED_DATA_DIR, 'html_snapshots')

me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)


def write(file_path, content):
    ensure_dir(file_path)
    with open(file_path, 'w') as f:
        f.write(content)


def ensure_dir(file_path):
    d = os.path.dirname(file_path)
    if not os.path.exists(d):
        os.makedirs(d)


def generate_urls():
    urls = []
    # Home page
    urls.append('')
    # Course pages
    for course in m.Course.objects:
        course_id = course.id
        urls.append('course/' + course_id)
    return urls

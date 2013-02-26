import rmc.shared.constants as c
import rmc.models as m

import mongoengine as me
import os
import subprocess
import sys

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
HTML_DIR = os.path.join(FILE_DIR, 'html')

def write(file_path, content):
    ensure_dir(file_path)
    with open(file_path, 'w') as f:
        f.write(content)

def ensure_dir(file_path):
    d = os.path.dirname(file_path)
    if not os.path.exists(d):
        os.makedirs(d)

def crawl_page(url):
    args = [
        'phantomjs',
        os.path.join(FILE_DIR, 'phantom-server.js'),
        url,
    ]
    rendered_html = subprocess.check_output(args)
    return rendered_html

def generate_urls():
    urls = []
    for course in m.Course.objects:
        course_id = course.id
        urls.append('course/' + course_id)
    return urls

def main():
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <server-root>' % sys.argv[0])

    SERVER_ROOT = sys.argv[1]

    urls = generate_urls()
    for url in urls:
        full_url = os.path.join(SERVER_ROOT, url)
        rendered_html = crawl_page(full_url)
        file_path = os.path.join(HTML_DIR, url)

        print 'Writing: %s' % url
        write(file_path, rendered_html)

if __name__ == "__main__":
    main()

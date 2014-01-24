import os
import subprocess
import sys

import mongoengine as me

import rmc.html_snapshots.utils as utils
import rmc.shared.constants as c


def crawl_page(url):
    args = [
        'phantomjs',
        '--disk-cache=true',
        os.path.join(utils.FILE_DIR, 'phantom-server.js'),
        url,
    ]
    rendered_html = subprocess.check_output(args)
    return rendered_html


def generate_snapshots():
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <server-root>' % sys.argv[0])

    SERVER_ROOT = sys.argv[1]

    urls = utils.generate_urls()
    for url in urls:
        # For urls that end with a trailing slash, create them
        # as the index page of a subdirectory
        if url and url[0] == '/':
            url = url[1:]
        if not url:
            file_path = 'index'
            file_url = ''
        elif url[-1] == '/':
            file_path = url + 'index'
            file_url = url
        else:
            file_path = url
            file_url = url

        file_path = os.path.join(utils.HTML_DIR, file_path)
        if os.path.isdir(file_path):
            print 'Cannot have file_path that is directory: %s' % file_path
        if os.path.isfile(file_path):
            continue

        full_url = os.path.join(SERVER_ROOT, file_url)
        rendered_html = crawl_page(full_url)

        print 'Writing: %s' % url
        utils.write(file_path, rendered_html)


if __name__ == "__main__":
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
    generate_snapshots()

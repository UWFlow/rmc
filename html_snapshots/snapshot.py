import rmc.html_snapshots.utils as utils

import os
import subprocess
import sys

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
        full_url = os.path.join(SERVER_ROOT, url)
        file_path = os.path.join(utils.HTML_DIR, url)
        if os.path.isfile(file_path):
            continue

        rendered_html = crawl_page(full_url)

        print 'Writing: %s' % url
        utils.write(file_path, rendered_html)

if __name__ == "__main__":
    generate_snapshots()

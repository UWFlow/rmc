import argparse
import os
import subprocess

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


def generate_snapshots(base_url, overwrite=False):
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
        if not overwrite and os.path.isfile(file_path):
            continue

        full_url = os.path.join(base_url, file_url)
        rendered_html = crawl_page(full_url)

        print 'Writing: %s' % url
        utils.write(file_path, rendered_html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description='Process snapshotting arguments')
    parser.add_argument('base_url', type=str)
    parser.add_argument('--overwrite', dest='overwrite', action='store_true')
    args = parser.parse_args()
    me.connect(c.MONGO_DB_RMC, host=c.MONGO_HOST, port=c.MONGO_PORT)
    generate_snapshots(args.base_url, args.overwrite)

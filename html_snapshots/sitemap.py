import os
import sys

import rmc.html_snapshots.utils as utils


def generate_sitemap():
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <server-root>' % sys.argv[0])

    SERVER_ROOT = sys.argv[1]
    relative_urls = utils.generate_urls()
    full_urls = [os.path.join(SERVER_ROOT, url) for url in relative_urls]
    print '\n'.join(full_urls)

if __name__ == "__main__":
    generate_sitemap()

import rmc.html_snapshots.utils as utils

def generate_sitemap():
    urls = utils.generate_urls()
    print '\n'.join(urls)

if __name__ == "__main__":
    generate_sitemap()

SHELL=/bin/bash

.PHONY: local setup import_menlo import_critiques aggregate_data init_data \
        prod_import prod_import_mongo html_snapshots sitemap deploy clean \
        test

local:
	./local_server.sh

setup:
	./setup.sh

# TODO(mack): Find better way to vary command based on prod/dev
# TODO(mack): Add command to clear cache directory:
# - Mac OS X: ~/Library/Caches/Ofi\ Labs/PhantomJS
# - Linux: Find out
html_snapshots:
	@if [ `whoami` = 'rmc' ]; then \
		PYTHONPATH=.. python html_snapshots/snapshot.py http://localhost:80; \
	else \
		PYTHONPATH=.. python html_snapshots/snapshot.py http://localhost:5000; \
	fi

sitemap:
	rm -f server/static/sitemap.txt
	PYTHONPATH=.. python html_snapshots/sitemap.py http://uwflow.com > server/static/sitemap.txt
	curl www.google.com/webmasters/tools/ping?sitemap=http://uwflow.com/static/sitemap.txt

import_menlo:
	PYTHONPATH=.. python data/processor.py all

import_critiques:
	PYTHONPATH=.. python data/evals/import_critiques.py data/evals/output/results_testing.txt

aggregate_data:
	PYTHONPATH=.. python data/aggregator.py all

init_data: import_menlo aggregate_data

export_data:
	mongodump --db rmc

prod_import: prod_import_mongo aggregate_data

prod_import_mongo:
	@if [ `whoami` = 'rmc' ]; then \
		echo "You're in prod!!! Don't dump our data :("; \
	else \
		rsync -avz rmc:~/dump .; \
		mongorestore --drop dump; \
	fi

deploy:
	@if [ `whoami` = 'rmc' ]; then \
		./deploy.sh; \
	else \
		cat deploy.sh | ssh rmc DEPLOYER=`whoami` sh; \
	fi

stats:
	PYTHONPATH=.. python analytics/stats.py

test:
	PYTHONPATH=.. nosetests

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

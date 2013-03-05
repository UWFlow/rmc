SHELL=/bin/bash

.PHONY: local setup import_menlo import_critiques aggregate_data init_data \
        prod_import prod_import_mongo html_snapshots sitemap deploy clean

local:
	./local_server.sh

setup:
	./setup.sh

# TODO(mack): Find better way to vary command based on prod/dev
html_snapshots:
	@if [ `whoami` = 'rmc' ]; then \
		PYTHONPATH=.. python html_snapshots/snapshot.py http://localhost:80; \
	else \
		PYTHONPATH=.. python html_snapshots/snapshot.py http://localhost:5000; \
	fi

sitemap:
	rm -f server/sitemap.txt
	PYTHONPATH=.. python html_snapshots/sitemap.py > server/sitemap.txt

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

# TODO(david): Actually run a test runner
test:
	PYTHONPATH=.. python shared/util_test.py

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

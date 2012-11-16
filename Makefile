SHELL=/bin/bash

.PHONY: local setup import_menlo import_critiques aggregate_data init_data \
        prod_import prod_import_mongo deploy clean

local:
	./local_server.sh

setup:
	./setup.sh

import_menlo:
	PYTHONPATH=.. python data/processor.py

import_critiques:
	PYTHONPATH=.. python data/evals/import_critiques.py data/evals/output/results_testing.txt

aggregate_data:
	PYTHONPATH=.. python data/aggregator.py all

init_data: import_menlo aggregate_data

prod_import: prod_import_mongo aggregate_data

prod_import_mongo:
	rsync -avz rmc:~/dump .
	mongorestore --drop dump

deploy:
	@if [ `whoami` = 'rmc' ]; then \
		./deploy.sh; \
	else \
		cat deploy.sh | ssh rmc DEPLOYER=`whoami` sh; \
	fi

stats:
	PYTHONPATH=.. python analytics/stats.py

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

SHELL=/bin/bash

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

deploy:
	@if [ `whoami` = 'rmc' ]; then \
		./deploy.sh; \
	else \
		cat deploy.sh | ssh rmc DEPLOYER=`whoami` sh; \
	fi

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

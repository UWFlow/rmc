SHELL=/bin/bash

local:
	./local_server.sh

setup:
	./setup.sh

import_data:
	PYTHONPATH=.. python data/processor.py

aggregate_data:
	PYTHONPATH=.. python data/aggregator.py all

init_data: import_data aggregate_data

deploy:
	@if [ `whoami` = 'rmc' ]; then \
		./deploy.sh; \
	else \
		cat deploy.sh | ssh rmc sh; \
	fi

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

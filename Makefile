SHELL=/bin/bash

local:
	./local_server.sh

setup:
	./setup.sh

import-data:
	PYTHONPATH=.. python data/processor.py

deploy:
	@if [ `whoami` = 'rmc' ]; then \
		./deploy.sh; \
	else \
		cat deploy.sh | ssh rmc sh; \
	fi

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

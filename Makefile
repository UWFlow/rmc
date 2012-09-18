SHELL=/bin/bash

local:
	./local_server.sh

setup:
	./setup.sh

import-data:
	PYTHONPATH=.. python data/processor.py

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

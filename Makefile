SHELL=/bin/bash

local:
	./local_server.sh

setup:
	./setup.sh

clean:
	find . -name '*.pyc' -delete
	rm -rf server/static/css

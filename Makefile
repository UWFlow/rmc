SHELL=/bin/bash

local:
	./local_server.sh

setup-compass:
	( cd server && compass init --config config.rb )

# TODO(david): make clean, setup

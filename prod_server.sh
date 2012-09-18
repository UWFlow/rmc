#!/bin/bash

# Runs the production server. Should be ran as a daemon.

# Bail on errors
set -e

# Compile compass
compass compile server/static/

# Start the uwsgi server
uwsgi -s /tmp/uwsgi.sock -w rmc.server.server:app --chmod-socket 666 \
  --logto /home/rmc/logs/uwsgi

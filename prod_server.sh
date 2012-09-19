#!/bin/bash

# Runs the production server. Should be ran as a daemon.

# Bail on errors
set -e

cd /home/rmc

# Compile compass
compass compile rmc/server/static/

# Install requirements
sudo pip install -r rmc/requirements.txt

# Start the uwsgi server
# TODO(david): Benchmark with ab and use worker processes if necessary
# TODO(david): Run as a daemon so will start on boot and can easily restart
uwsgi -s /tmp/uwsgi.sock -w rmc.server.server:app --chmod-socket 666 \
  --daemonize /home/rmc/logs/uwsgi.log

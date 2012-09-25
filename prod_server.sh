#!/bin/bash

# Runs the production server. Should be ran as a daemon.
# Args:
#   $1: name of pidfile

# Bail on errors
set -e

cd $HOME/rmc

# Start the uwsgi server
# TODO(david): Benchmark with ab and use worker processes if necessary
uwsgi \
  --socket /tmp/uwsgi.sock \
  --chmod-socket 666 \
  --env FLASK_CONFIG=/home/rmc/rmc/config/flask_prod.py \
  --wsgi rmc.server.server:app \
  --master \
  --daemonize /home/rmc/logs/uwsgi.log \
  --uid rmc \
  --pidfile $1

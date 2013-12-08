#!/bin/bash

# Runs the production server. Should be ran as a daemon.
# Args:
#   $1: name of pidfile

# Bail on errors
set -e

cd /home/rmc

# Start the uwsgi server
NEW_RELIC_CONFIG_FILE="/home/rmc/rmc/config/newrelic.ini" \
  newrelic-admin run-program uwsgi \
  --socket /tmp/uwsgi.sock \
  --chmod-socket 666 \
  --env FLASK_CONFIG=/home/rmc/rmc/config/flask_prod.py \
  --wsgi-file /home/rmc/rmc/server/server.wsgi \
  --callable app \
  --master \
  --workers 4 \
  --close-on-exec \
  --enable-threads \
  --daemonize /home/rmc/logs/uwsgi.log \
  --buffer-size 32768 \
  --pidfile $1

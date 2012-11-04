#!/bin/bash

# Bail on errors
set -e

function clean_up() {
  kill 0
  exit
}

# Kill all child processes on script abort
trap clean_up SIGTERM SIGINT

# TODO(mack): Could move to setup script
# First, make the necessary directory if it doesn't exist
mkdir -p mongodb
echo "Starting mongodb"
mongod --config config/mongodb_local.conf &

echo "Starting redis-server"
redis-server config/redis_local.conf &

echo "Starting compass watch"
compass watch server &

echo "Starting flask server"
FLASK_CONFIG=../config/flask_dev.py \
  PARENT_DIR=$(dirname `pwd`) \
  PYTHONPATH="${PARENT_DIR}" \
  python server/server.py

# Only exit on terminate or interrupt signal
while true; do
  sleep 1
done

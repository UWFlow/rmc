#!/bin/bash

# Bail on errors
set -e

function clean_up() {
  kill 0
  exit
}

# Kill all child processes on script abort
trap clean_up SIGTERM SIGINT

echo "Starting compass watch"
compass watch server &

echo "Starting flask server"
python server/server.py &

# Only exit on terminate or interrupt signal
while true; do
  sleep 1
done

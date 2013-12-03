#!/bin/bash

set -e

function clean_up() {
  set +e
  echo 'cleaning up'
  kill 0
  kill -9 `cat /tmp/rmc.pid`
  rm -f /tmp/rmc.pid
  exit
}

trap clean_up SIGTERM SIGINT ERR

mkdir -p mongodb
mkdir -p logs
echo "Starting mongodb"
mongod --config config/mongodb_local.conf &

echo "Starting redis-server"
redis-server config/redis_local.conf &

echo "Starting compass watch"
compass watch server &

echo "Starting uwsgi"
# Start the uwsgi server
PYTHONPATH=.. uwsgi \
  --socket /tmp/uwsgi.sock \
  --chmod-socket 666 \
  --env FLASK_CONFIG=../config/flask_dev.py \
  --wsgi-file server/server.wsgi \
  --callable app \
  --master \
  --workers 4 \
  --close-on-exec 1 \
  --enable-threads 1 \
  --virtualenv ~/.virtualenv/rmc \
  --daemonize /tmp/uwsgi.log \
  --buffer-size 32768 \
  --python-autoreload 1\
  --pidfile /tmp/rmc.pid

tail -F  /tmp/uwsgi.log

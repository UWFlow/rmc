#!/bin/bash

function clean_up() {
  set +e
  kill 0
  exit
}

# Kill all child processes on script abort
trap clean_up SIGTERM SIGINT

# Start a Python server to access test files from
( cd server && python -mSimpleHTTPServer 8000 & )

if [ ! -f node_modules/mocha-phantomjs/bin/mocha-phantomjs ]; then
  echo "mocha-phantomjs not found! Please run `npm install`"
  exit 1
fi
# Run the actual Mocha tests
node_modules/mocha-phantomjs/bin/mocha-phantomjs \
  http://127.0.0.1:8000/static/js/js_tests/test.html &

# We wait until the JS tests are done running before continuing
wait $!
status_code=$?
# Kill the most recent active process, in this case the Python server
kill %1
exit $status_code

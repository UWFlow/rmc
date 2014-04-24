#!/bin/bash

function clean_up() {
  set +e
  kill 0
  exit
}

# Kill all child processes on script abort
trap clean_up SIGTERM SIGINT

# Start a Python server to access test files from
# NOTE: We don't do this in a subshell because then $! doesn't catch that we did
# this as a background process.
cd server
python -mSimpleHTTPServer 8000 &
cd -

if [ ! -f node_modules/mocha-phantomjs/bin/mocha-phantomjs ]; then
  echo "mocha-phantomjs not found! Please run `npm install`"
  exit 1
fi

# Run the actual Mocha tests
node_modules/mocha-phantomjs/bin/mocha-phantomjs \
  http://127.0.0.1:8000/static/js/js_tests/test.html
status_code="$?"
kill "$!"
exit $status_code

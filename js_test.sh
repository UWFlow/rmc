#!/bin/bash

function clean_up() {
  set +e
  kill 0
  exit
}

# Kill all child processes on script abort
trap clean_up SIGTERM SIGINT

if [ ! -f node_modules/mocha-phantomjs/bin/mocha-phantomjs ]; then
  echo "mocha-phantomjs not found! Please run: npm install"
  exit 1
fi

# Start a Python server to access test files from
# NOTE: We don't do this in a subshell because then $! doesn't catch that we did
# this as a background process.
cd server
python -mSimpleHTTPServer 8000 &
cd -

TESTURL=http://127.0.0.1:8000/static/js/js_tests/test.html

# Wait for the server to boot up, retrying 9 times if the first one fails,
# waiting a second between tries.
server_running=0
for i in `seq 10`; do
  if curl "$TESTURL" > /dev/null 2>&1; then
    server_running=1
    break
  fi
  if [ "$i" != "10" ]; then
    sleep 1
  fi
done

if [ "$server_running" -eq "0" ]; then
  echo "Could not boot server. Exiting."
  exit 1
fi

# Run the actual Mocha tests
node_modules/mocha-phantomjs/bin/mocha-phantomjs "$TESTURL"
status_code="$?"
kill "$!"
exit $status_code

#!/bin/bash

# Terminate script on error
set -e

echo "Setup compass"
( cd server && compass init --config config.rb )

echo "Setup bundle"
( cd server && bundle install )

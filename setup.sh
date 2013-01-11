#!/bin/bash

# Terminate script on error
set -e

# Ruby stuffs: Install bundler so we can grab other gems
echo "Installing bundler"
gem install bundler

echo "Setup bundle"
( cd server && bundle install )

echo "Setup compass"
( cd server && compass init --config config.rb )

# Python stuffs: Install pip and virtualenv before we install any packages
echo "Installing pip"
easy_install pip

echo "Installing virtualenv"
pip install virtualenv

VENV_DIR="$HOME/.virtualenv"
RMC_VENV_DIR="$VENV_DIR/rmc"
echo "Creating virtualenv in $VENV_DIR"
mkdir $VENV_DIR
virtualenv $RMC_VENV_DIR
# TODO(Sandy): Couldn't find a better way to do this. Is this dangerous?
chown -R $SUDO_USER $VENV_DIR

echo "Activating virtualenv/rmc"
source $RMC_VENV_DIR/bin/activate

# Rest of Python stuff, under virtualenv
echo "Install pip requirements"
( pip install -r requirements.txt )

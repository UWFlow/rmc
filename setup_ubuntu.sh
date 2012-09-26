#!/bin/sh

# TODO(mack): integrate with Makefile

# Install pip
sudo apt-get install python-pip python-dev build-essential

# Install libraries needed for lxml
sudo apt-get install libxml2-dev libxslt-dev

# Remove pylint that's installed via distro's repo if it exists, since it can conflict with the one from pip
sudo apt-get remove pylint && sudo apt-get remove python-logilab-common && sudo apt-get remove python-logilab-astng

# Install MongoDB
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
sudo rm -rf /etc/apt/sources.list.d/10gen.list
sudo /bin/sh -c 'echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" > /etc/apt/sources.list.d/10gen.list'
sudo apt-get update
sudo apt-get install mongodb-10gen

sudo add-apt-repository ppa:chris-lea/node.js
sudo apt-get update
sudo apt-get install nodejs

sudo add-apt-repository ppa:rwky/redis
sudo apt-get update
sudo apt-get install redis-server

# Install rubygems, in order to install compass
sudo apt-get install ruby rubygems

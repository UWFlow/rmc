#!/bin/bash

set -e

install_packages() {
    # mongod starts automatically after install. We don't want that.
    should_stop_mongo=""
    if ! which mongod >/dev/null; then
      should_stop_mongo=yes
    fi

    # To get add-apt-repository
    if ! which add-apt-repository >/dev/null; then
      # Needed on a fresh install
      sudo apt-get update
      sudo apt-get install -y python-software-properties
    fi

    updated_apt_repo=""

    # To get the most recent nodejs, later.
    if ! ls /etc/apt/sources.list.d/ 2>&1 | grep -q chris-lea-node_js; then
        sudo add-apt-repository -y ppa:chris-lea/node.js
        updated_apt_repo=yes
    fi

    # To get the most recent git.
    if ! ls /etc/apt/sources.list.d/ 2>&1 | grep -q git-core-ppa; then
        sudo add-apt-repository -y ppa:git-core/ppa
        updated_apt_repo=yes
    fi

    # To get the most recent redis-server
    wget http://download.redis.io/redis-stable.tar.gz
    tar xvzf redis-stable.tar.gz
    cd redis-stable
    sudo make install
    cd ..
    sudo rm -rf redis-stable

    # To get the most recent mongodb
    if ! ls /etc/apt/sources.list.d/ 2>&1 | grep -q 10gen; then
        sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
        sudo rm -rf /etc/apt/sources.list.d/10gen.list
        sudo /bin/sh -c 'echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" > /etc/apt/sources.list.d/10gen.list'
        updated_apt_repo=yes
    fi

    # Register all that stuff we just did.
    if [ -n "$updated_apt_repo" ]; then
        sudo apt-get update -qq -y || true
    fi

    sudo apt-get install -y \
        build-essential \
        git \
        python-setuptools python-pip python-dev \
        libxml2-dev libxslt-dev \
        ruby rubygems ruby-dev \
        nodejs \
        redis-server \
        mongodb-10gen \
        unzip

    if [ -n "$should_stop_mongo" ]; then
        sudo service mongodb stop
    fi
}

install_phantomjs() {
    if ! which phantomjs >/dev/null; then
        (
            cd /usr/local/share
            case `uname -m` in
                i?86) mach=i686;;
                *) mach=x86_64;;
            esac
            sudo rm -rf phantomjs
            wget "https://phantomjs.googlecode.com/files/phantomjs-1.9.2-linux-${mach}.tar.bz2" -O- | sudo tar xfj -

            sudo ln -snf /usr/local/share/phantomjs-1.9.2-linux-${mach}/bin/phantomjs /usr/local/bin/phantomjs
        )
        which phantomjs >/dev/null
    fi
}

# Assumes that Chrome is installed
install_chromedriver() {
    if ! which chromedriver >/dev/null; then
        (
            case `uname -m` in
                i?86) bits=32;;
                *) bits=64;;
            esac

            TMP_FILE=$(tempfile)
            wget "http://chromedriver.storage.googleapis.com/2.9/chromedriver_linux${bits}.zip" -O $TMP_FILE
            sudo unzip $TMP_FILE chromedriver -d /usr/local/bin/
            rm $TMP_FILE
            sudo chmod 755 /usr/local/bin/chromedriver
        )
        which chromedriver >/dev/null
    fi
}

# Get password up front
sudo echo

install_packages
install_phantomjs
install_chromedriver

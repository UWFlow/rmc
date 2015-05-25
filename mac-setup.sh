#!/bin/bash

set -e

install_homebrew() {
    # If homebrew is already installed, don't do it again.
    if ! brew --help >/dev/null 2>&1; then
        echo "Installing Homebrew"
        ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    fi
    echo "Updating Homebrew"
    brew update > /dev/null

    # Make the cellar.
    mkdir -p /usr/local/Cellar
}

install_node() {
    if ! brew ls node >/dev/null 2>&1; then
        echo "Installing node"
        brew install node 2>&1
    fi
}

install_mongodb() {
    if ! brew ls mongodb >/dev/null 2>&1; then
        echo "Installing mongodb"
        brew install mongodb 2>&1
    fi
}

install_phantomjs() {
    if brew ls phantomjs >/dev/null 2>&1; then
        # If phantomjs is already installed via brew, check if it is outdated
        if brew outdated | grep -q -e 'phantomjs'; then
            # If phantomjs is outdated, update it
            echo "Upgrading phantomjs"
            brew upgrade phantomjs 2>&1
        fi
    else
        # Otherwise, install via brew
        echo "Installing phantomjs"
        brew install phantomjs 2>&1
    fi
}

install_redis() {
    if ! brew ls redis >/dev/null 2>&1; then
        echo "Installing redis"
        brew install redis 2>&1
    fi
}

install_chromedriver() {
    if brew ls chromedriver >/dev/null 2>&1; then
        if brew outdated | grep -q -e 'chromedriver'; then
            # If chromedriver is outdated, update it
            echo "Upgrading chromedriver"
            brew upgrade chromedriver 2>&1
        fi
    else
        # Otherwise, install via brew
        echo "Installing chromedriver"
        brew install chromedriver 2>&1
    fi
}

install_homebrew
install_node
install_mongodb
install_redis
install_phantomjs

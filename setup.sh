#!/bin/bash

# Terminate script on error
set -e

install_gems() {
    if ! which bundle >/dev/null 2>&1; then
        # Ruby stuffs: Install bundler so we can grab other gems
        echo "Installing bundler"
        sudo gem install bundler -v 1.11.2
    fi

    echo "Installing gems"
    ( cd server && sudo bundle install )
}

install_pip() {
    # Python stuffs: Install pip and virtualenv before we install any packages
    echo "Installing pip"
    if ! which pip >/dev/null 2>&1; then
        sudo easy_install pip
    fi
}

install_virtualenv() {
    if ! which virtualenv >/dev/null 2>&1; then
        echo "Installing virtualenv"
        sudo pip install virtualenv
    fi

    VENV_DIR="$HOME/.virtualenv"
    RMC_VENV_DIR="$VENV_DIR/rmc"

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtualenv in $VENV_DIR"
        mkdir -p $VENV_DIR
    fi

    virtualenv $RMC_VENV_DIR
    # TODO(Sandy): Hmm shouldn't even need to run this script with sudo (at least
    # for the gems, probably not for pip stuff either). Fix it next time I set up
    # TODO(Sandy): Couldn't find a better way to do this. Is this dangerous?
    # chown -R $SUDO_USER $VENV_DIR

    echo "Activating virtualenv/rmc"
    source $RMC_VENV_DIR/bin/activate
}

install_pip_requirements() {
    # Rest of Python stuff, under virtualenv
    echo "Install pip requirements"
    ( pip install -r requirements.txt )
}

install_third_party() {
    git submodule update --init --recursive
    ( cd third_party/rmc_linter && npm install )
    ln -sf ../../commit-msg-hook .git/hooks/commit-msg
}

install_secrets() {
  # Install secrets.py if not already there
  if [ ! -f shared/secrets.py ]; then
    echo "Copying secrets.py.example to secrets.py"
    cp shared/secrets.py.example shared/secrets.py
  fi
}

install_npm_packages() {
    echo "Installing npm packages"
    npm install
}

# Get password up front
sudo echo

install_gems
install_pip
install_virtualenv
install_pip_requirements
install_third_party
install_secrets
install_npm_packages

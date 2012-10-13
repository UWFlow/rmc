#!/bin/sh

# Updates and restarts rmc webapp on the machine.
# Can be run either directly on the machine, or by running
#
# $ cat deploy.sh | ssh rmc DEPLOYER=`whoami` sh
#
# Env Args:
#    $DEPLOYER: whoami
#
# TODO(mack): use fancy fabfile to do this and have backups/staging

set -e  # Bail on errors

cd $HOME/rmc

git pull

echo "Installing requirements"
sudo pip install -r requirements.txt

echo "Compiling compass"
compass compile server --output-style compressed --force

echo "Compiling js"
( cd server && node r.js -o build.js )

echo "Restarting daemon"
sudo service rmc_daemon restart

echo "Notifying HipChat"
PYTHONPATH=$HOME python notify_deploy.py $DEPLOYER

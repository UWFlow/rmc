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

REPOS_DIR="$HOME/repos"

# Generate a new directory name to clone to
NEW_CLONE=$REPOS_DIR/rmc-`date +%s`

# Clone into new directory
echo "Cloning rmc"
git clone git@github.com:divad12/rmc.git $NEW_CLONE > /dev/null

cd $NEW_CLONE

# TODO(david): Use virtualenv so we don't have to sudo pip install
echo "Installing requirements"
sudo pip install -r requirements.txt

echo "Compiling compass"
compass compile server --output-style compressed --force

echo "Compiling js"
( cd server && node r.js -o build.js )

echo "Symlink newly cloned rmc into place"
ln -snf $NEW_CLONE $HOME/rmc

echo "Restarting rmc_daemon"
sudo service rmc_daemon restart

echo "Removing old rmc clones"
cd $REPOS_DIR
for old in $(ls | head -n -2)
do
    rm -rf $old
done

cd $HOME/rmc
PYTHONPATH=$HOME python notify_deploy.py $DEPLOYER

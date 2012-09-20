#!/bin/sh

# Updates and restarts rmc webapp on the machine.
# Can be run either directly on the machine, or by running
#
# $ cat deploy.sh | ssh rmc sh
#
# TODO(mack): use fancy fabfile to do this and have backups/staging

cd $HOME/rmc
git pull
sudo service rmc_daemon restart

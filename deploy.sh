#!/bin/sh

# Updates and restarts rmc webapp on the machine.
# Can be run either directly on the machine, or by running
#
# $ cat update_and_restart.sh | ssh ka-ci sh
#
# TODO(mack): use fancy fabfile to do this and have backups/staging

cd $HOME/rmc
git pull
sudo service rmc_daemon restart

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

# Update cronjobs
cat aws_setup/crontab | crontab -

# TODO(david): Use virtualenv so we don't have to sudo pip install
echo "Installing requirements"
sudo pip install -r requirements.txt

echo "Compiling compass"
compass compile server --output-style compressed --force

echo "Compiling jsx"
node_modules/react-tools/bin/jsx -x jsx server/static/jsx/ server/static/js/ &
# TODO(david): Uncomment the two lines below to re-enable compiling and
#     minifying JS. This involves doing the following:
#     1. Fix this compile step: running this will result in an error right now.
#        This runs the Require.js optimizer (see
#        http://requirejs.org/docs/optimization.html), which parses out and
#        tries to run the contents of `require.config({})` in
#        server/static/js/main.js. However, in github.com/UWFlow/rmc/pull/161 we
#        moved the raw JSON contents of main.js:require.config() into its own
#        file, config_settings.js, in order to facilitate a consistent
#        environment for JS tests.
#     2. Change JS_DIR in flask_prod.py from 'js' to 'js_prod', where the
#        minified files end up. This will require producing source maps and
#        configuring Airbrake to use them.
#echo "Compiling js"
#( cd server && node r.js -o build.js )

sudo service rmc_daemon restart
sudo service celeryd restart

PYTHONPATH=$HOME python notify_deploy.py $DEPLOYER

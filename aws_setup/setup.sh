#!/bin/sh

# This sets up our continuous integration tools on EC2 Ubuntu12 AMI.
# Currently, only the continous deploy script and its web server is set up.
#
# Idempotent.
#
# This can be run like
#
# $ cat setup.sh | ssh <hostname of EC2 machine> sh

# Bail on any errors
set -e

CONFIG_DIR=$HOME/rmc/aws_setup

cd $HOME

sudo apt-get update

echo "Installing developer tools"
sudo apt-get install -y curl
sudo apt-get install -y python-pip
sudo apt-get install -y git
sudo apt-get install -y unzip
sudo apt-get install -y ruby rubygems
sudo REALLY_GEM_UPDATE_SYSTEM=1 gem update --system

echo "Prepping EBS mount points"
sudo mkdir -p /ebs/data
sudo chown $USER /ebs/data
ln -sf /ebs/data

cat <<EOF

# Format the EBS volume if attaching a new disk with nothing in it. You'll
# have to look up the device file (eg. /dev/xvdf) in EC2 console and ls /dev
sudo mkfs.ext3 /dev/xvdf

# If this is your first time setting up the machine, you'll need to add
# something like the following to /etc/fstab, then reboot from AWS console:
/dev/xvdf    /ebs/data         auto	defaults,comment=cloudconfig	0	2

# See for more info:
# http://yoodey.com/how-attach-and-mount-ebs-volume-ec2-instance-ubuntu-1010

# Also if this is the first time setting up the machine, run something like:
scp ~/.ssh/id_dsa* rmc:~/.ssh/

EOF

echo "Syncing rmc code base"
git clone git@github.com:divad12/rmc.git || ( cd rmc && git pull )

echo "Copying dotfiles"
for i in $CONFIG_DIR/dot_*; do
  cp "$i" ".`basename $i | sed 's/dot_//'`";
done

echo "Creating logs directory"
mkdir -p data/logs
ln -sf data/logs

echo "Setting up mongodb and installing as a daemon"
sudo apt-get install -y mongodb
sudo update-rc.d -f mongo_daemon remove
sudo ln -sfnv $CONFIG_DIR/etc/init.d/mongo_daemon /etc/init.d
sudo update-rc.d mongo_daemon defaults
sudo service mongo_daemon restart

echo "Setting up mongodb"

# XXX
#echo "Syncing aws-config codebase"
#git clone git://github.com/Khan/aws-config || ( cd aws-config && git pull )


# Don't need node yet
#echo "Installing node and npm"
#sudo apt-get install -y nodejs
#curl https://npmjs.org/install.sh | sudo sh

echo "Installing nginx"
sudo apt-get install -y nginx
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sfnv $CONFIG_DIR/etc/nginx/sites-available/mr_deploy \
  /etc/nginx/sites-available/mr_deploy
sudo ln -sfnv /etc/nginx/sites-available/mr_deploy \
  /etc/nginx/sites-enabled/mr_deploy
sudo service nginx restart

# We don't actually create a virtualenv for the user, so this installs
# it into the system Python's dist-package directory (which requires sudo)
sudo pip install -r gae-continuous-deploy/requirements.txt

echo "Installing gae-continuous-deploy as a daemon"
sudo update-rc.d -f mr-deploy-daemon remove
sudo ln -sfnv $CONFIG_DIR/etc/init.d/mr-deploy-daemon /etc/init.d
sudo update-rc.d mr-deploy-daemon defaults

echo "TODO: Then run sudo service exercise-screens-daemon start"

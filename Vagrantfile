# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
apt-get install make
sudo -i -u vagrant -- make -C /rmc install

# MongoDB can't use a VirtualBox shared folder as the data directory
sudo -u vagrant -- mkdir /var/tmp/mongodb
sudo -u vagrant -- ln -sf /var/tmp/mongodb /rmc
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "hashicorp/precise64"
  config.vm.network "forwarded_port", guest: 5000, host: 5000

  config.vm.synced_folder ".", "/rmc"
  config.vm.provision "shell", inline: $script
end

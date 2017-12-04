# These commands are run inside the Docker container
# whenever bash is started
#
# TODO(jlfwong): This could perhaps be replaced by
# 1) Changing the home directory of the root user to be /rmc
# and
# 2) Adding the virtualenv call to the root user's .bashrc
#
# Both of those changes would require rebuilding the Docker image
cd /rmc
source ~/.virtualenv/rmc/bin/activate

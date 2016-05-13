mongod &
sleep 2
source ~/.virtualenv/rmc/bin/activate
cd ..
nosetests -a '!slow'
RESULT=$?
mongod --shutdown
exit $RESULT

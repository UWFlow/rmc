#!/bin/sh
#
# Script to start a shell inside the Docker container. If a Docker
# container running Flow already exists, this will start a new shell in that
# container.

IMAGE_NAME="jgulbronson/uwflow"
CONTAINER_ID=`docker ps | grep $IMAGE_NAME | cut -d' ' -f1`
if [ ! "$CONTAINER_ID" ]; then
    echo "Starting new docker container"
	docker run -v \
        `pwd`:/rmc -p 0.0.0.0:5000:5000 \
        -it \
        "$IMAGE_NAME" \
        /bin/bash --init-file /rmc/docker_on_connect.sh
else
    echo "Connecting to container $CONTAINER_ID"
    docker exec -it "$CONTAINER_ID" \
        /bin/bash --init-file /rmc/docker_on_connect.sh
fi

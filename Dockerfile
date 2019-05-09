FROM ubuntu:trusty

RUN apt-get update
RUN apt-get install -y software-properties-common python-software-properties
RUN apt-get install -y apt-transport-https git sudo wget curl gcc make zlib1g-dev

ADD . /root/rmc

RUN make -C /root/rmc install

FROM ubuntu:trusty

RUN apt-get update
RUN apt-get -y install software-properties-common python-software-properties
RUN add-apt-repository ppa:git-core/ppa
RUN apt-get -y install git
RUN apt-get -y install sudo
RUN apt-get -y install wget

RUN git clone -b docker https://github.com/UWFlow/rmc.git ~/rmc

RUN apt-get install make
RUN apt-get -y install gcc
RUN apt-get -y install zlib1g-dev

RUN make -C ~/rmc install

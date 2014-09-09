FROM tomdesinto/docker-travis-run
MAINTAINER Alistair Lynn <arplynn@gmail.com>

RUN apt-get update
RUN apt-get -y install python-pip
RUN apt-get -y install python-dev
RUN apt-get -y install python-virtualenv
RUN mkdir ~/virtualenv
RUN virtualenv -p python2.7 ~/virtualenv/2.7
RUN virtualenv -p python3.4 ~/virtualenv/3.4
RUN apt-get -y install nodejs npm
RUN apt-get -y install php5 php5-cli
RUN apt-get -y install zip


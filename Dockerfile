FROM ubuntu:14.04
MAINTAINER Alistair Lynn <arplynn@gmail.com>

RUN apt-get update
RUN apt-get -y install python-virtualenv docker.io redis-server
RUN mkdir /tests
WORKDIR /tests
COPY requirements.txt /tests/requirements.txt
COPY setup-virtenv.sh /tests/setup-virtenv.sh
RUN bash setup-virtenv.sh
COPY travis-svr /tests/travis-svr
COPY daemon.py /tests/daemon.py
COPY bot.py /tests/bot.py
COPY run.sh /tests/run.sh
CMD ["/bin/bash", "run.sh"]


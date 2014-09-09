FROM ubuntu:14.04
MAINTAINER Alistair Lynn <arplynn@gmail.com>

RUN apt-get update
RUN apt-get -y install python-virtualenv docker.io redis-server
RUN mkdir /tests
WORKDIR /tests
COPY requirements.txt requirements.txt
RUN virtualenv -p python3 venv && source venv && pip install -r requirements.txt
COPY travis-svr
COPY daemon.py daemon.py
COPY bot.py bot.py
COPY run.sh run.sh
CMD ["/bin/bash", "run.sh"]


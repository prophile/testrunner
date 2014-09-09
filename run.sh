#!/bin/bash
set -e
set -v
service docker.io start
sleep 2
docker build -t alynn/svr-travis travis-svr
service redis-server start
source venv/bin/activate
python daemon.py &
python bot.py


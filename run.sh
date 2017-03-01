#!/bin/bash
# crontab 0 * * * * cd $(the deploy folder) && ./run.sh

rand=$[ 36 * ( $RANDOM % 100 ) ]
echo "Will wait for $rand seconds"
sleep $rand

./venv/bin/python2.7 notify.py

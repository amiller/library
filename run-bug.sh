#!/bin/bash

# Run one of the BFT-SMaRt provided examples
# Also includes an adversarial scheduler in python
# Uses tmux to display several windows
# 
# +--------------------------+
# |        |        |        |
# |        |        |        |
# | node0  | node1  | router |
# |________|________|________| 
# |        |        |        |
# |        |        |        |
# | node2  | node3  | client |
# |        |        |        |
# +--------------------------+ 
#

rm files/* data*/config/currentView

tmux new-session    'runscripts/smartrun.sh bftsmart.demo.counter.CounterServer 0' \;  \
    splitw -h -p 67 'runscripts/smartrun.sh bftsmart.demo.counter.CounterServer 1' \;  \
    splitw -h -p 50 'sleep 1; python amiller-bug.py' \; \
    splitw -v -p 50 'sleep 20; \
    runscripts/smartrun.sh bftsmart.demo.counter.CounterClient 0 1 10; \
    sleep 20; \
    runscripts/smartrun.sh bftsmart.demo.counter.CounterClient 0 1 10; \
    sleep 60; \
    runscripts/smartrun.sh bftsmart.demo.counter.CounterClient 0 1 10;\ 
    '  \; \
    selectp -t 0 \; \
    splitw -v -p 50 'runscripts/smartrun.sh bftsmart.demo.counter.CounterServer 2' \;  \
    selectp -t 2\; \
    splitw -v -p 50 'runscripts/smartrun.sh bftsmart.demo.counter.CounterServer 3'


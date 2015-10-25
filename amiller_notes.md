Notes on running `BFT-SMaRt` in an interactive environment
=======
Goals
- Run BFT-smart demos, with debug/log output showing leader election state
- Insert a "scheduler" that forwards ports.

   To do this we need to create a new directory for each replica, with substituted hostnames. For example, replica #0's `hosts.config` should be:
  ```
  0 127.0.0.1 12000  # Replica 0 listens on port 12000
  1 127.0.0.1 11010
  2 127.0.0.1 11020
  3 127.0.0.1 11030
  ```

  While Replica #1's `hosts.config` should be:
  ```
  0 127.0.0.1 11000  
  1 127.0.0.1 12010  # Replica 1 listens on port 12010
  2 127.0.0.1 11020
  3 127.0.0.1 11030
  ```

  Finally, it's necessary for the scheduler to effectively forward port `110XX` to port `120XX`


How to run several bft smart replicas, each in a screen

```
for x in 0 1 2 3
do 
   screen -S bft_$x -q -X quit
   screen -dmS bft_$x runscripts/smartrun.sh bftsmart.demo.counter.CounterServer $x
done
```

```
for x in 0 1 2 3
do 
   screen -S route_$x -q -X quit
   screen -dmS route_$x socat TCP-LISTEN:110${x}1,fork SYSTEM:"tee logs/${x}2r_$(date +'%s')_\$(date +'%s')_\$(rand) | socat - \"TCP:localhost:120${x}1\" | tee logs/r2${x}_$(date +'%s')_\$(date +'%s')_\$(rand) "
done
```
   # TCP-LISTEN:110${x}1,fork TCP:localhost:120${x}1

```
# Run the client
runscripts/smartrun.sh bftsmart.demo.counter.CounterClient 0 1
```

```
rm files/* data*/config/currentView; for x in 0 1 2 3; do     screen -S bft_$x -q -X quit;    screen -dmS bft_$x runscripts/smartrun.sh bftsmart.demo.counter.CounterServer $x; done
```

How to display all four bft screens in tmux:
```
tmux new-session 'screen -r bft_0' \;     split-window 'screen -r bft_1' \;     split-window 'screen -r bft_2' \;  split-window 'screen -r bft_3' \;    select-layout tiled
```

To run the scheduler in ipython (the routing behavior can be changed interactively!)
```
$ ipython
[1] run -i amiller-bug.py
[2] main()
```
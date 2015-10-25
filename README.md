Illustration of a timing bug in BFT-SMaRt
========
Andrew Miller

This repo provides some tools to interact with BFT-SMaRt, and in particular to visualize a bug that is triggered by an adversarial scheduler.

The source code of BFT-SMaRt is (minimally) modified (see `src/bftsmart/communication/server/ServersCommunicationLayer.java`) so that each node listens on port `120XX` but tries to connect to `110XX` (where XX is determined by the node's identifier).
The python file `amiller-bug.py` acts as an adversarial scheduler. It listens on ports `110XX`, (the nominal ports), and selectively forwards messages to `120XX` (the actual ports.

The following test script launches 4 nodes, (configuration: N=4, F=1), a client, and the adversarial scheduler. It uses `tmux` to create a split-pane view, useful for sceen casts and live interaction/monitoring.
```
$ ./run-test.sh 
```

The schedule that triggers a bug
--------------------
In this demonstration, the initial leader is node `0`, and the faulty node is node `1`.
- For the first 20 seconds, all messages are routed correctly. A client submit 10 requests, which are processed.
- For the next 70 seconds, the router temporarily partitions (i.e., delivers no messages to or from) the leader. Another client submits a request, but after 30 seconds it times out. After 60 seconds, all of the nodes attempt a view-change. 
- When the scheduler determines that a view-change is imminent (e.g., by deeply inspecting the packets, or by relying on hard-coded timing), it changes it behavior. Now, node `1` is partitioned, but the partition between `0` and `{2,3}` is healed. Hereafter, all messages are delivered between `0`,`2`,`3`, and `1` has effectively crashed.

Expected behavior:
- Once the partition between `0`,`2`,`3` is healed, the network should begin stabilize and process messages at the ordinary rate.

Observed behavior:
- All three nodes `0`,`,2`,`3`, fail to agree on a view, and get stuck in a perpetual loop of new view-changes.
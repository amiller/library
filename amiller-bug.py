# This is designed as a routing middle layer for 
import re
import sys
from gevent.server import StreamServer
import gevent.monkey
gevent.monkey.patch_socket()
from gevent import socket
from gevent import Greenlet
from gevent import subprocess

# This script listens on OUT_PORTS and forwards messages to IN_PORTS

# These are the ports that the replicas are listening on
IN_PORTS  = [11001, 11011, 11021, 11031]
# These are the ports that the replicas try to connect to.
OUT_PORTS = [12001, 12011, 12021, 12031]

def find_bftsmart_process_connecting_from_port(port):
    # This assumes bftsmart is of the form,
    #   java -cp bin/j.jar bftsmart.demo.counter.CounterServer 3
    # Our goal is to find 3
    log = subprocess.check_output('lsof -i :%d | grep "localhost:%d->"' % (port,port), shell=True)
    pid = int(re.match('^java\s+(\d+)', log).groups()[0])
    cmd = subprocess.check_output('ps ww %d | grep java' % pid, shell=True, universal_newlines=False)
    idx = int(re.match('.*\s(\d+)$', cmd).groups()[0])
    #print 'Estimated index', idx
    return idx

socket_map = {}

# COMMAND = 'GO', None # Deliver all threads
# COMMAND = 'GO', None
COMMAND = 'SOME', (0,1,2,3)  # Isolate some nodes

def allpairs(q):
    for i in q:
        for j in q:
            if i != j: yield i,j

def should_route(src, tgt):
    cmd, args = COMMAND
    if cmd == 'GO': return True
    if cmd == 'NONE': return False
    if cmd == 'SOME':
        if src in args and tgt in args: 
            return True
        else: return False
    if cmd == 'INTERFERE':
        leader, states = args
        if leader == src: return False
        if leader == tgt: return False
        if (src,tgt) in states: return True
        return False
    assert False, 'bad command'

ROUTING = []
def router(rd_sock, wr_sock, src, tgt):
    global COMMAND
    # Assumptions:
    #   rd_sock and wr_sock are NON-BLOCKING
    s = ''
    ROUTING.append((src,tgt))
    if len(ROUTING) == 6: print 'All routes established'
    while 1:
        # Wait to read, or 0.1 seconds
        try: 
            socket.wait_read(rd_sock.fileno(), timeout=0.5)
            s += rd_sock.recv(4096)
            if len(s):
                pass
                #print src,tgt, 'read', len(s) 
                #print 'timeout:', 'timeout' in s
                #print 'local:', 'local' in s
        except socket.timeout: pass

        if not should_route(src, tgt):
            gevent.sleep(0.1)
            continue

        # If we are in the 'misbehavior state', wait until we detect a new-view message
        if COMMAND[0] == 'INTERFERE':
            leader, states = COMMAND[1]
            if len(s) == 172:
                print 'I suspect a view change from', src, tgt
                newstate = set(states)
                if (src,tgt) in newstate: newstate.remove((src,tgt))
                newstate = tuple(newstate)
                if newstate == ():
                    # We have intercepted all of the commands. After a short break, it's time for the switch
                    print 'A view-change has been detected'
                    #gevent.sleep(5)
                    newleader = (leader+1)%4
                    followers = set(range(4)).difference((newleader,))
                    #COMMAND = 'INTERFERE', ((leader+1)%4, tuple(allpairs(followers)))
                    #print 'new leader:', newleader, COMMAND
                    #co0tinue
                    #COMMAND = 'SOME', (0,2,3)
                    if 0: # Run 3
                        COMMAND = 'SOME', (1,2,3)
                        print '[T+  80] Run 3: Leader is still partitioned'
                    if 0: # Run 4
                        COMMAND = 'SOME', (0,1,2,3)
                        print '[T+  80] Run 4: Healing all partitions, ordinary network resumed'
                    if 1: # Run 5
                        COMMAND = 'SOME', (0,2,3)
                        print '[T+  80] Run 5: Now routing all traffic between (0,2,3)'
                    continue
                else:
                    COMMAND = 'INTERFERE', (leader, newstate)

        # If we have something to write, write some of it
        if not len(s): continue
        socket.wait_write(wr_sock.fileno())
        written = wr_sock.send(s)
        assert written == len(s), 'write was incomplete'
        #print '[%d->%d] delivered len(%d)' % (src,tgt,len(s))
        s = ''

def handle_(my_idx):
    def handle(sock, (ip,port)):
        global log
        #print ip,port
        idx = find_bftsmart_process_connecting_from_port(port)
        other = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print 'connecting', idx, my_idx, OUT_PORTS[my_idx]
        try:
            other.connect(('127.0.0.1', OUT_PORTS[my_idx]))
        except socket.error: 
            print 'connect', idx, my_idx, 'failed'
            return
        sock.setblocking(0)
        other.setblocking(0)
        t1 = Greenlet(run=lambda: router(sock, other, my_idx, idx))
        t2 = Greenlet(run=lambda: router(other, sock, idx, my_idx))
        t1.start()
        t2.start()
        try:
            gevent.joinall((t1,t2))
        finally:
            gevent.killall((t1,t2))
        other.close()
        sock.close()
    return handle

def main():
    global COMMAND
    # Create three threads (Nodes with lower number always *receive*
    # from nodes with higher number)
    t0 = Greenlet(run=StreamServer(('127.0.0.1', 11001), handle_(0)).serve_forever)
    t1 = Greenlet(run=StreamServer(('127.0.0.1', 11011), handle_(1)).serve_forever)
    t2 = Greenlet(run=StreamServer(('127.0.0.1', 11021), handle_(2)).serve_forever)
    t0.start()
    t1.start()
    t2.start()


    def run_counter():
        subprocess.call('runscripts/smartrun.sh bftsmart.demo.counter.CounterClient 0 1 10', shell=True, stdout=sys.stdout, stderr=sys.stderr)

    print '[T+   0] Ordinary service for 20 seconds'; gevent.sleep(20)

    print '[T+  20] Suspending delivery to current leader (0)'
    COMMAND = 'INTERFERE', (0, tuple(allpairs((1,2,3))))

    try:
        gevent.joinall((t0,t1,t2))
    finally:
        gevent.killall((t0,t1,t2))
    
if __name__ == '__main__':
    try: __IPYTHON__
    except NameError:
        main()

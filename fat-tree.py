#!/usr/bin/python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import dumpNodeConnections
from mininet.link import Link, Intf, TCLink
import os
from time import sleep
import sys

class Topology(topo, k):
    def __init__(self):
        # Initialize topology
        topo.__init__(self)
        core = int(pow((k/2),2))
        aggr = int(((k/2)*k))
        edge = int(((k/2)*k))
        host = int((k*pow((k/2),2)))

        cores = []
        aggrs = []
        edges = []
        hosts = []

        for i in range(core):
            cores.append(self.addSwitch('core'+str(i)))

        for pod in range(k): # construct each pod
            for i in range(aggr/k):
                switch = self.addSwitch('aggr'+str(edge//k)+'_pod'+str(pod))
                aggrs.append(switch)
                for j in range(k*aggr//2, (k/2)*(aggr+1)):
                    self.addLink(switch, cores[j])

            for i in range(edge/k):
                switch = self.addSwitch('edge'+str(edge//k)+'_pod'+str(pod))
                edges.append(switch)
                for j in range( (edge/k*pod), (edge/k)*(pod+1)):
                    self.addLink(switch, aggrs[j])

                for j in range(host/k/(edge/pod)):
                    h = hosts.append(self.addHost('host'+str(host/k/(edge/pod))+'_pod'+str(pod)))



# This is for "mn --custom"
topos = { 'mytopo': ( lambda: Topology() ) }


# This is for "python *.py"
if __name__ == '__main__':
    setLogLevel( 'info' )

    topo = Topology()
    net = Mininet(topo=topo, link=TCLink)       # The TCLink is a special setting for setting the bandwidth in the future.

    # 1. Start mininet
    net.start()

    # Wait for links setup (sometimes, it takes some time to setup, so wait for a while before mininet starts)
    print "\nWaiting for links to setup . . . .",
    sys.stdout.flush()
    for time_idx in range(3):
        print ".",
        sys.stdout.flush()
        sleep(1)


    # 2. Start the CLI commands
    info( '\n*** Running CLI\n' )
    CLI( net )


    # 3. Stop mininet properly
    net.stop()
    print('Mininet stoped.')


    ### If you did not close the mininet, please run "mn -c" to clean up and re-run the mininet

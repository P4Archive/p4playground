#!/usr/bin/python

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink

from p4_mininet import P4Switch, P4Host

import argparse
from time import sleep
import os
import subprocess

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_THRIFT_BASE_PORT = 22222

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)
parser.add_argument('--json1', help='Path to JSON agg config file',
                    type=str, action="store", required=True)
parser.add_argument('--json2', help='Path to JSON edge config file',
                    type=str, action="store", required=True)
parser.add_argument('--cli', help='Path to BM CLI',
                    type=str, action="store", required=True)

args = parser.parse_args()





class MyTopo(Topo):
    def __init__(self, sw_path, json_path1, json_path2,
                 nb_hosts, nb_switches, links, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        # Edge switch
        self.addSwitch("s1", sw_path = sw_path,
                            json_path = args.json1,
                            thrift_port = _THRIFT_BASE_PORT + 1,
                            pcap_dump = True,
                            device_id = 1)
        # Aggregate switch
        self.addSwitch("s2", sw_path = sw_path,
                            json_path = args.json2,
                            thrift_port = _THRIFT_BASE_PORT + 2,
                            pcap_dump = True,
                            device_id = 2)
        # Edge switch
        self.addSwitch("s3", sw_path = sw_path,
                            json_path = args.json1,
                            thrift_port = _THRIFT_BASE_PORT + 3,
                            pcap_dump = True,
                            device_id = 3)

        for h in xrange(nb_hosts):
            host = self.addHost('h%d' % (h + 1))

        for a, b in links:
            self.addLink(a, b)

def read_topo():
    nb_hosts = 2
    nb_switches = 3
    links = [("h1", "s1"), ("s1", "s2"), ("s2", "s3"), ("s3", "h2")]
    return int(nb_hosts), int(nb_switches), links


def main():
    nb_hosts, nb_switches, links = read_topo()

    topo = MyTopo(args.behavioral_exe,
                  args.json1,
                  args.json2,
                  nb_hosts, nb_switches, links)

    net = Mininet(topo = topo,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None )
    net.start()

    for n in xrange(nb_hosts):
        h = net.get('h%d' % (n + 1))
        for off in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload eth0 %s off" % off
            print cmd
            h.cmd(cmd)
        print "disable ipv6"
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv4.tcp_congestion_control=reno")
        h.cmd("iptables -I OUTPUT -p icmp --icmp-type destination-unreachable -j DROP")

    sleep(1)

    cmd = [args.cli, "--json", args.json1,
           "--thrift-port", str(_THRIFT_BASE_PORT + 1)]
    with open("commands.txt", "r") as f:
        print " ".join(cmd)
        try:
            output = subprocess.check_output(cmd, stdin = f)
            print output
        except subprocess.CalledProcessError as e:
            print e
            print e.output

    sleep(1)

    cmd = [args.cli, "--json", args.json2,
           "--thrift-port", str(_THRIFT_BASE_PORT + 2)]
    with open("commands.txt", "r") as f:
        print " ".join(cmd)
        try:
            output = subprocess.check_output(cmd, stdin = f)
            print output
        except subprocess.CalledProcessError as e:
            print e
            print e.output

    sleep(1)

    cmd = [args.cli, "--json", args.json1,
           "--thrift-port", str(_THRIFT_BASE_PORT + 3)]
    with open("commands.txt", "r") as f:
        print " ".join(cmd)
        try:
            output = subprocess.check_output(cmd, stdin = f)
            print output
        except subprocess.CalledProcessError as e:
            print e
            print e.output

    sleep(1)

    print "Ready !"

    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    main()

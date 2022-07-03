#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import switchyard
from switchyard.lib.userlib import *
from to_cache import ToCache
from FWTable import *
from INTFQueue import INTFQueue


class Router(object):
    def __init__(self, net: switchyard.llnetbase.LLNetBase):
        self._net = net
        # other initialization stuff here
        self._interfaces = net.interfaces()
        self._DictIpIntf = {intf.ipaddr: intf for intf in self._interfaces}
        self._DictNameIntf = {intf.name: intf for intf in self._interfaces}
        # cache between ip address and mac address
        self._ARPcache = ToCache(TTL=10, capacity=10)
        # forwarding table of the router
        self._fwTable = FWTable(self._interfaces)
        # interface-Queues dict
        self._INTFQueues = {intf.name: INTFQueue(self._net, intf) for intf in self._interfaces}
        for entry in self._fwTable._table:
            if int(entry.nextHopAddr) != 0:
                self._INTFQueues[entry.intfName].add_queue(entry.nextHopAddr)

    def handle_packet(self, recv: switchyard.llnetbase.ReceivedPacket):
        timestamp, ifaceName, packet = recv

        arp = packet.get_header(Arp)

        if packet.has_header(Arp) and arp.operation == ArpOperation.Request:
            srcIP = arp.senderprotoaddr
            srcMAC = arp.senderhwaddr
            dstIP = arp.targetprotoaddr
            self._ARPcache.add_entry(srcIP, srcMAC)
            self._INTFQueues[ifaceName].update_dstMAC(dstIP=srcIP,dstMAC=srcMAC)
            self._ARPcache.printCache()
            if dstIP in self._DictIpIntf.keys():
                intf = self._DictIpIntf[dstIP]
                replyPkt = create_ip_arp_reply(srchw=intf.ethaddr, dsthw=srcMAC, srcip=intf.ipaddr, targetip=srcIP)
                self._net.send_packet(intf, replyPkt)

            else:
                dstMAC = self._ARPcache.get_value(dstIP)
                if dstMAC != None:
                    intf = self._DictNameIntf[ifaceName]
                    replyPkt = create_ip_arp_reply(srchw=dstMAC, dsthw=srcMAC, srcip=dstIP, targetip=srcIP)
                    self._net.send_packet(intf, replyPkt)

        elif packet.has_header(Arp) and arp.operation == ArpOperation.Reply:
            srcIP = arp.senderprotoaddr
            srcMAC = arp.senderhwaddr
            dstIP = arp.targetprotoaddr
            dstMAC = arp.targethwaddr
            self._ARPcache.add_entry(srcIP, srcMAC)
            self._INTFQueues[ifaceName].update_dstMAC(dstIP= srcIP,dstMAC=srcMAC)
            self._INTFQueues[ifaceName].clear(dstIP=srcIP)

        elif packet.has_header(IPv4):  # process other packets
            dstIP = packet.get_header(IPv4).dst
            if dstIP in self._DictIpIntf.keys():
                pass
            else:
                entry = self._fwTable.lookUp(dstIP=dstIP)
                if entry is not None:
                    print(entry.intfName)
                    curQueues = self._INTFQueues[entry.intfName]
                    if int(entry.nextHopAddr) != 0: #0.0.0.0
                        dstIP = entry.nextHopAddr
                    elif dstIP not in self._INTFQueues[entry.intfName]._queues.keys():  # no corresponding queue in the interface
                        self._INTFQueues[entry.intfName].add_queue(dstIP=dstIP)
                    self._ARPcache.printCache()
                    dstMAC = self._ARPcache.get_value(dstIP)
                    curQueues.add_packet(dstIP, packet)
                    if dstMAC is None:
                        curQueues.send_arp_request(dstIP=dstIP)
                    else:
                        curQueues.update_dstMAC(dstIP, dstMAC)
                        curQueues.clear(dstIP)
        else: pass

    def update(self):
        #update ARP cache and interface queues
        self._ARPcache.update()
        for queue in self._INTFQueues.values():
            queue.update_all_request()

    def start(self):
        '''A running daemon of the router.
        Receive packets until the end of time.
        '''
        while True:
            try:
                self.update()
                recv = self._net.recv_packet(timeout=1.0)
            except NoPackets:
                continue
            except Shutdown:
                break

            self.handle_packet(recv)

        self.stop()

    def stop(self):
        self._net.shutdown()


def main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    router = Router(net)
    router.start()

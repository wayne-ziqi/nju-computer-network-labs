#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import switchyard
from switchyard.lib.userlib import *
from to_cache import ToCache

class Router(object):
    def __init__(self, net: switchyard.llnetbase.LLNetBase):
        self._net = net
        # other initialization stuff here
        self._interfaces = net.interfaces()
        self._DictIpIntf = {intf.ipaddr:intf for intf in self._interfaces}
        self._DictNameIntf = {intf.name:intf for intf in self._interfaces}
        self._cache = ToCache(TTL=10, capacity=10)
        # self._IPs = [intf.ipaddr for intf in self._interfaces]

    def handle_packet(self, recv: switchyard.llnetbase.ReceivedPacket):
        timestamp, ifaceName, packet = recv
        # check whether the packet is an ARP request packet,
        # if so, extract the arp header
        # check whether the target ip address is one of my interfaces
        # if so, make an arp reply packet with src mac address of my interface
        arp = packet.get_header(Arp)

        if arp and arp.operation == ArpOperation.Request:
            srcIP = arp.senderprotoaddr
            srcMAC = arp.senderhwaddr
            dstIP = arp.targetprotoaddr
            self._cache.add_entry(srcIP,srcMAC)
            self._cache.printCache()
            if dstIP in self._DictIpIntf.keys():
                intf = self._DictIpIntf[dstIP]
                replyPkt = create_ip_arp_reply(srchw=intf.ethaddr,dsthw=srcMAC,srcip=intf.ipaddr,targetip=srcIP)
                self._net.send_packet(intf, replyPkt)
            else:
                dstMAC = self._cache.get_value(dstIP)
                if dstMAC != None:
                    intf = self._DictNameIntf[ifaceName]
                    replyPkt = create_ip_arp_reply(srchw=dstMAC, dsthw=srcMAC, srcip=dstIP, targetip=srcIP)
                    self._net.send_packet(intf, replyPkt)

    def start(self):
        '''A running daemon of the router.
        Receive packets until the end of time.
        '''
        while True:
            try:
                self._cache.update()
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

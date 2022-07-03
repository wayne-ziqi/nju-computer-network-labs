#!/usr/bin/env python3

import time
import threading
from random import randint

import switchyard
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
import random


class Middlebox:
    def __init__(
            self,
            net: switchyard.llnetbase.LLNetBase,
            dropRate="0.19"
    ):
        self._net = net
        self._dropRate = float(dropRate)
        self._DictNameIntf = {intf.name: intf for intf in net.interfaces()}
        self._intf0 = self._DictNameIntf['middlebox-eth0']
        self._intf1 = self._DictNameIntf['middlebox-eth1']

    def handle_packet(self, recv: switchyard.llnetbase.ReceivedPacket):
        _, fromIface, packet = recv
        if fromIface == self._intf0.name:
            log_debug("Received from blaster")
            '''
            Received data packet
            Should I drop it?
            If not, modify headers & send to blastee
            '''
            if (random.random() > self._dropRate):
            # if (1):
                packet.get_header(Ethernet).src = self._intf1.ethaddr
                packet.get_header(Ethernet).dst = EthAddr('20:00:00:00:00:01')
                packet.get_header(IPv4).ttl -= 1
                self._net.send_packet(self._intf1, packet)

        elif fromIface == self._intf1.name:
            log_debug("Received from blastee")
            '''
            Received ACK
            Modify headers & send to blaster. Not dropping ACK packets!
            net.send_packet("middlebox-eth0", pkt)
            '''
            packet.get_header(Ethernet).src = self._intf0.ethaddr
            packet.get_header(Ethernet).dst = EthAddr('10:00:00:00:00:01')
            packet.get_header(IPv4).ttl -= 1
            self._net.send_packet(self._intf0, packet)
        else:
            log_debug("Oops :))")

    def start(self):
        '''A running daemon of the router.
        Receive packets until the end of time.
        '''
        while True:
            try:
                recv = self._net.recv_packet(timeout=1.0)
            except NoPackets:
                continue
            except Shutdown:
                break

            self.handle_packet(recv)

        self.shutdown()

    def shutdown(self):
        self._net.shutdown()


def main(net, **kwargs):
    middlebox = Middlebox(net, **kwargs)
    middlebox.start()

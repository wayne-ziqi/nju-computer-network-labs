#!/usr/bin/env python3

import time
from random import randint
from struct import pack
from struct import unpack
import switchyard
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from queue import Queue


class Blaster:
    def __init__(
            self,
            net: switchyard.llnetbase.LLNetBase,
            blasteeIp='192.168.200.1',
            num='100',
            length="100",
            senderWindow="5",
            timeout="300",
            recvTimeout="100"
    ):
        self._net = net
        self._intf = net.interfaces()[0]
        self._boxMac = EthAddr('40:00:00:00:00:01')
        # TODO: store the parameters
        ...
        self._blasteeIp = blasteeIp
        self._numPkt = int(num)
        self._ploadLen = int(length)
        self._senderWindowSize = int(senderWindow)
        self._timeout = float(timeout) / 1000  # (s)
        self._recv_timeout = float(recvTimeout) / 1000
        self._lhs = 0
        self._rhs = 0  # window empty: rhs == lhs, rhs refer to last unackd packet + 1
        self._lastSendTime = time.time()
        self._startTime = self._lastSendTime
        self._finishTIme = 0.0
        self._unAckdPkts = {}  # store unAckd packets with the max size of window size, {sequence number : unAckdpacket}
        self._sendState = 0  # 0 for normal packets, 1 for retx packets
        self._nretx = 0
        self._nto = 0
        self._throughput = 0
        self._reput = 0

    def handle_packet(self, recv: switchyard.llnetbase.ReceivedPacket):
        _, fromIface, packet = recv
        print(f"I got a packet{packet}")
        if packet.has_header(IPv4) and packet[IPv4].dst == self._intf.ipaddr:
            if packet.has_header(RawPacketContents):
                rawContents = packet.get_header(RawPacketContents)
                sequence = unpack('>L', rawContents.data[0:4])[0]
                if sequence in self._unAckdPkts.keys():
                    self._unAckdPkts.pop(sequence)
                if sequence == self._lhs:
                    while self._lhs not in self._unAckdPkts.keys() and self._lhs < self._rhs:
                        self._lhs += 1
                    self._sendState = 0
                    self._lastSendTime = time.time()
                    while not self._retxQue.empty():
                        self._retxQue.get()
                    if self._lhs == self._numPkt:
                        self.end_log()


            else:
                raise ("no raw contents")

    def handle_no_packet(self):
        log_debug("Didn't receive anything")

        # Creating the headers for the packet
        # pkt = Ethernet() + IPv4() + UDP()
        # pkt[1].protocol = IPProtocol.UDP

        # normally send packet, has available packet to send
        if self._sendState == 0 and self._rhs - self._lhs < self._senderWindowSize and self._rhs < self._numPkt:
            pkt = Ethernet() + IPv4() + UDP()
            pkt[0].src = self._intf.ethaddr
            pkt[0].dst = self._boxMac
            pkt[1].protocol = IPProtocol.UDP
            pkt[1].src = self._intf.ipaddr
            pkt[1].dst = IPAddr(self._blasteeIp)
            pkt[1].ttl = 63
            pkt[2].src = 1111
            pkt[2].dst = 2222
            raw_seqNum = pack('>L', self._rhs)
            payLoadLen = randint(1, self._ploadLen)#self._ploadLen#
            raw_payLoadLen = pack('>H', payLoadLen)
            payLoad = [randint(0, 127) for _ in range(payLoadLen)]# [16 for _ in range(payLoadLen)]#
            raw_payLoad = bytes(payLoad)
            raw = RawPacketContents(raw_seqNum + raw_payLoadLen + raw_payLoad)
            pkt.add_header(raw)
            self._throughput += pkt.size()
            self._net.send_packet(self._intf, pkt)
            self._unAckdPkts[self._rhs] = pkt
            self._retxQue = Queue()
            self._rhs += 1

        elif self._sendState == 1 or time.time() - self._lastSendTime > self._timeout:
            def resend_packet():
                if not self._retxQue.empty():
                    resend = self._retxQue.get()
                    if resend in self._unAckdPkts.values():
                        self._nretx += 1
                        self._reput += resend.size()
                        self._throughput+= resend.size()
                        self._net.send_packet(self._intf, resend)
                if self._retxQue.empty():
                    self._sendState = 0

            if self._lhs in self._unAckdPkts.keys():
                if time.time() - self._lastSendTime > self._timeout:
                    self._nto += 1
                if self._sendState == 0:  # found the stuck for the first time
                    self._lastSendTime = time.time()
                    self._sendState = 1
                    for pkt in self._unAckdPkts.values():
                        self._retxQue.put(pkt)
                    resend_packet()
                else:  # send_state == 1, retransmit other packet in the queue
                    resend_packet()

            else:
                self._lastSendTime = time.time()
                self._sendState = 0


    def end_log(self):
        self._finishTIme = time.time()
        txTime = self._finishTIme - self._startTime
        print(f'\033[0;32;40mTotal TX time: {txTime} (seconds)\033[0m')
        print(f'\033[0;32;40mNumber of reTX: {self._nretx} packets\033[0m')
        print(f'\033[0;32;40mNumber of Coarse TOs: {self._nto}\033[0m')
        print(f'\033[0;32;40mThroughout: {self._throughput/txTime} (Bps)\033[0m')
        print(f'\033[0;32;40mGoodput: {(self._throughput - self._reput)/txTime} (Bps)\033[0m')

    def start(self):
        '''A running daemon of the blaster.
        Receive packets until the end of time.
        '''
        while True:
            try:
                recv = self._net.recv_packet(timeout=self._recv_timeout)
            except NoPackets:
                self.handle_no_packet()
                continue
            except Shutdown:
                break

            self.handle_packet(recv)

        self.shutdown()

    def shutdown(self):
        self._net.shutdown()


def main(net, **kwargs):
    blaster = Blaster(net, **kwargs)
    blaster.start()

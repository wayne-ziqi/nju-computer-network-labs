#!/usr/bin/env python3

import time
import threading
from struct import pack
from struct import unpack
import switchyard
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *


class Blastee:
    def __init__(
            self,
            net: switchyard.llnetbase.LLNetBase,
            blasterIp,
            num
    ):
        self._net = net
        # TODO: store the parameters
        self._blasterIp = blasterIp
        self._blasterPktNum = num
        self._intf = net.interfaces()[0]
        self._recv_pkt={}

    def handle_packet(self, recv: switchyard.llnetbase.ReceivedPacket):
        _, fromIface, packet = recv
        log_debug(f"I got a packet from {fromIface}")
        log_debug(f"Pkt: {packet}")
        eth = Ethernet()
        eth.src = packet.get_header(Ethernet).dst
        eth.dst = packet.get_header(Ethernet).src
        ipv4 = IPv4()
        ipv4.src = packet.get_header(IPv4).dst
        ipv4.dst = IPAddr(self._blasterIp)
        ipv4.ttl = 63
        ipv4.protocol = IPProtocol.UDP
        udp = UDP()
        udp.src = 2222
        udp.dst = 1111

        rawContent = packet.get_header(RawPacketContents)
        fromSeq = unpack('>L', rawContent.data[0:4])[0]
        payLoadLen = unpack('>H', rawContent.data[4:6])[0]
        payLoad = rawContent.data[6:6 + payLoadLen]
        byteList = list(payLoad[0:min(payLoadLen, 8)])
        for i in range(payLoadLen, 8):
            byteList.append(0)
        ackPayLoad = bytes(byteList)
        if fromSeq not in self._recv_pkt.keys():
            self._recv_pkt[fromSeq] = packet
        print(f'current number of received packets:{len(self._recv_pkt)} packets')
        print(f'from sequence: {fromSeq}, payLoad Length: {payLoadLen}')
        ackraw = RawPacketContents(pack('>L', fromSeq) + ackPayLoad)

        packet = eth + ipv4 + udp + ackraw
        print(packet)
        self._net.send_packet(self._intf, packet)

    def start(self):
        '''A running daemon of the blastee.
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
    blastee = Blastee(net, **kwargs)
    blastee.start()

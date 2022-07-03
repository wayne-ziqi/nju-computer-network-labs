'''
the queue should reserve :
    1. a queue that contains all packet waiting for arp solve
    2. a time limit to retransmit next arp
'''

from switchyard.lib.interface import Interface
from switchyard.lib.packet import *
from switchyard.lib.address import *
from time import time
from queue import Queue
import switchyard


class IPQueue:
    def __init__(self,
                 capacity: int,
                 srcMAC: EthAddr,
                 srcIP: IPv4Address,
                 dstIP: IPv4Address,
                 interface: Interface,
                 net: switchyard.llnetbase.LLNetBase):
        self._net = net
        self._queue = Queue()
        self._lastSendTime = 0.0
        self._timeLimit = 1.0
        self._cntTrial = 0
        self._trialLimit = 5
        self._capacity = capacity
        self._srcMAC = srcMAC
        self._srcIP = srcIP
        self._dstMAC = None
        self._dstIP = dstIP
        self._interface = interface

    def put(self, packet: Packet):
        self._queue.put(packet)

    def get(self) -> Packet:
        return self._queue.get()

    def add_packet(self, packet: Packet):
        self._queue.put(packet)

    def update_dstMAC(self, dstMAC):
        self._dstMAC = dstMAC

    def clear(self):
        if self._dstMAC is not None:
            print(f'forward dst IP:{self._dstIP}, forward dst mac: {self._dstMAC}')
            while not self._queue.empty():
                packet = self._queue.get()
                if packet.has_header(Ethernet):
                    packet.get_header(Ethernet).dst = self._dstMAC
                    packet.get_header(Ethernet).src = self._srcMAC
                else:   #ICMP error messages
                    eth = Ethernet()
                    eth.src = self._srcMAC
                    eth.dst = self._dstMAC
                    eth.ethertype = EtherType.IPv4
                    newPacket = Packet()
                    newPacket.add_header(eth)
                    headerName = packet.headers()
                    for i in range(len(headerName)):
                        newPacket.add_header(packet[i])
                    packet = newPacket
                    packet.get_header(IPv4).src = self._srcIP

                self._net.send_packet(self._interface, packet)

        # else:
        #     raise ("the dstMAC is not available")

    def send_arp_request(self):  # first find there's no IP-MAC entry in the ARP cache
        if not self._queue.empty():
            self._dstMAC = None
            self._cntTrial = 0
            self._lastSendTime = time()
            srcMAC = self._srcMAC
            srcIP = self._srcIP
            self._cntTrial += 1
            arpRequest = create_ip_arp_request(srchw=srcMAC, srcip=srcIP, targetip=self._dstIP)
            self._net.send_packet(self._interface, arpRequest)

    def update_request(self):
        # check if time is on , if so ,resend the arp request
        noHostPkt = []
        if self._queue.empty() and self._dstMAC is None or self._dstIP is None:
            pass
        elif self._dstMAC is None:
            now = time()
            if now - self._lastSendTime > self._timeLimit:
                if (self._cntTrial < self._trialLimit):
                    self._cntTrial += 1
                    self._lastSendTime = now
                    arpRequest = create_ip_arp_request(srchw=self._srcMAC, srcip=self._srcIP, targetip=self._dstIP)
                    self._net.send_packet(self._interface, arpRequest)
                else:
                    # send icmp errors for all packets
                    while not self._queue.empty():
                        packet = self._queue.get()
                        noHostPkt.append(packet)

        return noHostPkt


class INTFQueue(object):
    def __init__(self, net: switchyard.llnetbase.LLNetBase, interface: Interface):
        self._net = net
        self._interface = interface
        self._queues = {}

    def add_queue(self, dstIP):
        self._queues[dstIP] = IPQueue(capacity=10,
                                      srcMAC=self._interface.ethaddr,
                                      srcIP=self._interface.ipaddr,
                                      dstIP=dstIP,
                                      interface=self._interface,
                                      net=self._net)

    def add_packet(self, dstIP, packet: Packet):
        self._queues[dstIP].add_packet(packet=packet)

    def update_dstMAC(self, dstIP, dstMAC):
        self._queues[dstIP].update_dstMAC(dstMAC=dstMAC)

    def clear(self, dstIP):
        if dstIP in self._queues.keys():
            self._queues[dstIP].clear()


    def send_arp_request(self, dstIP):  # first find there's no IP-MAC entry in the ARP cache
        if dstIP in self._queues.keys():
            self._queues[dstIP].send_arp_request()

    def update_all_request(self):
        # check if time is on , if so ,resend the arp request
        noHostPktsList = []
        for ipqueue in self._queues.values():
            list = ipqueue.update_request()
            noHostPktsList.append(list)
        return noHostPktsList

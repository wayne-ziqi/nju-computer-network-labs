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
                 capacity:int,
                 srcMAC:EthAddr,
                 srcIP:IPv4Address,
                 dstIP:IPv4Address,
                 interface:Interface,
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
            print(f'forward dst mac: {self._dstMAC}')
            while not self._queue.empty():
                packet = self._queue.get()
                headList = packet.headers()
                for headName in headList:
                    header = packet.get_header_by_name(headName)
                    if isinstance(header, Ethernet):
                        header.dst = self._dstMAC
                        header.src = self._srcMAC
                    elif isinstance(header, IPv4):
                        header.ttl -= 1
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
                    # drop all packets
                    while not self._queue.empty():
                        self._queue.get()


class INTFQueue(object):
    def __init__(self, net: switchyard.llnetbase.LLNetBase, interface: Interface, capacity=10):
        self._net = net
        self._interface = interface
        self._queues = {}

    def add_queue(self,dstIP):
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
        for ipqueue in self._queues.values():
            ipqueue.update_request()

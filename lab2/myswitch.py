'''
Ethernet learning switch in Python.

Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)
'''
import logging

import switchyard
from switchyard.lib.userlib import *


class Chart(object):
    def __init__(self, capacity=5):
        self._size = 0
        self._capacity = capacity
        self._chart = [None for _ in range(capacity)]

    def entry_nr(self, mac):
        for i in range(self._size):
            if (self._chart[i] != None and self._chart[i][0] == mac): return i
        return self._capacity

    def get_interface(self, mac):
        idx = self.entry_nr(mac)
        if idx != self._capacity:
            return self._chart[idx][1]
        else:
            return None

    def add_entry(self, mac, interface):
        macIdx = self.entry_nr(mac)
        if macIdx != self._capacity:
            self._chart[macIdx][1] = interface
        elif self._size >= self._capacity:
            self._chart[self._capacity - 1] = [mac, interface]
        else:
            self._chart[self._size] = [mac, interface]
            self._size += 1

def main(net: switchyard.llnetbase.LLNetBase):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    chart = Chart()
    # logging.getLogger().setLevel(logging.DEBUG)

    while True:
        try:
            _, fromIface, packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            break
        log_debug(f"In {net.name} received packet {packet} on {fromIface}")

        eth = packet.get_header(Ethernet)
        if eth is None:
            log_info("Received a non-Ethernet packet?!")
            return
        if eth.dst in mymacs:
            log_info("Received a packet intended for me")
        else:
            chart.add_entry(eth.src.toStr(), fromIface)
            dstEth = eth.dst.toStr()
            found = False
            if dstEth != "ff:ff:ff:ff:ff:ff":
                ethChart = chart.get_interface(dstEth)
                if ethChart != None:
                    found = True
                    log_info(f"Unicast packet {packet} to {ethChart}")
                    for intf in my_interfaces:
                        if intf.name == ethChart and intf.name != fromIface:
                            net.send_packet(intf,packet)
                            break


            if dstEth == "ff:ff:ff:ff:ff:ff" or not found:
                for intf in my_interfaces:
                    if fromIface != intf.name:
                        log_info(f"Flooding packet {packet} to {intf.name}")
                        net.send_packet(intf, packet)

    net.shutdown()

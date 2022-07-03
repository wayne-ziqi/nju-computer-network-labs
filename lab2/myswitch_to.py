'''
Ethernet learning switch in Python.

Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)
'''

import switchyard
from switchyard.lib.userlib import *
import time


class Chart_to(object):
    def __init__(self, stayTime=10):
        self._size = 0
        self._dic = {}
        self._stayTime = stayTime
        # _dic = { mac : [interface, time stamp]}

    def printTable(self):
        for key, val in self._dic.items():
            print(f"MAC: {key}, interface: {val[0]}")

    def get_interface(self, mac):
        if mac in self._dic.keys():
            return self._dic[mac][0]
        else:
            return None

    def add_entry(self, mac, interface):
        # if mac not in self._dic.keys() or mac in self._dic.keys() and self._dic[mac][0] != interface:
        self._dic[mac] = [interface, time.time()]

    def update(self):
        curTime = time.time()
        for k in list(self._dic.keys()):
            if curTime - self._dic[k][1] >= self._stayTime: #pay attention to the stay time, must be equal to 10s
                self._dic.pop(k)


def main(net: switchyard.llnetbase.LLNetBase):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    chart = Chart_to()
    while True:
        try:
            chart.update()
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
            chart.printTable()
            if dstEth != "ff:ff:ff:ff:ff:ff":
                iface = chart.get_interface(dstEth)
                if iface != None:
                    log_info(f"Unicast packet {packet} to {iface}")
                    for intf in my_interfaces:
                        if intf.name == iface and fromIface != intf.name:
                            found = True
                            net.send_packet(intf, packet)
                            break

            if dstEth == "ff:ff:ff:ff:ff:ff" or not found:
                # packet._headers[0].dst = "ff:ff:ff:ff:ff:ff"
                for intf in my_interfaces:
                    if fromIface != intf.name:
                        log_info(f"Flooding packet {packet} to {intf.name}")
                        net.send_packet(intf, packet)

    net.shutdown()

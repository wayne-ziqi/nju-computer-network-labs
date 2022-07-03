'''
Ethernet learning switch in Python.

Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)
'''
import switchyard
from switchyard.lib.userlib import *
from Table_traffic import Table_traffic

def main(net: switchyard.llnetbase.LLNetBase):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    cache = Table_traffic()
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
            cache.add_entry(eth.src.toStr(), fromIface)
            dstEth = eth.dst.toStr()
            found = False
            cache.printTable()
            if dstEth != "ff:ff:ff:ff:ff:ff":
                iface = cache.get_interface(dstEth, packet.size())
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
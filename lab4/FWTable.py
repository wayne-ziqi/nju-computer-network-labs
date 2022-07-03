from switchyard.lib.address import *
from switchyard.lib.interface import Interface


class FWEntry(object):
    def __init__(self, networkAddr: IPv4Address, subnetAddr: IPv4Address, nextHopAddr: IPv4Address, intfName: str):
        self.networkAddr = networkAddr
        self.subnetAddr = subnetAddr
        self.nextHopAddr = nextHopAddr
        self.intfName = intfName
        self.prefixLen = self._get_prefix_len()

    def __str__(self):
        return f'network address: {self.networkAddr}, subnet address: {self.subnetAddr}, next hop: {self.nextHopAddr}, intf: {self.intfName}, prfix:{self.prefixLen}'

    def _get_prefix_len(self):
        netaddr = IPv4Network(str(self.networkAddr) + '/' + str(self.subnetAddr))
        return netaddr.prefixlen


class FWTable(object):
    def __init__(self, interfaces: [Interface]):
        self._table = []
        for intf in interfaces:
            networkAddr = intf.ipaddr
            subnetAddr = intf.netmask
            nextHopAddr = IPv4Address('0.0.0.0')
            networkAddr = IPv4Address(int(networkAddr) & int(subnetAddr))
            interface = intf.name
            self._table.append(FWEntry(networkAddr, subnetAddr, nextHopAddr, interface))

        with open('forwarding_table.txt', 'r', encoding='utf-8') as fp:
            for line in fp:
                tokens = [elem for elem in line.split()]
                networkAddr = IPv4Address(tokens[0])
                subnetAddr = IPv4Address(tokens[1])
                nextHopAddr = IPv4Address(tokens[2])
                networkAddr = IPv4Address(int(networkAddr) & int(subnetAddr))
                intfName = tokens[3]
                self._table.append(FWEntry(networkAddr, subnetAddr, nextHopAddr, intfName))
        self.print()

    def print(self):
        for entry in self._table:
            print(entry)

    # if the longest prefix entry is matched return the entry or the name
    def lookUp(self, dstIP: IPv4Address):
        ansEntry: FWEntry = None
        for entry in self._table:
            if (int(dstIP) & int(entry.subnetAddr)) == int(entry.networkAddr):
                if ansEntry is None or ansEntry.prefixLen < entry.prefixLen:
                    ansEntry = entry
        return ansEntry

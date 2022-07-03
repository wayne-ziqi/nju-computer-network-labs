from switchyard.lib.packet import *
from switchyard.lib.address import *
from enum import Enum


class ICMPErrorType(Enum):
    NetworkUnreachable = 0
    TimeLimitExceeded = 1
    HostUnreachable = 2
    PortUnreachable = 3


def create_icmp_ErrorMsg(type: ICMPErrorType, packet: Packet):
    i = packet.get_header_index(Ethernet)
    del packet[i]
    replyICMP = ICMP()
    if type == ICMPErrorType.NetworkUnreachable:
        replyICMP.icmptype = ICMPType.DestinationUnreachable
        replyICMP.icmpcode = ICMPCodeDestinationUnreachable.NetworkUnreachable
    elif type == ICMPErrorType.TimeLimitExceeded:
        replyICMP.icmptype = ICMPType.TimeExceeded
        replyICMP.icmpcode = ICMPCodeTimeExceeded.TTLExpired
    elif type == ICMPErrorType.HostUnreachable:
        replyICMP.icmptype = ICMPType.DestinationUnreachable
        replyICMP.icmpcode = ICMPCodeDestinationUnreachable.HostUnreachable
    elif type == ICMPErrorType.PortUnreachable:
        replyICMP.icmptype = ICMPType.DestinationUnreachable
        replyICMP.icmpcode = ICMPCodeDestinationUnreachable.PortUnreachable
    replyICMP.icmpdata.data = packet.to_bytes()[:28]
    replyIPv4 = IPv4()
    replyIPv4.protocol = IPProtocol.ICMP
    replyIPv4.src = packet.get_header(IPv4).dst
    replyIPv4.dst = packet.get_header(IPv4).src
    replyIPv4.ttl = 63

    return replyIPv4 + replyICMP

def create_icmp_EchoReply(packet:Packet, srcMAC:EthAddr, srcIP:IPAddr):
    # ICMP reply header
    icmp = packet.get_header(ICMP)
    replyICMP = ICMP()
    replyICMP.icmptype = ICMPType.EchoReply
    replyICMP.icmpcode = ICMPCodeEchoReply.EchoReply
    replyICMP.icmpdata.identifier = icmp.icmpdata.identifier
    replyICMP.icmpdata.sequence = icmp.icmpdata.sequence
    replyICMP.icmpdata.data = icmp.icmpdata.data
    # ipv4 header
    replyIPv4 = IPv4()
    replyIPv4.protocol = IPProtocol.ICMP
    replyIPv4.dst = packet.get_header(IPv4).src
    replyIPv4.src = srcIP
    replyIPv4.ttl = packet.get_header(IPv4).ttl
    # ethernet header
    replyEth = Ethernet()
    replyEth.src = srcMAC
    replyEth.dst = packet.get_header(Ethernet).src
    # construct packet
    return replyEth + replyIPv4 + replyICMP

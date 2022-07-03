from switchyard.lib.userlib import *


def new_arp_req(hwsrc, ipsrc, ipdst):
    ether = Ethernet(src=hwsrc, dst='ff:ff:ff:ff:ff:ff', ethertype=EtherType.ARP)
    arp = Arp(operation=ArpOperation.Request,
              senderhwaddr=hwsrc,
              senderprotoaddr=ipsrc,
              targethwaddr='ff:ff:ff:ff:ff:ff',
              targetprotoaddr=ipdst)
    return ether + arp

def new_arp_rpl(hwsrc, ipsrc, hwdst, ipdst):
    ether = Ethernet(src=hwsrc, dst= hwdst, ethertype=EtherType.ARP)
    arp = Arp(operation=ArpOperation.Reply,
              senderhwaddr=hwsrc,
              senderprotoaddr=ipsrc,
              targethwaddr=hwdst,
              targetprotoaddr=ipdst)
    return ether + arp

def new_icmp(hwsrc,  ipsrc, hwdst,ipdst, reply=False):
    ether = Ethernet(src=hwsrc, dst=hwdst, ethertype=EtherType.IP)
    ippkt = IPv4(src=ipsrc, dst=ipdst, protocol=IPProtocol.ICMP, ttl=32)
    icmppkt = ICMP()
    if reply:
        icmppkt.icmptype = ICMPType.EchoReply
    else:
        icmppkt.icmptype = ICMPType.EchoRequest
    return ether + ippkt + icmppkt


def test_router():
    s = TestScenario("basic router tests")
    s.add_interface('eth0', '10:00:00:00:00:01', '192.168.100.2')
    s.add_interface('eth1', '10:00:00:00:00:02', '192.168.200.2')
    # s.add_interface('eth2', '10:00:00:00:00:03')
    # s.add_interface('eth3', '10:00:00:00:00:04')

    # test case 1: a frame with broadcast destination should get sent out
    # all ports except ingress
    request = new_arp_req(
        '20:00:00:00:00:00',
        '192.168.100.1',
        '192.168.100.2'
    )
    s.expect(
        PacketInputEvent("eth0", request, display=Ethernet),
        ("the arp packet from 192.168.100.1 should be broadcast and arrive at ath0")
    )

    reply = new_arp_rpl(
        '10:00:00:00:00:01',
        '192.168.100.2',
        '20:00:00:00:00:00',
        '192.168.100.1'
    )
    s.expect(
        PacketOutputEvent('eth0',reply , display=Ethernet),
        ("the arp reply packet should be forwarded to eth0 "
         "with MAC 20:00:00:00:00:00")
    )



    # test case 2: a frame with any unicast address except one assigned to hub
    # interface should be sent out all ports except ingress
    request = new_arp_req(
        '30:00:00:00:00:00',
        '192.168.200.1',
        '192.168.200.2'
    )
    s.expect(
        PacketInputEvent("eth1", request, display=Ethernet),
        ("the arp packet from 192.168.200.1 should be broadcast and arrive at eth1")
    )

    reply = new_arp_rpl(
        '10:00:00:00:00:02',
        '192.168.200.2',
        '30:00:00:00:00:00',
        '192.168.200.1'
    )
    s.expect(
        PacketOutputEvent('eth1', reply, display=Ethernet),
        ("the arp reply packet should be forwarded to eth1 "
         "with MAC 30:00:00:00:00:00")
    )

    # test3. an icmp packet should be dropped
    icmp = new_icmp(
        '20:00:00:00:00:00',
        '192.168.100.1',
        '10:00:00:00:00:01',
        '192.168.100.2'
    )
    s.expect(
        PacketInputEvent("eth0", icmp, display=Ethernet),
        ("an icmp packet from 192.168.100.1 arrive at eth0")
    )
    s.expect(
        PacketInputTimeoutEvent(1.0),
        ("an icmp packet arrived and do nothing")
    )

    # test4.
    reply = new_arp_rpl(
        '20:00:00:00:00:00',
        '192.168.100.1',
        '10:00:00:00:00:01',
        '192.168.100.2'
    )

    s.expect(
        PacketInputEvent("eth0", reply, display=Ethernet),
        ("an arp reply packet from 192.168.100.1 arrive at eth0")
    )
    s.expect(
        PacketInputTimeoutEvent(1.0),
        ("an reply packet arrived and do nothing")
    )
    return s

scenario = test_router()
from switchyard.lib.userlib import *


def new_packet(hwsrc, hwdst, ipsrc, ipdst, reply=False):
    ether = Ethernet(src=hwsrc, dst=hwdst, ethertype=EtherType.IP)
    ippkt = IPv4(src=ipsrc, dst=ipdst, protocol=IPProtocol.ICMP, ttl=32)
    icmppkt = ICMP()
    if reply:
        icmppkt.icmptype = ICMPType.EchoReply
    else:
        icmppkt.icmptype = ICMPType.EchoRequest
    return ether + ippkt + icmppkt


def test_box():
    s = TestScenario("basic middleBox tests")
    s.add_interface('middlebox-eth0', '40:00:00:00:00:01', '192.168.100.2')
    s.add_interface('middlebox-eth1', '40:00:00:00:00:02', '192.168.200.2')


    # test case 1: a frame with broadcast destination should get sent out
    # all ports except ingress
    testpkt = new_packet(
        "10:00:00:00:00:01",
        "40:00:00:00:00:01",
        "192.168.100.1",
        "192.168.200.1"
    )
    forwardPpkt = new_packet(
        "40:00:00:00:00:02",
        "20:00:00:00:00:01",
        "192.168.100.1",
        "192.168.200.1"
    )
    s.expect(
        PacketInputEvent("middlebox-eth0", testpkt, display=Ethernet),
        ("Blaster-send packet "
         "should arrive on eth0")
    )
    s.expect(
        PacketOutputEvent("middlebox-eth1", forwardPpkt, display=Ethernet),
        ("should forward to blastee on eth1")
    )


    return s

scenario = test_box()

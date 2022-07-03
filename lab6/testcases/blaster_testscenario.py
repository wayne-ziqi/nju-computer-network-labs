from switchyard.lib.userlib import *
from struct import pack
from struct import unpack
from random import randint


def new_ack(rawContent: RawPacketContents,
            hwsrc=EthAddr('40:00:00:00:00:01'),
            hwdst=EthAddr('10:00:00:00:00:01'),
            ipsrc=IPAddr('192.168.200.1'),
            ipdst=IPAddr('192.168.100.1')
            ):
    eth = Ethernet()
    eth.src = hwsrc
    eth.dst = hwdst
    ipv4 = IPv4()
    ipv4.src = ipsrc
    ipv4.dst = ipdst
    ipv4.protocol = IPProtocol.UDP
    udp = UDP()
    udp.src = 2222
    udp.dst = 1111
    fromSeq = unpack('>L',rawContent.data[0:4])[0]
    payLoadLen = unpack('>H',rawContent.data[4:6])[0]
    payLoad = rawContent.data[6:6 + payLoadLen]
    byteList = list(payLoad[0:min(payLoadLen, 8)])
    for i in range(payLoadLen,8):
        byteList.append(0)
    ackPayLoad = bytes(byteList)

    # print(f'from sequence: {fromSeq}, payLoad Length: {payLoadLen}')
    ackraw = RawPacketContents(pack('>L', fromSeq) + ackPayLoad)
    return eth + ipv4 + udp + ackraw


def make_pkt(seqnumber, payLoadLen=128):
    pkt = Ethernet() + IPv4() + UDP()
    pkt[0].src = EthAddr('10:00:00:00:00:01')
    pkt[0].dst = EthAddr('40:00:00:00:00:01')
    pkt[1].protocol = IPProtocol.UDP
    pkt[1].src = IPAddr('192.168.100.1')
    pkt[1].dst = IPAddr('192.168.200.1')
    pkt[2].src = 1111
    pkt[2].dst = 2222
    raw_seqNum = pack('>L', seqnumber)
    raw_payLoadLen = pack('>H', payLoadLen)
    payLoad = [16 for _ in range(payLoadLen)]
    raw_payLoad = bytes(payLoad)
    raw = RawPacketContents(raw_seqNum + raw_payLoadLen + raw_payLoad)
    pkt.add_header(raw)
    return pkt


def test_blaster():
    s = TestScenario("blaster tests")
    s.add_interface('blaster-eth0', '10:00:00:00:00:01', '192.168.100.1')

    # test case 1: a frame with broadcast destination should get sent out
    # all ports except ingress
    sendpkt = make_pkt(0, 100)

    testACK = new_ack(sendpkt.get_header(RawPacketContents))

    s.expect(
        PacketOutputEvent("blaster-eth0", sendpkt),
        "blaster should send packet 0 to eth0"
    )

    s.expect(
        PacketInputEvent("blaster-eth0", testACK),
        ("Blastee-ack packet "
         "should arrive on eth0")
    )

    return s


scenario = test_blaster()

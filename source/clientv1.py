import socket
import sys
import time
from uplink.packet import Packet
from uplink.net import wordsToData
from uplink.errors import *

##############################################################
## Helper actions, these help us implement the protocol
##############################################################
def make_sock(host, port):
    """Make a socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, int(port)))
    return sock


def readloop(sock, timeout=3, silent=False, err=True):
    replies = []
    sock.settimeout(timeout)
    if not silent: print("[!] Receiving Data. data: .  handshake: -")
    try:
        while True:
            data = sock.recv(4)
            p = Packet(data)
            # Check if the packet is an Abort, if so
            # Raise the abort
            abr = p.is_abort
            if abr and err:
                raise abr
            elif abr and not err:
                replies.append(p)
            replies.append(p)
            if not silent:
                print(".", end="", flush=True)

    except socket.timeout:
        pass
    return replies


def uplink_get(sock, chan):
    """
    Query a channel from the socket

    Return
        bytes - the raw data

    Raise:
        UplinkAbort - All the uplink errors
    """
    p = Packet()
    p.fromValues(query=1, channel=chan, data=0)

    sock.send(p.raw)
    # Convert all the data words to data
    data = readloop(sock)
    # We dont need to save handshakes
    data = wordsToData([pac.data for pac in data if not p.is_handshake])
    return data


def uplink_set(sock, chan, word):
    """
    Set a channel to the value of word

    Return
        bytes - the raw data response

    Raise:
        UplinkAbort - All the uplink errors
    """
    p = Packet()
    p.fromValues(query=0, channel=chan, data=word)
    sock.send(p.raw)
    # Convert all the data words to data
    data = readloop(sock)
    data = wordsToData([pac.data for pac in data if not p.is_handshake])
    return data


##################################################################
## Program Functions: These help us test that our flags are online
## and that satellite state is working as expected
##################################################################
def uplink1(host, port=8001):
    """Test uplink 1"""
    sock = make_sock(host, port)
    try:
        data = uplink_get(sock, 0x001)
        print(data)
        data = uplink_get(sock, 0x002)
        print(data)
    except UplinkAbort as E:
        return False
    sock.close()
    # Now we just get the flag
    return True


def uplink2(host, port=9001):
    """Test uplink 2"""
    sock = make_sock(host, port)
    # Now we set the flag bit
    try:
        data = uplink_set(sock, 0o020, 0o01)
    except (UplinkAbort, AssertionError) as E:
        print("Channel write to 0o042 did not produce expected result. {}".format(E))
        print("Unexpected UplinkAbort", E)
        sock.close()
        return False
    # Flag bit is set, get the flag
    data = uplink_get(sock, 0o020)
    print(data)
    print("trigger abort...")
    try:
        packets = uplink_set(sock, 0o001, 0x000)
    except (UplinkAbort, AssertionError) as E:
        print("Got the abort:", E)
    # Get more packets
    print("Get shell")
    data = uplink_set(sock, 0o042, 1)
    print(data)
    data = uplink_get(sock, 0o042)
    print(data)
    return True

def brute2(host, port=9001):
    """Solve uplink 2"""
    sock = make_sock(host, port)
    for channel in range(0o020, 0o100):
        # Try to write to the channel
        try:
            packets = uplink_set(sock, channel, 0o001)
            break
        except UplinkAbort as E:
            print(E)
            sock.close()
            sock = make_sock(host, port)
            continue
        # WE DIDNT ERROR!!!
    print("We didnt abort on", channel)
    print("Reading from", channel)

    packets = uplink_get(sock, 0o042)
    print(packets)
    print("trigger abort...")
    packets = uplink_set(sock, 0o021, 0x000)
    # Get more packets
    print("Get shell")
    packets = uplink_get(sock, 0o021)
    print(packets)

    sock.close()


def main():
    def usage():
        print(sys.argv[0], "<host>:<port>")
        quit(1)

    if len(sys.argv) < 2:
        usage()

    try:
        host, port = sys.argv[1].split(":")
    except (ValueError, IndexError):
        usage()

    #brute2(host, port)
    #quit()

    print("Testing Uplink 1....")
    x = uplink1(host)
    print("Testing Uplink 2....")
    #y = uplink2(host, 9001)
    #print("[{}] Uplink 2".format(y))



if __name__ == "__main__":
    main()

"""
This implements a basic class that can be used for sending and receiving data
to the uplink
"""
import socketserver
import socket
import time
import random

from .packet import Packet, AbortPacket, HandshakePacket
from .errors import UplinkAbort

class Uplink(object):
    """This class will allow us to connect to a remote uplink and is also used
    by the uplink
    """
    def __init__(self):
        self.socket = None
        self.remote = None
        self.client = None
        self.debug = False
        self.lag_time = (0.2, 0.3) # Client needs to lag so it can do stuff well
        self.read_timeout = 1 # how many seconds to read data for
        self.global_timeout = 60 # How long to keep the connection open for
    
    def lag(self, lag=None):
        """Simulate a slow connection"""
        if lag:
            stime = random.uniform(*lag)
        else:
            stime = random.uniform(*self.lag_time)
        if stime:
            time.sleep(stime)
    
    def connect(self, remote, strict=True):
        """Connect to the given uplink"""
        if self.socket and self.remote:
            raise ValueError("Uplink is already connected")
        try:
            host, port = remote.split(":")
            port = int(port)
        except ValueError:
            raise ValueError("Uplink connect requires a 'host:port' string")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, int(port)))
        self.client = True
        if strict:
            deb = self.debug
            self.debug = False
            handshake = self.recv_packets(count=1)
            self.debug = deb
            if handshake:
                handshake = handshake.pop(0)
                if handshake.is_handshake:
                    return True
            raise ValueError("Did not receive handshake from Uplink")

    def setsocket(self, sock):
        if self.socket:
            raise ValueError("Uplink is already connected")
        self.socket = sock

    def send_data(self, abort, query, channel, data):
        """Send some data to the uplink on the given socket
        
        data expects a bytestring or a single 15 bit integer
        """
        p = Packet()
        p.fromValues(abort=abort, query=query, channel=channel)

        if isinstance(data, int):
            p.fromValues(data=data)
            self.socket.send(p.raw)
            return
        if isinstance(data, str):
            raise ValueError("Data must be bytes and not a string")
        words = convertWordSize(8, 15, data)
        for word in words:
            # If we are the server, add some lag
            p.fromValues(data=word)
            self.socket.send(p.raw)
            self.lag()

    

    def send_packet(self, packet):
        self.socket.send(packet.raw)

    def recv_packets(self, count=None):
        """Receive packets from the socket. Error on aborts
        """
        packets = []
        self.socket.settimeout(self.read_timeout)
        while True:
            if count and len(packets) >= count:
                break
            try:
                # Get a packet
                raw_packet = self.socket.recv(4)
                try:
                    if raw_packet:
                        packet = Packet(raw_packet)
                    else:
                        return packets
                except UplinkAbort as Abort:
                    raise Abort
                    # We might need this later
                    #if not self.client:
                    #    self.send_packet(AbortPacket(E))
                    #    self.abort = True
                    #    continue
                if self.debug:
                    print(".", end="", flush=True)
                if self.client and packet.is_abort:
                    raise packet.is_abort
                packets.append(packet)
            except socket.timeout:
                return packets
        return packets
    
    def recv(self, channel=None):
        """Receive raw bytes from the connection"""
        packets = self.recv_packets()
        buffer = []
        for packet in packets:
            # Filter out the channel if specified
            if channel and packet.channel != channel:
                continue
            # Ignore handshakes
            if packet.is_handshake:
                continue
            buffer.append(packet.data)
        data = bytes(convertWordSize(15, 8, buffer))
        return data
    
    def send_handshake(self):
        """Send a basic handshake"""
        self.send_packet(HandshakePacket())
        

def convertWordSize(size1, size2, words):
    """Convert a series of words from one size to another

    E.g. 16 bit words to 15 bit words

    When the byte size is increasing (15->16), padded zeros may be added
    When the byte size is decreasing (15->8), padded zeros will be ditched
    """
    # Turn it into a binary string
    binary = ""
    for word in words:
        if word > int('1'*size1):
            raise ValueError("Invalid WORD: {}. Exceeds wordsize {}".format(word, size1))
        binary += "{:0{}b}".format(word, size1)
    output = []
    # Break the binary up into words of the new size
    while binary:
        newword = binary[:size2]
        binary = binary[size2:]
        # Handle the case of extra data
        if len(newword) < size2:
            if size1 < size2:
                newword = "{:0<0{}}".format(newword, size2)
            else:
                break
        output.append(int(newword, 2))
    return output

def dataToWords(data):
    return convertWordSize(8, 15, data)

def wordsToData(words):
    return bytes(convertWordSize(15, 8, words))
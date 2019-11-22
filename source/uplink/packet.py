from .errors import UplinkInvalidSize, UplinkInvalidSig, UplinkError

class Word(int):
    pass

class Packet(object):
    def __init__(self, data=0):
        self.abort = 0
        self.query = 0
        self.channel = 0
        self.data = 0
        if data:
            self.fromData(data)
    
    @property
    def is_handshake(self):
        """True if handshake, false if not"""
        return self.abort == 0 and self.channel == 0o100 and self.data == 0x7fff
    
    @property
    def is_abort(self):
        """return the Exception if the packet is an abort"""
        if self.abort:
            return UplinkError(self.channel, self.data)
        return None

    def fromValues(self, abort=None, query=None, channel=None, data=None):
        if abort is not None:
            self.abort = abort
        if query is not None:
            self.query = query
        if channel is not None:
            self.channel = channel
        if data is not None:
            self.data = Word(data)
    
    def fromData(self, data):
        """Get A, Q, C, and D from the packet"""
        # Check the signature and size of the 4 bytes
        if len(data) != 4:
            raise UplinkInvalidSize()
        if data[0] >> 6 != 0:
            raise UplinkInvalidSig()
        if data[1] >> 6 != 1:
            raise UplinkInvalidSig()
        if data[2] >> 6 != 2:
            raise UplinkInvalidSig()
        if data[3] >> 6 != 3:
            raise UplinkInvalidSig()

        # Get the integers from the data
        # We know the first two bits here are 0, so we dont need to mask it
        self.abort = data[0] >> 5
        self.query = (data[0] & 16) >> 4

        # Build channel, this is in 2 bytes so it will come in 2 parts
        c1 = data[0] & 15   # xxxxcccc & 00001111 = 0000cccc
        c1 = c1 << 3        # cccc000   - c is only 7 bits
        c2 = data[1] & 56   # xxcccxxx & 00111000 = 00ccc000
        c2 = c2 >> 3        # 00000ccc
        self.channel = c1 | c2         # 0ccc c000 | 0000 0ccc = 0ccc cccc

        # Build data
        d1 = data[1] & 7    # xxxxxddd & 00000111 = 0000 0ddd
        d1 = d1 << 12       # 0ddd 0000 0000 0000
        d2 = data[2] & 63   # xxdddddd & 00111111 = 00dd dddd
        d2 = d2 << 6        # 0000 dddd dd00 0000
        d3 = data[3] & 63   # 00dd dddd
        self.data = d1 | d2 | d3
        self.data = Word(self.data)
    
    @property
    def raw(self):
        """Generate a compliant packet from the abort, query, channel, and data
        """
        # Base sig: 00... 01... 10... 11...
        pkt = [0x00, 0x40, 0x80, 0xc0]
        pkt[0] |= (self.abort & 1) << 5 # Set the A bit
        pkt[0] |= (self.query & 1) << 4 # Save the q bit

        # Set the channel
        pkt[0] |= (self.channel >> 3)
        pkt[1] |= ((self.channel &  7) << 3)

        # Set the data
        pkt[3] |= self.data & 63
        pkt[2] |= (self.data >> 6) & 63
        pkt[1] |= (self.data >> 12) & 7
        return bytes(pkt)

    def __repr__(self):
        return "UplinkPacket(abort:{:n}, query:{:n}, channel:0o{:o}, data:{})".format(self.abort, self.query, self.channel, self.data)

class HandshakePacket(Packet):
    """Handshake packet"""
    def __init__(self):
        self.abort = 0
        self.query = 0
        self.channel = 0o100
        self.data = 0o77777
    
    def __repr__(self):
        return "UplinkHandshake()"

class AbortPacket(Packet):
    """"Builds a packet from an abort"""
    def __init__(self, abort):
        self.abort = 1
        self.query = 0
        self.channel = abort.channel
        self.data = abort.ABORTCODE
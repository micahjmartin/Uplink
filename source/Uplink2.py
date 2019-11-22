"""
Uplink 2: Ctf challenge for RITSEC CTF 2019

Author: knif3
"""

import os
import time
import random
import struct

from uplink.server import UplinkServer, server_forever
from uplink.satellite import IOChannel, Satellite
from uplink.errors import UplinkUnknownIO, UplinkBadShell, UplinkClientTimeout

CHANNELTABLE = b"""0o000TLE Data  The TLE for the satellite
0o001Name  The name of the satellite
0o002Mass  The mass of the satellite (kg)
0x003Time  Current time
0o004UNUSED  UNUSED
0o005UNUSED  UNUSED
0o006UNUSED  UNUSED
0o007UNUSED  UNUSED
0o010Velocity  Current Velocity
0o011Altitude  Current Altitude
0o020ChannelTable  Show all the I/O channels
0o042AbortDebug  I/O Channel used for Abort debug shell
    """

TLE = b"""UPLINK 0o002
1 13337U 19001A   19320.46460751  .00000047  00000-0  57877-4 0  0010
2 13337  86.1277  71.0050 0021365  52.5321  58.8163 13.50219193000013
    """

FLAG = b"RITSEC{This_Sh3ll_is_mad_jank}    "


class Uplink2Server(UplinkServer):
    """Server for uplink 2"""
    def handle(self):
        """We got a new connection"""
        self.sat = Uplink2Sat()
        self.uplink_loop()

class Uplink2Sat(Satellite):
    """Satellite for Uplink 2"""
    def __init__(self):
        # We add extra data to make it easy on client librarys that arent quite to spec
        # or have trouble with converting 15 bit words
        self.channel_table = False

        self.abort = False
        self.lag = (0.2, 0.4) # lag
        super(Uplink2Sat, self).__init__()

    @IOChannel(0o000, readonly=True)
    def channelTLE(self, packet):
        """Return a fake TLE"""
        return TLE

    @IOChannel(0o001, readonly=True)
    def channelname(self, packet):
        return b"UPLINK CONSTELLATION 0o002"

    @IOChannel(0o002, readonly=True)
    def channelmass(self, packet):
        return 6362
    
    @IOChannel(0o003, readonly=True)
    def channeltime(self, packet):
        return int(time.time()).to_bytes(4, "big")

    @IOChannel(0o010, readonly=True)
    def channelvelocity(self, packet):
        return struct.pack("f", random.uniform(7.3060, 7.3079))

    @IOChannel(0o011, readonly=True)
    def channelaltitude(self, packet):
        return struct.pack("f", random.uniform(1115.0000, 1116.9999))

    # Old channel for this was 0o042
    @IOChannel(0o020, readonly=False)
    def secretchannel(self, packet):
        """The secret channel will not print anything, unless written to first.
        Once it is written to, it will dump the updated channel table"""
        if not packet.query:
            self.channel_table = True
            return b"..........................................."
        print("Secret channel:", self.channel_table)
        if self.channel_table:
            return CHANNELTABLE
        else:
            return
    
    # Old channel for this was 0o021
    @IOChannel(0o42, readonly=False, abortmode=True)
    def channeldebug(self, packet):
        """Spawn a secret debug shell"""
        # Only works in abort mode
        if not self.abort:
            raise UplinkBadShell(channel=packet.channel)
        # They have to write to us first
        if packet.query:
            return
        # Clear the buffer
        self.comms.recv()
        print("Spanning debug shell")
        self.comms.send_data(0, 0, packet.channel, b"UPLINK ABORT DEBUG SHELL\n\n$        ")
        self.comms.recv(channel=packet.channel)
        tm = time.time()
        while True:
            if (time.time() - tm) > 15:
                break
            # Flush
            try:
                command = self.comms.recv(channel=packet.channel)
                if not command:
                    continue
                command = command.decode("utf-8")
                print("Got command:", command)
                reply = shell(command)
                if not reply:
                    raise Exception()
                tm = time.time()
                self.comms.send_data(0, 0, packet.channel, reply)
                self.comms.lag((1, 1))

            except Exception as E:
                print(type(E), E)
                raise UplinkBadShell(channel=packet.channel)
        raise UplinkClientTimeout(channel=packet.channel)


def shell(command):
    args = command.strip().split()

    if args[0].upper().startswith("EXIT"):
        return None
    if args[0].upper().startswith("HELP"):
        return b"HELP:\nThese are the commands you can use.\nLS\tCAT\tPWD\tHELP\tEXIT"
    if args[0].startswith("LS"):
        return b"channels.txt\ncurrent.tle\nflag.txt"
    if args[0].startswith("CAT"):
        if len(args) > 1:
            if args[1].startswith("flag.txt"):
                print("Sending flag")
                return FLAG + b"\n"
            if args[1].startswith("channels.txt"):
                return CHANNELTABLE + b"\n"
            if args[1].startswith("current.tle"):
                return TLE + b"\n"
            return "FILE NOT FOUND: {}".format(args[1]).encode()
        return "FILE NOT FOUND: ".encode()
    if args[0].startswith("PWD"):
        return b"ROM://uplink/dbg/"
    return "COMMAND NOT FOUND: {}".format(command).encode()

def main():
    # Make it easy to change port in docker-compose
    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    try:
        port = os.environ.get("SERVER_PORT", "9001")
        port = int(port)
    except ValueError:
        port = 9001
    print("[+] Listening on {}:{}".format(host, port))
    server_forever(host, port, Uplink2Server)

main()

import os

from uplink.server import UplinkServer, server_forever
from uplink.satellite import IOChannel, Satellite
from uplink.errors import UplinkReadOnly




class Uplink1Sat(Satellite):
    """Satellite for Uplink 1"""
    def __init__(self):
        # We add extra data to make it easy on client librarys that arent quite to spec
        # or have trouble with converting 15 bit words
        self.flag = b"RITSEC{Did_You_lik3_that_latency?}      "
        self.abort = False
        self.lag = (0.0, 0.3)
        super(Uplink1Sat, self).__init__()

    # All of UP1 channels just return the flag
    @IOChannel(0o000, readonly=True)
    def channelTLE(self, packet):
        return self.flag

    @IOChannel(0o001, readonly=True)
    def channelname(self, packet):
        return self.flag

    @IOChannel(0o002, readonly=True)
    def channelmass(self, packet):
        return self.flag
    
    @IOChannel(0o003, readonly=True)
    def channeltime(self, packet):
        return self.flag

    @IOChannel(0o010, readonly=True)
    def channelvelocity(self, packet):
        return self.flag

    @IOChannel(0o011, readonly=True)
    def channelaltitude(self, packet):
        return self.flag


class Uplink1Server(UplinkServer):
    """Server for uplink 1"""
    sat = Uplink1Sat()


def main():
    # Make it easy to change port in docker-compose
    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    try:
        port = os.environ.get("SERVER_PORT", "8001")
        port = int(port)
    except ValueError:
        port = 8001
    print("[+] Listening on {}:{}".format(host, port))
    server_forever(host, port, Uplink1Server)

main()

import socketserver
import socket
import threading
import time

from .net import Uplink
from .errors import UplinkAbort
from .packet import AbortPacket
from .satellite import Satellite

class UplinkServer(socketserver.BaseRequestHandler):
    """This is a base object for the satellite listeners

    Create a subclass of this and define a handle function just like the handle function below
    """
    sat = None
    comms = None

    def handle(self):
        """We got a new connection"""
        # Make this your own custom satellite object!
        self.uplink_loop()

    def handle_packet(self, packet):
        # Handle the specific abort packet
        if packet.query == 0 and packet.channel == 0o101:
            raise UplinkAbort(channel=0o101)

        # IO with read or write
        buf = self.sat.IO(packet)
        #print("leaving IO")
        if buf:
            self.comms.send_data(packet.abort, packet.query, packet.channel, buf)

    def uplink_loop(self):
        # Make a new uplink handler with the socket
        self.comms = Uplink()
        self.sat.set_comms(self.comms)
        self.comms.setsocket(self.request)

        # Sleep for a time
        self.comms.lag()
        self.comms.send_handshake()

        abort_count = 0
        max_abort = getattr(self.sat, "max_abort", -1)
        tm = time.time()
        i = 200 # Max loops
        while i:
            i -= 1
            if max_abort and abort_count > max_abort:
                return
            try:
                packets = self.comms.recv_packets(1)
                if packets:
                    self.handle_packet(packets.pop())
                continue
            except UplinkAbort as abort:
                self.comms.send_packet(AbortPacket(abort))
                # Set the satelite to abort mode
                self.sat.abort = True
                abort_count += 1
                continue
            except socket.error as _:
                print("Connection died :(")
                return
            if (time.time() - tm) > 30:
                tm = time.time()
                self.comms.send_handshake()


class _ThreadedUplink(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def server_forever(host, port, uplink_server):
    server = _ThreadedUplink((host, port), uplink_server)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    server.serve_forever()
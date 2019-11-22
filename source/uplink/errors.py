
ERROR_CODES = {
    0o00000: "SYSTEM ABORTED",
    0o00001: "INVALID SIGNATURE",
    0o00002: "INVALID SIZE",
    0o00003: "READ ONLY VALUE",
    0o00004: "CLIENT TIMEOUT",
    # 0o00005
    0o00006: "UNKNOWN I/O CHANNEL",
    0o00007: "COMMAND SHELL ERROR"
}

def UplinkError(channel, code):
    return UplinkAbort(channel=channel, code=code)

class UplinkAbort(Exception):
    ABORTCODE = 0x00000
    ABORTMSG = ERROR_CODES.get(ABORTCODE, 0)
    def __init__(self, channel=0o0000, code=None):
        self.channel = channel
        if code is not None:
            self.ABORTCODE = code
        self.ABORTMSG = ERROR_CODES.get(self.ABORTCODE, 0)
        super(UplinkAbort, self).__init__(self.ABORTMSG)

    def __str__(self):
        return "UPLINK ABORT: {}: I/O CHAN. 0o{:o}".format(self.ABORTMSG, self.channel)

class UplinkInvalidSig(UplinkAbort):
    ABORTCODE = 0o00001


class UplinkInvalidSize(UplinkAbort):
    ABORTCODE = 0o00002

class UplinkReadOnly(UplinkAbort):
    ABORTCODE = 0o00003

class UplinkClientTimeout(UplinkAbort):
    ABORTCODE = 0o00004

class UplinkUnknownIO(UplinkAbort):
    ABORTCODE = 0o00006

class UplinkBadShell(UplinkAbort):
    ABORTCODE = 0o00007
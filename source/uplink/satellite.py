from functools import wraps
from .errors import UplinkUnknownIO, UplinkAbort, UplinkReadOnly


class IOChannel(object):
    def __init__(self, channel, readonly=False, abortmode=False):
        """
        channel - The IO channel that received this
        readonly - Whether or not this channel is read only
        abortmode - Whether or not this channel works in abort mode
        """
        self.channel = channel
        self.readonly = readonly
        self.abortmode = abortmode

    def __call__(self, func):
        func.IOCHANNEL = self.channel
        @wraps(func)
        def wrapped(satellite, packet):
            # Handle READ ONLY for the channels
            if not packet.query and self.readonly:
                raise UplinkReadOnly(channel=packet.channel)
            # If this channel doesnt work in abort mode, then abort
            if not self.abortmode and satellite.abort:
                print("We are in abort mode, exiting...", oct(packet.channel))
                raise UplinkAbort(channel=packet.channel, code=0o000)
            return func(satellite, packet)
        return wrapped

class Satellite(object):
    def __init__(self):
        self.abort = False
        # The communication channel
        self.comms = None
        # Max number of unhandled exceptions before exiting
        self.max_abort = 10
        # Load all the channel functions
        self.channel_map = {}
        

        for func in dir(self):
            func = getattr(self, func)
            channel = getattr(func, 'IOCHANNEL', False)
            if channel is not False:
                self.channel_map[channel] = func
    
    def set_comms(self, comms):
        self.comms = comms
        # Min and max lag
        lag = getattr(self, "lag", None)
        if lag:
            self.comms.lag_time = lag
        
        
    @IOChannel(0o101)
    def channel_abort(self, packet):
        if not packet.query and packet.data:
            raise UplinkAbort(channel=packet.channel)
        print(self.abort)        
        return
            
    def IO(self, packet):
        if packet.channel in self.channel_map:
            # Call the correct channel
            return self.channel_map[packet.channel](packet)
        else:
            raise UplinkUnknownIO(channel=packet.channel)
    
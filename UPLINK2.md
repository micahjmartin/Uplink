# Uplink II

This challenge wasn't ever solved iirc so I never released a writeup on it.

Basically, here is the steps to solve:

1. implement the spec
2. try to write to all the memory channels, all will abort except for 1
3. read from the channel that didnt abort. get this output
```
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
```

Notice how there is an abort debug shell...

4. trigger an abort
5. connect to the debug shell, cat flag
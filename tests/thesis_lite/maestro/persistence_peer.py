"""Fixed original-child malformed/foreign HELLO fixture, no persistence/workload."""

import array
import os
import socket
import sys

channel = socket.socket(fileno=int(sys.argv[1]))
mode = sys.argv[2]
wire = bytes.fromhex(sys.argv[3])
if mode == "malformed":
    channel.send(b"invalid")
elif mode == "rights":
    channel.sendmsg(
        [wire], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [0]))]
    )
elif mode == "mismatch":
    channel.send(wire)
elif mode == "eof":
    channel.close()
os.read(0, 1)
os._exit(0)

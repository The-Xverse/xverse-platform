"""Fixed owned test peer for malformed/foreign native ACK denial; no workload."""

import array
import os
import socket
import sys

channel = socket.socket(fileno=int(sys.argv[1]))
mode = sys.argv[2]
packet = bytes.fromhex(sys.argv[3])
if mode == "malformed":
    channel.send(b"invalid")
elif mode == "rights":
    channel.sendmsg(
        [packet], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [0]))]
    )
elif mode == "mismatch":
    channel.send(packet)
os.read(0, 1)
channel.close()

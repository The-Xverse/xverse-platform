"""Owned subreaper test harness; no production supervisor or launch API."""

import array
import ctypes
import json
import os
import signal
import socket
import struct
import subprocess
import sys
import time

libc = ctypes.CDLL(None, use_errno=True)
assert (
    libc.prctl(36, 1, 0, 0, 0) == 0
)  # PR_SET_CHILD_SUBREAPER, this isolated harness only
cgfd = int(sys.argv[2])
outer, inner = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
owner = os.fork()
if owner == 0:
    outer.close()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    now = time.monotonic_ns()
    guard = subprocess.Popen(
        [
            sys.argv[1],
            str(cgfd),
            str(child.fileno()),
            str(now + 8_000_000_000),
            str(now + 3_000_000_000),
            "500000000",
            "a" * 64,
        ],
        pass_fds=(cgfd, child.fileno()),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    child.close()
    parent.settimeout(2)
    ready = parent.recv(64)
    inner.sendmsg(
        [struct.pack("!Q", guard.pid) + ready],
        [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [parent.fileno()]))],
    )
    inner.recv(1)
    os._exit(0)
inner.close()
outer.settimeout(4)
guard_pid = None
channel = None
try:
    packet, ancillary, flags, _ = outer.recvmsg(72, socket.CMSG_SPACE(4))
    assert len(packet) == 72 and flags == 0 and len(ancillary) == 1
    guard_pid = struct.unpack("!Q", packet[:8])[0]
    fds = array.array("i")
    fds.frombytes(ancillary[0][2])
    assert len(fds) == 1
    channel = socket.socket(fileno=fds[0])
    assert struct.unpack("!4sIQQ32sQ", packet[8:])[1] == 16
    value = os.open("cgroup.freeze", os.O_WRONLY, dir_fd=cgfd)
    os.write(value, b"0")  # deliberately test-only thaw
    os.close(value)
    outer.send(b"x")
    assert os.waitpid(owner, 0)[1] == 0
    owner = None
    channel.settimeout(3)
    result = struct.unpack("!4sIQQ32sQ", channel.recv(64))
    assert result[1] == 18 and result[5] == 2
    until = time.monotonic() + 3
    while True:
        found, status = os.waitpid(guard_pid, os.WNOHANG)
        if found:
            assert status == 0
            guard_pid = None
            break
        assert time.monotonic() < until
        time.sleep(0.005)
    print(
        json.dumps(
            dict(
                reason=result[5],
                guard_reaped=True,
                owner_reaped=True,
                socket_still_open=channel.fileno() >= 0,
            )
        )
    )
finally:
    if owner is not None:
        os.kill(owner, signal.SIGKILL)
        os.waitpid(owner, 0)
    if guard_pid is not None:
        try:
            os.kill(guard_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.waitpid(guard_pid, 0)
    if channel:
        channel.close()
    outer.close()

"""Owned test-only worker faults; production worker has no injected modes."""

import os
import signal
import socket
import sys
from xverse.argus.writer import EvidenceRun
from xverse.maestro import persistence_worker

channel_fd, input_fd = map(int, sys.argv[1:3])
mode = sys.argv[3]
phase = None
receive = persistence_worker._receive


def receiving(*args, **kwargs):
    global phase
    value = receive(*args, **kwargs)
    phase = value["kind"]
    return value


persistence_worker._receive = receiving
name = "append_event" if mode == "append-fail" else "flush_buffer"
original = getattr(EvidenceRun, name)


def injected(*args, **kwargs):
    if phase != ("teardown" if mode.startswith("teardown-") else "probe"):
        return original(*args, **kwargs)
    if mode.endswith("-fail"):
        raise OSError("owned normal-outcome storage fault")
    result = original(*args, **kwargs)
    for _ in iter(int, 1):
        signal.pause()
    return result


setattr(EvidenceRun, name, injected)
try:
    persistence_worker.serve(socket.socket(fileno=channel_fd), input_fd)
    os._exit(0)
except Exception:
    os._exit(70)

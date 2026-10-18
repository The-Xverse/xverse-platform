"""Test-only original storage owner faults; never a production helper mode."""

import os
import socket
import sys
from xverse.argus.writer import EvidenceRun
from xverse.maestro import persistence_worker

channel, private = map(int, sys.argv[1:3])
mode = sys.argv[3]
phase = None
receive = persistence_worker._receive


def receiving(*args, **kwargs):
    global phase
    result = receive(*args, **kwargs)
    phase = result["kind"]
    return result


persistence_worker._receive = receiving
flush, abort = EvidenceRun.flush_buffer, EvidenceRun.abort


def flushing(self, *args, **kwargs):
    if phase == "closure" and mode == "flush-fail":
        raise OSError("owned flush fault")
    return flush(self, *args, **kwargs)


def aborting(self, *args, **kwargs):
    if phase == "closure" and mode == "abort-before":
        raise OSError("owned pre-abort fault")
    result = abort(self, *args, **kwargs)
    if phase == "closure" and mode == "abort-after":
        raise OSError("owned post-abort fault")
    return result


EvidenceRun.flush_buffer, EvidenceRun.abort = flushing, aborting
try:
    persistence_worker.serve(socket.socket(fileno=channel), private)
    os._exit(0)
except Exception:
    os._exit(70)

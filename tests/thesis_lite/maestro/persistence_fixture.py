"""Owned fixed service fault fixture; production service has no fault modes."""

import os
import signal
import socket
import sys
from xverse.argus.writer import EvidenceRun
from xverse.maestro.admission import PermitSession
from xverse.maestro import persistence_worker
from xverse_xdl.lifecycle import FileEvidenceJournal

channel_fd, input_fd, announce_fd, release_fd = map(int, sys.argv[1:5])
mode = sys.argv[5]
phase = None
receive = persistence_worker._receive


def receiving(*args, **kwargs):
    global phase
    frame = receive(*args, **kwargs)
    phase = frame["kind"]
    return frame


persistence_worker._receive = receiving
stage, disposition = mode.split("-", 1)
target, name = {
    "init": (FileEvidenceJournal, "__init__"),
    "claim": (FileEvidenceJournal, "claim_intent"),
    "append": (EvidenceRun, "append_event"),
    "flush": (EvidenceRun, "flush_buffer"),
    "revalidate": (PermitSession, "revalidate_start_intent"),
    "abort": (EvidenceRun, "abort"),
}[stage]
original = getattr(target, name)


def injected(*args, **kwargs):
    if stage == "revalidate" and phase != "revalidate":
        return original(*args, **kwargs)
    if disposition == "fail":
        os.write(announce_fd, b"F")
        raise OSError("owned injected storage failure")
    result = original(*args, **kwargs)
    os.write(announce_fd, b"H")
    if disposition == "ignoreterm":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    os.read(release_fd, 1)
    return result


setattr(target, name, injected)
try:
    persistence_worker.serve(socket.socket(fileno=channel_fd), input_fd)
    os._exit(0)
except Exception:
    os._exit(70)

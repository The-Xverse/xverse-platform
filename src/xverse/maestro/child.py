"""Exact supported child capabilities; no discovery or metadata-based adoption."""

import ctypes
import os
import signal
import subprocess


# Linux UAPI numbers, x86-64 syscall table and asm-generic (AArch64).
# Unknown hosts or denied KCMP_FILE reject bootstrap admission; no inode fallback.
_KCMP_NUMBER = {"x86_64": 312, "aarch64": 272}
_LIBC = None


def _same_description(first, second):
    number = _KCMP_NUMBER.get(os.uname().machine)
    if number is None:
        raise ValueError("ML-PIDFD-COMPARE-UNSUPPORTED")
    global _LIBC
    if _LIBC is None:
        _LIBC = ctypes.CDLL(None, use_errno=True)
        _LIBC.syscall.restype = ctypes.c_long
    result = _LIBC.syscall(
        ctypes.c_long(number),
        ctypes.c_int(os.getpid()),
        ctypes.c_int(os.getpid()),
        ctypes.c_int(0),
        ctypes.c_ulong(first),
        ctypes.c_ulong(second),
    )
    if result < 0:
        raise OSError(ctypes.get_errno(), "ML-PIDFD-COMPARE-UNAVAILABLE")
    return result == 0


class _PidfdCapability:
    """Private original duplicate, never borrowed for client-visible FD aliases."""

    def __init__(self, descriptor):
        self._original, self._pid = self, os.getpid()
        self._descriptor = os.dup(descriptor)
        try:
            self.check(descriptor)
        except Exception:
            os.close(self._descriptor)
            self._descriptor = -1
            raise

    def _holder(self):
        if (
            self._original is not self
            or self._pid != os.getpid()
            or self._descriptor < 0
        ):
            raise ValueError("ML-PIDFD-CAPABILITY")

    def check(self, descriptor):
        self._holder()
        if (
            type(descriptor) is not int
            or descriptor < 0
            or not _same_description(self._descriptor, descriptor)
        ):
            raise ValueError("ML-PIDFD-DESCRIPTION-MISMATCH")

    def fileno(self):
        self._holder()
        return self._descriptor

    def duplicate(self):
        return os.dup(self.fileno())

    def close(self):
        self._holder()
        os.close(self._descriptor)
        self._descriptor = -1

    def __reduce_ex__(self, protocol):
        raise TypeError("original pidfd capability cannot be copied or serialized")


def check_child(process, *, live=False):
    if type(process) is subprocess.Popen:
        return
    from .bootstrap import BootstrapChild

    if type(process) is not BootstrapChild:
        raise ValueError("ML-CHILD-CAPABILITY")
    process._holder()
    if live:
        process._ordinary()


def open_child_pidfd(process):
    check_child(process, live=True)
    if type(process) is subprocess.Popen:
        return os.pidfd_open(process.pid, 0)
    return process._capability.duplicate()


def wait_child(process, descriptor, *, consume=False):
    check_child(process)
    if type(process) is subprocess.Popen:
        flags = os.WEXITED | os.WNOHANG | (0 if consume else os.WNOWAIT)
        return os.waitid(os.P_PIDFD, descriptor, flags)
    return process._wait(descriptor, consume=consume)


def signal_child(process, descriptor, signum):
    """Signal only the original capability; a borrowed alias is not authority."""
    check_child(process)
    target = (
        descriptor
        if type(process) is subprocess.Popen
        else process._capability.fileno()
    )
    signal.pidfd_send_signal(target, signum)

"""Disposable private proposal worker; no workload/provider/permit capability."""

import hashlib
import os
import socket
import struct
import sys
import time

from .controller import ControllerError, _input, _frame, _read_input, _receive, _send


def main():
    if len(sys.argv) != 3:
        return 64
    channel_fd, input_fd = (int(v) for v in sys.argv[1:])
    raw = _read_input(input_fd)
    os.close(input_fd)
    config = _input(raw)
    scope = hashlib.sha256(raw).hexdigest()
    channel = socket.socket(fileno=channel_fd)
    try:
        if channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_SEQPACKET:
            raise ControllerError("ML-CONTROLLER-SOCKET")
        peer = struct.unpack("3i", channel.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        channel.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        channel.setblocking(False)
        _send(channel, _frame("hello", 0, config, scope,
            dict(host_session=config['session'], observed_at=time.monotonic())))
        sequence = 0
        vocabulary = {u['unit']: u['phases'] for u in config['units']}
        while sequence < 1024:
            # This end is computed only in this new controller clock session.
            request = _receive(channel, peer, time.monotonic_ns() + 5_000_000_000, lambda: None)
            if (request['kind'] != 'request' or request['sequence'] != sequence + 1
                or request['scope'] != scope or request['session'] != config['session']):
                raise ControllerError("ML-CONTROLLER-SCOPE")
            body = request['body']
            if set(body) != {'unit', 'phase', 'budget_ns'}:
                raise ControllerError("ML-CONTROLLER-REQUEST")
            unit, phase, budget = body['unit'], body['phase'], body['budget_ns']
            if (type(budget) is not int or not 0 < budget <= 5_000_000_000
                or not ((unit is None and phase == 'heartbeat') or
                    (type(unit) is str and unit in vocabulary and phase in vocabulary[unit]))):
                raise ControllerError("ML-CONTROLLER-REQUEST")
            end = time.monotonic_ns() + budget
            sequence += 1
            reply = _frame('ok', sequence, config, scope,
                dict(unit=unit, phase=phase, host_session=config['session'], observed_at=time.monotonic()))
            if time.monotonic_ns() >= end:
                raise ControllerError("ML-CONTROLLER-TIMEOUT")
            _send(channel, reply)
        return 0
    finally:
        channel.close()


if __name__ == '__main__':
    raise SystemExit(main())

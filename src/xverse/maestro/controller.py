"""Original disposable controller channel; productive authority stays in RunBroker."""

from dataclasses import dataclass, field
import array
import hashlib
import math
import os
import re
import select
import signal
import socket
import struct
import threading
import time
import uuid

from xverse.argus.schema import canonical_bytes
from .bootstrap import BootstrapChild, _CREATE, _sealed
from .owner import _Original, OwnerError, _deadline
from .persistence import _strict_json, _read_input
from .prbc import BoundaryDescriptor

MAX_PACKET = 65536


class ControllerError(OwnerError):
    pass


def _input(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_PACKET:
        raise ControllerError("ML-CONTROLLER-INPUT")
    data = _strict_json(raw)
    if (
        type(data) is not dict
        or set(data) != {"version", "run_id", "lifecycle", "session", "units"}
        or type(data["version"]) is not int or data["version"] != 1
        or type(data["run_id"]) is not str or not 0 < len(data["run_id"]) <= 128
        or type(data["lifecycle"]) is not str
        or re.fullmatch("[a-f0-9]{64}", data["lifecycle"]) is None
        or type(data["session"]) is not str
        or re.fullmatch("[A-Za-z0-9_.:-]{1,64}", data["session"]) is None
        or type(data["units"]) is not list or not 1 <= len(data["units"]) <= 16
    ):
        raise ControllerError("ML-CONTROLLER-INPUT")
    seen = set()
    for unit in data["units"]:
        if (
            type(unit) is not dict or set(unit) != {"unit", "phases"}
            or type(unit["unit"]) is not str or not 0 < len(unit["unit"]) <= 4096
            or unit["unit"] in seen
            or type(unit["phases"]) is not list or not 1 <= len(unit["phases"]) <= 5
            or any(type(p) is not str or p not in ("prepare", "start", "observe", "stop", "cleanup") for p in unit["phases"])
            or len(unit["phases"]) != len(set(unit["phases"]))
        ):
            raise ControllerError("ML-CONTROLLER-UNITS")
        seen.add(unit["unit"])
    if canonical_bytes(data) != raw:
        raise ControllerError("ML-CONTROLLER-CANONICAL")
    return data


def _decode(raw):
    if not raw or len(raw) > MAX_PACKET:
        raise ControllerError("ML-CONTROLLER-PACKET")
    frame = _strict_json(raw)
    if (
        type(frame) is not dict
        or set(frame) != {"version", "kind", "sequence", "scope", "session", "body"}
        or type(frame["version"]) is not int or frame["version"] != 1
        or frame["kind"] not in ("hello", "request", "ok")
        or type(frame["sequence"]) is not int or not 0 <= frame["sequence"] <= 1024
        or type(frame["scope"]) is not str or re.fullmatch("[a-f0-9]{64}", frame["scope"]) is None
        or type(frame["session"]) is not str or re.fullmatch("[A-Za-z0-9_.:-]{1,64}", frame["session"]) is None
        or type(frame["body"]) is not dict
    ):
        raise ControllerError("ML-CONTROLLER-FRAME")
    return frame


def _send(channel, frame):
    raw = canonical_bytes(frame)
    _decode(raw)
    if channel.send(raw) != len(raw):
        raise ControllerError("ML-CONTROLLER-SEND")


def _receive(channel, peer, until, check):
    while True:
        check()
        remaining = (until - time.monotonic_ns()) / 1e9
        if remaining <= 0:
            raise ControllerError("ML-CONTROLLER-TIMEOUT")
        if not select.select([channel], [], [], min(remaining, 0.01))[0]:
            continue
        try:
            raw, ancillary, flags, _ = channel.recvmsg(MAX_PACKET + 1,
                socket.CMSG_SPACE(12) + socket.CMSG_SPACE(32), socket.MSG_CMSG_CLOEXEC)
        except BlockingIOError:
            continue
        valid = not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
        credentials = []
        for level, kind, data in ancillary:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                received = array.array("i")
                received.frombytes(data[:len(data) - len(data) % received.itemsize])
                for fd in received:
                    os.close(fd)
                valid = False
            elif level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS and len(data) == 12:
                credentials.append(struct.unpack("3i", data))
            else:
                valid = False
        check()
        if not valid or credentials != [peer] or time.monotonic_ns() >= until:
            raise ControllerError("ML-CONTROLLER-PEER")
        return _decode(raw)


def _frame(kind, sequence, config, scope, body):
    return dict(version=1, kind=kind, sequence=sequence, scope=scope,
                session=config["session"], body=body)


@dataclass(frozen=True)
class ControllerRetirement:
    original_child_dead: bool
    original_child_reaped: bool
    own_boundary_released: bool
    workload_waits_known: bool = field(default=False, init=False)
    ready_for_execution: bool = field(default=False, init=False)


class ControllerSession(_Original):
    def __init__(self, key, broker, child, channel, descriptor, raw):
        if key is not _CREATE or type(child) is not BootstrapChild:
            raise ControllerError("ML-CONTROLLER-ORIGINAL")
        self._retain()
        self.broker, self.process, self.channel, self.descriptor = broker, child, channel, descriptor
        self.config, self.scope = _input(raw), hashlib.sha256(raw).hexdigest()
        self.session_id = self.config["session"]
        info = os.fstat(channel.fileno())
        self._channel_identity = info.st_dev, info.st_ino
        self._pins = broker, child, channel, descriptor, raw, self.session_id, self.scope, self._channel_identity
        self._peer = child.pid, os.getuid(), os.getgid()
        self._sequence = 0
        self._lock = threading.Lock()
        self._retired = False
        self._retirement = None
        self._phase = "unreconciled"
        self._recovery = None
        self._view = None
        channel.setblocking(False)

    def _holder(self):
        super()._holder()
        broker, child, channel, descriptor, raw, session, scope, identity = self._pins
        broker._holder()
        child._holder()
        if not self._retired:
            info = os.fstat(channel.fileno())
            if (info.st_dev, info.st_ino) != identity:
                raise ControllerError("ML-CONTROLLER-CHANNEL")
        if (
            self.broker is not broker or self.process is not child or self.channel is not channel
            or self.descriptor is not descriptor or self.config != _input(raw)
            or self.session_id != session or self.scope != scope
            or not any(self is c for c in broker._controllers)
            or child._root is not broker.session
            or child._root._clients.get(child._slot) is not self
            or child._root._issued[child._slot] != (5, descriptor, descriptor)
        ):
            raise ControllerError("ML-CONTROLLER-ORIGINAL")

    def _ordinary(self):
        self._holder()
        if self._retired or self.broker._current_controller is not self:
            raise ControllerError("ML-CONTROLLER-RETIRED")
        self.process._ordinary()
        if select.select([self.process._capability.fileno()], [], [], 0)[0]:
            raise ControllerError("ML-CONTROLLER-DEAD")

    def _start_access(self):
        self._ordinary()
        if self._phase != "active":
            raise ControllerError("ML-CONTROLLER-NOT-RECONCILED")
        if self is not self.broker._controllers[0]:
            if self._recovery is None or self._recovery.controller is not self:
                raise ControllerError("ML-CONTROLLER-NOT-RECONCILED")
            self._recovery._holder()
            if (self._view is None or self._recovery.view is not self._view
                or self.broker.owner._views.get(id(self._view)) is not self._view
                or self._recovery._result is None
                or not self._recovery._result.ordinary_reconciled):
                raise ControllerError("ML-CONTROLLER-NOT-RECONCILED")
            self._view._holder()

    def _ready(self, deadline):
        self._ordinary()
        until = self.broker._until(deadline)
        actual = _receive(self.channel, self._peer, until, self._ordinary)
        expected = _frame("hello", 0, self.config, self.scope, actual["body"])
        if actual != expected or set(actual["body"]) != {"observed_at", "host_session"}:
            raise ControllerError("ML-CONTROLLER-HELLO")
        self._clock(actual["body"])

    def _clock(self, body):
        value = body["observed_at"]
        if (body["host_session"] != self.session_id or type(value) not in (int, float)
            or not math.isfinite(value) or value < 0):
            raise ControllerError("ML-CONTROLLER-CLOCK")
        # It belongs to the controller's session; never compare with broker time.

    def request(self, unit, phase, deadline):
        self._ordinary()
        until = self.broker._until(deadline)
        vocabulary = {u["unit"]: u["phases"] for u in self.config["units"]}
        if not ((unit is None and phase == "heartbeat") or
                (type(unit) is str and unit in vocabulary and phase in vocabulary[unit])):
            raise ControllerError("ML-CONTROLLER-REQUEST")
        if self._sequence >= 1024:
            raise ControllerError("ML-CONTROLLER-CAPACITY")
        if not self._lock.acquire(False):
            raise ControllerError("ML-CONTROLLER-CONFLICT")
        try:
            sequence = self._sequence + 1
            body = dict(unit=unit, phase=phase, budget_ns=until - time.monotonic_ns())
            _send(self.channel, _frame("request", sequence, self.config, self.scope, body))
            reply = _receive(self.channel, self._peer, until, self._ordinary)
            self._sequence = sequence
            expected = _frame("ok", sequence, self.config, self.scope, reply["body"])
            if (reply != expected or set(reply["body"]) != {"unit", "phase", "observed_at", "host_session"}
                or reply["body"]["unit"] != unit or reply["body"]["phase"] != phase):
                raise ControllerError("ML-CONTROLLER-ACK")
            self._clock(reply["body"])
            self._ordinary()
            return reply["body"]
        except Exception:
            self._retired = True
            self.channel.close()
            try:
                signal.pidfd_send_signal(self.process._capability.fileno(), signal.SIGKILL)
            except (OSError, ValueError):
                pass  # A later explicit cleanup end must establish actual wait facts.
            raise
        finally:
            self._lock.release()

    def retire(self, deadline, *, terminate=False):
        self._holder()
        if type(terminate) is not bool:
            raise ControllerError("ML-CONTROLLER-RETIRE")
        if self._retirement is not None:
            return self._retirement
        until = _deadline(deadline, self.broker.owner.session)
        self._retired = True
        self.channel.close()
        if terminate:
            try:
                signal.pidfd_send_signal(self.process._capability.fileno(), signal.SIGKILL)
            except ProcessLookupError:
                pass
        result = None
        while time.monotonic_ns() < until:
            result = self.process._wait(self.process._capability.fileno(), consume=True)
            if result is not None:
                break
            select.select([self.process._capability.fileno()], [], [], min(0.01, max(0, (until-time.monotonic_ns())/1e9)))
        if result is None:
            return ControllerRetirement(False, False, False)
        manager = self.broker.session.boundaries
        manager.terminate(self.descriptor, deadline=deadline)
        released = manager.release_empty(self.descriptor, deadline=deadline)
        self._retirement = ControllerRetirement(True, True, released.boundary_released)
        return self._retirement

    def reconcile(self, policies, active_deadline, cleanup_deadline, *, _coordinator=None, _request=None):
        from .recovery import IssuerRecovery

        self._ordinary()
        if self._phase != "unreconciled" or self is self.broker._controllers[0]:
            raise ControllerError("ML-CONTROLLER-RECONCILE")
        recovery = IssuerRecovery(self.broker.session, self.broker.owner,
            policies=policies, controller=self, _coordinator=_coordinator, _request=_request)
        self._recovery = recovery
        result = recovery.reconcile(active_deadline, cleanup_deadline)
        try:
            if (not result.ordinary_reconciled or any(
                row.status == "owned" and row.native_running is not True
                or row.status == "released" and (row.unit_id not in recovery._released_units or row.native_running is not False)
                or row.status == "stopped" and (row.unit_id not in recovery._stopped_units or row.native_running is not False)
                for row in result.units)):
                raise ControllerError("ML-CONTROLLER-RECONCILE")
            view = recovery.view
            view.check_health(active_deadline, force=True)
            self._ordinary()
            for unit in view._released:
                view._fresh(unit)
            self._view = view
            self._phase = "active"
            self.broker.owner._starts_retired = False
            return view
        except Exception:
            self.broker.cancel("controller-reconciliation-incomplete", deadline=active_deadline)
            raise

    def dispose(self):
        _Original._holder(self)
        broker, child, channel, descriptor, raw, session, scope, identity = self._pins
        _Original._holder(broker)
        child._holder()
        if (self.broker is not broker or self.process is not child
            or self.channel is not channel or self.descriptor is not descriptor
            or self.session_id != session or self.scope != scope
            or self.config != _input(raw)
            or child._root is not broker._pins[0]
            or child._root._clients.get(child._slot) is not self
            or not any(self is c for c in broker._controllers)):
            raise ControllerError("ML-CONTROLLER-ORIGINAL")
        if child._result is None:
            raise ControllerError("ML-CONTROLLER-RETAINED")
        self._retired = True
        channel.close()


def admit_controller(broker, session_id, deadline):
    from .run_broker import RunBroker

    if type(broker) is not RunBroker:
        raise ControllerError("ML-CONTROLLER-BROKER")
    broker._holder()
    broker.session.check_start_authorization()
    broker.owner._check(deadline)
    broker._until(deadline)
    raw = canonical_bytes(dict(version=1, run_id=broker.storage.run_id,
        lifecycle=broker.storage.prepared.lifecycle_digest, session=session_id,
        units=[dict(unit=u.unit_id, phases=[a.phase for a in u.plan.actions]) for u in broker.storage.prepared.units]))
    _input(raw)
    if session_id == broker.owner.session:
        raise ControllerError("ML-CONTROLLER-HOST-SESSION")
    if (len(broker._controllers) >= broker._controller_budget or
        any(c.session_id == session_id for c in broker._controllers)):
        raise ControllerError("ML-CONTROLLER-ADMISSION")
    previous = broker._current_controller
    if previous is not None:
        previous._holder()
        if previous._retirement is None or not previous._retirement.own_boundary_released:
            raise ControllerError("ML-CONTROLLER-OLD-LIVE")
    if not broker._lock.acquire(False):
        raise ControllerError("ML-CONTROLLER-CONFLICT")
    entered = False
    try:
        broker.owner._check(deadline)
        broker.session.check_start_authorization()
        if (len(broker._controllers) >= broker._controller_budget
            or any(c.session_id == session_id for c in broker._controllers)):
            raise ControllerError("ML-CONTROLLER-ADMISSION")
        previous = broker._current_controller
        if previous is not None:
            previous._holder()
            if previous._retirement is None or not previous._retirement.own_boundary_released:
                raise ControllerError("ML-CONTROLLER-OLD-LIVE")
        descriptor = BoundaryDescriptor(broker.storage.run_id,
            "helper:controller:" + str(len(broker._controllers) + 1), 1,
            "controller-" + uuid.uuid4().hex, broker.session.boundaries.release_epoch)
        entered = True
        broker.session.boundaries.create_frozen(descriptor, deadline=deadline)
        broker._until(deadline)
        child, channel = broker.session._spawn_role(5, descriptor, descriptor,
            _sealed(raw, "maestro-original-controller"), deadline)
        client = ControllerSession(_CREATE, broker, child, channel, descriptor, raw)
        broker._controllers = (*broker._controllers, client)
        broker._controller_log = broker._controllers
        broker._current_controller = client
        broker.session._clients[child._slot] = client
        broker.session._client_log = tuple(sorted(broker.session._clients.items()))
        client._ready(deadline)
        if previous is None:
            client._phase = "active"
        return client
    except Exception:
        if entered:
            broker.cancel("controller-admission-uncertain", deadline=deadline)
        raise
    finally:
        broker._lock.release()

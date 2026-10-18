"""Original-child M3/Argus ownership and bounded supervisor RPC (partial lifecycle).

Bootstrap supplies an actual child/socket and private sealed configuration. This
module neither launches helpers/workloads nor authenticates operator approval.
The supervisor path performs no storage I/O; kernel/scheduler stalls remain external.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import array
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import select
import signal
import socket
import stat
import struct
import subprocess
import threading
import time
import uuid

from xverse.argus.schema import canonical_bytes
from .admission import _verify_prepared, validate_permits
from .owner import OwnerError, _Original, _deadline, _pin
from .projection import prepare_lifecycle
from .supervisor import CancellationLatch
from .time import HostDeadline

MAX_CONFIG = 1 << 20
MAX_PACKET = 1 << 16
SEALS = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL


class PersistenceError(OwnerError):
    pass


def _plain(value):
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _strict_json(data):
    def pairs(items):
        value = {}
        for key, child in items:
            if key in value:
                raise PersistenceError("ML-PERSIST-DUPLICATE")
            value[key] = child
        return value

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise PersistenceError("ML-PERSIST-NONFINITE")
        return result

    def bad(value):
        raise PersistenceError("ML-PERSIST-NONFINITE")

    try:
        return json.loads(
            data, object_pairs_hook=pairs, parse_constant=bad, parse_float=number
        )
    except (ValueError, RecursionError, UnicodeError) as error:
        raise PersistenceError("ML-PERSIST-JSON") from error


@dataclass(frozen=True)
class PersistenceInput:
    prepared: object
    run_id: str
    session: str
    generation_ns: int
    private_bytes: bytes = field(repr=False)
    result: object = field(repr=False)
    resources: tuple = field(repr=False)


def encode_configuration(
    prepared,
    result,
    resources,
    *,
    run_id,
    bindings,
    approvals,
    session,
    generation_deadline,
    journal_path,
    evidence_root,
):
    """Pure private bootstrap serialization, not approval or worker creation."""
    if (
        type(generation_deadline) is not HostDeadline
        or generation_deadline.session != session
    ):
        raise PersistenceError("ML-PERSIST-HOST-SESSION")
    generation_deadline.__post_init__()
    remaining = generation_deadline.monotonic_seconds - time.monotonic()
    if not 0 < remaining <= 394:
        raise PersistenceError("ML-PERSIST-GENERATION")
    validate_permits(
        prepared,
        result,
        resources,
        run_id=run_id,
        bindings=bindings,
        approvals=approvals,
        now=datetime.now(timezone.utc),
        initial_generation=1,
    )
    descriptors = tuple(dict.fromkeys(u.provider for u in prepared.units))
    check = prepare_lifecycle(
        result, resources, provider_descriptors=descriptors, limits=prepared.limits
    )
    if check.canonical_bytes != prepared.canonical_bytes:
        raise PersistenceError("ML-PERSIST-PREPARATION")
    documents = []
    for resource in resources:
        identity = resource.identity
        document = {
            "apiVersion": identity.api_version,
            "kind": identity.kind,
            "metadata": {
                "name": identity.name,
                "namespace": identity.namespace,
                "version": resource.revision,
                "provenance": _plain(resource.provenance),
                "labels": _plain(resource.labels),
            },
            "spec": _plain(resource.content),
        }
        for namespace, entry in resource.extensions.items():
            pointer = "/extensions/" + namespace.replace("~", "~0").replace("/", "~1")
            for payload in entry["payloads"]:
                if payload["pointer"] == pointer:
                    document.setdefault("extensions", {})[namespace] = _plain(
                        payload["value"]
                    )
        documents.append(document)
    roots = [str(Path(p)) for p in (journal_path, evidence_root)]
    if any(not Path(p).is_absolute() for p in roots):
        raise PersistenceError("ML-PERSIST-ROOT")
    generation_ns = int(generation_deadline.monotonic_seconds * 1e9)
    data = {
        "version": 1,
        "resources": documents,
        "providers": [asdict(d) for d in descriptors],
        "limits": asdict(prepared.limits),
        "experiment_digest": prepared.experiment_digest,
        "lifecycle_digest": prepared.lifecycle_digest,
        "run_id": run_id,
        "session": session,
        "generation_ns": generation_ns,
        "journal_path": roots[0],
        "evidence_root": roots[1],
        "bindings": [_plain(asdict(b)) for b in bindings],
        "approvals": [_plain(asdict(a)) for a in approvals],
    }
    encoded = canonical_bytes(data)
    if len(encoded) > MAX_CONFIG:
        raise PersistenceError("ML-PERSIST-CONFIG-LIMIT")
    return PersistenceInput(
        prepared, run_id, session, generation_ns, encoded, result, tuple(resources)
    )


def sealed_input_fd(config):
    """Bootstrap-only memfd creation; not included in RPC time-bound claims."""
    if type(config) is not PersistenceInput or len(config.private_bytes) > MAX_CONFIG:
        raise PersistenceError("ML-PERSIST-CONFIG")
    fd = os.memfd_create("maestro-private-input", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        view = memoryview(config.private_bytes)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise PersistenceError("ML-PERSIST-CONFIG-WRITE")
            view = view[written:]
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, SEALS)
        return fd
    except Exception:
        os.close(fd)
        raise


def _read_input(fd):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_CONFIG:
        raise PersistenceError("ML-PERSIST-CONFIG-LIMIT")
    if fcntl.fcntl(fd, fcntl.F_GET_SEALS) & SEALS != SEALS:
        raise PersistenceError("ML-PERSIST-CONFIG-SEALS")
    data = os.pread(fd, info.st_size + 1, 0)
    if len(data) != info.st_size:
        raise PersistenceError("ML-PERSIST-CONFIG-SHORT")
    return data


def _frame(kind, sequence, operation, deadline_ns, scope, body):
    return {
        "version": 1,
        "kind": kind,
        "sequence": sequence,
        "operation": operation,
        "deadline": deadline_ns,
        "scope": scope,
        "body": body,
    }


def _decode(data):
    if not data or len(data) > MAX_PACKET:
        raise PersistenceError("ML-PERSIST-PACKET")
    frame = _strict_json(data)
    if (
        type(frame) is not dict
        or set(frame)
        != {"version", "kind", "sequence", "operation", "deadline", "scope", "body"}
        or type(frame["version"]) is not int
        or frame["version"] != 1
        or frame["kind"]
        not in {"hello", "init", "commit", "revalidate", "abort", "ok", "error"}
        or type(frame["sequence"]) is not int
        or not 0 <= frame["sequence"] <= 128
        or type(frame["deadline"]) is not int
        or frame["deadline"] < 0
        or type(frame["operation"]) is not str
        or len(frame["operation"]) > 64
        or type(frame["scope"]) is not str
        or len(frame["scope"]) != 64
        or type(frame["body"]) is not dict
    ):
        raise PersistenceError("ML-PERSIST-FRAME")
    return frame


def _receive(channel, peer, until, check):
    while True:
        check()
        remaining = (until - time.monotonic_ns()) / 1e9
        if remaining <= 0:
            raise PersistenceError("ML-PERSIST-TIMEOUT")
        if not select.select([channel], [], [], min(remaining, 0.01))[0]:
            continue
        try:
            data, anc, flags, _ = channel.recvmsg(
                MAX_PACKET + 1,
                socket.CMSG_SPACE(12) + socket.CMSG_SPACE(32),
                socket.MSG_CMSG_CLOEXEC,
            )
        except BlockingIOError:
            continue
        credentials = []
        valid = not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
        for level, kind, payload in anc:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                values = array.array("i")
                values.frombytes(
                    payload[: len(payload) - len(payload) % values.itemsize]
                )
                for fd in values:
                    os.close(fd)
                valid = False
            elif (
                level == socket.SOL_SOCKET
                and kind == socket.SCM_CREDENTIALS
                and len(payload) == 12
            ):
                credentials.append(struct.unpack("3i", payload))
            else:
                valid = False
        check()
        if not valid or credentials != [peer] or time.monotonic_ns() >= until:
            raise PersistenceError("ML-PERSIST-SENDER")
        return _decode(data)


def _send(channel, frame):
    data = canonical_bytes(frame)
    if len(data) > MAX_PACKET or channel.send(data) != len(data):
        raise PersistenceError("ML-PERSIST-SEND")


@dataclass(frozen=True)
class _PersistenceReceipt:
    unit_id: str
    operation: str
    intent_digest: bytes
    flush_digest: bytes
    event_id: str
    deadline_ns: int
    ready_for_execution: bool = field(default=False, init=False)


@dataclass(frozen=True)
class PersistenceDrain:
    worker_reaped: bool
    identity_retained: bool
    returncode: int | None
    diagnostic: str | None
    ready_for_execution: bool = field(default=False, init=False)
    cleanup_complete: bool = field(default=False, init=False)


class PersistenceClient(_Original):
    """Original-child authority; actual creation/pins supplied by trusted bootstrap."""

    def __init__(self, process, channel, config, latch, *, deadline):
        if (
            type(process) is not subprocess.Popen
            or type(channel) is not socket.socket
            or type(config) is not PersistenceInput
            or type(latch) is not CancellationLatch
        ):
            raise PersistenceError("ML-PERSIST-INPUT")
        if (
            channel.family != socket.AF_UNIX
            or channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
            != socket.SOCK_SEQPACKET
            or not channel.getsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED)
        ):
            raise PersistenceError("ML-PERSIST-SOCKET")
        _verify_prepared(config.prepared, config.result, config.resources)
        self._resources = config.resources
        self._execution_ids = {
            b["unit_id"]: b["execution_id"]
            for b in _strict_json(config.private_bytes)["bindings"]
        }
        self._retain()
        self.process, self.channel, self.latch = process, channel, latch
        self.prepared, self.run_id, self.session, self.generation_ns = (
            config.prepared,
            config.run_id,
            config.session,
            config.generation_ns,
        )
        self._pins = (
            process,
            channel,
            latch,
            self.prepared,
            self.run_id,
            self.session,
            self.generation_ns,
        )
        self._scope = hashlib.sha256(config.private_bytes).hexdigest()
        self._pid_pin = process.pid
        info = os.fstat(channel.fileno())
        self._socket_identity = (info.st_dev, info.st_ino)
        self._pidfd, self._sequence = -1, 0
        self._lock = threading.Lock()
        self._failed, self._aborted, self._ready = False, False, False
        self._claims, self._attempted = {}, set()
        self._drain_deadline = None
        self._term_sent = self._kill_sent = False
        self._drained = None
        self.last_writer_state = "unknown"
        channel.setblocking(False)
        try:
            self._pidfd = os.pidfd_open(process.pid, 0)
            self._live()
            hello = _receive(channel, self._peer, self._until(deadline), self._live)
            if hello != _frame("hello", 0, "", 0, self._scope, {}):
                raise PersistenceError("ML-PERSIST-HELLO")
            _, _, facts = self._rpc("init", {}, deadline)
            if facts != {
                "run_id": self.run_id,
                "lifecycle_digest": self.prepared.lifecycle_digest,
                "session": self.session,
                "generation_ns": self.generation_ns,
            }:
                raise PersistenceError("ML-PERSIST-INIT-ACK")
            self._ready = True
            self.last_writer_state = "open"
        except Exception:
            try:
                self._fail()
            finally:
                if self._pidfd >= 0:
                    os.close(self._pidfd)
                    self._pidfd = -1
            raise

    @property
    def _peer(self):
        return self._pid_pin, os.getuid(), os.getgid()

    def _holder(self):
        super()._holder()
        current = (
            self.process,
            self.channel,
            self.latch,
            self.prepared,
            self.run_id,
            self.session,
            self.generation_ns,
        )
        if (
            any(a is not b for a, b in zip(current[:4], self._pins[:4]))
            or current[4:] != self._pins[4:]
        ):
            raise PersistenceError("ML-PERSIST-REPLACED")
        self._pins[2]._check()

    def _live(self, *, allow_cancel=False, allow_exit=False):
        self._holder()
        channel = self._pins[1]
        info = os.fstat(channel.fileno())
        if (
            self._pidfd < 0
            or self._pins[0].pid != self._pid_pin
            or (info.st_dev, info.st_ino) != self._socket_identity
        ):
            raise PersistenceError("ML-PERSIST-CHILD")
        exited = os.waitid(
            os.P_PIDFD, self._pidfd, os.WEXITED | os.WNOHANG | os.WNOWAIT
        )
        if not allow_exit and (
            exited is not None or select.select([self._pidfd], [], [], 0)[0]
        ):
            raise PersistenceError("ML-PERSIST-CHILD")
        if self._failed or (self._pins[2].cancelled and not allow_cancel):
            raise PersistenceError("ML-PERSIST-CLOSED")

    def _available(self):
        # A fork/copy must never be able to revoke the original parent's authority.
        self._holder()
        if self.latch.cancelled or self._aborted:
            raise PersistenceError("ML-PERSIST-NOT-OPEN")
        try:
            self._live()
            if not self._ready:
                raise PersistenceError("ML-PERSIST-NOT-OPEN")
        except Exception:
            self._fail()
            raise

    def _until(self, deadline):
        until = _deadline(deadline, self.session)
        if until > self.generation_ns:
            raise PersistenceError("ML-PERSIST-DEADLINE")
        return until

    def _fail(self):
        # Always target retained objects, even if a public alias was replaced.
        self._failed = True
        self._pins[2].cancel("persistence-uncertain")
        try:
            self._pins[1].shutdown(socket.SHUT_WR)
        except OSError:
            pass
        if self._pidfd >= 0 and not self._term_sent:
            try:
                signal.pidfd_send_signal(self._pidfd, signal.SIGTERM)
                self._term_sent = True
            except ProcessLookupError:
                pass

    def _rpc(self, kind, body, deadline):
        if not self._lock.acquire(blocking=False):
            raise PersistenceError("ML-PERSIST-CONFLICT")
        allow_cancel = kind == "abort"

        def check():
            return self._live(allow_cancel=allow_cancel, allow_exit=allow_cancel)

        try:
            self._live(allow_cancel=allow_cancel)
            until = self._until(deadline)
            if kind == "commit":
                if body["unit"] in self._attempted:
                    raise PersistenceError("ML-PERSIST-REPLAY-UNIT")
                self._attempted.add(body["unit"])
            sequence = self._sequence + 1
            if sequence > 128:
                raise PersistenceError("ML-PERSIST-SEQUENCE")
            operation = "ml-" + uuid.uuid4().hex
            request = _frame(kind, sequence, operation, until, self._scope, body)
            _send(self._pins[1], request)
            reply = _receive(self._pins[1], self._peer, until, check)
            self._sequence = sequence
            if (
                any(
                    reply[k] != request[k]
                    for k in ("version", "sequence", "operation", "deadline", "scope")
                )
                or reply["kind"] != "ok"
            ):
                raise PersistenceError("ML-PERSIST-ACK")
            check()
            if time.monotonic_ns() >= until:
                raise PersistenceError("ML-PERSIST-LATE")
            return operation, until, reply["body"]
        except Exception:
            self._fail()
            raise
        finally:
            self._lock.release()

    def commit_intent(self, unit_id, deadline):
        self._available()
        if unit_id in self._attempted or unit_id not in {
            u.unit_id for u in self.prepared.units
        }:
            raise PersistenceError("ML-PERSIST-REPLAY-UNIT")
        operation, until, body = self._rpc(
            "commit", {"unit": unit_id, "generation": 1}, deadline
        )
        try:
            if (
                set(body) != {"event", "intent", "flush"}
                or body["event"] != operation + "-intent"
            ):
                raise PersistenceError("ML-PERSIST-COMMIT-ACK")
            receipt = _PersistenceReceipt(
                unit_id,
                operation,
                _pin(body["intent"]),
                _pin(body["flush"]),
                body["event"],
                until,
            )
            self._claims[id(receipt)] = receipt
            return receipt
        except Exception:
            self._fail()
            raise

    def _claim_execution_id(self, receipt):
        self._holder()
        if self._claims.get(id(receipt)) is not receipt:
            raise PersistenceError("ML-PERSIST-CLAIM")
        return self._execution_ids[receipt.unit_id]

    def revalidate_intent(self, receipt, deadline):
        self._available()
        if (
            self._claims.get(id(receipt)) is not receipt
            or self._until(deadline) > receipt.deadline_ns
        ):
            raise PersistenceError("ML-PERSIST-CLAIM")
        _, _, body = self._rpc(
            "revalidate",
            {"unit": receipt.unit_id, "claim": receipt.operation},
            deadline,
        )
        if body != {}:
            self._fail()
            raise PersistenceError("ML-PERSIST-REVALIDATE-ACK")

    def abort(self, deadline):
        self._holder()
        if self._aborted:
            return self.last_writer_state
        _, _, body = self._rpc("abort", {}, deadline)
        if body != {"writer_state": "failed"}:
            self._fail()
            raise PersistenceError("ML-PERSIST-ABORT-ACK")
        self.last_writer_state, self._aborted = "failed", True
        self._pins[2].cancel("persistence-aborted")
        return self.last_writer_state

    def drain(self, deadline):
        """Bounded exact-child reap; never claims workload/C1 or evidence completion."""
        self._holder()
        if self._drained and self._drained.worker_reaped:
            return self._drained
        if not (self._failed or self._aborted):
            raise PersistenceError("ML-PERSIST-STILL-OPEN")
        until = self._until(deadline)
        if until - time.monotonic_ns() > 2_000_000_000:
            raise PersistenceError("ML-PERSIST-DRAIN-LIMIT")
        self._drain_deadline = min(self._drain_deadline or until, until)
        kill_at = min(time.monotonic_ns() + 100_000_000, self._drain_deadline)
        while True:
            try:
                result = os.waitid(os.P_PIDFD, self._pidfd, os.WEXITED | os.WNOHANG)
            except OSError:
                self._drained = PersistenceDrain(
                    False, True, None, "ML-PERSIST-WAIT-UNRESOLVED"
                )
                return self._drained
            if result is not None:
                code = (
                    result.si_status
                    if result.si_code == os.CLD_EXITED
                    else -result.si_status
                )
                self._pins[0].returncode = code
                self._drained = PersistenceDrain(True, True, code, None)
                return self._drained
            now = time.monotonic_ns()
            if now >= self._drain_deadline:
                self._drained = PersistenceDrain(
                    False, True, None, "ML-PERSIST-DRAIN-UNRESOLVED"
                )
                return self._drained
            if now >= kill_at and not self._kill_sent:
                try:
                    signal.pidfd_send_signal(self._pidfd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self._kill_sent = True
            select.select(
                [self._pidfd], [], [], min(0.01, (self._drain_deadline - now) / 1e9)
            )

    def dispose(self):
        self._holder()
        if not self._drained or not self._drained.worker_reaped:
            raise PersistenceError("ML-PERSIST-RETAINED")
        if self._pidfd >= 0:
            os.close(self._pidfd)
            self._pidfd = -1
        self._pins[1].close()

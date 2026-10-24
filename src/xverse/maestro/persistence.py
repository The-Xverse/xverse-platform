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
import re
from types import SimpleNamespace
import select
import signal
import socket
import stat
import struct
import threading
import time
import uuid

from xverse.argus.schema import canonical_bytes
from .child import check_child, open_child_pidfd, wait_child, signal_child
from .admission import _verify_prepared, validate_generation_contexts
from .owner import OwnerError, _Original, _deadline, _pin
from .projection import prepare_lifecycle
from .supervisor import CancellationLatch
from .time import HostDeadline

MAX_CONFIG = 1 << 20
MAX_PACKET = 1 << 16
MAX_REQUESTS = 8192
SEALS = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL


class PersistenceError(OwnerError):
    pass


# A request already sent when the run is cancelled may still receive its reply for this long; then the call
# fails closed as before. It stays well inside the admitted cancellation drain (<= 2 s, 024 detailed design),
# so a hung worker still releases a cancel promptly (thesis S1 FR-005).
CANCEL_REPLY_GRACE_NS = 500_000_000


class PersistenceCancelled(PersistenceError):
    """An ordinary call refused because the run was cancelled, while the storage owner is healthy.

    It keeps the ``ML-PERSIST-CLOSED`` code, but it is not a storage failure: the client is not failed,
    so the terminal records and the abort still reach the owner (thesis S1 FR-005; amendment of
    ADR-ML3-PERSISTENCE-0001 for in-flight cancellation)."""


@dataclass(frozen=True)
class PersistenceRPCFailure:
    """One local observation; never a durable outcome, ACK or cause attribution."""
    kind: str
    stage: str
    session: str
    sequence: int | None
    operation: str | None
    started_ns: int
    deadline_ns: int | None
    failed_ns: int
    diagnostic: str


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
    schedule: object = field(default=None, repr=False)
    future_contexts: tuple = field(default=(), repr=False)
    public_exports: tuple = field(default=(), repr=False)
    coverage: object = field(default=None, repr=False)
    broker_artifact: object = field(default=None, repr=False)
    collection: object = field(default=None, repr=False)


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
    schedule=None,
    future_contexts=(),
    public_exports=(),
    coverage=None,
    broker_artifact=None,
    collection=None,
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
    from .evidence import export_declarations
    exports = export_declarations(public_exports)
    bindings, approvals, resources = tuple(bindings), tuple(approvals), tuple(resources)
    futures = validate_generation_contexts(
        prepared,
        result,
        resources,
        run_id=run_id,
        bindings=bindings,
        approvals=approvals,
        now=datetime.now(timezone.utc),
        future_contexts=future_contexts,
    )
    descriptors = tuple(dict.fromkeys(u.provider for u in prepared.units))
    check = prepare_lifecycle(
        result, resources, provider_descriptors=descriptors, limits=prepared.limits,
        fault_clock=getattr(prepared, "fault_clock", None),
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
    if getattr(prepared, "fault_clock", None) is not None:  # ADR-ML3-SIMTIME-0001 note ST-1: optional key
        data["fault_clock"] = asdict(prepared.fault_clock)
    if futures:
        data["version"] = 2
        data["future_contexts"] = [
            {
                "binding": _plain(asdict(c.binding)),
                "approval": _plain(asdict(c.approval)),
            }
            for c in futures
        ]
    if schedule is not None:
        from .schedule_plan import ScheduleAdmission, decode_schedule

        if (
            type(schedule) is not ScheduleAdmission
            or decode_schedule(prepared, _strict_json(schedule.canonical_bytes))
            != schedule
        ):
            raise PersistenceError("ML-PERSIST-SCHEDULE")
        data["schedule"] = _strict_json(schedule.canonical_bytes)
        if schedule.required_requests + len(exports) > schedule.request_limit:
            raise PersistenceError("ML-EVIDENCE-EXPORT-CAPACITY")
    if exports:
        data["version"] = 3
        data["public_exports"] = [asdict(e) for e in exports]
    if coverage is not None:
        from .coverage import CoverageAdmission, bind_runtime_coverage, runtime_coverage_input
        if type(coverage) is not CoverageAdmission:
            raise PersistenceError("ML-COVERAGE-RUNTIME-ADMISSION")
        bind_runtime_coverage(coverage, coverage.digest, prepared, result, resources,
            run_id=run_id, session=session, generation_ns=generation_ns,
            bindings=bindings, future_contexts=futures, schedule=schedule)
        data["version"] = 4
        data["coverage"] = runtime_coverage_input(coverage)
    if broker_artifact is not None:
        from .public_blobs import BrokerArtifact, decode_broker_artifact
        if type(broker_artifact) is not BrokerArtifact or coverage is None:
            raise PersistenceError("ML-EVIDENCE-BLOB-ADMISSION")
        decode_broker_artifact(vars(broker_artifact),coverage,coverage.digest)
        if schedule is not None and schedule.required_requests+len(exports)+1 > schedule.request_limit:
            raise PersistenceError("ML-EVIDENCE-BLOB-CAPACITY")
        data["version"] = 5
        data["broker_artifact"] = vars(broker_artifact)
    if collection is not None:
        from .collection_plan import bind_collection
        if coverage is None or broker_artifact is None:
            raise PersistenceError('ML-COLLECTION-CONFIG')
        bind_collection(collection, coverage, coverage.digest, generation_ns=generation_ns,
                        schedule=schedule, exports=exports)
        data['version'] = 6
        data['collection'] = collection.configuration()
    encoded = canonical_bytes(data)
    if len(encoded) > MAX_CONFIG:
        raise PersistenceError("ML-PERSIST-CONFIG-LIMIT")
    return PersistenceInput(
        prepared,
        run_id,
        session,
        generation_ns,
        encoded,
        result,
        tuple(resources),
        schedule,
        futures,
        exports,
        coverage,
        broker_artifact,
        collection,
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
        not in {
            "hello",
            "init",
            "commit",
            "generation",
            "issued",
            "public-export",
            "public-blob",
            "collect",
            "terminal-report",
            "revalidate",
            "audit",
            "probe",
            "teardown",
            "tick",
            "schedule",
            "abort",
            "closure",
            "recovery",
            "ok",
            "error",
        }
        or type(frame["sequence"]) is not int
        or not 0 <= frame["sequence"] <= MAX_REQUESTS
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


def _receive_packet(channel, peer, until, check, *, maximum_blob=0, blob_purposes=('broker-projection',)):
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
        credentials, rights = [], []
        valid = not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
        try:
            for level, kind, payload in anc:
                if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                    values = array.array("i")
                    values.frombytes(payload[:len(payload)-len(payload)%values.itemsize])
                    rights.extend(values)
                    if len(payload)%values.itemsize:valid=False
                elif level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS and len(payload)==12:
                    credentials.append(struct.unpack("3i",payload))
                else:valid=False
            check()
            if not valid or credentials != [peer] or time.monotonic_ns() >= until:
                raise PersistenceError("ML-PERSIST-SENDER")
            frame=_decode(data)
            if frame['kind']=='public-blob':
                if maximum_blob<=0 or len(rights)!=1 or not 0<frame['deadline']<=until:
                    raise PersistenceError('ML-EVIDENCE-BLOB-RIGHTS')
                from .public_blobs import read_public_blob
                return frame,read_public_blob(rights[0],frame['body'],frame['deadline'],maximum_blob,check,
                                             purposes=blob_purposes)
            if rights:raise PersistenceError("ML-PERSIST-SENDER")
            return frame,None
        finally:
            for fd in rights:os.close(fd)


def _receive(channel, peer, until, check, *, maximum_blob=0, with_blob=False, blob_purposes=('broker-projection',)):
    packet=_receive_packet(channel,peer,until,check,maximum_blob=maximum_blob,blob_purposes=blob_purposes)
    return packet if with_blob else packet[0]


def _send(channel, frame):
    data = canonical_bytes(frame)
    if len(data) > MAX_PACKET or channel.send(data) != len(data):
        raise PersistenceError("ML-PERSIST-SEND")


def _send_public_blob(channel, frame, fd):
    data=canonical_bytes(frame)
    if (len(data)>MAX_PACKET or channel.sendmsg([data],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[fd]))])!=len(data)):
        raise PersistenceError('ML-EVIDENCE-BLOB-SEND')


@dataclass(frozen=True)
class _PersistenceReceipt:
    unit_id: str
    operation: str
    intent_digest: bytes
    flush_digest: bytes
    event_id: str
    deadline_ns: int
    execution_id: str
    generation: int
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
        check_child(process, live=True)
        if (
            type(channel) is not socket.socket
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
        serialized = _strict_json(config.private_bytes)
        self.schedule = None
        if "schedule" in serialized:
            from .schedule_plan import decode_schedule

            self.schedule = decode_schedule(config.prepared, serialized["schedule"])
        if self.schedule != config.schedule:
            raise PersistenceError("ML-PERSIST-SCHEDULE")
        if type(config.future_contexts) is not tuple or serialized.get(
            "future_contexts", []
        ) != [
            {
                "binding": _plain(asdict(c.binding)),
                "approval": _plain(asdict(c.approval)),
            }
            for c in config.future_contexts
        ]:
            raise PersistenceError("ML-PERSIST-FUTURE-CONTEXTS")
        self._future_contexts = self._future_contexts_pin = config.future_contexts
        from .evidence import decode_exports
        if decode_exports(serialized) != config.public_exports or type(config.public_exports) is not tuple:
            raise PersistenceError("ML-EVIDENCE-EXPORT-CONFIG")
        self._public_exports = self._public_exports_pin = config.public_exports
        self.coverage = config.coverage
        if self.coverage is None:
            if "coverage" in serialized:
                raise PersistenceError("ML-COVERAGE-RUNTIME-CONFIG")
        else:
            from .coverage import CoverageAdmission, bind_runtime_coverage, runtime_coverage_input
            if type(self.coverage) is not CoverageAdmission:
                raise PersistenceError("ML-COVERAGE-RUNTIME-ADMISSION")
            bind_runtime_coverage(self.coverage, self.coverage.digest, config.prepared, config.result, config.resources,
                run_id=config.run_id, session=config.session, generation_ns=config.generation_ns,
                bindings=tuple(SimpleNamespace(**b) for b in serialized["bindings"]),
                future_contexts=config.future_contexts, schedule=self.schedule)
            if serialized.get("version") != (6 if config.collection is not None else 5 if config.broker_artifact is not None else 4) or serialized.get("coverage") != runtime_coverage_input(self.coverage):
                raise PersistenceError("ML-COVERAGE-RUNTIME-CONFIG")
        self._coverage_pin = (self.coverage, self.coverage.digest if self.coverage is not None else None)
        self._broker_artifact = config.broker_artifact
        self._broker_publication = self._broker_publication_pin = None
        self._publication_lock = self._publication_lock_pin = threading.Lock()
        if self._broker_artifact is None:
            if "broker_artifact" in serialized:raise PersistenceError('ML-EVIDENCE-BLOB-ADMISSION')
        else:
            from .public_blobs import BrokerArtifact,decode_broker_artifact
            if (type(self._broker_artifact) is not BrokerArtifact or self.coverage is None
                or decode_broker_artifact(serialized.get('broker_artifact'),self.coverage,self.coverage_digest)!=self._broker_artifact):
                raise PersistenceError('ML-EVIDENCE-BLOB-ADMISSION')
        self._broker_artifact_pin=(self._broker_artifact,canonical_bytes(vars(self._broker_artifact)) if self._broker_artifact is not None else None)
        self.collection = config.collection
        if self.collection is None:
            if 'collection' in serialized:
                raise PersistenceError('ML-COLLECTION-CONFIG')
        else:
            from .collection_plan import bind_collection, decode_collection
            if self.coverage is None or self._broker_artifact is None:
                raise PersistenceError('ML-COLLECTION-CONFIG')
            expected = bind_collection(self.collection, self.coverage, self.coverage_digest,
                generation_ns=config.generation_ns, schedule=self.schedule, exports=self._public_exports)
            if decode_collection(serialized.get('collection'), self.coverage, self.coverage_digest) != expected:
                raise PersistenceError('ML-COLLECTION-CONFIG')
        self._collection_pin = self.collection, self.collection.canonical_bytes if self.collection is not None else None
        self._collection_lock = self._collection_lock_pin = threading.Lock()
        self._collection_attempted = False
        self._collection_outcome = self._collection_outcome_pin = None
        self._terminal_lock = self._terminal_lock_pin = threading.Lock()
        self._terminal_attempted = False
        self._terminal_outcome = self._terminal_outcome_pin = None
        self._rpc_failure = self._rpc_failure_pin = None
        self._rpc_failure_values = None
        self._export_receipts = self._export_receipts_pin = {}
        self._request_limit = self.schedule.request_limit if self.schedule else 128
        self._schedule_pin = self.schedule, self._request_limit
        self._resources = config.resources
        self._result_input = config.result
        self._input_pins = self._resources, self._result_input
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
        self._probe_receipts, self._probe_attempted = {}, set()
        self._issued_receipts = self._issued_receipts_pin = {}
        self._issuance_sequence = 0
        self._generation_probe_receipts = {}
        self._generation_teardown_receipts = {}
        self._evidence_sequence = self._evidence_ordinal = self._evidence_m3 = 0
        self._teardown_sequence = 0
        self._teardown_receipts, self._teardown_attempted = {}, set()
        self._schedule_used = {}
        self._recovery_used = {}
        self._schedule_sequence = 0
        self._schedule_last_event = None
        self._drain_deadline = None
        self._term_sent = self._kill_sent = False
        self._drained = None
        self._disposed = False
        self._dispose_error = None
        self.last_writer_state = "unknown"
        self._closure_attempted, self._closure_result = False, None
        channel.setblocking(False)
        try:
            self._pidfd = open_child_pidfd(process)
            self._live()
            hello = _receive(channel, self._peer, self._until(deadline), self._live)
            if hello != _frame("hello", 0, "", 0, self._scope, {}):
                raise PersistenceError("ML-PERSIST-HELLO")
            init_operation, _, facts = self._rpc("init", {}, deadline)
            expected = {
                "run_id": self.run_id,
                "lifecycle_digest": self.prepared.lifecycle_digest,
                "session": self.session,
                "generation_ns": self.generation_ns,
            }
            if self.schedule is not None:
                expected.update(
                    schedule_digest=self.schedule.digest,
                    request_limit=self._request_limit,
                )
            if self.coverage is not None:
                validation = facts.get("validation")
                expected.update(validation=dict(admission_digest=self.coverage.digest,
                    event_id=self.run_id, ingestion_ordinal=1, operation_id=init_operation))
                if (type(validation) is not dict or type(validation.get("ingestion_ordinal")) is not int):
                    raise PersistenceError("ML-COVERAGE-VALIDATION-ACK")
            if facts != expected:
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
    def coverage_digest(self):
        return self._coverage_pin[1]

    @property
    def rpc_failure(self):
        # Failure/cleanup observations must not depend on ordinary live aliases.
        _Original._holder(self)
        try:
            record = self._rpc_failure
            if record is not self._rpc_failure_pin:
                raise PersistenceError('ML-PERSIST-RPC-CONTEXT')
            if record is not None:
                if type(record) is not PersistenceRPCFailure:
                    raise PersistenceError('ML-PERSIST-RPC-CONTEXT')
                values = tuple(getattr(record, n) for n in PersistenceRPCFailure.__dataclass_fields__)
                if values != self._rpc_failure_values:
                    raise PersistenceError('ML-PERSIST-RPC-CONTEXT')
        except (AttributeError, TypeError):
            raise PersistenceError('ML-PERSIST-RPC-CONTEXT') from None
        return record

    @property
    def _peer(self):
        return self._pid_pin, os.getuid(), os.getgid()

    def _holder(self):
        if (self._terminal_lock is not self._terminal_lock_pin
            or self._terminal_outcome is not self._terminal_outcome_pin
            or self._terminal_outcome is not None and self._terminal_outcome[2].public_bytes != self._terminal_outcome[3]):
            raise PersistenceError('ML-TERMINAL-REPLACED')
        if (self.collection is not self._collection_pin[0]
            or self.collection is not None and self.collection.canonical_bytes != self._collection_pin[1]
            or self._collection_lock is not self._collection_lock_pin
            or self._collection_outcome is not self._collection_outcome_pin
            or self._collection_outcome is not None and self._collection_outcome[2].public_bytes != self._collection_outcome[3]):
            raise PersistenceError('ML-COLLECTION-REPLACED')
        if (self._broker_artifact is not self._broker_artifact_pin[0]
            or self._broker_artifact is not None and canonical_bytes(vars(self._broker_artifact)) != self._broker_artifact_pin[1]
            or self._broker_publication is not self._broker_publication_pin
            or self._broker_publication is not None and self._broker_publication[1].public_bytes != self._broker_publication[2]
            or self._publication_lock is not self._publication_lock_pin):
            raise PersistenceError('ML-EVIDENCE-BLOB-REPLACED')
        if (self.coverage is not self._coverage_pin[0]
            or self.coverage is not None and self.coverage.digest != self._coverage_pin[1]):
            raise PersistenceError("ML-COVERAGE-RUNTIME-REPLACED")
        if (self._public_exports is not self._public_exports_pin
            or self._export_receipts is not self._export_receipts_pin):
            raise PersistenceError("ML-EVIDENCE-EXPORT-REGISTRY")
        if self._issued_receipts is not self._issued_receipts_pin:
            raise PersistenceError("ML-ISSUED-REGISTRY")
        super()._holder()
        if (
            self._resources is not self._input_pins[0]
            or self._result_input is not self._input_pins[1]
        ):
            raise PersistenceError("ML-PERSIST-INPUT-REPLACED")
        if (
            self._future_contexts is not self._future_contexts_pin
            or self.schedule is not self._schedule_pin[0]
            or self._request_limit != self._schedule_pin[1]
        ):
            raise PersistenceError("ML-PERSIST-SCHEDULE-REPLACED")
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

    def _live(self, *, allow_cancel=False, allow_exit=False, in_flight=False):
        # ``in_flight``: the request is already sent; after a cancel its reply may still arrive within the
        # caller's bounded grace (S1 FR-005). Child exit, identity and failure are still checked.
        self._holder()
        cancelled = self._pins[2].cancelled and not self._failed
        if cancelled and not allow_cancel and not in_flight:
            raise PersistenceCancelled("ML-PERSIST-CLOSED")
        # After a cancel the bootstrap root refuses ordinary use, so a call already in flight checks the
        # child as the terminal kinds do; exit and identity are still checked below.
        live = not (allow_exit or allow_cancel or (in_flight and cancelled))
        try:
            check_child(self._pins[0], live=live)
        except Exception:
            # RB1 (S1a-1 revision): a cancel that landed after the read above is checked as the terminal
            # kinds check it; a refusal without a cancel, or after a storage failure, still fails closed.
            if not (live and self._pins[2].cancelled and not self._failed):
                raise
            check_child(self._pins[0], live=False)
        channel = self._pins[1]
        info = os.fstat(channel.fileno())
        if (
            self._pidfd < 0
            or self._pins[0].pid != self._pid_pin
            or (info.st_dev, info.st_ino) != self._socket_identity
        ):
            raise PersistenceError("ML-PERSIST-CHILD")
        exited = wait_child(self._pins[0], self._pidfd)
        if not allow_exit and (
            exited is not None or select.select([self._pidfd], [], [], 0)[0]
        ):
            raise PersistenceError("ML-PERSIST-CHILD")
        if self._failed:
            raise PersistenceError("ML-PERSIST-CLOSED")
        if self._pins[2].cancelled and not allow_cancel and not in_flight:
            raise PersistenceCancelled("ML-PERSIST-CLOSED")  # RB1: a late cancel is not a storage failure

    def _available(self):
        # A fork/copy must never be able to revoke the original parent's authority.
        self._holder()
        if self.latch.cancelled or self._aborted:
            raise PersistenceError("ML-PERSIST-NOT-OPEN")
        try:
            self._live()
            if not self._ready:
                raise PersistenceError("ML-PERSIST-NOT-OPEN")
        except PersistenceCancelled:
            raise  # a cancel that raced the check above is not a storage failure (S1 FR-005)
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
                signal_child(self._pins[0], self._pidfd, signal.SIGTERM)
                self._term_sent = True
            except ProcessLookupError:
                pass

    def _rpc(self, kind, body, deadline, *, public_blob_fd=None):
        if not self._lock.acquire(blocking=False):
            raise PersistenceError("ML-PERSIST-CONFLICT")
        started_ns = time.monotonic_ns()
        stage, sequence, operation, until = 'validation', None, None, None
        allow_cancel = kind in ("abort", "closure", "public-export", "public-blob", "collect", "terminal-report") or (
            kind == 'teardown' and self.collection is not None
        ) or (
            kind == "schedule"
            and body.get("kind")
            in ("failure", "step-disposition", "unit-disposition", "run-terminal")
        )

        cancel_seen = []

        def check():
            in_flight = stage in ('receive', 'acknowledgement', 'post-ack')
            if in_flight and not allow_cancel and self._pins[2].cancelled and not self._failed:
                now = time.monotonic_ns()
                if not cancel_seen:
                    cancel_seen.append(now)
                elif now - cancel_seen[0] > CANCEL_REPLY_GRACE_NS:
                    raise PersistenceError("ML-PERSIST-CANCEL-GRACE")  # no reply within the grace: fail closed (DR-1)
            return self._live(
                allow_cancel=allow_cancel, allow_exit=kind in ("abort", "closure") or (
                    kind == 'terminal-report' and body.get('action') == 'close'),
                in_flight=in_flight,
            )

        try:
            self._live(allow_cancel=allow_cancel)
            until = self._until(deadline)
            if kind == "commit":
                if body["unit"] in self._attempted:
                    raise PersistenceError("ML-PERSIST-REPLAY-UNIT")
                self._attempted.add(body["unit"])
            sequence = self._sequence + 1
            if sequence > self._request_limit:
                raise PersistenceError("ML-PERSIST-SEQUENCE")
            operation = "ml-" + uuid.uuid4().hex
            request = _frame(kind, sequence, operation, until, self._scope, body)
            stage = 'send'
            if public_blob_fd is None:_send(self._pins[1], request)
            elif kind=='public-blob' and self._broker_artifact is not None:
                _send_public_blob(self._pins[1],request,public_blob_fd)
            else:raise PersistenceError('ML-EVIDENCE-BLOB-RIGHTS')
            stage = 'receive'
            reply = _receive(self._pins[1], self._peer, until, check)
            stage = 'acknowledgement'
            self._sequence = sequence
            if (
                any(
                    reply[k] != request[k]
                    for k in ("version", "sequence", "operation", "deadline", "scope")
                )
                or reply["kind"] != "ok"
            ):
                raise PersistenceError("ML-PERSIST-ACK")
            stage = 'post-ack'
            check()
            if time.monotonic_ns() >= until:
                raise PersistenceError("ML-PERSIST-LATE")
            return operation, until, reply["body"]
        except PersistenceCancelled:
            if stage != 'validation':
                self._fail()  # defensive: a cancel refusal is only raised before the request is sent
            raise  # nothing was sent: storage stays healthy and no RPC failure is recorded (S1 FR-005)
        except Exception as error:
            try:
                if self._rpc_failure_pin is None:
                    code = str(error)
                    safe = code if len(code) <= 128 and re.fullmatch(r'ML-[A-Z0-9-]+', code) else 'ML-PERSIST-RPC-FAILED'
                    kinds = ('init','commit','generation','issued','public-export','public-blob',
                             'collect','terminal-report','revalidate','audit','probe','teardown',
                             'tick','schedule','abort','closure','recovery')
                    self._rpc_failure = PersistenceRPCFailure(
                        kind if type(kind) is str and kind in kinds else 'unknown', stage,
                        self._pins[5], sequence, operation, started_ns, until,
                        time.monotonic_ns(), safe)
                    self._rpc_failure_pin = self._rpc_failure
                    self._rpc_failure_values = tuple(getattr(self._rpc_failure, n) for n in PersistenceRPCFailure.__dataclass_fields__)
                if isinstance(error, PersistenceError):
                    try:error.rpc_failure = self.rpc_failure
                    except (ValueError, AttributeError):pass
            except Exception:
                pass  # Optional observations never bypass original fail-closed cleanup.
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
                self._execution_ids[unit_id],
                1,
            )
            self._claims[id(receipt)] = receipt
            return receipt
        except Exception:
            self._fail()
            raise

    def prepare_generation(self, broker, statement, deadline):
        from .run_broker import RunBroker, _GenerationStatement

        self._available()
        if (
            type(broker) is not RunBroker
            or type(statement) is not _GenerationStatement
            or broker.storage is not self
            or broker._active_generation is not statement
        ):
            raise PersistenceError("ML-GENERATION-ORIGINAL")
        broker._holder()
        issuer = statement.issuer
        issuer.revalidate_issued(issuer._handle)
        old = issuer.recipe.descriptor
        if (
            broker.issuer(old.unit_id) is not issuer
            or self._claims.get(id(statement.prior)) is not statement.prior
            or self._teardown_receipts.get(old.unit_id) is not statement.cleanup
            or not broker.session.boundaries.record(
                old, deadline=deadline
            ).boundary_released
            or self._until(deadline) > statement.deadline_ns
        ):
            raise PersistenceError("ML-GENERATION-ORIGINAL")
        context = next(
            (
                c
                for c in self._future_contexts
                if c.binding.unit_id == old.unit_id
                and c.binding.generation == statement.descriptor.generation
            ),
            None,
        )
        if context is None:
            raise PersistenceError("ML-GENERATION-NOT-ADMITTED")
        from .owner import _hash

        request = dict(
            unit=old.unit_id,
            generation=statement.descriptor.generation,
            prior=statement.prior.operation,
            handle=asdict(issuer._handle),
            boundary_digest="sha256:" + _hash(list(old.key)).hex(),
            cleanup_event=statement.cleanup.event_id,
        )
        operation, until, body = self._rpc("generation", request, deadline)
        try:
            if (
                set(body) != {"event", "intent", "flush", "generation"}
                or body["event"] != operation + "-intent"
                or type(body["generation"]) is not int
                or body["generation"] != statement.descriptor.generation
            ):
                raise PersistenceError("ML-GENERATION-ACK")
            receipt = _PersistenceReceipt(
                old.unit_id,
                operation,
                _pin(body["intent"]),
                _pin(body["flush"]),
                body["event"],
                until,
                context.binding.execution_id,
                context.binding.generation,
            )
            self._claims[id(receipt)] = receipt
            self._execution_ids[old.unit_id] = context.binding.execution_id
            if old.unit_id in self._probe_receipts:
                self._generation_probe_receipts[old.unit_id, old.generation] = (
                    self._probe_receipts.pop(old.unit_id)
                )
            self._generation_teardown_receipts[old.unit_id, old.generation] = (
                self._teardown_receipts.pop(old.unit_id)
            )
            return receipt
        except Exception:
            self._fail()
            raise

    def _claim_execution_id(self, receipt):
        self._holder()
        if self._claims.get(id(receipt)) is not receipt:
            raise PersistenceError("ML-PERSIST-CLAIM")
        return receipt.execution_id

    def revalidate_intent(self, receipt, deadline, *, issuance=None):
        self._available()
        if (
            self._claims.get(id(receipt)) is not receipt
            or self._until(deadline) > receipt.deadline_ns
        ):
            raise PersistenceError("ML-PERSIST-CLAIM")
        request = {"unit":receipt.unit_id,"claim":receipt.operation}
        if issuance is not None:
            if self._issued_receipts.get((receipt.unit_id,receipt.generation)) is not issuance:
                raise PersistenceError("ML-ISSUED-ORIGINAL")
            request["issued"] = issuance.event_id
        _, _, body = self._rpc(
            "revalidate",
            request,
            deadline,
        )
        if body != {}:
            self._fail()
            raise PersistenceError("ML-PERSIST-REVALIDATE-ACK")

    def revalidate_run(self, broker, deadline):
        """Read-only original history audit; never reauthorizes a start intent."""
        from .run_broker import RunBroker

        self._available()
        if type(broker) is not RunBroker or broker.storage is not self:
            raise PersistenceError("ML-PERSIST-ORIGINAL-BROKER")
        broker._holder()
        _, _, body = self._rpc("audit", {}, deadline)
        if body != {}:
            self._fail()
            raise PersistenceError("ML-PERSIST-AUDIT-ACK")

    def record_issued(self, issuer, statement, deadline):
        from .run_broker import RunUnitIssuer
        from .issuance_evidence import IssuanceStatement, validate_issued

        self._available()
        if (type(issuer) is not RunUnitIssuer or type(statement) is not IssuanceStatement
            or issuer.owner.persistence is not self or issuer._active_issuance is not statement
            or statement.issuer is not issuer or statement.handle is not issuer._handle
            or issuer._issuance_proof is None or statement.native_ack is not issuer._issuance_proof[0]
            or self._claims.get(id(statement.claim)) is not statement.claim
            or self._until(deadline)>statement.deadline_ns):
            raise PersistenceError("ML-ISSUED-ORIGINAL")
        issuer.revalidate_issued(statement.handle)
        issuer._boundary()
        key = issuer.unit_id, issuer.recipe.descriptor.generation
        if key in self._issued_receipts:
            raise PersistenceError("ML-ISSUED-REPLAY")
        operation, _, body = self._rpc("issued",dict(unit=issuer.unit_id,
            generation=key[1],claim=statement.claim.operation,handle=asdict(statement.handle),
            observed_at=statement.observed_at,session=self.session),deadline)
        try:
            receipt = validate_issued(self,statement,operation,body)
            self._issued_receipts[key] = receipt
            self._issuance_sequence += 1
            self._evidence_m3 = receipt.m3_sequence
            self._evidence_ordinal = body["event"]["ingestionOrdinal"]
            return receipt
        except Exception:
            self._fail()
            raise

    def publish_broker_artifact(self, broker, deadline):
        from .run_broker import RunBroker
        from .public_blobs import sealed_public_blob,validate_broker_receipt
        self._holder()
        until=self._until(deadline)
        if type(broker) is not RunBroker or broker.storage is not self or self._broker_artifact is None:
            raise PersistenceError('ML-EVIDENCE-BLOB-ORIGINAL')
        broker._holder()
        if not self._publication_lock.acquire(False):raise PersistenceError('ML-EVIDENCE-BLOB-CONFLICT')
        try:
            if self._broker_publication is not None:
                if self._broker_publication[0] is not broker:raise PersistenceError('ML-EVIDENCE-BLOB-ORIGINAL')
                return self._broker_publication[1]
            data=broker.public_projection(deadline).public_bytes
            if len(data)>self._broker_artifact.maximum_bytes:raise PersistenceError('ML-EVIDENCE-BLOB-SIZE')
            def check():
                self._live(allow_cancel=True)
                if time.monotonic_ns()>=until:raise PersistenceError('ML-EVIDENCE-BLOB-DEADLINE')
            fd=sealed_public_blob(data,check)
            try:
                _,_,body=self._rpc('public-blob',dict(purpose='broker-projection',bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest()),deadline,public_blob_fd=fd)
                receipt=validate_broker_receipt(self,data,body)
                self._broker_publication=self._broker_publication_pin=(broker,receipt,receipt.public_bytes)
                return receipt
            except Exception:
                self._fail();raise
            finally:os.close(fd)
        finally:self._publication_lock.release()

    def collect_outputs(self, broker, deadline):
        """Original bounded collection after factual teardown; no new start authority."""
        from .collection_runtime import collect_outputs
        return collect_outputs(self, broker, deadline)

    def finish_run(self, broker, deadline):
        """Original report/ACK-bound writer closure; full helper closure is separate."""
        from .terminal_runtime import finish_run
        return finish_run(self, broker, deadline)

    def export_public_inputs(self, declaration, deadline):
        from .evidence import validate_export

        self._holder()
        self._until(deadline)
        if not any(declaration is e for e in self._public_exports):
            raise PersistenceError("ML-EVIDENCE-EXPORT-ORIGINAL")
        path = declaration.relative_path
        if path in self._export_receipts:
            return self._export_receipts[path]
        _, _, body = self._rpc("public-export", {"relative_path": path}, deadline)
        try:
            receipt = validate_export(self, declaration, body)
            self._export_receipts[path] = receipt
            return receipt
        except Exception:
            self._fail()
            raise

    def probe_receipt(self, unit_id):
        self._holder()
        return self._probe_receipts.get(unit_id)

    def record_probe(self, facade, observed, deadline):
        from .providers import ProcessReadiness, ReadinessObservation
        from .lifecycle_evidence import LifecycleReceipt, validate_receipt
        from .owner import _hash

        self._available()
        if (
            type(facade) is not ProcessReadiness
            or type(observed) is not ReadinessObservation
        ):
            raise PersistenceError("ML-EVIDENCE-ORIGINAL")
        facade._holder()
        binding = facade._bound(observed.unit_id)
        key = observed.unit_id, observed.sequence
        if (
            facade._owner.persistence is not self
            or facade._observations.get(observed.unit_id) is not observed
            or observed.unit_id not in facade._released
            or observed.host_session != self.session
            or observed.generation != binding.launcher.recipe.descriptor.generation
            or observed.handle_digest != _hash(asdict(binding.handle)).hex()
            or key in self._probe_attempted
        ):
            raise PersistenceError("ML-EVIDENCE-ORIGINAL")
        claim = facade._owner._claims[observed.unit_id].receipt
        if self._claims.get(id(claim)) is not claim:
            raise PersistenceError("ML-EVIDENCE-CLAIM")
        self._probe_attempted.add(key)
        operation, _, body = self._rpc(
            "probe",
            {
                "unit": observed.unit_id,
                "claim": claim.operation,
                "generation": observed.generation,
                "handle": asdict(binding.handle),
                "sample_sequence": observed.sequence,
                "session": observed.host_session,
                "observed_at": observed.observed_at,
                "ready": observed.ready,
                "freshness": facade._policies[observed.unit_id].freshness_seconds,
            },
            deadline,
        )
        try:
            validate_receipt(
                body,
                facade,
                observed,
                claim,
                operation,
                self._probe_receipts.get(observed.unit_id),
            )
            receipt = LifecycleReceipt(
                observed.unit_id,
                observed.sequence,
                tuple(e["eventId"] for e in body["events"]),
                tuple(body["m3_sequences"]),
                canonical_bytes(body["events"]),
            )
            self._probe_receipts[observed.unit_id] = receipt
            self._evidence_sequence = body["events"][-1]["producerSequence"]
            self._evidence_ordinal = body["events"][-1]["ingestionOrdinal"]
            self._evidence_m3 = body["m3_sequences"][-1]
            return receipt
        except Exception:
            self._fail()
            raise

    def schedule_call(self, dispatcher, statement, deadline):
        from .dispatcher import FiniteDispatcher, _Statement, validate_schedule_reply

        self._holder()
        if (
            type(dispatcher) is not FiniteDispatcher
            or type(statement) is not _Statement
        ):
            raise PersistenceError("ML-SCHEDULE-ORIGINAL")
        dispatcher._holder()
        if (
            dispatcher.client is not self
            or dispatcher._active is not statement
            or id(statement) in self._schedule_used
            or self._aborted
            or not self._ready
        ):
            raise PersistenceError("ML-SCHEDULE-ORIGINAL")
        self._schedule_used[id(statement)] = statement
        request = _strict_json(statement.request_bytes)
        operation, _, reply = self._rpc(statement.channel_kind, request, deadline)
        try:
            validate_schedule_reply(
                reply, request, dispatcher, operation, statement.channel_kind
            )
            return reply
        except Exception:
            self._fail()
            raise

    def record_teardown(self, controller, step, deadline):
        from .teardown import ReverseTeardown, _Step
        from .teardown_evidence import TeardownReceipt, validate_teardown_reply
        from .owner import _hash

        if type(controller) is not ReverseTeardown or type(step) is not _Step:
            raise PersistenceError("ML-TEARDOWN-RECORD-ORIGINAL")
        controller._holder()
        if (
            controller.owner.persistence is not self
            or controller._active is not step
            or step.step_id in self._teardown_attempted
            or controller._registry.get(step.unit_id)
            is not controller.owner._launchers.get(step.unit_id)
        ):
            raise PersistenceError("ML-TEARDOWN-RECORD-ORIGINAL")
        launcher = controller._registry[step.unit_id]
        launcher.revalidate_issued(step.handle)
        if step.descriptor != launcher.recipe.descriptor:
            raise PersistenceError("ML-TEARDOWN-RECORD-ORIGINAL")
        claim = controller.owner._claims[step.unit_id].receipt
        if self._claims.get(id(claim)) is not claim:
            raise PersistenceError("ML-TEARDOWN-RECORD-CLAIM")
        prior = controller._intents.get((step.unit_id, step.phase))
        request = {
            "unit": step.unit_id,
            "claim": claim.operation,
            "generation": step.descriptor.generation,
            "phase": step.phase,
            "stage": step.stage,
            "handle": asdict(step.handle),
            "step": step.step_id,
            "intent": prior.operation if prior is not None else None,
            "session": self.session,
            "observed_at": step.observed_at,
            "boundary_digest": "sha256:" + _hash(list(step.descriptor.key)).hex(),
            "leader_reaped": step.leader_reaped,
            "empty": step.empty,
            "released": step.released,
            "force_observed": step.force_observed,
        }
        if self.latch.cancelled:
            if not controller._terminal_scope():
                raise PersistenceError('ML-TEARDOWN-TERMINAL-SCOPE')
            broker = controller.owner._run_broker_pin
            # ReverseTeardown holds the original broker mutation lock. Root
            # service has its own original channel/lock and native fence proof.
            broker.session._service_terminal(HostDeadline(self.session, min(
                deadline.monotonic_seconds, time.monotonic() + .5, broker.session._lease / 1e9)),
                authority=broker.connection)
            self._live(allow_cancel=True)
        else:
            self._available()
        self._teardown_attempted.add(step.step_id)
        operation, _, body = self._rpc("teardown", request, deadline)
        try:
            validate_teardown_reply(body, request, self, controller, operation)
            event = body["event"]
            receipt = TeardownReceipt(
                step.unit_id,
                step.phase,
                step.stage,
                operation,
                event["eventId"],
                body["m3_sequence"],
                canonical_bytes(event),
            )
            self._teardown_receipts[step.unit_id] = receipt
            self._teardown_sequence = event["producerSequence"]
            self._evidence_ordinal = event["ingestionOrdinal"]
            self._evidence_m3 = body["m3_sequence"]
            return receipt
        except Exception:
            self._fail()
            raise

    def reconcile_snapshot(self, controller, statement, deadline):
        from .recovery import IssuerRecovery, _RecoveryStatement, validate_snapshot

        self._holder()
        if (
            type(controller) is not IssuerRecovery
            or type(statement) is not _RecoveryStatement
        ):
            raise PersistenceError("ML-RECOVERY-STATEMENT")
        controller._holder()
        if (
            controller.client is not self
            or controller._active is not statement
            or id(statement) in self._recovery_used
        ):
            raise PersistenceError("ML-RECOVERY-STATEMENT")
        self._recovery_used[id(statement)] = statement
        try:
            body = _strict_json(statement.body)
            _, _, reply = self._rpc("recovery", body, deadline)
            validate_snapshot(controller, body, reply)
            return reply
        except PersistenceCancelled:
            raise  # refused before send because the run was cancelled: storage stays healthy (review 1 R1-2)
        except Exception:
            self._fail()
            raise

    def close_incomplete(self, deadline):
        """One original-worker public-state/flush/abort/reader attempt; never finalize."""
        from .writer_closure import decode_closure, unresolved

        self._holder()
        if self._closure_attempted:
            return self._closure_result
        self._closure_attempted = True
        prior = self.last_writer_state
        self._closure_result = unresolved(prior)
        try:
            _, _, body = self._rpc("closure", {}, deadline)
            facts = decode_closure(body, prior)
        except Exception:
            self._fail()
            return self._closure_result
        self._closure_result = facts
        self.last_writer_state = facts.after_state
        if facts.abort_completed:
            self._aborted = True
        else:
            self._fail()
        self.latch.cancel("persistence-closure")
        return facts

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
                result = wait_child(self._pins[0], self._pidfd, consume=True)
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
                    signal_child(self._pins[0], self._pidfd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                self._kill_sent = True
            select.select(
                [self._pidfd], [], [], min(0.01, (self._drain_deadline - now) / 1e9)
            )

    def dispose(self):
        self._holder()
        if not self._lock.acquire(False):
            raise PersistenceError("ML-PERSIST-CONFLICT")
        try:
            if self._dispose_error is not None:
                raise PersistenceError("ML-PERSIST-DISPOSE-UNRESOLVED") from self._dispose_error
            if self._disposed:
                return
            if not self._drained or not self._drained.worker_reaped:
                from .bootstrap import BootstrapChild

                # The root can have consumed the original wait after the local
                # drain expired. This observation never rewrites that old receipt.
                if type(self._pins[0]) is not BootstrapChild:
                    raise PersistenceError("ML-PERSIST-RETAINED")
                try:
                    observed = wait_child(self._pins[0], self._pidfd, consume=True)
                except (ValueError, OSError):
                    raise PersistenceError("ML-PERSIST-RETAINED") from None
                if observed is None:
                    raise PersistenceError("ML-PERSIST-RETAINED")
            try:
                if self._pidfd >= 0:
                    descriptor, self._pidfd = self._pidfd, -1
                    os.close(descriptor)
                self._pins[1].close()
            except OSError as error:
                self._dispose_error = error
                raise PersistenceError("ML-PERSIST-DISPOSE-UNRESOLVED") from error
            self._disposed = True
        finally:
            self._lock.release()

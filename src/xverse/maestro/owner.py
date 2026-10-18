"""Original-owner M3/Argus/frozen-Stage to RG06 composition, not complete lifecycle.

Storage/kernel calls still need disposable-worker supervision for whole caller
bounds. Bootstrap supplies actual original objects; this module authenticates
neither operator approval nor helper creation. Component observations are not ready.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import array
import hashlib
import os
import select
import socket
import stat
import struct
import threading
import time
import uuid

from xverse.argus.schema import canonical_bytes
from xverse.argus.writer import EvidenceRun
from xverse.argus.planbinding import plan_identity
from .child import check_child, open_child_pidfd, wait_child
from .admission import PermitSession
from .fence import GatePacket
from .prbc import BoundaryDescriptor, ProcessBoundaryOps
from .supervisor import CancellationLatch
from .time import HostDeadline


class OwnerError(ValueError):
    pass


def _hash(value):
    return hashlib.sha256(canonical_bytes(value)).digest()


def _pin(value):
    if type(value) is not str or not value.startswith("sha256:") or len(value) != 71:
        raise OwnerError("ML-OWNER-ARTIFACT")
    try:
        decoded = bytes.fromhex(value[7:])
        if len(decoded) != 32 or decoded.hex() != value[7:]:
            raise ValueError("noncanonical digest")
        return decoded
    except ValueError as error:
        raise OwnerError("ML-OWNER-ARTIFACT") from error


def _deadline(value, session):
    if type(value) is not HostDeadline or value.session != session:
        raise OwnerError("ML-OWNER-HOST-SESSION")
    value.__post_init__()
    remaining = value.monotonic_seconds - time.monotonic()
    if not 0 < remaining <= 5:
        raise OwnerError("ML-OWNER-DEADLINE")
    return int(value.monotonic_seconds * 1e9)


class _Original:
    def _retain(self):
        self._original, self._pid = self, os.getpid()

    def _holder(self):
        if self._original is not self or self._pid != os.getpid():
            raise OwnerError("ML-OWNER-HOLDER")

    def __reduce_ex__(self, protocol):
        raise TypeError("original owner authority cannot be copied or serialized")


class GateConnection(_Original):
    """Original actual child/channel, supplied before dispatch by trusted bootstrap.

    The bootstrap must set SO_PASSCRED before READY, pass only admitted FDs,
    pin the executable, and prevent other waiters. No child creation is done here.
    """

    def __init__(
        self,
        process,
        channel,
        *,
        scope,
        epoch,
        lease_ns,
        artifact_digest,
        latch,
        deadline,
        boundaries=None,
        descriptor=None,
    ):
        check_child(process, live=True)
        if type(channel) is not socket.socket or type(latch) is not CancellationLatch:
            raise OwnerError("ML-OWNER-GATE-INPUT")
        if (
            channel.family != socket.AF_UNIX
            or channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
            != socket.SOCK_SEQPACKET
            or not channel.getsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED)
        ):
            raise OwnerError("ML-OWNER-GATE-SOCKET")
        GatePacket(16, 0, lease_ns, scope, epoch)
        _pin(artifact_digest)
        self._expect_boundary = None
        self._boundary_proven = None
        if boundaries is not None or descriptor is not None:
            if (
                type(boundaries) is not ProcessBoundaryOps
                or type(descriptor) is not BoundaryDescriptor
            ):
                raise OwnerError("ML-OWNER-GATE-BOUNDARY")
            boundaries._holder()
            boundaries.residual_membership(descriptor)
            entry = boundaries._entry(descriptor)
            info = os.fstat(entry.fd)
            self._expect_boundary = (info.st_dev, info.st_ino)
        self._retain()
        self.process, self.channel = process, channel
        self.scope, self.epoch, self.lease_ns = scope, epoch, lease_ns
        self.artifact_digest, self.latch = artifact_digest, latch
        self._channel_pin, self._process_pin, self._latch_pin = channel, process, latch
        self.host_session = deadline.session
        self._config_pin = (scope, epoch, lease_ns, artifact_digest, self.host_session)
        self._identity = os.fstat(channel.fileno())
        self._process_pid = process.pid
        self._pidfd = -1
        self._sequence = 0
        self._lock = threading.Lock()
        channel.setblocking(False)
        try:
            self._pidfd = open_child_pidfd(process)
            self._live()
            response = self._receive(_deadline(deadline, self.host_session))
            if response != GatePacket(16, 0, lease_ns, scope, epoch):
                raise OwnerError("ML-OWNER-GATE-READY")
        except Exception:
            self.cancel("gate-ready-failed")
            if self._pidfd >= 0:
                os.close(self._pidfd)
            self._pidfd = -1
            raise

    def _live(self):
        self._holder()
        check_child(self._process_pin, live=True)
        if (
            self.channel is not self._channel_pin
            or self.process is not self._process_pin
            or self.latch is not self._latch_pin
            or (
                self.scope,
                self.epoch,
                self.lease_ns,
                self.artifact_digest,
                self.host_session,
            )
            != self._config_pin
        ):
            raise OwnerError("ML-OWNER-GATE-REPLACED")
        self.latch._check()
        current = os.fstat(self.channel.fileno())
        if (
            self.process.pid != self._process_pid
            or (current.st_dev, current.st_ino)
            != (self._identity.st_dev, self._identity.st_ino)
            or self._pidfd < 0
        ):
            raise OwnerError("ML-OWNER-GATE-IDENTITY")
        if self.latch.cancelled or select.select([self._pidfd], [], [], 0)[0]:
            raise OwnerError("ML-OWNER-GATE-CLOSED")
        if wait_child(self._process_pin, self._pidfd) is not None:
            raise OwnerError("ML-OWNER-GATE-PARENT")

    def _receive(self, until):
        while True:
            remaining = (until - time.monotonic_ns()) / 1e9
            if (
                remaining <= 0
                or not select.select([self.channel], [], [], remaining)[0]
            ):
                raise OwnerError("ML-OWNER-GATE-TIMEOUT")
            try:
                data, anc, flags, _ = self.channel.recvmsg(
                    257,
                    socket.CMSG_SPACE(12) + socket.CMSG_SPACE(32),
                    socket.MSG_CMSG_CLOEXEC,
                )
            except BlockingIOError:
                continue
            credentials = []
            received = []
            valid = not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
            for level, kind, payload in anc:
                if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                    values = array.array("i")
                    values.frombytes(
                        payload[: len(payload) - len(payload) % values.itemsize]
                    )
                    received.extend(values)
                elif (
                    level == socket.SOL_SOCKET
                    and kind == socket.SCM_CREDENTIALS
                    and len(payload) == 12
                ):
                    credentials.append(struct.unpack("3i", payload))
                else:
                    valid = False
            try:
                if (
                    not valid
                    or credentials != [(self._process_pid, os.getuid(), os.getgid())]
                    or time.monotonic_ns() >= until
                ):
                    raise OwnerError("ML-OWNER-GATE-SENDER")
                packet = GatePacket.decode(data)
                if self._expect_boundary is not None:
                    if len(received) != 1 or packet.kind != 16:
                        raise OwnerError("ML-OWNER-GATE-BOUNDARY")
                    info = os.fstat(received[0])
                    if (
                        not stat.S_ISDIR(info.st_mode)
                        or (info.st_dev, info.st_ino) != self._expect_boundary
                    ):
                        raise OwnerError("ML-OWNER-GATE-BOUNDARY")
                    self._boundary_proven = self._expect_boundary
                    self._expect_boundary = None
                elif received:
                    raise OwnerError("ML-OWNER-GATE-SENDER")
                return packet
            finally:
                for fd in received:
                    os.close(fd)

    def exchange(self, packet, expected, deadline):
        self._live()
        until = min(_deadline(deadline, self.host_session), self.lease_ns)
        if (
            packet.scope != self.scope
            or packet.epoch != self.epoch
            or packet.sequence != self._sequence + 1
        ):
            raise OwnerError("ML-OWNER-GATE-SCOPE")
        if not self._lock.acquire(blocking=False):
            raise OwnerError("ML-OWNER-CONFLICT")
        try:
            self._live()
            if time.monotonic_ns() >= until:
                raise OwnerError("ML-OWNER-GATE-TIMEOUT")
            if self.channel.send(packet.encode()) != 256:
                raise OwnerError("ML-OWNER-GATE-SEND")
            response = self._receive(until)
            self._sequence = packet.sequence
            self._live()
            if (
                response.kind != expected
                or response.scope != self.scope
                or response.epoch != self.epoch
                or response.sequence != packet.sequence
            ):
                raise OwnerError("ML-OWNER-GATE-ACK")
            return response
        except Exception:
            self.cancel("gate-uncertain")
            raise
        finally:
            self._lock.release()

    def cancel(self, reason="owner-cancel"):
        self._holder()
        self._latch_pin.cancel(reason)
        try:
            self._channel_pin.shutdown(socket.SHUT_WR)
        except OSError:
            pass

    def dispose(self):
        self._holder()
        if self._pidfd >= 0:
            if not select.select([self._pidfd], [], [], 0)[0]:
                raise OwnerError("ML-OWNER-GATE-LIVE")
            os.close(self._pidfd)
            self._pidfd = -1


@dataclass(frozen=True)
class _StageAck:
    digest: bytes
    descriptor: BoundaryDescriptor
    membership: tuple = field(repr=False)
    gate: GateConnection = field(repr=False)
    expires_ns: int


class StageSupervisor(_Original):
    def __init__(self, boundaries, latch):
        if (
            type(boundaries) is not ProcessBoundaryOps
            or type(latch) is not CancellationLatch
            or boundaries._latch is not latch
        ):
            raise OwnerError("ML-OWNER-SUPERVISOR")
        boundaries._holder()
        self._retain()
        self.boundaries, self.latch = boundaries, latch
        self._pins = (boundaries, latch)
        self._acks = {}

    def _holder(self):
        super()._holder()
        if self.boundaries is not self._pins[0] or self.latch is not self._pins[1]:
            raise OwnerError("ML-OWNER-SUPERVISOR-REPLACED")

    def acknowledge(self, descriptor, gate, deadline):
        self._holder()
        gate._live()
        until = _deadline(deadline, gate.host_session)
        if (
            self.latch.cancelled
            or gate.latch is not self.latch
            or descriptor.creation_epoch != gate.epoch
        ):
            raise OwnerError("ML-OWNER-STAGE-EPOCH")
        members = self.boundaries.residual_membership(descriptor)
        record = self.boundaries.record(descriptor)
        if not members or record.state != "frozen" or not record.membership_complete:
            raise OwnerError("ML-OWNER-STAGE")
        gate._live()
        if time.monotonic_ns() >= until:
            raise OwnerError("ML-OWNER-STAGE-LATE")
        digest = _hash(
            [
                list(descriptor.key),
                list(members),
                until,
                self.boundaries._admission.supervisor_session,
            ]
        )
        ack = _StageAck(digest, descriptor, members, gate, until)
        self._acks[id(ack)] = ack
        return ack

    def revalidate(self, ack):
        self._holder()
        if (
            self._acks.get(id(ack)) is not ack
            or time.monotonic_ns() >= ack.expires_ns
            or self.latch.cancelled
        ):
            raise OwnerError("ML-OWNER-STAGE-ACK")
        ack.gate._live()
        if self.boundaries.residual_membership(ack.descriptor) != ack.membership:
            raise OwnerError("ML-OWNER-STAGE-CHANGED")


@dataclass(frozen=True)
class ReleaseObservation:
    unit_id: str
    generation: int
    native_unfreeze_observed: bool
    intent_event_id: str
    ready_for_execution: bool = field(default=False, init=False)


@dataclass
class _Claim:
    receipt: object
    operation: str
    intent_digest: bytes
    flush_digest: bytes
    event_id: str
    deadline_ns: int
    attempted: bool = False


def _persist_intent(permits, writer, session, unit_id, deadline, check, operation=None):
    """Actual original-owner storage sequence, shared by local and isolated paths."""
    until = check(deadline)
    domains = ("host:" + session, "utc:" + session)
    receipt = permits.claim_start_intent(unit_id, now=datetime.now(timezone.utc))
    check(deadline)
    operation = operation or "ml-" + uuid.uuid4().hex
    public = permits.public_start_intent(receipt, now=datetime.now(timezone.utc))
    check(deadline)
    intent = _hash(public)
    payload = {
        "schemaVersion": "2.0",
        "lifecycleDigest": "sha256:" + permits._prepared.lifecycle_digest,
        "runId": permits._run_id,
        "sessionId": session,
        "scope": "unit",
        "unitId": unit_id,
        "generation": 1,
        "operationId": operation,
        "action": "intent",
        "outcome": "pending",
        "sourceRefs": [
            {
                "kind": "m3-record",
                "id": "m3-intent-" + str(receipt.m3_sequence),
                "sha256": "sha256:" + intent.hex(),
                "sequence": receipt.m3_sequence,
            }
        ],
        "dependencies": [],
    }
    event_id = operation + "-intent"
    ordinal = writer.append_event(
        event_id=event_id,
        producer_id="maestro.owner7",
        event_kind="annotation",
        producer_sequence=receipt.m3_sequence,
        correlation_id=permits._run_id,
        clocks={
            "host": {
                "domain": domains[0],
                "unit": "s",
                "value": time.monotonic(),
            },
            "utc": {
                "domain": domains[1],
                "unit": "s",
                "value": datetime.now(timezone.utc).timestamp(),
            },
        },
        annotation={"text": "Maestro durable start intent"},
        extensions={"xverse.maestro": payload},
    )
    check(deadline)
    writer.flush_buffer()
    check(deadline)
    permits.revalidate_start_intent(receipt, now=datetime.now(timezone.utc))
    check(deadline)
    return _Claim(
        receipt,
        operation,
        intent,
        _hash([event_id, ordinal, payload]),
        event_id,
        until,
    )


class ReleaseOwner(_Original):
    def __init__(self, permits, writer, supervisor, latch):
        if (
            type(permits) is not PermitSession
            or type(writer) is not EvidenceRun
            or type(supervisor) is not StageSupervisor
            or type(latch) is not CancellationLatch
        ):
            raise OwnerError("ML-OWNER-INPUT")
        permits._holder()
        supervisor._holder()
        latch._check()
        facts = supervisor.boundaries._admission
        if (
            permits._initial_generation != 1
            or writer.run_id != permits._run_id
            or facts.run_id != permits._run_id
            or supervisor.latch is not latch
            or writer.writer_state != "open"
        ):
            raise OwnerError("ML-OWNER-SCOPE")
        self._retain()
        self.permits, self.writer, self.supervisor, self.latch = (
            permits,
            writer,
            supervisor,
            latch,
        )
        self._pins = (permits, writer, supervisor, latch)
        self.session = facts.teardown_deadline.session
        self._domains = ("host:" + self.session, "utc:" + self.session)
        if not set(self._domains) <= writer.declared_domains:
            raise OwnerError("ML-OWNER-CLOCKS")
        expected_plan, diagnostics = plan_identity(permits._result.plan)
        if diagnostics or writer._plan_block != expected_plan:
            raise OwnerError("ML-OWNER-WRITER-PLAN")
        self._writer_pin = (
            _hash(expected_plan),
            writer.run_id,
            writer.declared_domains,
        )
        self.persistence = self._persistence_pin = None
        self._prepared, self._run_id = permits._prepared, permits._run_id
        self._context_pin = (self._prepared, self._run_id)
        self._claims, self._attempted, self._gates = {}, set(), []
        self._launchers = {}
        self._lock = threading.Lock()
        self._closed = False

    @classmethod
    def from_persistence(cls, client, supervisor, latch):
        from .persistence import PersistenceClient

        if (
            cls is not ReleaseOwner
            or type(client) is not PersistenceClient
            or type(supervisor) is not StageSupervisor
            or type(latch) is not CancellationLatch
        ):
            raise OwnerError("ML-OWNER-INPUT")
        client._available()
        supervisor._holder()
        facts = supervisor.boundaries._admission
        if (
            client.latch is not latch
            or supervisor.latch is not latch
            or client.run_id != facts.run_id
            or client.session != facts.teardown_deadline.session
            or client.generation_ns
            > int(facts.teardown_deadline.monotonic_seconds * 1e9)
        ):
            raise OwnerError("ML-OWNER-SCOPE")
        owner = cls.__new__(cls)
        owner._retain()
        owner.permits = owner.writer = None
        owner.supervisor, owner.latch = supervisor, latch
        owner.persistence = owner._persistence_pin = client
        owner._pins = (None, None, supervisor, latch)
        owner._prepared, owner._run_id = client.prepared, client.run_id
        owner._context_pin = (owner._prepared, owner._run_id)
        owner.session = client.session
        owner._claims, owner._attempted, owner._gates = {}, set(), []
        owner._launchers = {}
        owner._lock, owner._closed = threading.Lock(), False
        return owner

    def _stage_claim(self, unit_id, deadline):
        self._check(deadline)
        claim = self._claims.get(unit_id)
        if (
            claim is None
            or claim.attempted
            or self._check(deadline) > claim.deadline_ns
        ):
            raise OwnerError("ML-OWNER-CLAIM")
        self._revalidate(claim, deadline)
        self._check(deadline)
        return claim

    def _register_launcher(self, launcher):
        from .launcher import CatalogLauncher

        if (
            type(launcher) is not CatalogLauncher
            or launcher.owner is not self
            or launcher.unit_id in self._launchers
        ):
            raise OwnerError("ML-OWNER-LAUNCHER")
        self._holder()
        self._launchers[launcher.unit_id] = launcher

    def _check_launcher(self, unit_id, descriptor, gate):
        if (
            self._unit(unit_id).provider.kind == "process"
            and unit_id not in self._launchers
        ):
            raise OwnerError("ML-OWNER-LAUNCHER-MISSING")
        if unit_id in self._launchers:
            self._launchers[unit_id]._validate_release(descriptor, gate)

    def _revalidate(self, claim, deadline):
        if self.persistence is None:
            self.permits.revalidate_start_intent(
                claim.receipt, now=datetime.now(timezone.utc)
            )
        else:
            self.persistence.revalidate_intent(claim.receipt, deadline)

    def _check(self, deadline):
        self._holder()
        if any(
            a is not b
            for a, b in zip(
                (self.permits, self.writer, self.supervisor, self.latch), self._pins
            )
        ):
            raise OwnerError("ML-OWNER-REPLACED")
        if (
            self.persistence is not self._persistence_pin
            or (self._prepared, self._run_id) != self._context_pin
        ):
            raise OwnerError("ML-OWNER-REPLACED")
        self.supervisor._holder()
        if self.persistence is not None:
            self.persistence._available()
            if (
                self._prepared is not self.persistence.prepared
                or self._run_id != self.persistence.run_id
            ):
                raise OwnerError("ML-OWNER-REPLACED")
        else:
            self.permits._holder()
            if (
                self._prepared is not self.permits._prepared
                or self._run_id != self.permits._run_id
            ):
                raise OwnerError("ML-OWNER-REPLACED")
        if (
            self.persistence is None
            and (
                _hash(self.writer._plan_block),
                self.writer.run_id,
                self.writer.declared_domains,
            )
            != self._writer_pin
        ):
            raise OwnerError("ML-OWNER-WRITER-REPLACED")
        if (
            self._closed
            or self.latch.cancelled
            or (self.writer is not None and self.writer.writer_state != "open")
        ):
            raise OwnerError("ML-OWNER-CLOSED")
        until = _deadline(deadline, self.session)
        if until > int(
            self.supervisor.boundaries._admission.teardown_deadline.monotonic_seconds
            * 1e9
        ):
            raise OwnerError("ML-OWNER-DEADLINE")
        return until

    def _unit(self, unit_id):
        unit = next((u for u in self._prepared.units if u.unit_id == unit_id), None)
        if unit is None:
            raise OwnerError("ML-OWNER-UNIT")
        return unit

    def scope(self, unit_id, descriptor, artifact_digest):
        self._holder()
        self._unit(unit_id)
        _pin(artifact_digest)
        facts = self.supervisor.boundaries._admission
        if (
            type(descriptor) is not BoundaryDescriptor
            or descriptor.run_id != self._run_id
            or descriptor.unit_id != unit_id
            or descriptor.generation != 1
            or descriptor.creation_epoch != facts.initial_epoch
        ):
            raise OwnerError("ML-OWNER-DESCRIPTOR")
        return _hash(
            [
                "xverse.maestro.owner7",
                self._prepared.lifecycle_digest,
                list(descriptor.key),
                self.session,
                facts.supervisor_session,
                facts.affa_session,
                artifact_digest,
            ]
        )

    def cancel(self, reason="owner-cancel"):
        self._holder()
        self._pins[3].cancel(reason)
        for gate in tuple(self._gates):
            gate.cancel(reason)
        for launcher in tuple(self._launchers.values()):
            launcher.cancel(reason)

    def commit_intent(self, unit_id, deadline):
        until = self._check(deadline)
        self._unit(unit_id)
        if not self._lock.acquire(blocking=False):
            raise OwnerError("ML-OWNER-CONFLICT")
        try:
            if unit_id in self._attempted:
                raise OwnerError("ML-OWNER-REPLAY")
            self._attempted.add(unit_id)
            if self.persistence is None:
                claim = _persist_intent(
                    self.permits,
                    self.writer,
                    self.session,
                    unit_id,
                    deadline,
                    self._check,
                )
            else:
                receipt = self.persistence.commit_intent(unit_id, deadline)
                self._check(deadline)
                claim = _Claim(
                    receipt,
                    receipt.operation,
                    receipt.intent_digest,
                    receipt.flush_digest,
                    receipt.event_id,
                    until,
                )
            self._claims[unit_id] = claim
            return claim.event_id
        except Exception:
            self._closed = True
            self.cancel("intent-uncertain")
            raise
        finally:
            self._lock.release()

    def release(self, unit_id, descriptor, gate, deadline):
        self._check(deadline)
        if (
            type(gate) is not GateConnection
            or gate.latch is not self.latch
            or gate.scope != self.scope(unit_id, descriptor, gate.artifact_digest)
        ):
            raise OwnerError("ML-OWNER-GATE-SCOPE")
        if not self._lock.acquire(blocking=False):
            raise OwnerError("ML-OWNER-CONFLICT")
        try:
            claim = self._claims.get(unit_id)
            if claim is None or claim.attempted:
                raise OwnerError("ML-OWNER-CLAIM")
            self._gates.append(gate)
            if self._check(deadline) > claim.deadline_ns:
                raise OwnerError("ML-OWNER-ORIGINAL-DEADLINE")
            claim.attempted = True
            self._check_launcher(unit_id, descriptor, gate)
            self._revalidate(claim, deadline)
            self._check_launcher(unit_id, descriptor, gate)
            ack = self.supervisor.acknowledge(descriptor, gate, deadline)
            self._check(deadline)
            until = min(_deadline(deadline, self.session), gate.lease_ns)
            arm = GatePacket(
                3,
                gate._sequence + 1,
                until,
                gate.scope,
                gate.epoch,
                operation=_hash(claim.operation),
                intent=claim.intent_digest,
                flush=claim.flush_digest,
                stage=ack.digest,
            )
            ticket = gate.exchange(arm, 20, deadline)
            if replace(ticket, kind=3, nonce=bytes(32)) != arm:
                raise OwnerError("ML-OWNER-TICKET")
            self._check(deadline)
            self._revalidate(claim, deadline)
            self.supervisor.revalidate(ack)
            self._check_launcher(unit_id, descriptor, gate)
            response = gate.exchange(
                replace(ticket, kind=4, sequence=gate._sequence + 1), 21, deadline
            )
            if response != replace(
                ticket, kind=21, sequence=gate._sequence, nonce=bytes(32)
            ):
                raise OwnerError("ML-OWNER-RELEASE-ACK")
            self._check(deadline)
            return ReleaseObservation(unit_id, 1, True, claim.event_id)
        except Exception:
            self._closed = True
            self.cancel("release-uncertain")
            raise
        finally:
            self._lock.release()

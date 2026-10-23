"""Private original-supervisor AF17 transport; hashes are never M3 approval."""

from dataclasses import dataclass, replace, field
import array
import os
import select
import signal
import socket
import struct
import threading
import time

from .affa_protocol import AuthorityConfig, AuthorityFrame, AuthorityKind as K, STATE_MASK
from .bootstrap import BootstrapChild, BootstrapError, _CREATE
from .child import _PidfdCapability
from .owner import _Original, _deadline
from .time import HostDeadline

ZERO = bytes(32)
_REPLIES = {
    K.REGISTER: K.REGISTERED,
    K.INTENT: K.INTENT_RECORDED,
    K.STAGE: K.STAGED,
    K.ARM: K.ARMED,
    K.RELEASE: K.RELEASED,
    K.QUERY: K.OBSERVED,
    K.STOP: K.STOPPED,
    K.RETIRE: K.RETIRED,
    K.RENEW: K.RENEWED,
    K.CANCEL: K.CANCELLED,
    K.QUERY_ISSUED: K.STAGED,
    K.ADVANCE: K.ADVANCED,
    K.FAULT_KILL: K.FAULTED,
    K.FAULT_FREEZE: K.FAULTED,
    K.FAULT_THAW: K.FAULTED,
    K.TERM: K.TERM_SENT,  # S1b: not in _CLEANUP, so refused after a cancel before it is sent
}
_FAULTS = (K.FAULT_KILL, K.FAULT_FREEZE, K.FAULT_THAW)  # Phase 5: FAULT_REFUSED is their other valid answer
_CLEANUP = (K.QUERY, K.QUERY_ISSUED, K.STOP, K.RETIRE, K.CANCEL)


@dataclass(frozen=True, slots=True)
class AuthorityRevocation:
    issuer_dead: bool
    issuer_reaped: bool
    diagnostic: str | None
    workload_waits_known: bool = field(default=False, init=False)
    boundaries_released: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class AuthorityEpochAdvance(_Original):
    """Original retained native ACK; public/frame values cannot construct authority."""

    _pins: tuple = field(repr=False)

    def __init__(self, key, connection, request, reply, descriptor):
        if key is not _CREATE:
            raise BootstrapError("ML-AFFA-EPOCH-ISSUER")
        object.__setattr__(self, "_original", self)
        object.__setattr__(self, "_pid", os.getpid())
        object.__setattr__(self, "_pins", (connection, request, reply, descriptor))

    def _holder(self):
        _Original._holder(self)
        connection, request, reply, descriptor = self._pins
        connection._holder()
        if not any(self is r for r in connection._advance_receipts):
            raise BootstrapError("ML-AFFA-EPOCH-RECEIPT")
        return connection, request, reply, descriptor


class AuthorityConnection(_Original):
    def __init__(self, key, child, channel, config):
        if (
            key is not _CREATE
            or type(child) is not BootstrapChild
            or type(config) is not AuthorityConfig
        ):
            raise BootstrapError("ML-AFFA-ORIGINAL-CHILD")
        child._ordinary()
        root = child._root
        if (
            root.config.version != 2
            or root._issued[child._slot][0] != 4
            or root._authority_input != config
        ):
            raise BootstrapError("ML-AFFA-BOOTSTRAP-BINDING")
        if (
            type(channel) is not socket.socket
            or channel.family != socket.AF_UNIX
            or channel.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE)
            != socket.SOCK_SEQPACKET
            or not channel.getsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED)
        ):
            raise BootstrapError("ML-AFFA-CHANNEL")
        self._retain()
        self.child, self.channel, self.config = child, channel, config
        self._pins = (
            child,
            channel,
            config,
            config.encode(),
            os.fstat(channel.fileno()),
        )
        self.sequence, self._lease = 0, config.lease_ns
        self._epoch_history = self._epoch_history_pin = ()
        self._advance_receipts = self._advance_receipts_pin = ()
        self._starts_closed, self._revoked = False, False
        self._lock = threading.Lock()
        self._pidfds, self._tickets = [], {}
        self._handles = {}
        self._handle_inventory, self._handle_log = self._handles, ()
        self._pidfd_inventory, self._ticket_inventory = self._pidfds, self._tickets
        self._pidfd_log, self._ticket_log = (), ()
        channel.setblocking(False)

    def _holder(self):
        super()._holder()
        child, channel, config, raw, identity = self._pins
        child._holder()
        actual = os.fstat(channel.fileno())
        if (
            self.child is not child
            or self.channel is not channel
            or self.config is not config
            or config.encode() != raw
            or (actual.st_dev, actual.st_ino) != (identity.st_dev, identity.st_ino)
            or child._root._clients.get(child._slot) is not self
            or self._pidfds is not self._pidfd_inventory
            or self._tickets is not self._ticket_inventory
            or tuple(self._pidfds) != self._pidfd_log
            or tuple(self._tickets.items()) != self._ticket_log
            or self._handles is not self._handle_inventory
            or tuple(self._handles.items()) != self._handle_log
            or self._epoch_history is not self._epoch_history_pin
            or self._advance_receipts is not self._advance_receipts_pin
        ):
            raise BootstrapError("ML-AFFA-REPLACED")
        for fd, capability in self._pidfds:
            capability.check(fd)

    @property
    def epoch(self):
        return (
            self._epoch_history[-1].epoch
            if self._epoch_history
            else self._pins[2].epoch
        )

    @property
    def lease_ns(self):
        self._holder()
        return self._lease

    def _receive(self, until):
        while True:
            self._holder()
            if self._revoked:
                raise BootstrapError("ML-AFFA-REVOKED")
            remaining = (until - time.monotonic_ns()) / 1e9
            if remaining <= 0:
                raise BootstrapError("ML-AFFA-TIMEOUT")
            if not select.select([self.channel], [], [], min(remaining, 0.01))[0]:
                continue
            try:
                raw, ancillary, flags, _ = self.channel.recvmsg(
                    321,
                    socket.CMSG_SPACE(12) + socket.CMSG_SPACE(8 * 4),
                    socket.MSG_CMSG_CLOEXEC,
                )
            except BlockingIOError:
                continue
            fds, peers, rights = [], [], 0
            valid = not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
            try:
                for level, kind, data in ancillary:
                    if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                        rights += 1
                        values = array.array("i")
                        if len(data) % values.itemsize:
                            valid = False
                        values.frombytes(
                            data[: len(data) - len(data) % values.itemsize]
                        )
                        fds.extend(values)
                    elif (
                        level == socket.SOL_SOCKET
                        and kind == socket.SCM_CREDENTIALS
                        and len(data) == 12
                    ):
                        peers.append(struct.unpack("3i", data))
                    else:
                        valid = False
                if (
                    not valid
                    or rights > 1
                    or peers != [(self.child.pid, os.getuid(), os.getgid())]
                ):
                    raise BootstrapError("ML-AFFA-SENDER")
                frame = AuthorityFrame.decode(raw)
                result = fds[:]
                fds.clear()
                return frame, result
            finally:
                for fd in fds:
                    os.close(fd)

    def _ready(self, deadline):
        self._holder()
        until = min(_deadline(deadline, self.child._root.session), self._lease)
        reply, fds = self._receive(until)
        try:
            if (
                fds
                or reply
                != AuthorityFrame(
                    K.READY,
                    0,
                    self._lease,
                    self.config.scope,
                    epoch=self.epoch,
                    lease_ns=self._lease,
                )
                or time.monotonic_ns() >= until
            ):
                raise BootstrapError("ML-AFFA-READY")
            self._epoch_history = (reply,)
            self._epoch_history_pin = self._epoch_history
        finally:
            for fd in fds:
                os.close(fd)

    def _watched(self, fd):
        root = self.child._root
        identity = BootstrapChild._fd_identity(fd)
        descriptor = root._watches.get(identity)
        if descriptor is None:
            raise BootstrapError("ML-AFFA-UNWATCHED")
        entry = root.boundaries._entry(descriptor)
        root.boundaries._authority(entry)
        root.boundaries._verify(entry)
        if BootstrapChild._fd_identity(entry.fd) != identity:
            raise BootstrapError("ML-AFFA-C1-IDENTITY")
        return descriptor

    def watch_token(self, fd):
        """The supervisor's WATCH token for an exact watched original C1 (F-02, finding 403)."""
        self._watched(fd)
        token = self.child._root._watch_tokens.get(BootstrapChild._fd_identity(fd))
        if token is None:
            raise BootstrapError("ML-AFFA-UNWATCHED")
        return token

    def _validate(self, request, fds):
        self._holder()
        if (
            type(request) is not AuthorityFrame
            or request.kind not in _REPLIES
            or type(fds) is not tuple
        ):
            raise BootstrapError("ML-AFFA-REQUEST")
        request._validate()
        until, now = request.deadline_ns, time.monotonic_ns()
        if (
            request.sequence != self.sequence + 1
            or request.epoch != self.epoch
            or request.scope != self.config.scope
            or not now < until <= now + 5_000_000_000
            or until > self.config.generation_ns - 2_000_000_000
        ):
            raise BootstrapError("ML-AFFA-REQUEST-SCOPE")
        if self._revoked or self._starts_closed and request.kind not in _CLEANUP:
            raise BootstrapError("ML-AFFA-CLOSED")
        if request.kind not in _CLEANUP:
            self.child._ordinary()
            if until > self._lease:
                raise BootstrapError("ML-AFFA-LEASE")
        # S1b: a REGISTER carries a fifth fd, the private stderr directory, only for a declared stderr;
        # the native authority checks the count and the identity against the sealed AR17 v2 recipe.
        expected_rights = (
            (4, 5) if request.kind is K.REGISTER else (1,) if request.kind is K.ADVANCE else (0,)
        )
        if len(fds) not in expected_rights or any(
            type(fd) is not int or fd < 3 for fd in fds
        ):
            raise BootstrapError("ML-AFFA-RIGHTS")
        if fds:
            self._watched(fds[0])
            if request.kind is K.ADVANCE and request.ticket != self.watch_token(fds[0]):
                raise BootstrapError("ML-AFFA-WATCH-TOKEN")
        if request.kind is K.RELEASE:
            ticket = self._tickets.get(
                (request.slot, request.generation, request.handle)
            )
            if ticket is None or request.ticket != ticket[0] or until > ticket[1]:
                raise BootstrapError("ML-AFFA-TICKET-END")

    def _match(self, request, reply, fds):
        expected_epoch = self.epoch + (
            request.kind is K.ADVANCE
            or request.kind is K.CANCEL
            and not self._starts_closed
        )
        if reply.kind is K.REJECTED:
            raise BootstrapError("ML-AFFA-NATIVE-REJECTED")
        kind = _REPLIES[request.kind]
        if request.kind in _FAULTS and reply.kind is K.FAULT_REFUSED:
            kind = K.FAULT_REFUSED
        if len(fds) != (1 if kind is K.STAGED else 0):
            raise BootstrapError("ML-AFFA-ACK-RIGHTS")
        if kind is K.CANCELLED:
            expected = AuthorityFrame(
                kind,
                request.sequence,
                request.deadline_ns,
                request.scope,
                epoch=expected_epoch,
                state=reply.state,
                reason=reply.reason,
            )
            if reply.state >= 1 << len(self.config.units) or reply.reason not in (5, 6):
                raise BootstrapError("ML-AFFA-CANCEL-ACK")
        else:
            expected = replace(
                request,
                kind=kind,
                epoch=expected_epoch,
                state=reply.state,
                reason=0,
                handle=reply.handle if kind is K.STAGED else request.handle,
                # F-02 (finding 403): the ADVANCE watch token is never echoed in ADVANCED.
                ticket=reply.ticket if kind is K.ARMED else bytes(32) if kind is K.ADVANCED else request.ticket,
                lease_ns=request.lease_ns if kind is K.RENEWED else 0,
            )
            if reply.state & ~STATE_MASK:
                raise BootstrapError("ML-AFFA-ACK-STATE")
        if reply != expected:
            raise BootstrapError("ML-AFFA-ACK-SCOPE")

    def _exchange(self, request, *, fds=()):
        """Private trusted-broker operation; frame digests do not prove M3/Argus."""
        if not self._lock.acquire(False):
            raise BootstrapError("ML-AFFA-CONFLICT")
        received = []
        sent = False
        try:
            self._validate(request, fds)
            ancillary = (
                [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", fds))]
                if fds
                else []
            )
            sent = True
            if self.channel.sendmsg([request.encode()], ancillary) != 320:
                raise BootstrapError("ML-AFFA-SEND")
            self.sequence = request.sequence
            reply, received = self._receive(request.deadline_ns)
            self._match(request, reply, received)
            if self._revoked or time.monotonic_ns() >= request.deadline_ns:
                raise BootstrapError("ML-AFFA-LATE-ACK")
            if received:
                fd = received[0]
                identity = (reply.slot, reply.generation)
                retained = self._handles.get(identity)
                if retained is not None:
                    token, capability = retained
                    if token != reply.handle:
                        raise BootstrapError("ML-AFFA-ISSUED-HANDLE")
                    capability.check(fd)
                    os.close(fd)
                else:
                    try:
                        signal.pidfd_send_signal(fd, 0)
                    except ProcessLookupError:
                        pass
                    capability = _PidfdCapability(fd)
                    self._pidfds.append((fd, capability))
                    self._pidfd_log = tuple(self._pidfds)
                    self._handles[identity] = (reply.handle, capability)
                    self._handle_log = tuple(self._handles.items())
                received.clear()
            if reply.kind in (K.CANCELLED, K.ADVANCED):
                self._epoch_history = (*self._epoch_history, reply)
                self._epoch_history_pin = self._epoch_history
            if reply.kind is K.ADVANCED:
                descriptor = self._watched(fds[0])
                receipt = AuthorityEpochAdvance(
                    _CREATE, self, request, reply, descriptor
                )
                self._advance_receipts = (*self._advance_receipts, receipt)
                self._advance_receipts_pin = self._advance_receipts
                self.child._root.boundaries.admit_epoch(receipt)
            if reply.kind is K.ARMED:
                self._tickets[(reply.slot, reply.generation, reply.handle)] = (
                    reply.ticket,
                    reply.deadline_ns,
                )
                self._ticket_log = tuple(self._tickets.items())
            if reply.kind in (K.CANCELLED, K.ADVANCED):
                self._tickets.clear()
                self._ticket_log = ()
            if reply.kind is K.CANCELLED:
                self._starts_closed = True
            if reply.kind is K.RENEWED:
                self._lease = reply.lease_ns
            return reply
        except Exception:
            if sent:
                self.revoke(
                    HostDeadline(
                        self.child._root.session,
                        min(
                            time.monotonic() + 1,
                            self.config.generation_ns / 1e9,
                            request.deadline_ns / 1e9
                            if request.kind in _CLEANUP
                            else float("inf"),
                        ),
                    )
                )
            raise
        finally:
            for fd in received:
                os.close(fd)
            self._lock.release()

    def revoke(self, deadline):
        """Independent of the exchange lock; no C1 or workload-wait inference."""
        self._holder()
        if (
            type(deadline) is not HostDeadline
            or deadline.session != self.child._root.session
        ):
            raise BootstrapError("ML-AFFA-REVOKE-SESSION")
        deadline.__post_init__()
        if deadline.monotonic_seconds - time.monotonic() > 5:
            raise BootstrapError("ML-AFFA-REVOKE-END")
        until = min(int(deadline.monotonic_seconds * 1e9), self.config.generation_ns)
        self._revoked = self._starts_closed = True
        self.child._root.latch.cancel("original-authority-revocation")
        capability = self.child._capability
        try:
            signal.pidfd_send_signal(capability.fileno(), signal.SIGKILL)
        except ProcessLookupError:
            pass
        waited = self.child._result
        while not waited and time.monotonic_ns() < until:
            try:
                waited = self.child._wait(capability.fileno(), consume=True)
            except BootstrapError as error:
                if str(error) != "ML-BOOT-WAIT-CONFLICT":
                    break
            except (ValueError, OSError):
                break
            if waited:
                break
            select.select(
                [capability.fileno()],
                [],
                [],
                min(0.01, max(0, (until - time.monotonic_ns()) / 1e9)),
            )
        dead = bool(select.select([capability.fileno()], [], [], 0)[0])
        return AuthorityRevocation(
            dead, bool(waited), None if waited else "ML-AFFA-WAIT-UNRESOLVED"
        )

    def dispose(self):
        self._holder()
        if self.child._result is None:
            raise BootstrapError("ML-AFFA-RETAINED")
        for fd, capability in self._pidfds:
            capability.close()
            os.close(fd)
        self._pidfds.clear()
        self._pidfd_log = ()
        self.channel.close()

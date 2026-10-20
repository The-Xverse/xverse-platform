"""Private AF17 values and closed ABI; parsing never creates execution authority."""

from dataclasses import dataclass, field
from enum import IntEnum
import struct


class ProtocolError(ValueError):
    pass


class AuthorityKind(IntEnum):
    REGISTER = 1
    INTENT = 2
    STAGE = 3
    ARM = 4
    RELEASE = 5
    QUERY = 6
    STOP = 7
    RETIRE = 8
    RENEW = 9
    CANCEL = 10
    QUERY_ISSUED = 11
    READY = 16
    REGISTERED = 17
    INTENT_RECORDED = 18
    STAGED = 19
    ARMED = 20
    RELEASED = 21
    OBSERVED = 22
    STOPPED = 23
    RETIRED = 24
    RENEWED = 25
    CANCELLED = 26
    REJECTED = 27


_PACKET = struct.Struct("!4sIQQ32sQQQ16s32s32s32s32s32s32sQQQ8s")
_ZERO16, _ZERO32 = bytes(16), bytes(32)
_UINT64 = 2**64 - 1


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ProtocolError("ML-AFFA-INTEGER")


def _bytes(value, length):
    if type(value) is not bytes or len(value) != length:
        raise ProtocolError("ML-AFFA-BYTES")


@dataclass(frozen=True, slots=True)
class AuthorityFrame:
    kind: AuthorityKind
    sequence: int
    deadline_ns: int
    scope: bytes = field(repr=False)
    slot: int = 0
    epoch: int = 0
    generation: int = 0
    operation: bytes = field(default=_ZERO16, repr=False)
    first: bytes = field(default=_ZERO32, repr=False)
    second: bytes = field(default=_ZERO32, repr=False)
    third: bytes = field(default=_ZERO32, repr=False)
    fourth: bytes = field(default=_ZERO32, repr=False)
    ticket: bytes = field(default=_ZERO32, repr=False)
    handle: bytes = field(default=_ZERO32, repr=False)
    state: int = 0
    reason: int = 0
    lease_ns: int = 0

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if type(self) is not AuthorityFrame or type(self.kind) is not AuthorityKind:
            raise ProtocolError("ML-AFFA-TYPE")
        _integer(self.sequence, 0 if self.kind is AuthorityKind.READY else 1, 8192)
        _integer(self.deadline_ns, 1, _UINT64)
        _integer(self.slot, 0, 16)
        _integer(self.epoch, 0, _UINT64)
        _integer(self.generation, 0, _UINT64)
        _integer(self.state, 0, 65535)
        _integer(self.reason, 0, 7)
        _integer(self.lease_ns, 0, _UINT64)
        _bytes(self.scope, 32)
        _bytes(self.operation, 16)
        for value in self._digests() + (self.ticket, self.handle):
            _bytes(value, 32)
        if self.scope == _ZERO32:
            raise ProtocolError("ML-AFFA-SCOPE")
        kind = self.kind
        if kind is AuthorityKind.READY:
            self._run_shape()
            if self.sequence or self.lease_ns != self.deadline_ns or self.state or self.reason:
                raise ProtocolError("ML-AFFA-READY")
        elif kind in (AuthorityKind.RENEW, AuthorityKind.CANCEL, AuthorityKind.RENEWED, AuthorityKind.CANCELLED, AuthorityKind.REJECTED):
            self._run_shape()
            if (kind in (AuthorityKind.RENEW, AuthorityKind.RENEWED)) != (self.lease_ns > 0):
                raise ProtocolError("ML-AFFA-LEASE")
            if kind in (AuthorityKind.RENEW, AuthorityKind.CANCEL) and (self.state or self.reason):
                raise ProtocolError("ML-AFFA-REQUEST")
            if kind is AuthorityKind.RENEWED and (self.state or self.reason):
                raise ProtocolError("ML-AFFA-RENEWED")
            if kind is AuthorityKind.REJECTED and (not self.reason or self.state):
                raise ProtocolError("ML-AFFA-REJECTED")
        else:
            if not self.slot or not self.generation or self.lease_ns:
                raise ProtocolError("ML-AFFA-UNIT")
            if any(value == _ZERO32 for value in self._digests()):
                raise ProtocolError("ML-AFFA-IDENTITY")
            if kind in (AuthorityKind.REGISTER, AuthorityKind.REGISTERED):
                if self.operation != _ZERO16 or self.ticket != _ZERO32 or self.handle != _ZERO32:
                    raise ProtocolError("ML-AFFA-REGISTER")
            else:
                if self.operation == _ZERO16:
                    raise ProtocolError("ML-AFFA-OPERATION")
                no_handle = kind in (AuthorityKind.INTENT, AuthorityKind.STAGE, AuthorityKind.QUERY_ISSUED, AuthorityKind.INTENT_RECORDED)
                if no_handle != (self.handle == _ZERO32):
                    raise ProtocolError("ML-AFFA-HANDLE")
                needs_ticket = kind in (AuthorityKind.RELEASE, AuthorityKind.ARMED, AuthorityKind.RELEASED)
                if needs_ticket != (self.ticket != _ZERO32):
                    raise ProtocolError("ML-AFFA-TICKET")
            if kind.value < 16 and (self.state or self.reason):
                raise ProtocolError("ML-AFFA-REQUEST")

    def _digests(self):
        return (self.first, self.second, self.third, self.fourth)

    def _run_shape(self):
        if (self.slot or self.generation or self.operation != _ZERO16
            or any(value != _ZERO32 for value in self._digests())
            or self.ticket != _ZERO32 or self.handle != _ZERO32):
            raise ProtocolError("ML-AFFA-RUN")

    def encode(self):
        self._validate()
        return _PACKET.pack(
            b"AF17", self.kind.value, self.sequence, self.deadline_ns, self.scope,
            self.slot, self.epoch, self.generation, self.operation,
            *self._digests(), self.ticket, self.handle,
            self.state, self.reason, self.lease_ns, bytes(8),
        )

    @classmethod
    def decode(cls, data):
        if cls is not AuthorityFrame or type(data) is not bytes or len(data) != _PACKET.size:
            raise ProtocolError("ML-AFFA-PACKET")
        magic, kind, *values, reserved = _PACKET.unpack(data)
        if magic != b"AF17" or reserved != bytes(8):
            raise ProtocolError("ML-AFFA-PACKET")
        try:
            kind = AuthorityKind(kind)
        except ValueError:
            raise ProtocolError("ML-AFFA-KIND") from None
        return cls(kind, *values)

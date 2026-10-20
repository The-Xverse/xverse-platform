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


_CONFIG = struct.Struct("!4sIQQQQ32s32s24s")
_UNIT = struct.Struct("!32s32s32sQQQQQ24s")
_RECIPE = struct.Struct("!4sIII")
_LENGTH = struct.Struct("!I")


@dataclass(frozen=True, slots=True)
class AuthorityUnit:
    binding: bytes = field(repr=False)
    image: bytes = field(repr=False)
    recipe: bytes = field(repr=False)
    boundary_device: int = field(repr=False)
    boundary_inode: int = field(repr=False)
    cwd_device: int = field(repr=False)
    cwd_inode: int = field(repr=False)
    generation: int

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if type(self) is not AuthorityUnit:
            raise ProtocolError("ML-AFFA-UNIT-TYPE")
        for digest in (self.binding, self.image, self.recipe):
            _bytes(digest, 32)
            if digest == _ZERO32:
                raise ProtocolError("ML-AFFA-UNIT-DIGEST")
        for value in (self.boundary_device, self.cwd_device):
            _integer(value, 0, _UINT64)
        for value in (self.boundary_inode, self.cwd_inode, self.generation):
            _integer(value, 1, _UINT64)

    def encode(self):
        self._validate()
        return _UNIT.pack(self.binding, self.image, self.recipe,
                          self.boundary_device, self.boundary_inode,
                          self.cwd_device, self.cwd_inode, self.generation, bytes(24))

    @classmethod
    def decode(cls, data):
        if cls is not AuthorityUnit or type(data) is not bytes or len(data) != _UNIT.size:
            raise ProtocolError("ML-AFFA-UNIT-PACKET")
        *values, reserved = _UNIT.unpack(data)
        if reserved != bytes(24):
            raise ProtocolError("ML-AFFA-UNIT-RESERVED")
        return cls(*values)


@dataclass(frozen=True, slots=True)
class AuthorityConfig:
    generation_ns: int
    lease_ns: int
    epoch: int
    scope: bytes = field(repr=False)
    supervisor_session: bytes = field(repr=False)
    units: tuple[AuthorityUnit, ...] = field(repr=False)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if type(self) is not AuthorityConfig:
            raise ProtocolError("ML-AFFA-CONFIG-TYPE")
        _integer(self.generation_ns, 1, _UINT64)
        _integer(self.lease_ns, 1, _UINT64)
        _integer(self.epoch, 0, _UINT64 - 1)
        if self.lease_ns + 2_000_000_000 > self.generation_ns:
            raise ProtocolError("ML-AFFA-CONFIG-RESERVE")
        for value in (self.scope, self.supervisor_session):
            _bytes(value, 32)
            if value == _ZERO32:
                raise ProtocolError("ML-AFFA-CONFIG-IDENTITY")
        if type(self.units) is not tuple or not 1 <= len(self.units) <= 16:
            raise ProtocolError("ML-AFFA-CONFIG-UNITS")
        for unit in self.units:
            if type(unit) is not AuthorityUnit:
                raise ProtocolError("ML-AFFA-CONFIG-UNITS")
            unit._validate()
        if (len({u.binding for u in self.units}) != len(self.units)
            or len({(u.boundary_device, u.boundary_inode) for u in self.units}) != len(self.units)):
            raise ProtocolError("ML-AFFA-CONFIG-DUPLICATE")

    def encode(self):
        self._validate()
        return _CONFIG.pack(b"AC17", 1, self.generation_ns, self.lease_ns,
                            self.epoch, len(self.units), self.scope,
                            self.supervisor_session, bytes(24)) + b"".join(u.encode() for u in self.units)

    @classmethod
    def decode(cls, data):
        if (cls is not AuthorityConfig or type(data) is not bytes
            or not _CONFIG.size + _UNIT.size <= len(data) <= _CONFIG.size + 16 * _UNIT.size):
            raise ProtocolError("ML-AFFA-CONFIG-PACKET")
        magic, version, generation, lease, epoch, count, scope, session, reserved = _CONFIG.unpack_from(data)
        if (magic != b"AC17" or version != 1 or reserved != bytes(24)
            or not 1 <= count <= 16 or len(data) != _CONFIG.size + count * _UNIT.size):
            raise ProtocolError("ML-AFFA-CONFIG-PACKET")
        units = tuple(AuthorityUnit.decode(data[i:i + _UNIT.size]) for i in range(_CONFIG.size, len(data), _UNIT.size))
        return cls(generation, lease, epoch, scope, session, units)


@dataclass(frozen=True, slots=True)
class AuthorityRecipe:
    argv: tuple[str, ...] = field(repr=False)
    environment: tuple[str, ...] = field(repr=False)

    def __post_init__(self):
        self._payload()

    def _payload(self):
        import re

        if (type(self) is not AuthorityRecipe or type(self.argv) is not tuple
            or type(self.environment) is not tuple or not 1 <= len(self.argv) <= 32
            or len(self.environment) > 64):
            raise ProtocolError("ML-AFFA-RECIPE-TYPE")
        body = bytearray(_RECIPE.pack(b"AR17", 1, len(self.argv), len(self.environment)))
        keys = set()
        for index, text in enumerate(self.argv + self.environment):
            if type(text) is not str or len(text) > 4096 or "\0" in text:
                raise ProtocolError("ML-AFFA-RECIPE-WORD")
            try:
                raw = text.encode("utf-8", errors="strict")
            except UnicodeError:
                raise ProtocolError("ML-AFFA-RECIPE-UTF8") from None
            if len(raw) > 4096 or (index == 0 and not raw):
                raise ProtocolError("ML-AFFA-RECIPE-WORD")
            if index >= len(self.argv):
                key, separator, _value = text.partition("=")
                if (not separator or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) is None
                    or key in keys):
                    raise ProtocolError("ML-AFFA-RECIPE-ENVIRONMENT")
                keys.add(key)
            if len(body) + 4 + len(raw) + 1 > 65536:
                raise ProtocolError("ML-AFFA-RECIPE-CAPACITY")
            body.extend(_LENGTH.pack(len(raw)))
            body.extend(raw)
            body.append(0)
        return bytes(body)

    def encode(self):
        return self._payload()

    @classmethod
    def decode(cls, data):
        if cls is not AuthorityRecipe or type(data) is not bytes or not 16 <= len(data) <= 65536:
            raise ProtocolError("ML-AFFA-RECIPE-PACKET")
        magic, version, argc, envc = _RECIPE.unpack_from(data)
        if magic != b"AR17" or version != 1 or not 1 <= argc <= 32 or envc > 64:
            raise ProtocolError("ML-AFFA-RECIPE-PACKET")
        offset, values = 16, []
        for _ in range(argc + envc):
            if offset + 4 > len(data):
                raise ProtocolError("ML-AFFA-RECIPE-PACKET")
            size = _LENGTH.unpack_from(data, offset)[0]
            offset += 4
            if size > 4096 or offset + size >= len(data) or data[offset + size] != 0:
                raise ProtocolError("ML-AFFA-RECIPE-PACKET")
            try:
                value = data[offset:offset + size].decode("utf-8", errors="strict")
            except UnicodeError:
                raise ProtocolError("ML-AFFA-RECIPE-UTF8") from None
            values.append(value)
            offset += size + 1
        if offset != len(data):
            raise ProtocolError("ML-AFFA-RECIPE-PACKET")
        return cls(tuple(values[:argc]), tuple(values[argc:]))

"""Inert private RG06 codec; bytes/digests confer no run or Release authority.

The original trusted bootstrap owner must validate actual M3/Argus/Stage receipts
and retain the private original channel. No process, C1, ticket registry, provider,
callback, clock read or successful lifecycle result is created by this module.
"""

from dataclasses import dataclass, field
import struct

_ZERO = bytes(32)
_WIRE = struct.Struct("!4sIQQ32sQQ32s32s32s32s32s24s")
_COMMANDS = (1, 2, 3, 4)
_KINDS = _COMMANDS + (16, 17, 18, 19, 20, 21)


class GateProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class GatePacket:
    kind: int
    sequence: int
    deadline_ns: int
    scope: bytes
    epoch: int
    reason: int = 0
    operation: bytes = _ZERO
    intent: bytes = field(default=_ZERO, repr=False)
    flush: bytes = field(default=_ZERO, repr=False)
    stage: bytes = field(default=_ZERO, repr=False)
    nonce: bytes = field(default=_ZERO, repr=False)

    def __post_init__(self):
        for value in (
            self.kind,
            self.sequence,
            self.deadline_ns,
            self.epoch,
            self.reason,
        ):
            if type(value) is not int or not 0 <= value < 2**64:
                raise GateProtocolError("ML-FENCE-INTEGER")
        if self.kind not in _KINDS or self.reason > 7 or self.deadline_ns == 0:
            raise GateProtocolError("ML-FENCE-HEADER")
        if (self.kind in (18, 19)) != (self.reason != 0):
            raise GateProtocolError("ML-FENCE-RESPONSE-REASON")
        if self.kind == 16 and self.sequence != 0:
            raise GateProtocolError("ML-FENCE-READY-SEQUENCE")
        values = (
            self.scope,
            self.operation,
            self.intent,
            self.flush,
            self.stage,
            self.nonce,
        )
        if any(type(v) is not bytes or len(v) != 32 for v in values):
            raise GateProtocolError("ML-FENCE-DIGEST")
        if self.kind in _COMMANDS and (self.reason or not self.sequence):
            raise GateProtocolError("ML-FENCE-COMMAND")
        facts = (self.operation, self.intent, self.flush, self.stage)
        if self.kind in (3, 4, 20, 21):
            if any(v == _ZERO for v in facts):
                raise GateProtocolError("ML-FENCE-ACK-IDENTITY")
            if (self.kind in (4, 20)) != (self.nonce != _ZERO):
                raise GateProtocolError("ML-FENCE-TICKET")
        elif any(v != _ZERO for v in facts + (self.nonce,)):
            raise GateProtocolError("ML-FENCE-SURPLUS")

    def encode(self) -> bytes:
        self.__post_init__()
        return _WIRE.pack(
            b"RG06",
            self.kind,
            self.sequence,
            self.deadline_ns,
            self.scope,
            self.reason,
            self.epoch,
            self.operation,
            self.intent,
            self.flush,
            self.stage,
            self.nonce,
            bytes(24),
        )

    @classmethod
    def decode(cls, data: bytes) -> "GatePacket":
        if type(data) is not bytes or len(data) != _WIRE.size:
            raise GateProtocolError("ML-FENCE-SIZE")
        (
            magic,
            kind,
            sequence,
            deadline,
            scope,
            reason,
            epoch,
            op,
            intent,
            flush,
            stage,
            nonce,
            reserved,
        ) = _WIRE.unpack(data)
        if magic != b"RG06" or reserved != bytes(24):
            raise GateProtocolError("ML-FENCE-WIRE")
        return cls(
            kind,
            sequence,
            deadline,
            scope,
            epoch,
            reason,
            op,
            intent,
            flush,
            stage,
            nonce,
        )

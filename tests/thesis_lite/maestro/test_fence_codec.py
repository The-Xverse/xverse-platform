import struct
from dataclasses import replace

import pytest

from xverse.maestro.fence import GatePacket, GateProtocolError


def packet(**changes):
    fields = dict(
        kind=3,
        sequence=1,
        deadline_ns=123,
        scope=b"s" * 32,
        epoch=7,
        operation=b"o" * 32,
        intent=b"i" * 32,
        flush=b"f" * 32,
        stage=b"a" * 32,
    )
    fields.update(changes)
    return GatePacket(**fields)


def test_wire_offsets_are_literal_and_not_a_second_state_machine():
    p = packet()
    data = p.encode()
    assert len(data) == 256 and data[:8] == b"RG06\x00\x00\x00\x03"
    assert struct.unpack("!QQ", data[8:24]) == (1, 123)
    assert data[24:56] == b"s" * 32 and data[56:64] == bytes(8)
    assert data[64:72] == (7).to_bytes(8, "big")
    assert data[72:200] == b"o" * 32 + b"i" * 32 + b"f" * 32 + b"a" * 32
    assert data[200:] == bytes(56)
    assert GatePacket.decode(data) == p


@pytest.mark.parametrize(
    "field", ["sequence", "deadline_ns", "epoch", "reason", "kind"]
)
@pytest.mark.parametrize("bad", [True, -1, 2**64, 1.5, "1"])
def test_integer_identity_is_strict(field, bad):
    with pytest.raises(GateProtocolError):
        replace(packet(), **{field: bad})


@pytest.mark.parametrize(
    "field", ["scope", "operation", "intent", "flush", "stage", "nonce"]
)
def test_digest_transport_is_exact_immutable_bytes(field):
    with pytest.raises(GateProtocolError):
        replace(packet(), **{field: bytearray(32)})


@pytest.mark.parametrize("field", ["operation", "intent", "flush", "stage"])
def test_arm_cannot_omit_an_ack_identity(field):
    with pytest.raises(GateProtocolError):
        replace(packet(), **{field: bytes(32)})


@pytest.mark.parametrize("bad", [b"", bytes(64), bytes(257), b"LG05" + bytes(252)])
def test_bad_wire_size_or_magic_denied(bad):
    with pytest.raises(GateProtocolError):
        GatePacket.decode(bad)


def test_reserved_command_data_and_nonce_rules():
    data = bytearray(packet().encode())
    data[-1] = 1
    with pytest.raises(GateProtocolError):
        GatePacket.decode(bytes(data))
    with pytest.raises(GateProtocolError):
        replace(packet(), kind=4)
    with pytest.raises(GateProtocolError):
        replace(packet(), nonce=b"n" * 32)
    with pytest.raises(GateProtocolError):
        replace(packet(), kind=1)
    with pytest.raises(GateProtocolError):
        replace(packet(), reason=1)
    released = packet(kind=21)
    assert GatePacket.decode(released.encode()) == released
    assert "iiii" not in repr(released)


def test_contradictory_response_headers_never_decode_as_success():
    for kind, sequence, reason in [(16, 1, 0), (16, 0, 1), (18, 0, 0), (19, 0, 0)]:
        with pytest.raises(GateProtocolError):
            GatePacket(kind, sequence, 123, b"s" * 32, 7, reason)

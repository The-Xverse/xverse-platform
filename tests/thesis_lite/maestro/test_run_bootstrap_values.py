"""Literal successor expectations authored before bootstrap implementation."""

from dataclasses import replace
import struct

import pytest
from xverse.maestro.bootstrap import BootstrapPacket


def test_distinct_watch_packet_literal():
    packet = BootstrapPacket(4, 1, 123, bytes(range(32)), slot=128, version=2)
    literal = struct.pack(
        "!4sIQQ32sQQ32sQQQ",
        b"BS17",
        4,
        1,
        123,
        bytes(range(32)),
        128,
        0,
        bytes(32),
        0,
        0,
        0,
    )
    assert packet.encode() == literal
    assert BootstrapPacket.decode(literal, version=2) == packet
    with pytest.raises(ValueError):
        BootstrapPacket.decode(literal)


def test_legacy_cannot_request_authority_role_or_watch():
    for kind, state in ((1, 4), (4, 0), (20, 0)):
        with pytest.raises(ValueError):
            BootstrapPacket(kind, 1, 123, bytes(32), slot=1, state=state)


def test_successor_birth_has_explicit_fourth_role():
    value = BootstrapPacket(1, 1, 123, bytes(32), slot=1, state=4, version=2)
    assert BootstrapPacket.decode(value.encode(), version=2) == value
    with pytest.raises(ValueError):
        replace(value, version=1)


@pytest.mark.parametrize(
    "changes",
    [
        dict(pid=2),
        dict(token=b"x" * 32),
        dict(state=1),
        dict(slot=0),
        dict(slot=129),
        dict(sequence=0),
    ],
)
def test_watch_rejects_nonempty_or_out_of_range_fields(changes):
    with pytest.raises(ValueError):
        replace(BootstrapPacket(4, 1, 123, bytes(32), slot=1, version=2), **changes)


def test_successor_controller_role5_is_literal_and_legacy_rejects_it():
    value = BootstrapPacket(1, 1, 123, bytes(32), slot=1, state=5, version=2)
    literal = struct.pack("!4sIQQ32sQQ32sQQQ", b"BS17", 1, 1, 123,
        bytes(32), 1, 0, bytes(32), 5, 0, 0)
    assert value.encode() == literal
    assert BootstrapPacket.decode(literal, version=2) == value
    with pytest.raises(ValueError):
        replace(value, version=1)

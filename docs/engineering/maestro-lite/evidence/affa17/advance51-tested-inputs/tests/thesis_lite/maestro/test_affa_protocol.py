"""Independent AF17 offsets and rejection controls; no process authority."""

import dataclasses
import struct

import pytest
from xverse.maestro.affa_protocol import AuthorityFrame, AuthorityKind, ProtocolError


SCOPE = b"s" * 32
DIGESTS = (b"a" * 32, b"i" * 32, b"m" * 32, b"b" * 32)


def release():
    return AuthorityFrame(
        AuthorityKind.RELEASE, 7, 123456789, SCOPE, 2, 3, 1,
        b"o" * 16, *DIGESTS, b"t" * 32, b"h" * 32,
    )


def test_literal_release_offsets_are_the_frozen_native_abi():
    encoded = release().encode()
    expected = (
        b"AF17" + struct.pack("!IQQ", 5, 7, 123456789) + SCOPE
        + struct.pack("!QQQ", 2, 3, 1) + b"o" * 16 + b"".join(DIGESTS)
        + b"t" * 32 + b"h" * 32 + bytes(32)
    )
    assert len(expected) == 320 and encoded == expected
    assert AuthorityFrame.decode(expected) == release()
    assert "oooo" not in repr(release()) and "tttt" not in repr(release())


@pytest.mark.parametrize("mode", ["short", "long", "magic", "reserved", "kind", "sequence", "slot", "generation", "ticket", "handle", "state", "reason", "lease"])
def test_native_frame_mutations_reject_without_callbacks(mode):
    packet = bytearray(release().encode())
    if mode == "short":
        packet.pop()
    elif mode == "long":
        packet.append(0)
    elif mode == "magic":
        packet[:4] = b"NOPE"
    elif mode == "reserved":
        packet[319] = 1
    elif mode == "kind":
        packet[4:8] = struct.pack("!I", 15)
    elif mode == "sequence":
        packet[8:16] = bytes(8)
    elif mode == "slot":
        packet[56:64] = bytes(8)
    elif mode == "generation":
        packet[72:80] = bytes(8)
    elif mode == "ticket":
        packet[224:256] = bytes(32)
    elif mode == "handle":
        packet[256:288] = bytes(32)
    elif mode == "state":
        packet[288:296] = struct.pack("!Q", 1)
    elif mode == "reason":
        packet[296:304] = struct.pack("!Q", 1)
    else:
        packet[304:312] = struct.pack("!Q", 123)
    with pytest.raises(ProtocolError):
        AuthorityFrame.decode(bytes(packet))


@pytest.mark.parametrize("field,value", [("sequence", True), ("deadline_ns", float("inf")), ("epoch", -1), ("generation", 2**64), ("scope", bytearray(SCOPE)), ("operation", "o" * 16)])
def test_authority_values_are_strict_inert_bounded_fields(field, value):
    with pytest.raises(ProtocolError):
        dataclasses.replace(release(), **{field:value})


def test_run_cancellation_and_renewal_have_no_unit_or_ticket_authority():
    cancel = AuthorityFrame(AuthorityKind.CANCEL, 8, 123456790, SCOPE, epoch=3)
    assert AuthorityFrame.decode(cancel.encode()) == cancel
    with pytest.raises(ProtocolError):
        dataclasses.replace(cancel, slot=1)
    with pytest.raises(ProtocolError):
        dataclasses.replace(cancel, ticket=b"t" * 32)
    renew = AuthorityFrame(AuthorityKind.RENEW, 9, 123456791, SCOPE, epoch=3, lease_ns=123456999)
    assert AuthorityFrame.decode(renew.encode()) == renew
    with pytest.raises(ProtocolError):
        dataclasses.replace(renew, lease_ns=0)


def test_ready_is_sequence_zero_and_contains_only_the_original_run_lease():
    ready = AuthorityFrame(AuthorityKind.READY, 0, 123456790, SCOPE, epoch=3, lease_ns=123456790)
    assert AuthorityFrame.decode(ready.encode()) == ready
    with pytest.raises(ProtocolError):
        dataclasses.replace(ready, sequence=1)
    with pytest.raises(ProtocolError):
        dataclasses.replace(ready, lease_ns=123456789)


def test_register_and_query_issued_do_not_fabricate_resource_handles():
    register = AuthorityFrame(AuthorityKind.REGISTER, 1, 123456790, SCOPE, 1, 0, 1, first=DIGESTS[0], second=DIGESTS[1], third=DIGESTS[2], fourth=DIGESTS[3])
    assert AuthorityFrame.decode(register.encode()) == register
    issued = dataclasses.replace(release(), kind=AuthorityKind.QUERY_ISSUED, ticket=bytes(32), handle=bytes(32))
    assert AuthorityFrame.decode(issued.encode()) == issued
    with pytest.raises(ProtocolError):
        dataclasses.replace(issued, handle=b"h" * 32)


def test_selective_generation_advance_has_no_old_handle_or_release_ticket():
    advance = AuthorityFrame(AuthorityKind.ADVANCE, 10, 123456790, SCOPE, 2, 3, 2,
                             b"n" * 16, *DIGESTS)
    assert AuthorityFrame.decode(advance.encode()) == advance
    assert struct.unpack_from("!I", advance.encode(), 4)[0] == 12
    acknowledged = dataclasses.replace(advance, kind=AuthorityKind.ADVANCED, epoch=4)
    assert AuthorityFrame.decode(acknowledged.encode()) == acknowledged
    with pytest.raises(ProtocolError):
        dataclasses.replace(advance, handle=b"h" * 32)
    with pytest.raises(ProtocolError):
        dataclasses.replace(advance, ticket=b"t" * 32)

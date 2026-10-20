"""AC17/AR17 independently specified bytes and hostile input controls."""

from dataclasses import replace
import struct

import pytest
from xverse.maestro.affa_protocol import (
    AuthorityConfig, AuthorityRecipe, AuthorityUnit, ProtocolError,
)


def unit():
    return AuthorityUnit(b"u" * 32, b"i" * 32, b"r" * 32, 29, 100, 29, 200, 1, 2)


def config():
    return AuthorityConfig(10_000_000_000, 5_000_000_000, 3, b"s" * 32, b"c" * 32, (unit(),))


def test_sealed_configuration_matches_the_independent_native_offsets():
    expected = (
        b"AC17" + struct.pack("!IQQQQ", 2, 10_000_000_000, 5_000_000_000, 3, 1)
        + b"s" * 32 + b"c" * 32 + bytes(24)
        + b"u" * 32 + b"i" * 32 + b"r" * 32
        + struct.pack("!QQQQQQ", 29, 100, 29, 200, 1, 2) + bytes(16)
    )
    assert len(expected) == 288 and config().encode() == expected
    assert AuthorityConfig.decode(expected) == config()


@pytest.mark.parametrize("mode", ["truncated", "suffix", "version", "reserved-header", "reserved-unit", "count", "zero-unit", "zero-cwd", "zero-generation"])
def test_malformed_original_config_is_not_an_admission(mode):
    data = bytearray(config().encode())
    if mode == "truncated":
        data.pop()
    elif mode == "suffix":
        data.append(0)
    elif mode == "version":
        data[4:8] = struct.pack("!I", 3)
    elif mode == "reserved-header":
        data[127] = 1
    elif mode == "reserved-unit":
        data[-1] = 1
    elif mode == "count":
        data[32:40] = struct.pack("!Q", 17)
    elif mode == "zero-unit":
        data[128:160] = bytes(32)
    elif mode == "zero-cwd":
        data[248:256] = bytes(8)
    else:
        data[256:264] = bytes(8)
    with pytest.raises(ProtocolError):
        AuthorityConfig.decode(bytes(data))


def test_original_unit_and_boundary_sets_are_unique_and_leave_cancel_capacity():
    with pytest.raises(ProtocolError):
        replace(config(), units=(unit(), unit()))
    with pytest.raises(ProtocolError):
        replace(config(), units=(unit(), replace(unit(), binding=b"v" * 32)))
    with pytest.raises(ProtocolError):
        replace(config(), epoch=2**64 - 1)
    with pytest.raises(ProtocolError):
        replace(config(), generation_ns=6_000_000_000)
    with pytest.raises(ProtocolError):
        replace(config(), lease_ns=True)


def test_recipe_is_exact_utf8_argv_and_environment_without_shell_parsing():
    recipe = AuthorityRecipe(("/fixture", "--unit=µ", ""), ("MODE=test",))
    words = (b"/fixture", b"--unit=\xc2\xb5", b"", b"MODE=test")
    expected = b"AR17" + struct.pack("!III", 1, 3, 1)
    expected += b"".join(struct.pack("!I", len(w)) + w + b"\0" for w in words)
    assert recipe.encode() == expected and AuthorityRecipe.decode(expected) == recipe


@pytest.mark.parametrize("mode", ["duplicate-env", "bad-key", "no-equals", "nul", "too-long", "too-many-args", "mutable-args", "empty-argv0"])
def test_recipe_cannot_expand_its_original_bounded_scope(mode):
    argv, env = ("/fixture",), ("MODE=test",)
    if mode == "duplicate-env":
        env += ("MODE=other",)
    elif mode == "bad-key":
        env = ("1MODE=test",)
    elif mode == "no-equals":
        env = ("MODE",)
    elif mode == "nul":
        argv += ("bad\0arg",)
    elif mode == "too-long":
        argv += ("x" * 4097,)
    elif mode == "too-many-args":
        argv = ("x",) * 33
    elif mode == "mutable-args":
        argv = ["/fixture"]
    else:
        argv = ("",)
    with pytest.raises(ProtocolError):
        AuthorityRecipe(argv, env)


@pytest.mark.parametrize("mode", ["short", "suffix", "bad-utf8", "unterminated", "oversized-length"])
def test_untrusted_recipe_bytes_reject_before_any_io(mode):
    packet = bytearray(AuthorityRecipe(("/fixture",), ()).encode())
    if mode == "short":
        packet.pop()
    elif mode == "suffix":
        packet.append(0)
    elif mode == "bad-utf8":
        packet[20] = 255
    elif mode == "unterminated":
        packet[-1] = 1
    else:
        packet[16:20] = struct.pack("!I", 4097)
    with pytest.raises(ProtocolError):
        AuthorityRecipe.decode(bytes(packet))


def test_generation_budget_is_explicit_and_jointly_bounded():
    with pytest.raises(ProtocolError):
        replace(unit(), max_generation=0)
    with pytest.raises(ProtocolError):
        replace(unit(), max_generation=True)
    with pytest.raises(ProtocolError):
        replace(unit(), max_generation=129)
    first = replace(unit(), max_generation=128)
    second = replace(first, binding=b"v" * 32, boundary_inode=101)
    with pytest.raises(ProtocolError):
        replace(config(), units=(first, second))


def test_recipe_total_byte_cap_is_independent_of_individual_word_caps():
    with pytest.raises(ProtocolError):
        AuthorityRecipe(("/fixture",) + ("x" * 4096,) * 31, ())

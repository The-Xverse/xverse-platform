"""V03/V04 time grammar: quantities, mappings, rounding (D6-4)."""

from __future__ import annotations

import pytest

from xverse.flows import FlowError, parse_mapping, parse_quantity_ns, seconds_to_ns


@pytest.mark.parametrize("quantity, ns", [
    ({"value": 3, "unit": "tick"}, 3), ({"value": 2, "unit": "us"}, 2000), ({"value": 0.1, "unit": "ms"}, 100000),
    ({"value": 1.5, "unit": "s"}, 1500000000), ({"value": 0, "unit": "ns"}, 0),
])
def test_quantities_convert_exactly(quantity, ns):
    assert parse_quantity_ns(quantity, code="X") == ns


@pytest.mark.parametrize("quantity", [
    {"value": -1, "unit": "ns"}, {"value": 0.5, "unit": "ns"}, {"value": 1, "unit": "minute"}, {"value": True, "unit": "s"},
    {"value": float("nan"), "unit": "s"}, {"value": 1}, {"value": 1, "unit": "s", "extra": 1}, "1s",
])
def test_quantities_refused(quantity):
    with pytest.raises(FlowError) as caught:
        parse_quantity_ns(quantity, code="XVERSE-FLOW-QUALITY-INVALID")
    assert caught.value.code == "XVERSE-FLOW-QUALITY-INVALID"


@pytest.mark.parametrize("text, offset", [("identity", 0), ("offset:5ns", 5), ("offset:-2us", -2000), ("offset:+1tick", 1), ("offset:3s", 3 * 10**9)])
def test_mapping_grammar(text, offset):
    assert parse_mapping(text) == offset


@pytest.mark.parametrize("text", ["scale:2", "offset:1.5ns", "offset:5", "offset:5min", "", None, "identity "])
def test_mapping_grammar_refuses_everything_else(text):
    with pytest.raises(FlowError) as caught:
        parse_mapping(text)
    assert caught.value.code == "XVERSE-FLOW-MAPPING-UNSUPPORTED"


def test_seconds_round_half_even():
    assert seconds_to_ns(1.0) == 10**9 and seconds_to_ns(2.5e-9) == 2 and seconds_to_ns(3.5e-9) == 4 and seconds_to_ns(0) == 0
    for bad in (-1.0, float("inf"), True, "1"):
        with pytest.raises(ValueError):
            seconds_to_ns(bad)

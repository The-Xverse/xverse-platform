"""S1a-3 (thesis S-D9; ADR-ML3-EVIDENCE-0001 amendment S1a-4): the per-element ``_bounded`` encoding is byte-identical
to the original single ``iterencode`` for every input, refuses exactly the same sizes, and checks the deadline once
per element rather than once per encoder chunk."""

import json
import random

import pytest

from xverse.maestro import evidence
from xverse.maestro.evidence import PublicInputError


def original_bounded(value, maximum, checkpoint):  # the pre-S1a-4 implementation, verbatim
    encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    chunks, size = [], 0
    for part in encoder.iterencode(value):
        checkpoint()
        encoded = part.encode()
        size += len(encoded)
        if size > maximum:
            raise PublicInputError('ML-EVIDENCE-EXPORT-SIZE')
        chunks.append(encoded)
    return b''.join(chunks)


def _value(rng, depth):
    kind = rng.randrange(9 if depth < 4 else 6)
    if kind == 0:
        return None
    if kind == 1:
        return rng.choice([True, False])
    if kind == 2:
        return rng.randint(-2**63, 2**63)
    if kind == 3:
        return rng.choice([0.0, -0.0, 1e-310, 1.5, -2.25e100, 3.141592653589793, 1e16])
    if kind in (4, 5):
        return ''.join(rng.choice(['a', 'Z', '"', '\\', '\n', 'é', ' ', '\U0001f600', '\x00', '/', ' '])
                       for _ in range(rng.randrange(8)))
    if kind == 6:
        return [_value(rng, depth + 1) for _ in range(rng.randrange(5))]
    return {''.join(rng.choice('abcXYZ_é"') for _ in range(rng.randrange(1, 4))): _value(rng, depth + 1)
            for _ in range(rng.randrange(5))}


def _body(rng):
    return dict(schemaVersion='1.0', runId='run-é', lifecycleDigest='sha256:' + 'a' * 64, trustBoundary={'k': [1, 2]},
                annotations=[_value(rng, 1) for _ in range(rng.randrange(30))], publicM3=[_value(rng, 1) for _ in range(5)],
                **({'zEmpty': []} if rng.random() < 0.5 else {}), **({'nested': {'a': [[], {}]}} if rng.random() < 0.5 else {}))


@pytest.mark.parametrize("seed", range(300))
def test_byte_identical_to_the_original_encoding(seed):
    rng = random.Random(seed)
    value = _body(rng) if seed % 3 else _value(rng, 0)
    assert evidence._bounded(value, 1 << 24, lambda: None) == original_bounded(value, 1 << 24, lambda: None)


@pytest.mark.parametrize("seed", range(60))
def test_refuses_exactly_the_same_sizes(seed):
    rng = random.Random(1000 + seed)
    value = _body(rng)
    size = len(original_bounded(value, 1 << 24, lambda: None))
    assert evidence._bounded(value, size, lambda: None) == original_bounded(value, size, lambda: None)
    for cap in (size - 1, max(0, size // 2), 0):
        with pytest.raises(PublicInputError, match='ML-EVIDENCE-EXPORT-SIZE'):
            evidence._bounded(value, cap, lambda: None)
        with pytest.raises(PublicInputError, match='ML-EVIDENCE-EXPORT-SIZE'):
            original_bounded(value, cap, lambda: None)


def test_nan_is_refused_as_before():
    for value in ({'annotations': [float('nan')]}, [float('inf')]):
        with pytest.raises(ValueError):
            evidence._bounded(value, 1 << 20, lambda: None)
        with pytest.raises(ValueError):
            original_bounded(value, 1 << 20, lambda: None)


def test_checkpoint_runs_per_element_and_can_stop_the_encoding():
    events = [{'eventId': f'e{i}', 'payload': 'x' * 200, 'nested': {'k': list(range(20))}} for i in range(800)]
    value = dict(schemaVersion='1.0', annotations=events, publicM3=[])
    calls = []
    evidence._bounded(value, 1 << 24, lambda: calls.append(1))
    original = []
    original_bounded(value, 1 << 24, lambda: original.append(1))
    assert len(calls) <= len(events) + len(value) + 1 < len(original) // 10

    def stop_after(n):
        seen = []

        def check():
            seen.append(1)
            if len(seen) > n:
                raise PublicInputError('ML-TERMINAL-DEADLINE')
        return check
    with pytest.raises(PublicInputError, match='ML-TERMINAL-DEADLINE'):
        evidence._bounded(value, 1 << 24, stop_after(10))

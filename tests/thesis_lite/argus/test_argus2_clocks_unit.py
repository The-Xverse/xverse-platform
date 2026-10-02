"""ARGUS2-SR-004-U: explicit clock domains without ambient clocks (frozen unit cases)."""

from __future__ import annotations

import pytest

from xverse.argus import EvidenceError, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _open(tmp_path, **kwargs):
    return S.open_run(S.run_root(tmp_path), **kwargs)


def test_source_and_observation_clocks_stored_with_declared_units(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection(
            [
                S.observation_record(
                    sourceClock={"domain": "clock.source", "unit": "us", "value": 11},
                    observationClock={"domain": "clock.observation", "unit": "ns", "value": 22},
                )
            ]
        )
    )
    run.finalize()
    record = EvidenceStore.read_run(S.run_root(tmp_path)).records()[0]["observation"]
    assert record["sourceClock"] == {"domain": "clock.source", "unit": "us", "value": 11}
    assert record["observationClock"] == {"domain": "clock.observation", "unit": "ns", "value": 22}


def test_clock_value_without_domain_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"unit": "ns", "value": 1}},
        )
    assert "ARGUS2-INPUT-CLOCK-MISSING" in error.value.codes


def test_clock_value_without_unit_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"domain": "d1", "value": 1}},
        )
    assert "ARGUS2-INPUT-UNIT-MISSING" in error.value.codes


def test_nonfinite_clock_value_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="annotation",
            clocks={"source": {"domain": "d1", "unit": "ns", "value": float("nan")}},
        )
    assert "ARGUS2-INPUT-NONFINITE" in error.value.codes


def test_no_cross_domain_conversion_or_sorting(tmp_path):
    run = _open(tmp_path)
    run.import_observation(
        S.projection(
            [
                S.observation_record(
                    sourceClock={"domain": "clock.a", "unit": "us", "value": 5},
                    observationClock={"domain": "clock.b", "unit": "ns", "value": 5000000},
                ),
                S.observation_record(
                    sourceClock={"domain": "clock.a", "unit": "ns", "value": 1},
                    observationClock={"domain": "clock.b", "unit": "ns", "value": 1},
                ),
            ]
        )
    )
    run.finalize()
    records = EvidenceStore.read_run(S.run_root(tmp_path)).records()
    assert [item["ingestionOrdinal"] for item in records] == [1, 2]
    first = records[0]["observation"]
    second = records[1]["observation"]
    assert first["sourceClock"]["unit"] == "us" and first["sourceClock"]["value"] == 5
    assert second["sourceClock"]["unit"] == "ns" and second["sourceClock"]["value"] == 1
    assert first["observationClock"]["value"] == 5000000


def test_undeclared_clock_mapping_reported_unresolved(tmp_path):
    run = _open(tmp_path, clocks={"declared": {"domain": "d1", "unit": "ns", "value": 0}})
    run.append_event(
        event_id="e1",
        producer_id="p1",
        event_kind="annotation",
        clocks={"source": {"domain": "dZ", "unit": "ns", "value": 1}},
    )
    run.finalize()
    reader = EvidenceStore.read_run(S.run_root(tmp_path))
    assert "ARGUS2-CLOCK-UNRESOLVED" in {item.code for item in reader.diagnostics}


def test_observation_event_requires_declared_clocks(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.append_event(
            event_id="e1",
            producer_id="p1",
            event_kind="observation",
            observation=S.observation_record(),
        )
    assert "ARGUS2-INPUT-CLOCK-MISSING" in error.value.codes


def test_missing_opened_at_clock_is_absent_not_ambient(tmp_path):
    run = S.open_run(S.run_root(tmp_path, "a"))
    manifest = run.finalize()
    assert "openedAt" not in manifest.data
    clock = {"domain": "clock.opened", "unit": "ns", "value": 0}
    run_b = S.open_run(S.run_root(tmp_path, "b"), run_envelope={"openedAt": clock})
    manifest_b = run_b.finalize()
    assert manifest_b.data["openedAt"] == clock

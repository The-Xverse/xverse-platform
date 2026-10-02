"""ARGUS2-SR-008-U: X-COM observation projection import (frozen unit cases)."""

from __future__ import annotations

import socket
import subprocess

import pytest

from xverse.argus import EvidenceError, EvidenceStore

try:
    from tests.thesis_lite.argus import support as S
except ImportError:  # pragma: no cover - copied tests-directory layout
    import sys as _argus2_sys
    from pathlib import Path as _argus2_path

    _argus2_sys.path.insert(0, str(_argus2_path(__file__).resolve().parent))
    import support as S


def _open(tmp_path, name="run", **kwargs):
    return S.open_run(S.run_root(tmp_path, name), **kwargs)


_MAPPED_FIELDS = (
    "contractId",
    "contractVersion",
    "interfaceId",
    "endpointId",
    "schemaId",
    "schemaVersion",
    "interactionKind",
    "origin",
    "sourceClock",
    "observationClock",
    "sequence",
    "correlationId",
    "causationId",
    "routeId",
    "providerId",
    "sourcePayloadSize",
    "providerOutcome",
    "payloadViewState",
    "payloadSchemaState",
    "visibleBytesHex",
    "visibleByteCount",
    "tapId",
    "counters",
)


def test_real_owned_projection_preserves_every_accessor_value(tmp_path):
    produced = S.run_producer()
    records = produced["projection"]["records"]
    run = _open(tmp_path)
    run.import_observation(produced["projection"])
    run.import_snapshot(produced["snapshot"])
    run.finalize()
    stored = [item["observation"] for item in EvidenceStore.read_run(S.run_root(tmp_path)).records() if item["eventKind"] == "observation"]
    assert len(stored) == len(records)
    for source, imported in zip(records, stored):
        for field in _MAPPED_FIELDS:
            assert imported[field] == source[field], field


def test_projection_requires_upstream_contract_identity(tmp_path):
    run = _open(tmp_path)
    envelope = S.projection([S.observation_record()])
    del envelope["projectionVersion"]
    del envelope["upstreamContractVersion"]
    with pytest.raises(EvidenceError) as error:
        run.import_observation(envelope)
    assert "ARGUS2-INPUT-PROJECTION-INCOMPLETE" in error.value.codes


def test_unknown_projection_major_version_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.import_observation(S.projection([S.observation_record()], projectionVersion="2.0"))
    assert "ARGUS2-SCHEMA-MAJOR-UNSUPPORTED" in error.value.codes


def test_narrower_gateway_record_rejected_as_full_projection(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.import_observation(S.projection([S.gateway_record()]))
    assert "ARGUS2-INPUT-PROJECTION-INCOMPLETE" in error.value.codes


def test_import_exposes_no_callback_hub_or_delivery_authority(tmp_path):
    run = _open(tmp_path)
    run.import_observation(S.projection([S.observation_record()]))
    forbidden = ("callback", "hub", "deliver", "tap_handle", "provider_handle", "dispatch")
    names = [name.lower() for name in dir(run)]
    assert not any(any(token in name for token in forbidden) for name in names)


def test_provider_outcome_is_not_promoted_to_experiment_validity(tmp_path):
    run = _open(
        tmp_path,
        obligations=[{"obligationId": "o1", "kind": "no-known-loss", "required": True}],
    )
    run.import_observation(S.projection([S.observation_record(providerOutcome="accepted")]))
    manifest = run.finalize()
    stored = [item["observation"] for item in EvidenceStore.read_run(S.run_root(tmp_path)).records()][0]
    assert stored["providerOutcome"] == "accepted"
    assert manifest.evidence_status == "complete"


def test_visible_byte_count_mismatch_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.import_observation(
            S.projection(
                [
                    S.observation_record(
                        sourcePayloadSize=3,
                        visibleBytesHex="00ff",
                        visibleByteCount=3,
                    )
                ]
            )
        )
    assert "ARGUS2-INPUT-PAYLOAD-LENGTH" in error.value.codes


def test_payload_schema_state_other_than_undecoded_rejected(tmp_path):
    run = _open(tmp_path)
    with pytest.raises(EvidenceError) as error:
        run.import_observation(
            S.projection([S.observation_record(payloadSchemaState="decoded")])
        )
    assert "ARGUS2-SCHEMA-UNKNOWN-FIELD" in error.value.codes


def test_unknown_nested_projection_field_rejected(tmp_path):
    run = _open(tmp_path)
    record = S.observation_record()
    record["counters"] = dict(record["counters"], unexpected=1)
    with pytest.raises(EvidenceError) as error:
        run.import_observation(S.projection([record]))
    assert "ARGUS2-SCHEMA-UNKNOWN-FIELD" in error.value.codes


def test_projection_record_missing_required_identity_rejected(tmp_path):
    run = _open(tmp_path)
    record = S.observation_record()
    del record["contractId"]
    del record["schemaId"]
    with pytest.raises(EvidenceError) as error:
        run.import_observation(S.projection([record]))
    assert "ARGUS2-INPUT-IDENTITY-MISSING" in error.value.codes


def test_import_attaches_no_live_tap_and_performs_no_io(tmp_path, monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("no socket or subprocess access is permitted")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    run = _open(tmp_path)
    run.import_observation(S.projection([S.observation_record()]))
    run.finalize()
    assert len(EvidenceStore.read_run(S.run_root(tmp_path)).records()) == 1


def test_projection_roundtrip_preserves_values_exactly(tmp_path):
    source = S.observation_record(correlationId="correlation.alpha", causationId="causation.alpha")
    run = _open(tmp_path)
    run.import_observation(S.projection([source]))
    run.finalize()
    document = __import__("json").loads(EvidenceStore.read_run(S.run_root(tmp_path)).export_json())
    stored = document["records"][0]["observation"]
    for field in _MAPPED_FIELDS:
        assert stored[field] == source[field], field

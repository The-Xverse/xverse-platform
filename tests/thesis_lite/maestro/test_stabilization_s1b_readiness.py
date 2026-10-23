"""S1b readiness, evidence, coverage and privacy (FR-010, FR-011): the nonce marker through real stacks.

Broker stacks use ``test_run_broker.broker_stack`` with the actual v0.2 catalog payload and an admitted
collection (``test_collection_runtime.configure``), whose source root contains each marker unit's cwd.
Coverage acceptance uses the synthetic ``test_coverage.Fixture`` and is labelled as such.
Design: ``design-stabilization-s1b.md``.
"""

import json
import os
from pathlib import Path
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.coverage import CoverageAdmission, _payload, canonical, verify_closed
from xverse.maestro.owner import OwnerError
from xverse.maestro.probe_identity import READINESS_PROBES
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.teardown import ReverseTeardown
from .test_stabilization_s1b_broker import declare, private, started
from .test_stabilization_s1b_native import flood
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline, launch_stack as launch_stack

MARKER = dict(condition="nonce-marker", cwd="sink", observe_timeout=1.5)


def window(monkeypatch, seconds=1.5):
    """The readiness window W = min(policy timeout, observe timeout); the fixture's cadence is kept."""
    from . import test_run_broker

    monkeypatch.setattr(test_run_broker, "ProbePolicy",
                        lambda unit, freshness, cadence, _timeout: ProbePolicy(unit, freshness, cadence, seconds))


def marker_stack(request, monkeypatch, mode):
    from .test_collection_runtime import configure

    saved = configure(monkeypatch)
    window(monkeypatch)
    declare(monkeypatch, {"sink-binding": dict(MARKER, mode=mode)})
    return request.getfixturevalue("broker_stack"), saved


def annotations(work, unit):
    events = EvidenceStore.read_run(work.parent / "argus").records()
    return [e["extensions"]["xverse.maestro"] for e in events
            if e.get("extensions", {}).get("xverse.maestro", {}).get("unitId") == unit
            and e["extensions"]["xverse.maestro"]["action"] in ("probe", "ready", "health", "health-loss")]


def test_identities_are_the_admitted_pair():
    assert READINESS_PROBES == ("running", "nonce-marker")


def test_marker_readiness_records_the_declared_identity_and_health_stays_running(request, monkeypatch):
    stack, _ = marker_stack(request, monkeypatch, "marker")
    broker, facade, client, work = stack
    source, sink = broker.owner._prepared.resource_order
    issuer = broker.issuer(sink)
    assert issuer.readiness_probe == "nonce-marker" and broker.issuer(source).readiness_probe == "running"
    units = {u["unitId"]: u for u in client.coverage.data(client.coverage_digest)["units"]}
    assert units[sink]["readinessProbe"] == "nonce-marker" and "readinessProbe" not in units[source]
    end = stage_all(stack)
    assert facade.start(source, broker.issuer(source).recipe.descriptor, broker.connection, end).probe_id == "running"
    ready = facade.start(sink, issuer.recipe.descriptor, broker.connection, end)
    assert ready.ready and ready.probe_id == "nonce-marker"
    challenge = (work / "sink" / ".xverse-ready" / "challenge").read_bytes()
    assert (work / "sink" / ".xverse-ready" / "ready").read_bytes() == challenge
    health = facade.check_unit_health(sink, deadline(1))
    assert health.ready and health.probe_id == "running"
    rows = annotations(work, sink)
    assert [(r["action"], r["probeId"]) for r in rows] == [
        ("probe", "nonce-marker"), ("ready", "nonce-marker"), ("health", "running")]
    assert all(r["probeId"] == "running" for r in annotations(work, source))
    ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))


def test_marker_late_within_the_window_is_ready_on_a_spaced_attempt(request, monkeypatch):
    stack, _ = marker_stack(request, monkeypatch, "marker-late")
    broker, facade, _, work = stack
    source, sink = broker.owner._prepared.resource_order
    end = stage_all(stack)
    facade.start(source, broker.issuer(source).recipe.descriptor, broker.connection, end)
    ready = facade.start(sink, broker.issuer(sink).recipe.descriptor, broker.connection, end)
    assert ready.ready and ready.probe_id == "nonce-marker"
    rows = annotations(work, sink)
    outcomes = [(r["action"], r["outcome"]) for r in rows]
    assert outcomes[0] == ("probe", "failed") and outcomes[-2:] == [("probe", "succeeded"), ("ready", "succeeded")]
    assert len([r for r in rows if r["action"] == "probe"]) <= 3
    ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))


def test_marker_that_never_appears_is_not_ready_after_three_spaced_attempts(request, monkeypatch):
    stack, _ = marker_stack(request, monkeypatch, "marker-never")
    broker, facade, _, work = stack
    source, sink = broker.owner._prepared.resource_order
    end = stage_all(stack)
    facade.start(source, broker.issuer(source).recipe.descriptor, broker.connection, end)
    began = time.monotonic()
    with pytest.raises(ValueError, match="ML-PROBE-NOT-READY"):
        facade.start(sink, broker.issuer(sink).recipe.descriptor, broker.connection, end)
    assert time.monotonic() - began >= 1.0  # attempts at t0, t0 + W/3 and t0 + 2W/3 with W = 1.5 s
    events = [e for e in EvidenceStore.read_run(work.parent / "argus").records()
              if e.get("extensions", {}).get("xverse.maestro", {}).get("unitId") == sink
              and e["extensions"]["xverse.maestro"]["action"] == "probe"]
    assert [(e["extensions"]["xverse.maestro"]["outcome"], e["extensions"]["xverse.maestro"]["probeId"])
            for e in events] == [("failed", "nonce-marker")] * 3
    times = [e["clocks"]["host"]["value"] for e in events]
    assert all(b - a >= 0.45 for a, b in zip(times, times[1:]))
    assert broker.owner.latch.cancelled


@pytest.mark.parametrize("mode", ["no-collection", "shared-cwd", "stale", "outside-root", "unsupported"])
def test_marker_admission_fails_closed(request, monkeypatch, tmp_path, mode):
    from .test_collection_runtime import configure

    controls, code = dict(MARKER, mode="marker"), {
        "no-collection": "ML-RUN-PROBE-ROOT", "shared-cwd": "ML-RUN-PROBE-CWD", "stale": "ML-RUN-PROBE-STALE",
        "outside-root": "ML-RUN-PROBE-ROOT", "unsupported": "ML-RUN-PROBE-UNSUPPORTED"}[mode]
    if mode not in ("no-collection", "unsupported"):  # an admitted coverage refuses it earlier (ML-COVERAGE-PROBE)
        configure(monkeypatch)
    if mode == "shared-cwd":
        controls.pop("cwd")
    elif mode == "stale":
        controls["stale"] = True
    elif mode == "outside-root":
        controls["cwd"] = str(private(tmp_path, "outside-root"))
    elif mode == "unsupported":
        controls["condition"] = "http-ok"
    declare(monkeypatch, {"sink-binding": controls})
    with pytest.raises(OwnerError, match=code):
        request.getfixturevalue("broker_stack")


def test_lc09_refuses_every_s1b_declaration(request, monkeypatch):
    declare(monkeypatch, {"source-binding": dict(stop=1), "sink-binding": dict(stop=1)})
    owner, client, manager, config, work, launch, gate = request.getfixturevalue("launch_stack")
    with pytest.raises(ValueError, match="ML-LAUNCH-CONTROL-UNSUPPORTED"):
        launch()


def test_privacy_canary_stderr_content_and_path_never_reach_public_outputs(request, monkeypatch, tmp_path):
    from .test_collection_runtime import configure

    token = "s1b-private-canary-" + os.urandom(8).hex()
    errors = private(tmp_path, token)
    configure(monkeypatch)
    declare(monkeypatch, {"sink-binding": dict(stderr=4096, mode="stderr-flood")}, stderr={"sink-binding": str(errors)})
    stack = request.getfixturevalue("broker_stack")
    broker, facade, client, work = stack
    started(stack)
    path = errors / "stderr-g1"
    end = time.monotonic() + 1.5
    while not (path.exists() and path.stat().st_size == 16384):
        assert time.monotonic() < end
        time.sleep(0.005)
    projection = broker.public_projection(deadline(1))
    ReverseTeardown(facade, per_unit_seconds=0.8).run(deadline(2))
    receipt = client.collect_outputs(broker, deadline(2))
    assert path.read_bytes() == flood(4096) and broker.issuer(broker.owner._prepared.resource_order[-1])._stop_ack.state & 4096
    content = flood()
    needles = [content[:128], content[2000:2128], content[4000:4096], token.encode(), str(errors).encode()]
    from xverse_xdl.lifecycle import FileEvidenceJournal

    public = [projection.public_bytes, receipt.public_bytes,
              canonical(list(FileEvidenceJournal(work.parent / "m3.jsonl").public_records()))]
    scanned = 0
    for root, dirs, files in os.walk(tmp_path):
        if Path(root) == errors:
            dirs[:] = []
            continue
        for name in files:
            data = (Path(root) / name).read_bytes()
            scanned += 1
            assert not any(n in data for n in needles), Path(root) / name
    for data in public:
        assert not any(n in data for n in needles)
    assert scanned > 5 and token not in str(EvidenceStore.read_run(work.parent / "argus").records())


# ---- coverage acceptance (synthetic, labelled) ------------------------------------------------------

def synthetic(tmp_path, monkeypatch, *, matching):
    """test_coverage.Fixture with unit a admitted as nonce-marker; its unit probe/ready annotations carry
    the declared identity when `matching`, and the fixture's `running` otherwise."""
    from . import test_coverage as tc

    chosen = {}
    original_admit = tc.admit_coverage

    def admit(*args, **kwargs):
        body = json.loads(original_admit(*args, **kwargs).public_bytes)
        body["units"][0]["readinessProbe"] = "nonce-marker"
        chosen["unit"] = body["units"][0]["unitId"]
        return CoverageAdmission(canonical(body))

    original_open = EvidenceStore.open_run.__func__

    def open_run(cls, *args, **kwargs):
        writer = original_open(cls, *args, **kwargs)
        append = writer.append_event

        def rewritten(**fields):
            p = fields["extensions"].get("xverse.maestro", {})
            if (matching and p.get("unitId") == chosen["unit"] and p.get("scope") == "unit"
                    and p.get("action") in ("probe", "ready")):
                p["probeId"] = "nonce-marker"
            return append(**fields)

        writer.append_event = rewritten
        return writer

    monkeypatch.setattr(tc, "admit_coverage", admit)
    monkeypatch.setattr(EvidenceStore, "open_run", classmethod(open_run))
    return tc.Fixture(tmp_path), chosen["unit"]


@pytest.mark.parametrize("matching", [True, False])
def test_coverage_ready_requires_the_declared_readiness_probe(tmp_path, monkeypatch, matching):
    from .test_coverage import row

    f, unit = synthetic(tmp_path, monkeypatch, matching=matching)
    f.close()
    report = verify_closed(f.admission, f.root, expected_admission_digest=f.admission.digest).coverage.report()
    if matching:
        assert report["overallStatus"] == "complete" and report["normalRecordStatus"] == "complete"
        assert row(report, "ready", unit, 1)["status"] == "satisfied"
    else:
        assert report["overallStatus"] != "complete" and report["normalRecordStatus"] != "complete"


def test_coverage_payload_identity_rules(tmp_path, monkeypatch):
    f, unit = synthetic(tmp_path, monkeypatch, matching=True)
    other = f.b
    by = {(e["extensions"]["xverse.maestro"]["unitId"], e["extensions"]["xverse.maestro"]["action"]): e
          for e in f.events if e["extensions"]["xverse.maestro"]["action"] in ("probe", "ready", "health")}
    assert _payload(by[unit, "ready"], f.ad) is not None and _payload(by[unit, "health"], f.ad) is not None
    assert _payload(by[other, "ready"], f.ad) is not None
    forged = json.loads(json.dumps(by[unit, "health"]))
    forged["extensions"]["xverse.maestro"]["probeId"] = "nonce-marker"  # health is liveness-only
    assert _payload(forged, f.ad) is None
    forged = json.loads(json.dumps(by[other, "ready"]))
    forged["extensions"]["xverse.maestro"]["probeId"] = "nonce-marker"  # an undeclared unit stays running
    assert _payload(forged, f.ad) is None
    f.writer.abort(reason="Synthetic test completed")


def test_coverage_admission_rejects_an_unadmitted_readiness_probe(tmp_path, monkeypatch):
    f, _ = synthetic(tmp_path, monkeypatch, matching=True)
    f.writer.abort(reason="Synthetic test completed")
    for value in ("running", "http-ok", 1):
        body = json.loads(f.admission.public_bytes)
        body["units"][0]["readinessProbe"] = value
        with pytest.raises(ValueError):
            admission = CoverageAdmission(canonical(body))
            admission.data(admission.digest)

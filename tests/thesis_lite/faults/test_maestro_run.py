"""U-ADM-01…03 and the end-to-end fault run on the native Maestro stack (thesis V06, V08, V09, V10 inputs).

The projection admits only statically resolvable schedules and carries them into the prepared
lifecycle; a fault-less plan keeps its Phase 3 canonical bytes. The run tests reuse the shared
dispatcher fixture (real persistence worker, broker, launcher helpers and owned children): faults
on the flow relay, the sensor relay and a frozen unit complete cleanly with their Argus chains;
a crash with ``recovery: manual`` ends the run as a documented failure attributed to the fault.
Worker-side code is involved: run with one installed version (finding 442; venv built from this tree).
"""

from __future__ import annotations

import copy
import time

import pytest

from xverse.argus import EvidenceStore
from xverse.faults.evidence import closure_report, reconstruct
from xverse.maestro import PreparationError, prepare

from ..maestro import test_launcher, test_lazy_dispatcher, test_shared_dispatcher
from ..maestro.test_lazy_dispatcher import run
from ..maestro.test_preparation import PIN, compiled, documents as maestro_documents
from ..maestro.test_run_broker import broker_stack as broker_stack  # noqa: F401 - fixture re-export
from ..maestro.test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary  # noqa: F401
from ..maestro.test_affa_native import authority_binary as authority_binary  # noqa: F401
from ..maestro.test_boundary import environment as environment  # noqa: F401
from ..maestro.test_launcher import binaries as binaries  # noqa: F401
from .support import fault, parameter, with_sensor


def _docs_with(faults):
    docs = with_sensor(maestro_documents())
    docs["scenario.json"]["spec"]["faults"] = copy.deepcopy(faults)
    return docs


def test_u_adm_01_resolvable_schedule_is_prepared():
    faults = [fault("f-s", "stale", "sample-flow", at=1, duration=1), fault("f-c", "crash", "source-instance", at=2, duration=0, recovery="manual")]
    result, resources = compiled(_docs_with(faults))
    prepared = prepare(result, resources, provider_descriptors=(PIN,))
    assert [item["faultId"] for item in prepared.faults] == ["f-s", "f-c"]
    plain, plain_resources = compiled(_docs_with([]))
    baseline = prepare(plain, plain_resources, provider_descriptors=(PIN,))
    assert baseline.faults == () and baseline.lifecycle_digest != prepared.lifecycle_digest
    assert b'"faults"' not in baseline.canonical_bytes and b'"faults"' in prepared.canonical_bytes


def test_u_adm_02_unresolvable_schedule_is_rejected():
    for faults, code in (
        ([fault("f-x", "meteor", "sample-flow", at=1, duration=1)], "XVERSE-FAULT-KIND"),
        ([fault("f-c", "crash", "source-instance", at=1, duration=0, recovery="automatic")], "XVERSE-FAULT-RECOVERY"),
        ([fault("f-h", "stale", "sample-flow", at=50000, duration=1)], "XVERSE-FAULT-HORIZON"),
    ):
        result, resources = compiled(_docs_with(faults))
        with pytest.raises(PreparationError) as caught:
            prepare(result, resources, provider_descriptors=(PIN,))
        assert "ML-UNSUPPORTED" in str(caught.value) and code in str(caught.value)


def test_u_adm_03_faultless_plans_unchanged():
    result, resources = compiled()
    prepared = prepare(result, resources, provider_descriptors=(PIN,))
    assert prepared.faults == () and prepared.fault_seed == 0 and b'"faults"' not in prepared.canonical_bytes


def _scheduled_with_faults(request, monkeypatch, faults):
    base = test_launcher.documents

    def documents():
        docs = with_sensor(base())
        docs["scenario.json"]["spec"]["faults"] = copy.deepcopy(faults)
        return docs

    monkeypatch.setattr(test_launcher, "documents", documents)
    # Fault statements are extra bounded round trips inside the active window: use the fixture's
    # paused variant (8 s window instead of 4.8 s) so the window holds them under host load.
    shared = test_shared_dispatcher.scheduled
    monkeypatch.setattr(test_shared_dispatcher, "scheduled",
                        lambda request, monkeypatch, **kw: shared(request, monkeypatch, pauses=2, **kw))
    return test_lazy_dispatcher.scheduled(request, monkeypatch)


def _events(stack):
    return EvidenceStore.read_run(stack[3].parent / "argus").records()


def test_fault_run_relays_and_freeze_complete(request, monkeypatch):
    """stale on the flow relay, sensorDropout on the sensor relay and a freeze/thaw on the sink unit."""

    faults = [
        fault("f-stale", "stale", "sample-flow", at=1, duration=1),
        fault("f-drop", "sensorDropout", "front-sensor", at=1, duration=1),
        fault("f-freeze", "freeze", "sink-instance", at=1, duration=1),
    ]
    stack, _, driver = _scheduled_with_faults(request, monkeypatch, faults)
    result = run(driver)
    assert result.execution_succeeded and result.diagnostic is None, result.diagnostic
    assert driver._faults is not None and driver._faults.outcomes == {"fault:f-stale": "cleared", "fault:f-drop": "cleared", "fault:f-freeze": "cleared"}
    chains = reconstruct(_events(stack))
    report = closure_report(chains)
    assert set(chains) == {"f-stale", "f-drop", "f-freeze"} and report["complete"], report
    sink = stack[2]
    assert sink.rpc_failure is None


def _unit(driver, element):
    return f"{driver.prepared.units[0].unit_id.split('#')[0]}#componentInstances/{element}"


def _failure_events(stack, diagnostic):
    return [e for e in _events(stack) if e.get("extensions", {}).get("xverse.maestro", {}).get("diagnosticCode") == diagnostic]


@pytest.mark.parametrize("tick", [1, 2])
def test_fault_run_manual_crash_is_a_documented_failure_of_the_unit(request, monkeypatch, tick):
    """H1: an applied crash with recovery: manual ends the run at once as a documented failure of the
    crashed unit, journaled and in Argus, whether or not a health obligation of the unit follows."""

    faults = [fault("f-crash", "crash", "source-instance", at=tick, duration=0, recovery="manual")]
    stack, _, driver = _scheduled_with_faults(request, monkeypatch, faults)
    result = run(driver)
    assert not result.execution_succeeded
    assert result.diagnostic == "ML-SCHEDULE-TERMINATED-BY-FAULT", result.diagnostic
    unit = _unit(driver, "source-instance")
    assert driver.facade._terminated.get(unit) == "fault:f-crash"
    failures = _failure_events(stack, "ML-SCHEDULE-TERMINATED-BY-FAULT")
    assert failures and failures[0]["extensions"]["xverse.maestro"]["unitId"] == unit
    chains = reconstruct(_events(stack))
    assert chains["f-crash"].applied and chains["f-crash"].status == "closed"  # statements were sent
    assert chains["f-crash"].phases[-1] == ("outcome", "applied")
    finals = [d for d in driver._faults.decisions if d.phase == "final"]
    assert [(d.entry_id, d.outcome, d.diagnostic) for d in finals] == [("fault:f-crash", "applied", "XVERSE-FAULT-ENDED-RUN")]


def test_fault_run_failure_thaws_an_active_freeze(request, monkeypatch):
    """H2: when the run fails while a freeze is active, the scheduler is cancelled first: the frozen
    unit is thawed (clear decision) and every entry gets exactly one final outcome."""

    faults = [
        fault("f-freeze", "freeze", "sink-instance", at=1, duration=2),
        fault("z-crash", "crash", "source-instance", at=1, duration=0, recovery="manual"),
    ]
    stack, _, driver = _scheduled_with_faults(request, monkeypatch, faults)
    result = run(driver)
    assert result.diagnostic == "ML-SCHEDULE-TERMINATED-BY-FAULT"
    clears = [d for d in driver._faults.decisions if d.entry_id == "fault:f-freeze" and d.phase == "clear"]
    assert clears and clears[0].outcome == "cleared"
    finals = sorted((d.entry_id, d.outcome) for d in driver._faults.decisions if d.phase == "final")
    assert finals == [("fault:f-freeze", "cancelled"), ("fault:z-crash", "applied")]
    assert _unit(driver, "sink-instance") not in driver.facade._suspended
    report = closure_report(reconstruct(_events(stack)))
    assert report["complete"], report  # both chains closed on the failure path


def test_run_authority_refuses_faults_before_release(request, monkeypatch):
    """M2: the native authority refuses a fault on a staged but unreleased generation (a thaw there
    would undo the staging freeze); the run then completes normally."""

    stack, _, driver = test_shared_dispatcher.scheduled(request, monkeypatch)
    broker = stack[0]
    for issuer in broker.issuers:
        # within the lease: the authority's lease is short before the run renews it
        assert issuer.fault(issuer._handle, "thaw", test_launcher.deadline(0.3)) == (False, 6)
        assert issuer.fault(issuer._handle, "kill", test_launcher.deadline(0.3)) == (False, 6)
    result = test_shared_dispatcher.run(driver)
    assert result.execution_succeeded, result.diagnostic


def test_u_adm_03b_faultless_digest_equals_platform_main():
    """U-ADM-03: a fault-less plan prepared by this candidate has the same lifecycle digest as the
    accepted platform main (read-only sibling checkout), so Phase 3 plans are unchanged."""

    import subprocess, sys
    from pathlib import Path

    main = Path("/home/jefferson/xverse-platform")
    if not (main / "src" / "xverse" / "maestro" / "projection.py").is_file():
        pytest.skip("platform main checkout not available")
    script = (
        "import sys; sys.path[:0] = [%r, %r];"
        "from tests.thesis_lite.maestro.test_preparation import prepared;"
        "print(prepared().lifecycle_digest)" % (str(main / "src"), str(main))
    )
    expected = subprocess.check_output([sys.executable, "-I", "-c", script], text=True, cwd=str(main)).strip()
    result, resources = compiled()
    assert prepare(result, resources, provider_descriptors=(PIN,)).lifecycle_digest == expected

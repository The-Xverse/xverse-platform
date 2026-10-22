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


def test_fault_run_crash_before_a_health_obligation_is_attributed(request, monkeypatch):
    """A crash applied at tick 1, before observe-source runs at tick 1, ends the run as a documented
    failure whose diagnostic names the fault, not an anonymous health loss."""

    faults = [fault("f-crash", "crash", "source-instance", at=1, duration=0, recovery="manual")]
    stack, _, driver = _scheduled_with_faults(request, monkeypatch, faults)
    result = run(driver)
    assert not result.execution_succeeded
    assert result.diagnostic == "ML-PROBE-TERMINATED-BY-FAULT", result.diagnostic
    assert driver.facade._terminated.get(_unit(driver, "source-instance")) == "fault:f-crash"
    applied = [d for d in driver._faults.decisions if d.entry_id == "fault:f-crash" and d.phase == "apply"]
    assert applied and applied[0].outcome == "applied" and applied[0].tick == 1
    chains = reconstruct(_events(stack))
    assert chains["f-crash"].applied


def test_fault_run_crash_before_stop_completes_with_the_termination_recorded(request, monkeypatch):
    """A crash applied at tick 2, after the last health obligation of the unit, leaves the run to
    complete through the ordinary stop/cleanup of a reaped leader; the fault is cleared by
    definition and the termination stays attributed in the facade and the Argus chain."""

    faults = [fault("f-crash", "crash", "source-instance", at=2, duration=0, recovery="manual")]
    stack, _, driver = _scheduled_with_faults(request, monkeypatch, faults)
    result = run(driver)
    assert result.execution_succeeded and result.diagnostic is None, result.diagnostic
    assert driver._faults.outcomes == {"fault:f-crash": "cleared"}
    assert driver.facade._terminated.get(_unit(driver, "source-instance")) == "fault:f-crash"
    report = closure_report(reconstruct(_events(stack)))
    assert report["complete"] and report["statuses"] == {"f-crash": "closed"}

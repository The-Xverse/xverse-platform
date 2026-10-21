"""DV09-P failed lifecycle on the actual native stack (increment19, findings 437, 439-444).

The declared sink workload dies after its start step completed (an external crash written to its
own cgroup.kill by the test, never a runtime action). The run must not succeed, and the closed
evidence is then reconstructed independently: lifecycle completeness is assessed apart from the
execution outcome. Worker-side code is involved, so run with one installed version (finding 442).
"""
import json
import os
import time

import pytest

from xverse.argus import EvidenceStore
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_terminal_runtime import scheduled, run, verify
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


def failed_run(request, monkeypatch):
    stack, _, driver = scheduled(request, monkeypatch)
    broker, facade, client, work = stack
    source, leaf = driver.prepared.resource_order
    killed, statement = [], driver._statement

    def crash_sink_after_start(kind, step, **kw):
        response = statement(kind, step, **kw)
        if kind == "step-complete" and step.step_id == "start-sink" and not killed:
            descriptor = broker.issuer(leaf)._image.admission.descriptor
            fd = broker.session.boundaries._entries[descriptor.key].fd
            control = os.open("cgroup.kill", os.O_WRONLY | os.O_CLOEXEC, dir_fd=fd)
            try:
                os.write(control, b"1")
            finally:
                os.close(control)
            killed.append(time.monotonic())
        return response

    monkeypatch.setattr(driver, "_statement", crash_sink_after_start)
    result = run(driver)
    from xverse.maestro import coverage as coverage_module
    invalid, assess = [], coverage_module._Assessment.assess

    def observed_assess(self):
        value = assess(self)
        invalid.extend((self.payloads.get(eid, {}).get("action"), self.payloads.get(eid, {}).get("outcome"), state)
                       for eid, state in self.valid.items() if state != "satisfied")
        return value

    monkeypatch.setattr(coverage_module._Assessment, "assess", observed_assess)
    checked = verify(client, work.parent / "argus")
    facts = result.terminal.public_data() if result.terminal is not None else None
    path = work.parent / "argus" / "lifecycle-coverage.json"
    coverage = json.loads(path.read_text()) if path.exists() else {}
    open_rows = [{k: r.get(k) for k in ("obligationId", "status", "diagnostic")}
                 for r in coverage.get("rows", []) if r.get("status") not in ("satisfied", "not-applicable")]
    events = EvidenceStore.read_run(work.parent / "argus").records()
    leaf_events = [(p.get("action"), p.get("outcome"), p.get("handleRef") is not None)
                   for p in (e.get("extensions", {}).get("xverse.maestro", {}) for e in events)
                   if p.get("unitId") == leaf and p.get("scope") == "unit" and p.get("action") != "disposition"]
    print("DV09-P1", json.dumps(dict(killed=bool(killed), succeeded=result.execution_succeeded,
                                     terminal=result.terminal_recorded, diagnostic=result.diagnostic,
                                     rpc_failure=str(client.rpc_failure), invalid=invalid, open_rows=open_rows,
                                     statuses={k: v for k, v in coverage.items() if k.endswith("Status")},
                                     report=facts and facts["report"], offline_complete=checked.complete,
                                     leaf_events=leaf_events,
                                     m3=[(r.kind, r.status) for r in FileEvidenceJournal(work.parent / "m3.jsonl").records]),
                                default=str))
    assert killed
    assert not result.execution_succeeded and result.terminal_recorded, result.diagnostic
    assert result.cleanup.unit_cleanup_complete
    return result, checked, facts, coverage, open_rows, invalid


def test_actual_native_failed_lifecycle_records_are_complete_apart_from_the_execution_outcome(request, monkeypatch):
    """F-10 (findings 439-443): every lifecycle obligation of the failed run is satisfied."""
    result, checked, facts, coverage, open_rows, invalid = failed_run(request, monkeypatch)
    assert not invalid and not open_rows, (invalid, open_rows)
    assert coverage["normalRecordStatus"] == "complete"
    assert facts["report"]["normalComplete"] and facts["report"]["requiredRowsSatisfied"]
    assert facts["report"]["blockers"] == ["terminal-outcome"]


@pytest.mark.xfail(strict=True, reason="DIVERGENT D-09 (finding 444): writer is aborted, not closed, after a failed "
                                       "execution, so offline overall stays incomplete; author ruling at T01")
def test_actual_native_failed_lifecycle_is_overall_complete_per_design_branch(request, monkeypatch):
    """Design branch normal-documented-failure: overall complete, execution failed."""
    result, checked, facts, coverage, open_rows, invalid = failed_run(request, monkeypatch)
    assert checked.complete, checked

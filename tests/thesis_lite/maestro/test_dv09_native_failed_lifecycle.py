"""DV09-P failed lifecycle on the actual native stack (increment19, finding 437).

The declared sink workload dies after its start step completed (an external crash written to its
own cgroup.kill by the test, never a runtime action). The run must not succeed, and the closed
evidence is then reconstructed independently: whether every lifecycle obligation is satisfied is
assessed apart from the execution outcome, and the observed result is recorded either way.
"""
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


@pytest.mark.xfail(strict=True, reason="F-10 (finding 439): health-loss/unknown source rejected by coverage.py:531")
def test_actual_native_failed_lifecycle_is_assessed_apart_from_its_execution_outcome(request, monkeypatch):
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
    checked = verify(client, work.parent / "argus")
    facts = result.terminal.public_data() if result.terminal is not None else None
    events = EvidenceStore.read_run(work.parent / "argus").records()
    dispositions = {(p.get("stepId") or p.get("unitId"), p.get("scope")): p.get("disposition")
                    for p in (e.get("extensions", {}).get("xverse.maestro", {}) for e in events)
                    if p.get("action") == "disposition"}
    print("DV09-P1", dict(killed=bool(killed), succeeded=result.execution_succeeded, terminal=result.terminal_recorded,
                          diagnostic=result.diagnostic, complete=checked.complete,
                          blockers=getattr(checked, "blockers", None), report=facts and facts["report"],
                          dispositions=dispositions,
                          m3=[(r.kind, r.status) for r in FileEvidenceJournal(work.parent / "m3.jsonl").records]))
    import json
    coverage = json.loads((work.parent / "argus" / "lifecycle-coverage.json").read_text())
    print("DV09-P1-ROWS", json.dumps(dict(
        statuses={k: v for k, v in coverage.items() if k.endswith("Status")},
        open_rows=[{k: r.get(k) for k in ("obligationId", "obligationClass", "status", "required", "applicable", "diagnostic")}
                   for r in coverage.get("rows", []) if r.get("status") not in ("satisfied", "not-applicable")])))
    sink_events = [(p.get("action"), p.get("outcome"), [r.get("sequence") for r in p.get("sourceRefs", []) if r.get("kind") == "m3-record"])
                   for p in (e.get("extensions", {}).get("xverse.maestro", {}) for e in events)
                   if p.get("unitId") == leaf and p.get("scope") == "unit" and p.get("action") != "disposition"]
    m3_sink = [(i, r.kind, r.status, r.action_id) for i, r in enumerate(FileEvidenceJournal(work.parent / "m3.jsonl").records)
               if r.details.get("maestroUnitId") == leaf]
    print("DV09-P1-SINK", json.dumps(dict(events=sink_events, m3=m3_sink), default=str))
    assert killed
    assert not result.execution_succeeded and result.terminal_recorded, result.diagnostic
    assert result.cleanup.unit_cleanup_complete
    # The assessment is recorded, not forced: finding 437 states the expected value and its reading.
    assert checked.complete, checked
    assert facts["report"]["entry"] is not None

"""DV04-N restarted prerequisite on the native stack (increment19, finding 450).

The source is restarted to generation 2 and is then observed not running, while its earlier ready
observation is still cached. The leaf's generation-2 start must be blocked: the release guard
queries every prerequisite fresh through its current binding, so old readiness is not inherited.
"""
from dataclasses import replace
import time

import pytest

from xverse.argus import EvidenceStore
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.run_broker import RunUnitIssuer
from xverse.maestro.run_closure import RunClosure
from xverse_xdl.lifecycle import FileEvidenceJournal
from .test_generation_claim import ready, release
from .test_generation_dependents import advance
from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def test_dependent_start_is_blocked_by_a_restarted_prerequisite_that_is_not_running(request, monkeypatch):
    stack, controller, leaf, _ = ready(request, monkeypatch)
    broker, facade, client, work = stack
    source = broker.owner._prepared.resource_order[0]
    release(controller, leaf)
    release(controller, source)
    advance(stack, controller, source)
    cached = facade._observations.get(source)
    observe, lost = RunUnitIssuer.observe, []

    def not_running(self, handle, until):
        value = observe(self, handle, until)
        if self.unit_id == source and self.recipe.descriptor.generation == 2:
            lost.append(time.monotonic())
            return replace(value, leader_alive=False)  # the running property derives from the leader (finding 451)
        return value

    monkeypatch.setattr(RunUnitIssuer, "observe", not_running)
    old = broker.issuer(leaf).recipe.descriptor
    descriptor = BoundaryDescriptor(old.run_id, leaf, old.generation + 1,
                                    'explicit-' + str(broker.issuer(leaf).slot) + '-' + str(old.generation + 1),
                                    broker.session.boundaries.release_epoch)
    broker.session.boundaries.create_frozen(descriptor)
    end = deadline(1.3)
    prepared = broker._prepare_generation(controller, leaf, descriptor, end)
    fresh = broker.advance_generation(prepared, end)
    handle = fresh.stage(end)
    facade.bind(fresh, handle)
    with pytest.raises(ValueError) as raised:
        facade.start(leaf, descriptor, broker.connection, end)
    events = [e["extensions"]["xverse.maestro"] for e in EvidenceStore.read_run(work.parent / "argus").records()
              if e.get("extensions", {}).get("xverse.maestro", {}).get("unitId") == leaf]
    leaf2 = [(p["action"], p["outcome"]) for p in events if p.get("generation") == 2]
    m3 = [(r.kind, r.status) for r in FileEvidenceJournal(work.parent / "m3.jsonl").records
          if r.details.get("maestroUnitId") == leaf and r.details.get("generation") == 2]
    closure = RunClosure(broker.session).close(deadline(6))
    print("DV04-N2", dict(error=str(raised.value), lost=len(lost), cached_ready=bool(cached and cached.ready),
                          cached_generation=getattr(cached, "generation", None), leaf_generation2_events=leaf2,
                          leaf_generation2_m3=m3, closure_complete=closure.cleanup_complete,
                          diagnostics=closure.diagnostics))
    assert lost and cached is not None and cached.ready and cached.generation == 2  # finding 462
    assert str(raised.value) == "ML-PROBE-DEPENDENCY", raised.value
    assert broker.owner.latch.cancelled
    assert not any(a in ("started", "ready") for a, _ in leaf2), leaf2
    assert ("outcome", "running") not in m3, m3
    assert closure.root_reaped and all(h.process_reaped for h in closure.helpers)
    assert all(b.empty and b.released for b in closure.boundaries)

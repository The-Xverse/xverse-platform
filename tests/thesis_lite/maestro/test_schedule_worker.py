"""Actual original worker tick/health composition and existing native lease renewal."""

from dataclasses import replace
import json
from pathlib import Path
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.argus.schema import canonical_bytes
from xverse.maestro.schedule_plan import admit_schedule
from xverse.maestro.providers import ProcessReadiness, ProbePolicy
from xverse.maestro.teardown import ReverseTeardown
from xverse.maestro.time import HostDeadline
from .test_bootstrap import (
    boot_stack as boot_stack,
    supervisor_binary as supervisor_binary,
)
from .test_boundary import environment as environment, native as native
from .test_launcher import binaries as binaries, deadline


def scheduled(request, monkeypatch):
    from . import test_bootstrap

    configure = test_bootstrap.configured

    def configured(*args, **kwargs):
        config, pin, work = configure(*args, **kwargs)
        plan = admit_schedule(
            config.prepared,
            policies=tuple(
                ProbePolicy(u.unit_id, 2, 1, 0.1) for u in config.prepared.units
            ),
            ticks=(0, 0, config.prepared.clock.horizon_ticks),
            active_seconds=1,
            operation_seconds=0.1,
            request_limit=256,
        )
        body = json.loads(config.private_bytes)
        body["schedule"] = json.loads(plan.canonical_bytes)
        return (
            replace(config, schedule=plan, private_bytes=canonical_bytes(body)),
            pin,
            work,
        )

    monkeypatch.setattr(test_bootstrap, "configured", configured)
    return request.getfixturevalue("boot_stack")


def complete(storage, index, tick):
    return storage._rpc(
        "schedule",
        {
            "kind": "tick-complete",
            "index": index,
            "tick": tick,
            "observed_at": time.monotonic(),
        },
        deadline(1),
    )[2]


def test_actual_supervised_tick_pauses_interleave_with_durable_health(
    request, monkeypatch
):
    stack = scheduled(request, monkeypatch)
    owner, storage, descriptor, launcher, handle, gate, original = stack[6]()
    assert storage._request_limit == 256 and storage.schedule is not None
    first = storage._rpc("tick", {"index": 1, "previous": 0}, deadline(1))[2]
    assert first == {"index": 1, "tick": 0, "schedule_digest": storage.schedule.digest}
    assert complete(storage, 1, 0)["event"]["producerSequence"] == 1
    facade = ProcessReadiness(owner, policies=storage.schedule.policies)
    facade.bind(launcher, handle)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    assert (
        storage._rpc("tick", {"index": 2, "previous": 0}, deadline(1))[2]["tick"] == 0
    )
    assert complete(storage, 2, 0)["event"]["producerSequence"] == 2
    assert facade.check_health(original, force=True)[0].ready
    final = storage._rpc("tick", {"index": 3, "previous": 0}, deadline(1))[2]
    assert final["tick"] == 10000
    complete(storage, 3, 10000)
    result = ReverseTeardown(facade).run(deadline(2))
    assert result.unit_cleanup_complete and result.normal_records_complete
    assert not result.lifecycle_complete
    events = EvidenceStore.read_run(stack[4].parent / "argus").records()
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(
        json.loads(
            Path(__file__).with_name("lifecycle-payload-v2.schema.json").read_text()
        )
    )
    ticks = []
    for event in events:
        payload = event["extensions"]["xverse.maestro"]
        validator.validate(payload)
        if event["producerId"] == "maestro.scheduler14":
            ticks.append(event["clocks"]["simulation"]["value"])
            assert payload["sourceRefs"][0]["kind"] == "admitted-lifecycle"
    assert ticks == [0, 0, 10000]
    probes = [
        e["producerSequence"] for e in events if e["producerId"] == "maestro.outcomes12"
    ]
    assert probes == list(range(1, len(probes) + 1))


@pytest.mark.parametrize(
    "mode", ["wrong-index", "wrong-prior", "double-pull", "wrong-tick", "without-pull"]
)
def test_original_worker_rejects_tick_state_forgery(request, monkeypatch, mode):
    stack = scheduled(request, monkeypatch)
    owner, storage, descriptor, launcher, handle, gate, original = stack[6]()
    with pytest.raises(ValueError):
        if mode == "wrong-index":
            storage._rpc("tick", {"index": 2, "previous": 0}, deadline(1))
        elif mode == "wrong-prior":
            storage._rpc("tick", {"index": 1, "previous": 1}, deadline(1))
        elif mode == "without-pull":
            complete(storage, 1, 0)
        else:
            storage._rpc("tick", {"index": 1, "previous": 0}, deadline(1))
            if mode == "double-pull":
                storage._rpc("tick", {"index": 2, "previous": 0}, deadline(1))
            else:
                complete(storage, 1, 1)
    assert owner.latch.cancelled and storage._failed
    assert stack[1].force_cleanup(descriptor).boundary_released
    assert not list(stack[4].glob("*.marker"))


def test_legacy_session_keeps_original_cap_and_rejects_tick(boot_stack):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    assert storage.schedule is None and storage._request_limit == 128
    with pytest.raises(ValueError):
        storage._rpc("tick", {"index": 1, "previous": 0}, deadline(1))
    assert owner.latch.cancelled
    assert boot_stack[1].force_cleanup(descriptor).boundary_released


def test_original_native_gate_renewal_updates_only_after_exact_ack(boot_stack):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    prior = gate.lease_ns
    lease = HostDeadline(
        owner.session, min(boot_stack[0]._lease / 1e9, time.monotonic() + 4.5)
    )
    receipt = gate.renew(lease, deadline(1))
    assert gate.lease_ns > prior and receipt == lease
    # Renewal did not Release the staged workload or change its original scope.
    assert not list(boot_stack[4].glob("*.marker"))
    facade = ProcessReadiness(
        owner,
        policies=tuple(ProbePolicy(u.unit_id, 2, 1, 1) for u in owner._prepared.units),
    )
    facade.bind(launcher, handle)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready


@pytest.mark.parametrize("mode", ["foreign", "shorter", "over-five"])
def test_invalid_gate_renewal_has_no_release_or_lease_change(boot_stack, mode):
    owner, storage, descriptor, launcher, handle, gate, original = boot_stack[6]()
    before = gate.lease_ns
    lease = (
        HostDeadline("foreign", time.monotonic() + 4)
        if mode == "foreign"
        else HostDeadline(owner.session, before / 1e9 - 0.1)
        if mode == "shorter"
        else deadline(6)
    )
    with pytest.raises(ValueError):
        gate.renew(lease, deadline(1))
    assert gate.lease_ns == before and not list(boot_stack[4].glob("*.marker"))


def test_scoped_stop_and_cleanup_keep_other_unit_health_and_repeat_facts(boot_stack):
    from .test_teardown import pair

    facade, owner, a, b = pair(boot_stack)
    controller = ReverseTeardown(facade)
    stopped = controller.phase(b[0].unit_id, "stop", deadline(1))
    assert stopped.leader_reaped and stopped.boundary_empty
    assert not stopped.boundary_released and not stopped.normal_records_complete
    assert controller.phase(b[0].unit_id, "stop", deadline(1)) is stopped
    assert [v.unit_id for v in facade.check_health(deadline(1), force=True)] == [
        a[0].unit_id
    ]
    assert not owner.latch.cancelled and facade.next_health_deadline is not None
    cleaned = controller.phase(b[0].unit_id, "cleanup", deadline(1))
    assert cleaned.unit_cleanup_complete and cleaned.normal_records_complete
    assert controller.phase(b[0].unit_id, "cleanup", deadline(1)) is cleaned
    assert facade.check_health(deadline(1), force=True)[0].ready
    assert controller.phase(a[0].unit_id, "stop", deadline(1)).leader_reaped
    assert facade.next_health_deadline is None
    assert controller.phase(a[0].unit_id, "cleanup", deadline(1)).unit_cleanup_complete
    result = controller.run(deadline(1))
    assert [v.unit_id for v in result.units] == [b[0].unit_id, a[0].unit_id]
    assert result.unit_cleanup_complete and result.normal_records_complete


def test_scoped_phase_rejects_prerequisite_or_premature_cleanup_without_effect(
    boot_stack,
):
    from .test_teardown import pair

    facade, owner, a, b = pair(boot_stack)
    controller = ReverseTeardown(facade)
    with pytest.raises(ValueError):
        controller.phase(a[0].unit_id, "stop", deadline(1))
    with pytest.raises(ValueError):
        controller.phase(b[0].unit_id, "cleanup", deadline(1))
    assert not owner.latch.cancelled
    assert all(v.ready for v in facade.check_health(deadline(1), force=True))


def test_first_release_without_sample_has_no_invented_health_deadline(
    boot_stack, monkeypatch
):
    from .test_provider import runtime

    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    query = ProcessReadiness._query
    before = []

    def inspect(self, unit, until):
        before.append(self.next_health_deadline)
        return query(self, unit, until)

    monkeypatch.setattr(ProcessReadiness, "_query", inspect)
    assert facade.start(descriptor.unit_id, descriptor, gate, original).ready
    assert before[0] is None
    assert facade.next_health_deadline is not None


def test_short_scoped_window_retains_emergency_c1_reserve(boot_stack):
    import fcntl
    import os
    from .test_provider import runtime

    facade, owner, descriptor, launcher, handle, gate, original = runtime(boot_stack)
    lock = os.open(boot_stack[4].parent / "m3.jsonl.lock", os.O_RDWR)
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        until = deadline(0.5)
        result = ReverseTeardown(facade, per_unit_seconds=1).phase(
            descriptor.unit_id, "stop", until
        )
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        os.close(lock)
    assert result.emergency and not result.normal_records_complete
    assert result.boundary_released

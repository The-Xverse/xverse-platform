"""Real native epoch receipts; no fresh M3 permit/restart admission claim."""

from dataclasses import replace
import copy

import pytest
from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.prbc import BoundaryDescriptor, BoundaryLimits
from .test_affa_client import connect
from .test_run_bootstrap import (
    run_stack as run_stack,
    run_bootstrap_binary as run_bootstrap_binary,
)
from .test_affa_native import authority_binary as authority_binary, digest, wait_marker
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline


def test_two_actual_advances_extend_only_original_creation_epochs(
    run_stack, monkeypatch
):
    client = connect(run_stack, monkeypatch, maximum_generation=3)
    session, manager, h, _, _, _, work = run_stack
    admission = manager._admission
    for i in range(2):
        h.stage(i)
        h.arm(i)
        h.release(i)
        wait_marker(work / f"u{i}.marker")
    initial = h.frame(K.QUERY, 0)
    retained = []
    for generation in (2, 3):
        h.stop_retire(0)
        old_descriptor = h.units[0]["descriptor"]
        terminal = manager.force_cleanup(old_descriptor)
        assert terminal.boundary_released
        next_scope = BoundaryDescriptor(
            "run", "u0", generation, f"next-{generation}", generation - 2
        )
        manager.create_frozen(next_scope)
        session.watch(next_scope, deadline(2))
        unit = h.units[0]
        unit.update(
            generation=generation,
            operation=bytes([generation + 10]) * 16,
            intent=digest(b"intent" + bytes([generation])),
            mirror=digest(b"mirror" + bytes([generation])),
            boundary=digest(b"boundary" + bytes([generation])),
        )
        unit.pop("handle")
        unit.pop("ticket")
        fd = manager._entry(next_scope).fd
        reply = h.rpc(h.frame(K.ADVANCE, 0), (fd,))
        assert reply.kind is K.ADVANCED and reply.epoch == generation - 1
        assert (
            manager.release_epoch == generation - 1 and manager._admission is admission
        )
        receipt = client._advance_receipts[-1]
        assert manager.admit_epoch(receipt) == generation - 1
        retained.append(receipt)
        assert manager.force_cleanup(old_descriptor) == terminal
        unit["descriptor"], unit["cg"] = next_scope, fd
        h.stage(0)
        h.arm(0)
        h.release(0)
        wait_marker(work / "u0.marker", generation)
        assert h.rpc(h.frame(K.QUERY, 1)).state & 4
    assert manager.admit_epoch(retained[0]) == 1 and manager.release_epoch == 2
    assert h.rpc(initial).state & 256
    assert (work / "u1.marker").read_bytes() == b"EXEC\n"
    stale = BoundaryDescriptor("run", "extra", 1, "stale", 0)
    before = len(manager._entries)
    with pytest.raises(ValueError):
        manager.create_frozen(stale)
    assert len(manager._entries) == before
    with pytest.raises(TypeError):
        copy.copy(retained[0])
    h.cancel()
    for i in range(2):
        h.stop_retire(i)


def test_raw_epoch_or_parsed_ack_is_not_an_original_receipt(run_stack, monkeypatch):
    client = connect(run_stack, monkeypatch)
    manager = run_stack[1]
    for value in (1, client.config, client._epoch_history[-1]):
        with pytest.raises(ValueError):
            manager.admit_epoch(value)
    with pytest.raises(AttributeError):
        client.epoch = 9
    assert manager.release_epoch == 0


def test_capacity_is_checked_before_authority_birth(run_stack):
    session, manager, h, helper, _, _, _ = run_stack
    for unit in h.units:
        session.watch(unit["descriptor"], deadline(2))
    config = replace(
        h.config,
        scope=session.authority_scope,
        supervisor_session=session.authority_supervisor,
        units=tuple(replace(u, max_generation=8) for u in h.config.units),
    )
    with pytest.raises(ValueError, match="CAPACITY"):
        session.authority(config, helper, deadline(2))
    assert not session._issued and not session._children


@pytest.mark.parametrize("count", [True, 0, 193])
def test_explicit_boundary_capacity_is_bounded(count):
    with pytest.raises(ValueError):
        BoundaryLimits(2, max_boundaries=count)


def test_explicit_boundary_capacity_keeps_original_default():
    assert BoundaryLimits(2).max_boundaries == 16
    assert BoundaryLimits(2, max_boundaries=192).max_boundaries == 192


def test_native_cancel_without_local_latch_closes_new_C1_creation(
    run_stack, monkeypatch
):
    client = connect(run_stack, monkeypatch)
    session, manager, h, _, _, _, _ = run_stack
    h.cancel()
    assert client.epoch == 1 and not manager._latch.cancelled
    assert manager.release_epoch == 0  # local fence is not a native ACK
    before = len(manager._entries)
    with pytest.raises(ValueError):
        manager.create_frozen(BoundaryDescriptor("run", "extra", 1, "after-cancel", 0))
    assert len(manager._entries) == before


def test_actual_advance_during_C1_creation_leaves_only_partial_scope(
    run_stack, monkeypatch
):
    client = connect(run_stack, monkeypatch, maximum_generation=3)
    session, manager, h, _, _, _, _ = run_stack
    for i in range(2):
        h.stage(i)
        h.arm(i)
        h.release(i)
    h.stop_retire(0)
    assert manager.force_cleanup(h.units[0]["descriptor"]).boundary_released
    target = BoundaryDescriptor("run", "u0", 2, "next-target", 0)
    manager.create_frozen(target)
    session.watch(target, deadline(2))
    unit = h.units[0]
    unit.update(
        generation=2,
        operation=b"n" * 16,
        intent=digest(b"next-intent"),
        mirror=digest(b"next-mirror"),
        boundary=digest(b"next-boundary"),
    )
    unit.pop("handle")
    unit.pop("ticket")
    pending = BoundaryDescriptor("run", "pending", 1, "pending", 0)
    original = manager._freeze

    def advance_during_freeze(entry):
        original(entry)
        if entry.descriptor == pending:
            frame = h.frame(K.ADVANCE, 0)
            assert h.rpc(frame, (manager._entry(target).fd,)).epoch == 1

    monkeypatch.setattr(manager, "_freeze", advance_during_freeze)
    with pytest.raises(ValueError) as observed:
        manager.create_frozen(pending)
    assert observed.value.record.state == "partial"
    assert manager._entry(pending).c1 is not None
    receipt = client._advance_receipts[-1]
    with pytest.raises(AttributeError):
        receipt._pins = ()
    with pytest.raises(ValueError):
        manager.admit_epoch(receipt._pins[2])  # parsed ACK is still inert
    h.cancel()
    h.stop_retire(1)


def test_explicit_original_capacity_admits_seventeen_empty_leaf_scopes(environment):
    import time
    from xverse.maestro.prbc import ProcessBoundaryOps, BoundaryAdmission
    from xverse.maestro.supervisor import CancellationLatch
    from xverse.maestro.time import HostDeadline

    _, _, root = environment
    facts = BoundaryAdmission(
        "capacity",
        "supervisor",
        "affa",
        "bootstrap-approval",
        "cleanup-approval",
        "reservation-approval",
        HostDeadline("host-session", time.monotonic() + 30),
        0,
    )
    manager = ProcessBoundaryOps(
        root, facts, CancellationLatch(), BoundaryLimits(2, max_boundaries=17)
    )
    scopes = []
    try:
        for n in range(17):
            descriptor = BoundaryDescriptor(
                "capacity", f"unit-{n}", 1, f"boundary-{n}", 0
            )
            assert manager.create_frozen(descriptor).state == "frozen"
            scopes.append(descriptor)
        with pytest.raises(ValueError):
            manager.create_frozen(
                BoundaryDescriptor("capacity", "overflow", 1, "overflow", 0)
            )
        assert len(manager._entries) == 17
    finally:
        for descriptor in scopes:
            assert manager.force_cleanup(descriptor).boundary_released
        manager.close()

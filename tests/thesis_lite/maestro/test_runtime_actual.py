"""ML3 host-owned bounded runtime lane: the nine actual process cases, by exact identifier.

The identifiers are the ``RUNTIME_CASES`` carried by the 024 validation matrices and by
``xverse.maestro.runtime_admission`` facility attestations: ``test_affa``,
``test_trusted_launcher``, ``test_prbc``, ``test_bounded_bootstrap``,
``test_atomic_release_cancel_stage``, ``test_lease_loss``, ``test_pre_handle_crash_survival``,
``test_residual_membership`` and ``test_unrelated_sentinel``.

Seven cases live here. ``test_atomic_release_cancel_stage`` and
``test_pre_handle_crash_survival`` are implemented, under exactly those names, in
``test_composed_authority_interruptions`` against the whole original lifecycle and are not
duplicated here. Every case below drives real owned child processes inside private frozen
cgroup boundaries through the reviewed native helpers (boundary fixture, release gate,
AFFA authority, run bootstrap), keeps an unrelated heartbeat sentinel alive in a separate
boundary for the whole case, and retains a receipt under ``MAESTRO_BOUNDARY_RECEIPTS``.
No case is skipped, xfailed or replaced by a model assertion; a missing kernel, launcher
or containment primitive fails the case with its concrete reason.

Disposable component boundaries only: not an admitted M1 run, not a production workload,
not legacy execution, and not acceptance or scientific evidence.
"""
from dataclasses import asdict, replace
import hashlib
import os
from pathlib import Path
import select
import time

import pytest
from xverse.maestro.affa_protocol import AuthorityKind as K
from xverse.maestro.runtime_admission import RUNTIME_CASES, validate_run_admission

from .test_boundary import environment as environment, native as native, descriptor, _write
from .test_leaseguard import guards as guards, frozen
from .test_releasegate import guard_binary as guard_binary, staged, arm, receive, empty, silent
from .test_affa_native import authority as authority, authority_binary as authority_binary, wait_marker
from .test_launcher import binaries as binaries, deadline
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_bootstrap_launcher import startup as startup
from .test_runtime_admission import inputs as inputs
from .test_composed_authority_interruptions import (
    heartbeat_binary as heartbeat_binary, sentinel as sentinel, retain, observed_members)

SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
LANE_CASES = ("test_affa", "test_trusted_launcher", "test_prbc", "test_bounded_bootstrap",
              "test_lease_loss", "test_residual_membership", "test_unrelated_sentinel")
COMPOSED_CASES = ("test_atomic_release_cancel_stage", "test_pre_handle_crash_survival")


def test_lane_identifiers_match_runtime_admission_cases():
    assert tuple(RUNTIME_CASES) == (
        "test_affa", "test_trusted_launcher", "test_prbc", "test_bounded_bootstrap",
        "test_atomic_release_cancel_stage", "test_lease_loss", "test_pre_handle_crash_survival",
        "test_residual_membership", "test_unrelated_sentinel")
    assert set(LANE_CASES) | set(COMPOSED_CASES) == set(RUNTIME_CASES)
    assert all(callable(globals().get(name)) for name in LANE_CASES)


def _public(value):
    """JSON-safe projection of retained facts: bytes become hex, dataclasses become dicts."""
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {str(k): _public(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_public(v) for v in value]
    if hasattr(value, "__dataclass_fields__"):
        return _public(asdict(value))
    return value


def _receipt(case, sentinel_before, sentinel_after, **facts):
    retain("runtime-actual-" + case + ".json", dict(case=case, sentinel_before=sentinel_before,
        sentinel_after=sentinel_after, source_sha256=SOURCE_SHA256, **_public(facts),
        disposable_component_boundaries=True, admitted_m1_run=False, full_runtime_lane_complete=False,
        accepted=False, scientific_result=False))


def _wait(predicate, bound=2.0):
    end = time.monotonic() + bound
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def test_affa(authority, sentinel):
    """AFFA epoch/ticket ordering against the real authority helper and frozen boundaries."""
    before = sentinel()
    h, work = authority
    began = time.monotonic()
    for i in range(2):
        h.stage(i)
        h.arm(i)
    assert h.release(0).kind is K.RELEASED
    wait_marker(work / "u0.marker")
    epoch_before_cancel = h.epoch
    cancel = h.cancel()
    assert cancel.kind is K.CANCELLED and h.epoch > epoch_before_cancel
    # A Cancel committed before a later Release yields zero workload instructions,
    # and the consumed one-use ticket performs none on replay either.
    assert h.release(1).kind is K.REJECTED
    assert h.release(0).kind is K.REJECTED
    assert h.manager.residual_membership(h.units[1]["descriptor"]) != ()
    assert not (work / "u1.marker").exists()
    assert (work / "u0.marker").read_bytes() == b"EXEC\n"
    retired = [h.stop_retire(i).kind.name for i in range(2)]
    assert not (work / "u1.marker").exists()
    after = sentinel()
    _receipt("test_affa", before, after, epoch_before_cancel=epoch_before_cancel, epoch_after_cancel=h.epoch,
             retired=retired, markers={p.name: p.read_text() for p in work.glob("*.marker")},
             elapsed_seconds=time.monotonic() - began)


def test_trusted_launcher(environment, native, guards, sentinel):
    """Only the explicit one-use gate release thaws the exact staged boundary; a stale ticket never does."""
    before = sentinel()
    manager, unit, child, marker, fd, process, channel, gate_deadline = staged(environment, native, guards)
    assert frozen(fd) and child.poll() is None
    silent(marker)
    ticket = arm(channel, gate_deadline)
    assert frozen(fd)
    silent(marker)
    channel.send(replace(ticket, kind=4, sequence=2).encode())
    released = receive(channel)
    assert released.kind == 21 and released.epoch == 7
    assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"M"
    assert not frozen(fd)
    members = observed_members(fd)  # running boundary: raw observation, not certified membership
    assert members
    # Cancel rotates the epoch and refreezes; the consumed ticket cannot be replayed through the gate.
    channel.send(empty(2, 3, gate_deadline).encode())
    stopped = receive(channel)
    assert stopped.kind == 18 and stopped.epoch == 8
    assert process.wait(timeout=2) == 0 and frozen(fd)
    with pytest.raises((BrokenPipeError, ConnectionResetError)):
        channel.send(replace(ticket, kind=4, sequence=4).encode())
    assert manager.residual_membership(unit) == members  # certified again once frozen
    result = manager.force_cleanup(unit)
    assert result.termination_observed and result.boundary_released and result.residual_count == 0
    after = sentinel()
    _receipt("test_trusted_launcher", before, after, members=list(members), release=asdict(released),
             stopped=asdict(stopped), cleanup=asdict(result))


def test_prbc(environment, native, sentinel):
    """Pre-registered cleanup capability covers the spawn-to-acknowledgement window and reservations."""
    before = sentinel()
    factory, spawn, _ = environment
    manager, _ = factory(seconds=8)
    staged_unit, reserved_unit = descriptor("prbc-staged"), descriptor("prbc-reserved")
    manager.create_frozen(staged_unit)
    manager.create_frozen(reserved_unit)
    process, marker, line = spawn(native, manager, staged_unit)
    assert line.startswith("CHILD "), line
    child_pid = int(line.split()[1])
    assert manager.residual_membership(staged_unit) == (child_pid,)
    fd = manager._entries[staged_unit.key].fd
    assert frozen(fd)
    silent(marker)
    # No handle was ever acknowledged: cleanup-only authority terminates the frozen child.
    staged_result = manager.force_cleanup(staged_unit)
    assert staged_result.termination_observed and staged_result.boundary_released
    assert staged_result.residual_count == 0
    assert process.wait(timeout=2) is not None
    assert os.read(marker, 1) == b""  # pipe closed by the dead child: no "M" was ever written
    # A reservation without any child releases without claiming a termination.
    reserved_result = manager.force_cleanup(reserved_unit)
    assert reserved_result.boundary_released and reserved_result.residual_count == 0
    assert not reserved_result.termination_observed
    after = sentinel()
    _receipt("test_prbc", before, after, child_pid=child_pid, staged=asdict(staged_result),
             reserved=asdict(reserved_result))


def test_bounded_bootstrap(startup, inputs, sentinel):
    """A bounded bootstrap supervisor runs and is reclaimed within its finite deadline; inert pins stay not-ready."""
    before = sentinel()
    reserve, manager, latch, _ = startup
    owner = reserve()
    began = time.monotonic()
    session = owner.launch(deadline(2))
    assert owner.outcome.registered and not owner.outcome.ready_for_execution
    assert not latch.cancelled
    result = owner.drain(deadline(1.8))
    elapsed = time.monotonic() - began
    assert result.supervisor_reaped and result.registered_helpers_reaped
    assert result.unacknowledged_births == 0 and elapsed < 4.0
    assert session._root_result is not None
    owner.dispose()
    persistence, boot, authorization, facility, kwargs = inputs
    admission = validate_run_admission(persistence, boot, authorization, facility, **kwargs)
    assert not admission.ready_for_execution
    with pytest.raises(ValueError):
        validate_run_admission(persistence, boot, authorization, facility,
                               **dict(kwargs, expected_facility_digest="sha256:" + "0" * 64))
    after = sentinel()
    _receipt("test_bounded_bootstrap", before, after, elapsed_seconds=elapsed, outcome=asdict(owner.outcome),
             drain=asdict(result), admission_ready_for_execution=admission.ready_for_execution)


def test_lease_loss(environment, native, guards, sentinel):
    """Lease expiry fails closed natively: epoch bump, the armed ticket is dead, zero release, membership kept."""
    before = sentinel()
    manager, unit, child, marker, fd, process, channel, gate_deadline = staged(environment, native, guards, lease=0.4)
    ticket = arm(channel, gate_deadline)
    silent(marker)
    expired = receive(channel)  # no Python tick, provider routine or heartbeat services the guard
    assert expired.kind == 18 and expired.epoch == 8 and expired.reason == 1
    assert process.wait(timeout=2) == 0 and frozen(fd)
    with pytest.raises((BrokenPipeError, ConnectionResetError)):
        channel.send(replace(ticket, kind=4, sequence=2).encode())
    silent(marker)
    members = manager.residual_membership(unit)
    assert members and child.poll() is None
    result = manager.force_cleanup(unit)
    assert result.termination_observed and result.boundary_released and result.residual_count == 0
    after = sentinel()
    _receipt("test_lease_loss", before, after, expired=asdict(expired), members=list(members), cleanup=asdict(result))


def test_residual_membership(environment, native, sentinel):
    """Exact membership observation, not a signal, proves release of a dead-leader/live-descendant boundary."""
    before = sentinel()
    factory, spawn, _ = environment
    manager, _ = factory(seconds=8)
    unit = descriptor("residual")
    manager.create_frozen(unit)
    process, marker, line = spawn(native, manager, unit, mode="descendant")
    assert line.startswith("CHILD "), line
    leader = int(line.split()[1])
    fd = manager._entries[unit.key].fd
    assert manager.residual_membership(unit) == (leader,)
    _write(fd, "cgroup.freeze", b"0")  # test-only thaw; never a runtime Release
    assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"M"
    assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"D"
    assert _wait(lambda: process.poll() is not None)  # the leader exited after forking
    running = observed_members(fd)
    assert running and leader not in running
    _write(fd, "cgroup.freeze", b"1")  # test-only refreeze: certified membership requires a frozen boundary
    assert _wait(lambda: frozen(fd))
    members = manager.residual_membership(unit)
    assert members == running and leader not in members
    result = manager.force_cleanup(unit)
    assert result.termination_observed and result.boundary_released and result.residual_count == 0
    for pid in members:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    after = sentinel()
    _receipt("test_residual_membership", before, after, leader=leader, descendants=list(members), cleanup=asdict(result))


def test_unrelated_sentinel(environment, native, sentinel):
    """An unrelated sentinel in a separate boundary survives the target's exact teardown untouched."""
    before = sentinel()
    factory, spawn, _ = environment
    manager, _ = factory(seconds=8)
    target = descriptor("sentinel-target")
    manager.create_frozen(target)
    process, marker, line = spawn(native, manager, target)
    assert line.startswith("CHILD "), line
    fd = manager._entries[target.key].fd
    _write(fd, "cgroup.freeze", b"0")
    assert select.select([marker], [], [], 1)[0] and os.read(marker, 1) == b"M"
    members = observed_members(fd)  # running target: raw observation, not certified membership
    assert members == (int(line.split()[1]),)
    result = manager.force_cleanup(target)
    assert result.termination_observed and result.boundary_released and result.residual_count == 0
    assert process.wait(timeout=2) is not None
    after = sentinel()
    assert after["members"] == before["members"] and after["boundary_identity"] == before["boundary_identity"]
    for pid in after["members"]:
        os.kill(pid, 0)  # existence only: the sentinel is alive and untouched
    _receipt("test_unrelated_sentinel", before, after, target_members=list(members), cleanup=asdict(result))

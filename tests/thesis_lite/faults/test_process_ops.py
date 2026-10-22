"""U-PRC-01 … U-PRC-04: owned kill/freeze/thaw through the native catalog launcher (thesis V06, V12).

Reuses the Maestro launcher stack: a real helper compiled from ``native/catalog_launcher.c`` stages
a frozen child inside an owned cgroup-v2 boundary; the release gate unfreezes it; the test then
freezes, thaws and kills it through the launcher's ``fault`` operation on the exact handle. No other
process is signalled; refusals leave everything as it was.
"""

from __future__ import annotations

from dataclasses import replace
import os
import time

import pytest

from xverse.maestro.launcher import LauncherError

from ..maestro.test_boundary import environment as environment  # noqa: F401 - fixture re-export
from ..maestro.test_launcher import binaries as binaries  # noqa: F401 - fixture re-export
from ..maestro.test_launcher import deadline, launch_stack as launch_stack  # noqa: F401 - fixture re-export


def _released(launch_stack, work):
    """Stage, release through the bound gate and wait until the workload has executed."""

    owner, client, manager, config, _, launch, gate = launch_stack
    descriptor, launcher, handle, original = launch()
    connection = gate(descriptor, original)
    result = owner.release(descriptor.unit_id, descriptor, connection, original)
    assert result.native_unfreeze_observed
    marker = work / "source-binding.marker"
    until = time.monotonic() + 1
    while not marker.exists() and time.monotonic() < until:
        time.sleep(0.005)
    assert marker.read_text() == "EXEC\n"
    assert launcher.observe(replace(handle), deadline()).running
    return descriptor, launcher, handle


def _finish(launch_stack, descriptor, launcher):
    """Cancel, drain and clean up exactly as the Maestro launcher test does."""

    owner, client, manager, *_ = launch_stack
    owner.cancel()
    launcher.drain(deadline(1))
    manager.force_cleanup(descriptor)
    client.abort(deadline(1))


def _frozen(manager, descriptor) -> int:
    """Read ``cgroup.events frozen`` of the owned boundary through the manager's fd."""

    fd = os.open("cgroup.events", os.O_RDONLY | os.O_CLOEXEC, dir_fd=manager._entries[descriptor.key].fd)
    try:
        text = os.read(fd, 4096).decode()
    finally:
        os.close(fd)
    return int(next(line.split()[1] for line in text.splitlines() if line.startswith("frozen ")))


def test_u_prc_02_and_01_freeze_thaw_then_kill_through_owned_handle(launch_stack, tmp_path):
    """U-PRC-02 then U-PRC-01 on one staged child."""

    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle = _released(launch_stack, work)
    assert _frozen(manager, descriptor) == 0
    assert launcher.fault(replace(handle), "freeze", deadline()) == (True, 0)
    assert _frozen(manager, descriptor) == 1
    assert launcher.observe(replace(handle), deadline()).leader_alive
    assert launcher.fault(replace(handle), "thaw", deadline()) == (True, 0)
    assert _frozen(manager, descriptor) == 0
    assert launcher.fault(replace(handle), "kill", deadline()) == (True, 0)
    until = time.monotonic() + 2
    observed = launcher.observe(replace(handle), deadline())
    while not observed.leader_reaped and time.monotonic() < until:
        time.sleep(0.01)
        observed = launcher.observe(replace(handle), deadline())
    assert observed.leader_reaped and observed.returncode == -9
    _finish(launch_stack, descriptor, launcher)


def test_u_prc_04_kill_after_exit_is_refused(launch_stack):
    """U-PRC-04: a second kill on a reaped child answers reason 6 and changes nothing."""

    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle = _released(launch_stack, work)
    assert launcher.fault(replace(handle), "kill", deadline()) == (True, 0)
    until = time.monotonic() + 2
    while not launcher.observe(replace(handle), deadline()).leader_reaped and time.monotonic() < until:
        time.sleep(0.01)
    assert launcher.fault(replace(handle), "kill", deadline()) == (False, 6)
    assert launcher.fault(replace(handle), "freeze", deadline()) == (False, 6)
    _finish(launch_stack, descriptor, launcher)


def test_u_prc_03_forged_handle_and_unknown_operation(launch_stack):
    """U-PRC-03: a foreign handle or an unknown operation is refused before any request."""

    owner, client, manager, config, work, launch, gate = launch_stack
    descriptor, launcher, handle = _released(launch_stack, work)
    forged = replace(handle, opaque_id="0" * 64)
    with pytest.raises(LauncherError) as caught:
        launcher.fault(forged, "kill", deadline())
    assert caught.value.args[0] == "ML-LAUNCH-HANDLE"
    with pytest.raises(LauncherError) as caught:
        launcher.fault(replace(handle), "pause", deadline())
    assert caught.value.args[0] == "ML-LAUNCH-FAULT-OPERATION"
    assert launcher.observe(replace(handle), deadline()).running
    _finish(launch_stack, descriptor, launcher)

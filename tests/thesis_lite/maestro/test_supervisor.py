from dataclasses import FrozenInstanceError
import copy
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import threading
import time

import pytest

from xverse.maestro.supervisor import (
    CancellationLatch,
    SupervisionError,
    WatchLimits,
    WorkerMonitor,
)


pytestmark = pytest.mark.skipif(
    not hasattr(os, "pidfd_open"), reason="Linux pidfd monitor"
)


@pytest.fixture
def children():
    processes = []
    descriptors = []

    def spawn(mode="provider", *, code=0):
        read, write = os.pipe()
        descriptors.append(read)
        args = [
            sys.executable,
            "-I",
            str(Path(__file__).with_name("worker_fixture.py")),
            mode,
            str(write),
        ]
        inherited = [write]
        if mode == "storage":
            blocked_read, blocked_write = os.pipe()
            descriptors.extend([blocked_read, blocked_write])
            args.append(str(blocked_read))
            inherited.append(blocked_read)
        elif mode == "exit":
            args.append(str(code))
        try:
            process = subprocess.Popen(
                args,
                pass_fds=inherited,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            os.close(write)
        processes.append(process)
        assert select.select([read], [], [], 3)[0], "fixture did not become ready"
        assert os.read(read, 1) == b"R"
        return process

    yield spawn
    for process in processes:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=3)
    for descriptor in descriptors:
        os.close(descriptor)


def limits(operation=0.15):
    return WatchLimits(
        operation_seconds=operation,
        term_seconds=0.1,
        kill_seconds=0.5,
        poll_seconds=0.005,
    )


@pytest.mark.parametrize(
    "field", ["operation_seconds", "term_seconds", "kill_seconds", "poll_seconds"]
)
@pytest.mark.parametrize(
    "value", [True, False, 0, -1, float("nan"), float("inf"), "1", 10**1000]
)
def test_bad_limits_are_rejected(field, value):
    kwargs = dict(
        operation_seconds=0.15, term_seconds=0.1, kill_seconds=0.5, poll_seconds=0.005
    )
    kwargs[field] = value
    with pytest.raises(SupervisionError, match="ML-ADMISSION"):
        WatchLimits(**kwargs)


def test_upper_bounds_and_frozen_limits():
    for kwargs in [
        dict(operation_seconds=5.01),
        dict(term_seconds=5.01),
        dict(kill_seconds=5.01),
        dict(poll_seconds=0.051),
    ]:
        with pytest.raises(SupervisionError):
            WatchLimits(
                **(
                    dict(
                        operation_seconds=1,
                        term_seconds=1,
                        kill_seconds=1,
                        poll_seconds=0.01,
                    )
                    | kwargs
                )
            )
    with pytest.raises(FrozenInstanceError):
        limits().operation_seconds = 2


def test_latch_is_irreversible_and_idempotent():
    latch = CancellationLatch()
    assert latch.epoch == 0 and not latch.cancelled
    assert latch.cancel("operator-stop") == 1
    assert latch.cancel("another-reason") == 1
    assert latch.reason == "operator-stop" and latch.cancelled
    with pytest.raises(SupervisionError):
        copy.copy(latch).cancel("copy")


@pytest.mark.parametrize("mode", ["provider", "storage", "tick"])
def test_deadline_kills_actual_blocked_worker_without_callback(mode, children):
    worker = children(mode)
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits())
    started = time.monotonic()
    result = monitor.watch(ref)
    assert time.monotonic() - started < 2
    assert result.disposition == "timed-out"
    assert result.worker_reaped and result.returncode == -signal.SIGTERM
    assert result.signals_sent == ("TERM",)
    assert not result.identity_retained
    assert monitor.latch.cancelled and result.cancel_epoch == 1
    assert not result.cleanup_complete and not result.ready_for_execution
    assert monitor.watch(ref) is result


def test_kill_escalation_does_not_touch_sentinel(children):
    worker, sentinel = children("ignore-term"), children()
    monitor = WorkerMonitor(CancellationLatch())
    result = monitor.watch(monitor.retain(worker, limits()))
    assert result.disposition == "timed-out"
    assert result.worker_reaped and result.returncode == -signal.SIGKILL
    assert result.signals_sent == ("TERM", "KILL")
    assert sentinel.poll() is None


def test_independent_cancel_does_not_wait_for_worker(children):
    worker = children("storage")
    latch = CancellationLatch()
    monitor = WorkerMonitor(latch)
    ref = monitor.retain(worker, limits(2))
    results = []
    thread = threading.Thread(target=lambda: results.append(monitor.watch(ref)))
    thread.start()
    began = time.monotonic()
    latch.cancel("operator-stop")
    thread.join(2)
    assert not thread.is_alive()
    assert time.monotonic() - began < 1
    assert results[0].disposition == "cancelled" and results[0].worker_reaped


def test_cancel_before_registration_rejects_without_signal(children):
    worker = children()
    latch = CancellationLatch()
    latch.cancel("stop")
    monitor = WorkerMonitor(latch)
    with pytest.raises(SupervisionError, match="ML-CANCELLED"):
        monitor.retain(worker, limits())
    assert worker.poll() is None


@pytest.mark.parametrize("code", [0, 7])
def test_actual_exit_is_worker_observation_only(code, children):
    worker = children("exit", code=code)
    monitor = WorkerMonitor(CancellationLatch())
    result = monitor.watch(monitor.retain(worker, limits(1)))
    assert result.disposition == "exited" and result.returncode == code
    assert result.worker_reaped and not result.signals_sent
    assert result.cancel_epoch == 0
    assert not result.cleanup_complete and not result.ready_for_execution
    assert not hasattr(result, "pid") and not hasattr(result, "pidfd")
    with pytest.raises(FrozenInstanceError):
        result.disposition = "ready"


def test_late_exit_after_cancel_cannot_report_normal_exit(children):
    worker = children("exit")
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(1))
    monitor.latch.cancel("cancelled-before-observation")
    result = monitor.watch(ref)
    assert result.disposition == "cancelled" and result.worker_reaped


def test_registration_deadline_is_not_extended_by_delayed_watch(children):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(0.02))
    time.sleep(0.05)
    result = monitor.watch(ref)
    assert result.disposition == "timed-out" and result.worker_reaped


def test_original_holder_and_object_are_required(children):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(1))
    with pytest.raises(SupervisionError, match="ML-OWNERSHIP"):
        copy.copy(monitor).watch(ref)
    with pytest.raises(SupervisionError):
        monitor.retain(worker, limits())
    with pytest.raises(SupervisionError):
        monitor.watch("unknown")
    monitor.latch.cancel("test-cleanup")
    assert monitor.watch(ref).worker_reaped


def test_reaped_or_wrong_child_is_rejected(children):
    worker = children("exit")
    worker.wait(timeout=2)
    monitor = WorkerMonitor(CancellationLatch())
    for value in [worker, object(), 1, None]:
        with pytest.raises(SupervisionError):
            monitor.retain(value, limits())


def test_signal_denial_retains_original_identity(monkeypatch, children):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(0.01))
    with monkeypatch.context() as patch:
        patch.setattr(
            signal,
            "pidfd_send_signal",
            lambda *args: (_ for _ in ()).throw(PermissionError("denied")),
        )
        result = monitor.watch(ref)
    assert result.disposition == "unresolved" and result.identity_retained
    assert not result.worker_reaped and worker.poll() is None
    assert result.diagnostic == "ML-OWNERSHIP-SIGNAL"
    # Test harness cleans its original child, then releases the retained identity.
    worker.kill()
    worker.wait(timeout=2)
    assert monitor.watch(ref) is result  # Cached uncertainty cannot become success.
    monitor.dispose_reaped(ref)


def test_stolen_wait_ownership_is_unknown(monkeypatch, children):
    worker = children("exit")
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(1))
    worker.wait(timeout=2)  # forbidden concurrent waiter, injected integration fault
    result = monitor.watch(ref)
    assert result.disposition == "unresolved" and result.identity_retained
    assert result.diagnostic == "ML-OWNERSHIP-WAIT"
    assert not result.worker_reaped
    assert monitor.latch.cancelled
    monitor.dispose_reaped(ref)


def test_limits_are_snapshotted_at_registration(children, monkeypatch):
    worker = children()
    original = limits()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, original)
    object.__setattr__(original, "term_seconds", 0.001)
    object.__setattr__(original, "poll_seconds", float("nan"))
    waits = []
    original_select = select.select

    def observe_wait(*args):
        waits.append(args[3])
        return original_select(*args)

    with monkeypatch.context() as patch:
        patch.setattr(select, "select", observe_wait)
        result = monitor.watch(ref)
    assert result.disposition == "timed-out" and result.worker_reaped
    assert waits[0] > 0


def test_dispose_reaps_confirmed_exited_worker(children):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(1))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            os, "waitid", lambda *args: (_ for _ in ()).throw(OSError("failure"))
        )
        assert monitor.watch(ref).disposition == "unresolved"
    with pytest.raises(SupervisionError, match="LIVE"):
        monitor.dispose_reaped(ref)
    worker.kill()
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            monitor.dispose_reaped(ref)
            break
        except SupervisionError:
            time.sleep(0.005)
    else:
        pytest.fail("original child's exit was not observed")
    assert worker.returncode == -signal.SIGKILL


def test_watch_does_not_use_popen_wait_poll_or_child_output(children, monkeypatch):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits())
    with monkeypatch.context() as patch:

        def forbidden(*args, **kwargs):
            raise AssertionError("blocking wrapper or child output used")

        patch.setattr(subprocess.Popen, "wait", forbidden)
        patch.setattr(subprocess.Popen, "poll", forbidden)
        patch.setattr(os, "read", forbidden)
        assert monitor.watch(ref).worker_reaped


def test_observation_error_closes_latch_without_signalling(children, monkeypatch):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(1))
    with monkeypatch.context() as patch:
        patch.setattr(
            select, "select", lambda *args: (_ for _ in ()).throw(OSError("failure"))
        )
        result = monitor.watch(ref)
    assert result.diagnostic == "ML-OWNERSHIP-OBSERVE"
    assert (
        monitor.latch.cancelled and result.identity_retained and not result.signals_sent
    )
    worker.kill()
    worker.wait(timeout=2)
    monitor.dispose_reaped(ref)


def test_cancellation_at_exit_commit_is_not_success(children, monkeypatch):
    worker = children("exit")
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(1))
    original_wait = os.waitid

    def cancel_at_reap(*args):
        reply = original_wait(*args)
        if reply is not None and not args[2] & os.WNOWAIT:
            monitor.latch.cancel("commit-race")
        return reply

    with monkeypatch.context() as patch:
        patch.setattr(os, "waitid", cancel_at_reap)
        result = monitor.watch(ref)
    assert result.disposition == "cancelled" and result.worker_reaped


def test_expired_entire_lease_returns_unresolved_without_new_force(children):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, WatchLimits(0.01, 0.01, 0.01, 0.005))
    time.sleep(0.05)
    result = monitor.watch(ref)
    assert result.disposition == "unresolved" and not result.signals_sent
    assert result.identity_retained and not result.worker_reaped
    worker.kill()
    worker.wait(timeout=2)
    monitor.dispose_reaped(ref)


def test_inherited_holder_cannot_signal_from_fork(children):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, limits(1))
    read, write = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read)
        try:
            monitor.watch(ref)
            os.write(write, b"bad")
        except SupervisionError as exc:
            os.write(write, exc.code.encode())
        finally:
            os._exit(0)
    os.close(write)
    try:
        assert select.select([read], [], [], 2)[0]
        assert os.read(read, 128) == b"ML-OWNERSHIP-WORKER-HOLDER"
    finally:
        os.close(read)
        os.kill(child, signal.SIGKILL)
        os.waitpid(child, 0)
    assert worker.poll() is None
    monitor.latch.cancel("test-cleanup")
    assert monitor.watch(ref).worker_reaped


def test_delayed_observation_cannot_signal_after_final_deadline(children, monkeypatch):
    worker = children()
    monitor = WorkerMonitor(CancellationLatch())
    ref = monitor.retain(worker, WatchLimits(0.01, 0.01, 0.01, 0.005))
    monitor.latch.cancel("operator-stop")
    original_wait = os.waitid
    delayed = False

    def slow_observation(*args):
        nonlocal delayed
        if not delayed:
            delayed = True
            time.sleep(0.05)
        return original_wait(*args)

    with monkeypatch.context() as patch:
        patch.setattr(os, "waitid", slow_observation)
        result = monitor.watch(ref)
    try:
        assert result.disposition == "unresolved" and not result.signals_sent
        assert worker.poll() is None
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.wait(timeout=2)
        monitor.dispose_reaped(ref)

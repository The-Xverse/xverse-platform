"""S1a-2 diagnosis (thesis specs/029-lite-stabilization S1-T06b; platform review-stabilization-s1a.md findings
18-20): a run cancel that meets a busy authority connection.

``RunBroker.cancel`` sends K.CANCEL through ``connection._exchange``, whose lock is non-blocking. In the owned
live harness the cancel runs on the operator's thread while the dispatcher thread may be inside another
exchange. These tests hold that lock in place of the concurrent exchange and record what the cancel does to the
storage (persistence) worker. Reproduction before repair: the busy case is expected to fail on main
``b28a2aacf`` if the finding-19/20 mechanism is right (conflict -> revoke -> the root kills every child)."""

import time

from xverse.maestro.child import wait_child

from .test_run_broker import broker_stack as broker_stack
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries


def _storage_exited(storage, seconds=2.0):
    """Whether the storage worker exits within ``seconds`` (polled; the root reacts asynchronously)."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if wait_child(storage._pins[0], storage._pidfd) is not None:
            return True
        time.sleep(0.02)
    return False


def _cancel(broker, *, busy):
    lock = broker.connection._lock
    if busy:
        assert lock.acquire(False)  # stands in for a dispatcher exchange in flight on another thread
    try:
        return broker.cancel("s1a2-diagnosis-" + ("busy" if busy else "idle"))
    finally:
        if busy:
            lock.release()


def test_cancel_on_idle_connection_keeps_storage_worker(broker_stack):
    broker, _, storage, _ = broker_stack
    result = _cancel(broker, busy=False)
    print("idle cancel result:", result)
    assert result.native_epoch_confirmed
    assert not _storage_exited(storage)


def test_cancel_on_busy_connection_keeps_storage_worker(broker_stack):
    broker, _, storage, _ = broker_stack
    result = _cancel(broker, busy=True)
    print("busy cancel result:", result)
    assert not _storage_exited(storage), f"storage worker exited after a cancel on a busy connection: {result}"
    assert result.native_epoch_confirmed, result

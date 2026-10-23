"""S1a-2 diagnosis (thesis specs/029-lite-stabilization S1-T06b; platform review-stabilization-s1a.md findings
18-20): a run cancel that meets a busy authority connection.

``RunBroker.cancel`` sends K.CANCEL through ``connection._exchange``, whose lock is non-blocking. In the owned
live harness the cancel runs on the operator's thread while the dispatcher thread may be inside another
exchange. These tests hold that lock in place of the concurrent exchange and record what the cancel does to the
storage (persistence) worker.

Reproduction before repair (finding 21): on main ``b28a2aacf`` a cancel on a busy connection is revoked at once
(conflict -> revoke -> the root kills every child, including storage). After amendment S1a-3 a cancel waits up to
``CANCEL_LOCK_WAIT_SECONDS`` for the connection: a busy connection that becomes free in time gives a confirmed
cancel and a living storage worker, and one that stays busy past the bound still gives the unchanged revoke."""

import threading
import time

from xverse.maestro.child import wait_child
from xverse.maestro.run_broker import CANCEL_LOCK_WAIT_SECONDS

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


def _cancel(broker, *, busy_seconds=None):
    """Cancel while the connection lock is held for ``busy_seconds`` (None: idle), as by a concurrent exchange."""
    lock = broker.connection._lock
    releaser = None
    if busy_seconds is not None:
        assert lock.acquire(False)  # stands in for a dispatcher exchange in flight on another thread
        releaser = threading.Timer(busy_seconds, lock.release)
        releaser.start()
    began = time.monotonic()
    try:
        return broker.cancel("s1a2-diagnosis"), time.monotonic() - began
    finally:
        if releaser is not None:
            releaser.join()


def test_cancel_on_idle_connection_keeps_storage_worker(broker_stack):
    broker, _, storage, _ = broker_stack
    result, took = _cancel(broker)
    print("idle cancel result:", result, "took", round(took, 4))
    assert result.native_epoch_confirmed
    assert not _storage_exited(storage)


def test_cancel_waits_for_a_briefly_busy_connection_and_keeps_storage_worker(broker_stack):
    broker, _, storage, _ = broker_stack
    result, took = _cancel(broker, busy_seconds=0.1)  # an ordinary exchange finishing within the bound
    print("busy-0.1s cancel result:", result, "took", round(took, 4))
    assert result.native_epoch_confirmed and result.frozen_units == 3, result
    assert 0.1 <= took < CANCEL_LOCK_WAIT_SECONDS + 0.5
    assert not _storage_exited(storage), f"storage worker exited after a cancel on a busy connection: {result}"


def test_cancel_on_a_connection_busy_past_the_bound_still_revokes(broker_stack):
    broker, _, storage, _ = broker_stack
    result, took = _cancel(broker, busy_seconds=CANCEL_LOCK_WAIT_SECONDS + 0.4)  # a stalled exchange
    print("busy-past-bound cancel result:", result, "took", round(took, 4))
    assert not result.native_epoch_confirmed and result.issuer_dead, result  # the unchanged fail-safe
    assert CANCEL_LOCK_WAIT_SECONDS <= took

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


def test_stale_cancel_frame_after_a_concurrent_winner_is_retried(broker_stack, monkeypatch):
    """Another cancel wins between this cancel's frame build and its lock (review finding 23, MEDIUM-1)."""
    from xverse.maestro.affa_protocol import AuthorityFrame, AuthorityKind as K

    broker, _, storage, _ = broker_stack
    connection = broker.connection
    exchange = connection._exchange
    refused = []

    def winner_first(request, **kw):
        if request.kind is K.CANCEL and not refused:
            fresh = AuthorityFrame(K.CANCEL, connection.sequence + 1, request.deadline_ns, connection.config.scope,
                                   epoch=connection.epoch)
            exchange(fresh)  # the concurrent winner: CANCELLED advances the epoch
            try:
                return exchange(request, **kw)  # now stale
            except ValueError as error:
                refused.append(str(error))
                raise
        return exchange(request, **kw)

    monkeypatch.setattr(connection, "_exchange", winner_first)
    result = broker.cancel("s1a2-stale-frame")
    print("stale-frame cancel result:", result, refused)
    assert refused == ["ML-AFFA-REQUEST-SCOPE"]
    assert result.native_epoch_confirmed and result.frozen_units == 3, result
    assert not _storage_exited(storage)


def test_two_concurrent_cancels_are_both_confirmed(broker_stack):
    """Smoke test: the operator's stop and the dispatcher's own cancel arrive together (finding 23, MEDIUM-2).

    It does not force the stale-frame interleaving and may not overlap (re-review, finding 25): the stale-frame and
    after-CANCELLED tests are the ones that discriminate the repair."""
    broker, _, storage, _ = broker_stack
    barrier, results, errors = threading.Barrier(2), [], []

    def cancel(name):
        barrier.wait()
        try:
            results.append(broker.cancel(name))
        except Exception as error:  # recorded, then asserted
            errors.append(repr(error))

    threads = [threading.Thread(target=cancel, args=(name,)) for name in ("operator-stop", "dispatcher-failed")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
    print("concurrent cancel results:", results, errors)
    assert not errors and len(results) == 2
    assert all(r.native_epoch_confirmed and not r.issuer_dead for r in results), results
    assert not _storage_exited(storage)


def test_cancel_exchange_after_cancelled_returns_the_retained_reply(broker_stack):
    broker, _, storage, _ = broker_stack
    first = broker.cancel("s1a2-first")
    assert first.native_epoch_confirmed
    sequence = broker.connection.sequence
    reply = broker._cancel_exchange(time.monotonic() + 1, float("inf"))
    assert reply is broker.connection._epoch_history[-1] and broker.connection.sequence == sequence
    assert not _storage_exited(storage)

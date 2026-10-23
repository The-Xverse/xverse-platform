"""S1b review findings 14 and 15: a start-up readiness failure must still close its evidence (P4).

Reproduction before repair. Each test asserts the CORRECT behaviour; the cases marked as controls pass today and the
others fail while the defect is present.

Mechanism (finding 15). ``ProcessReadiness.start`` raises ``ML-PROBE-NOT-READY`` and cancels through the owner,
which calls ``RunBroker.cancel(reason)`` with no deadline. The K.CANCEL frame then carries
``deadline_ns = now + 1 s``, never clamped to the authority lease, and the client-side ``_validate`` exempts the
cleanup kinds from the lease check. The native authority admits a frame on an open authority only when
``until <= g->lease`` (``run_authority.c`` validity check), CANCEL included, and answers an invalid frame by
``cleanup`` and exit. The client receives no reply (``ML-AFFA-SENDER``) and revokes. So a cancel issued in the
last second of an unrenewed authority lease always revokes. S1b exposes it: a ``nonce-marker`` start spends up to
the readiness window W (2 s in the live run, attempts at t0, t0 + 0.875 s and t0 + 1.75 s) inside one start
step without a lease renewal, so the failure lands near the end of the lease. Before S1b a start-up failure (a
child exit) was seen within milliseconds of RELEASE.

The tests place the cancel in the last second of the authority lease by waiting before it is issued; they never
alter a request or a reply.
"""

import time

import pytest
from xverse.maestro.affa_client import AuthorityConnection
from xverse.maestro.providers import ProcessReadiness
from .test_stabilization_s1b_broker import declare
from .test_run_broker import broker_stack as broker_stack, stage_all
from .test_runtime_entry import runtime as runtime
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries

# Any remaining lease in (0, 1) s reproduces it: the CANCEL deadline is now + 1 s.
LEASE_REMAINING_SECONDS = 0.6


def _wait_until_lease_remaining(connection, remaining):
    lease = connection._lease / 1e9
    gap = lease - remaining - time.monotonic()
    if gap > 0:
        time.sleep(gap)
    left = connection._lease / 1e9 - time.monotonic()
    assert 0.1 < left < 1.0, left  # inside the last second of the lease and before its expiry
    return left


def _record_exchanges(monkeypatch):
    """Test-only capture of every AF17 exchange error: (kind, code, deadline_ns - authority lease_ns)."""
    errors = []
    original = AuthorityConnection._exchange

    def exchange(self, request, *, fds=()):
        try:
            return original(self, request, fds=fds)
        except Exception as error:
            errors.append((request.kind.name, str(error), request.deadline_ns - self._lease))
            raise

    monkeypatch.setattr(AuthorityConnection, "_exchange", exchange)
    return errors


@pytest.mark.parametrize("remaining", [2.0, LEASE_REMAINING_SECONDS])
def test_a_cancel_in_the_last_second_of_the_authority_lease_is_confirmed_natively(broker_stack, monkeypatch, remaining):
    """The lowest level: RunBroker.cancel with no deadline (as the readiness facade calls it). 2.0 s is the control."""
    broker, facade, _, _ = broker_stack
    errors = _record_exchanges(monkeypatch)
    stage_all(broker_stack)
    left = _wait_until_lease_remaining(broker.connection, remaining) if remaining < 1 else None
    if left is None:
        assert broker.connection._lease / 1e9 - time.monotonic() > 1.0
    result = broker.cancel("readiness-start-failed")
    observed = dict(native_epoch_confirmed=result.native_epoch_confirmed, issuer_dead=result.issuer_dead, exchange_errors=errors)
    # the authority helper's own exit (si_code 1, status 0: its cleanup) versus a revoke SIGKILL (si_code 2)
    assert observed == dict(native_epoch_confirmed=True, issuer_dead=False, exchange_errors=[]), (
        left, broker.connection.child._result)


@pytest.fixture
def marker_never_runtime(request, monkeypatch):
    """The composed runtime fixture with the sink declaring ``nonce-marker`` in ``marker-never`` mode."""
    declare(monkeypatch, {"sink-binding": dict(condition="nonce-marker", cwd="sink", mode="marker-never")})
    return request.getfixturevalue("runtime")


@pytest.mark.parametrize("placed_in_last_second", [False, True], ids=["control-early-cancel", "last-second-of-lease"])
def test_a_never_ready_marker_unit_at_start_up_closes_its_evidence(marker_never_runtime, monkeypatch, placed_in_last_second):
    """The full runtime entry (_OriginalRuntimeRun): the sink never writes its ready file, so start-up fails
    ML-PROBE-NOT-READY. In the second case the readiness failure's cancel waits until the last second of the
    authority lease, as in the live run (the only test-side change). Correct in both: the cancel is confirmed
    natively (no revoke), no persistence failure, cleanup complete, and the writer failed or closed.

    The persistence failure (the root kills the storage worker once the authority helper is gone) is a race with
    the dispatcher's terminal service; it appears in some runs only. The revoke and the incomplete closure are
    deterministic."""
    entry, scope, work = marker_never_runtime
    errors = _record_exchanges(monkeypatch)
    placed = []
    original_cancel = ProcessReadiness.cancel

    def cancel(self, reason="readiness-cancel"):
        if placed_in_last_second and reason == "readiness-start-failed" and not placed:
            placed.append(_wait_until_lease_remaining(entry._broker.connection, LEASE_REMAINING_SECONDS))
        return original_cancel(self, reason)

    monkeypatch.setattr(ProcessReadiness, "cancel", cancel)
    result = entry.start(scope)
    cancelled = entry._broker._cancel_result
    assert bool(placed) is placed_in_last_second and result.dispatch is not None and result.dispatch.diagnostic == "ML-PROBE-NOT-READY", result
    failure = result.persistence_failure
    observed = dict(
        native_epoch_confirmed=cancelled.native_epoch_confirmed, issuer_dead=cancelled.issuer_dead,
        exchange_errors=errors, persistence_failure=failure and (failure.diagnostic, failure.kind, failure.stage),
        cleanup_complete=result.cleanup_complete, workload_wait_unknown="ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN" in result.closure.diagnostics,
        writer_failed_or_closed=entry._storage.last_writer_state in ("failed", "closed"))
    assert observed == dict(native_epoch_confirmed=True, issuer_dead=False, exchange_errors=[], persistence_failure=None,
                            cleanup_complete=True, workload_wait_unknown=False, writer_failed_or_closed=True), (
        placed, entry._storage.last_writer_state, result.closure.diagnostics)

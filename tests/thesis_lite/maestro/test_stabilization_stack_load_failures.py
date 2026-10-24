"""S1b review findings 21 and 22: the two failures of the stack ``b049585bf`` under load 8.4-8.7 (S1c finding 45).

Reproduction before repair. Each test asserts the CORRECT behaviour, so it fails while the defect is present.
The tests never alter a request or a reply. Repaired per thesis DR-15 (S1b review finding 23): (B) by RB1
(ADR-ML3-PERSISTENCE-0001, S1a-1 revision); (A) by RA1 (ADR-ML3-PROBE-0001, S1b-1 revision), which refuses the
live W = 3.5 s at admission and caps an admitted window at run time, and RA4 (ADR-ML3-AFFA-0001, S1a-6).

(A) ``…-004408-freeze-vcu``: the start step of a ``nonce-marker`` unit is capped at the bootstrap lease
(``dispatcher.py`` ``_end``: ``min(end, bootstrap._lease)``). Nothing renews that lease inside one step: the
dispatcher renews only at a statement boundary with at most ``renew_margin`` (1.9 s live) left, and the
schedule admission never relates the readiness window W to the lease (5 s maximum, native). With W = 3.5 s
the attempts are at t0, t0 + 1.625 s and t0 + 3.25 s, and the third one is dropped by the lease cap
(``providers.py``: ``if at >= deadline.monotonic_seconds: break``). The readiness failure then cancels with
well under a second of lease left. The run-bootstrap root ends at its own lease (``bootstrap.c``
``now>=s.lease`` -> ``cleanup``), which SIGKILLs every helper, the storage worker and the authority
included, unless the cancel and the terminal fence (which moves the root into terminal mode) finish first.
A cancel that takes longer than the remaining lease (a native freeze that waits on a unit blocked in the
kernel, or load) therefore loses the authority and the storage worker: revoke, ``ML-PERSIST-CHILD``,
``ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN``.

(B) ``…-004728-cancel-paused``: ``PersistenceClient._live`` reads the cancel latch twice. A cancel that lands
between the first read (which raises the healthy ``PersistenceCancelled``) and the final check is refused as
a plain ``PersistenceError("ML-PERSIST-CLOSED")`` (or, one call earlier, as ``ML-BOOT-CLOSED`` from the
child check). ``_rpc`` records it as the persistence failure and calls ``_fail()``: the storage worker gets
SIGTERM, so no terminal record reaches the writer and the closure is incomplete. Live: the RPC started
0.17 ms before the cancel request and failed 0.31 ms after it.
"""

import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro import persistence as persistence_module
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.persistence import PersistenceClient
from xverse.maestro.providers import (CANCEL_CLOSE_RESERVE_SECONDS, NATIVE_CANCEL_CLOSE_SECONDS, ProbePolicy,
                                      ProcessReadiness, readiness_window_bound)
from xverse.maestro.schedule_plan import ScheduleError

from .test_stabilization_s1b_broker import NS, declare
from .test_stabilization_s1b_start_failure import _record_exchanges
from .test_affa_native import authority_binary as authority_binary
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_runtime_entry import runtime as runtime

# ---------------------------------------------------------------------------------------------------------------
# (B) a cancel between the two latch reads of PersistenceClient._live
# ---------------------------------------------------------------------------------------------------------------

TARGET = 2  # the second ordinary tick-complete statement, as in test_stabilization_cancel.py


@pytest.mark.parametrize("window", ["control-before-live", "before-final-check", "before-child-check",
                                    "in-flight-child-check"])
def test_a_cancel_between_the_live_checks_is_not_a_storage_failure(runtime, monkeypatch, window):
    """The cancel is issued from another thread (as the live harness's canceller does) while the dispatcher's
    ordinary ``schedule`` call is inside its ``validation`` stage, after ``_live`` has read the latch as not
    cancelled. ``before-final-check``: after the child wait (``persistence.py`` final check, live signature
    ``ML-PERSIST-CLOSED`` at ``validation``). ``before-child-check``: before ``check_child(live=True)``, whose
    root check then refuses the cancelled run. Correct: the refusal is the healthy ``PersistenceCancelled``, so
    the storage owner stays usable, the terminal records and the writer close, and cleanup completes.
    ``control-before-live``: the cancel lands before ``_live`` (the S1a pre-send case); it passes today, so the
    expected outcome is reachable on this stack. ``in-flight-child-check`` (added with the RB1 repair, finding
    23): the same window in the first in-flight ``_live`` of that call, after the request is sent; the reply is
    then still accepted within the S1a-1 grace."""
    entry, scope, work = runtime
    stopped = threading.Event()
    seen, armed, placed = [], threading.local(), []

    def stop_from_another_thread():
        def stop():
            entry.stop("fixture-run", reason="owned-cancel-" + window)
            stopped.set()

        thread = threading.Thread(target=stop)
        thread.start()
        thread.join(5)
        assert stopped.is_set(), "entry.stop did not return within 5 s"

    original_rpc = PersistenceClient._rpc

    def rpc(self, kind, body, end, **kw):
        if kind == "schedule" and isinstance(body, dict) and body.get("kind") == "tick-complete":
            seen.append(True)
        armed.value = len(seen) == TARGET and not stopped.is_set() and not placed
        if armed.value and window == "control-before-live":
            armed.value = False
            placed.append(time.monotonic())
            stop_from_another_thread()
        try:
            return original_rpc(self, kind, body, end, **kw)
        finally:
            armed.value = False

    name = "wait_child" if window in ("control-before-live", "before-final-check") else "check_child"
    original_hook = getattr(persistence_module, name)
    calls = []

    def hook(*args, **kwargs):
        if getattr(armed, "value", False):
            calls.append(True)  # in-flight-child-check: the 1st call is _live at validation, the 2nd in flight
        if getattr(armed, "value", False) and (window != "in-flight-child-check" or len(calls) == 2):
            armed.value = False
            assert not entry._storage.latch.cancelled  # the first latch read in _live saw a live run
            placed.append(time.monotonic())
            stop_from_another_thread()
        return original_hook(*args, **kwargs)

    monkeypatch.setattr(PersistenceClient, "_rpc", rpc)
    monkeypatch.setattr(persistence_module, name, hook)
    result = entry.start(scope)
    assert placed and stopped.is_set(), "the targeted call was never reached"
    storage = entry._storage
    failure = result.persistence_failure
    observed = dict(
        storage_failed=storage._failed,
        persistence_failure=failure and (failure.diagnostic, failure.kind, failure.stage),
        dispatch=result.dispatch and result.dispatch.diagnostic,
        writer_failed_or_closed=storage.last_writer_state in ("failed", "closed"),
        cleanup_complete=result.cleanup_complete,
        workload_wait_unknown="ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN" in result.closure.diagnostics)
    assert observed == dict(storage_failed=False, persistence_failure=None, dispatch="ML-SCHEDULE-CANCELLED",
                            writer_failed_or_closed=True, cleanup_complete=True, workload_wait_unknown=False), (
        storage.last_writer_state, result.closure.diagnostics)
    reader = EvidenceStore.read_run(work.parent / "argus")
    terminals = [e for e in reader.records()
                 if e.get("extensions", {}).get("xverse.maestro", {}).get("action") == "run-terminal"]
    assert len(terminals) == 1 and terminals[0]["extensions"]["xverse.maestro"]["outcome"] == "cancelled", terminals


# ---------------------------------------------------------------------------------------------------------------
# (A) a long readiness window inside one unrenewed bootstrap lease
# ---------------------------------------------------------------------------------------------------------------

WINDOW_SECONDS = 3.5  # the live harness's OWNED_READINESS_TIMEOUT_S
# RA1 (finding 23): W = 3.5 s cannot fit a fresh lease and is refused at admission; the run-time cap is exercised
# with an admitted window below the fixture's bound 5 - 2.25 - 0.5 = 2.25 s (2.0 s, the value of thesis DR-15 H1).
ADMITTED_WINDOW_SECONDS = 2.0
ACTION_TIMEOUTS = {"prepare": 2, "start": 5, "observe": 4, "stop": 5, "cleanup": 5}  # the live harness's budgets
# The start step is dispatched with this much bootstrap lease left: above the dispatcher's renewal margin
# (service_operation_count 4 x operation 0.5 s + 0.5 s = 2.5 s in this fixture, 1.9 s live), so it is not
# renewed, and below W, as in the live run (2.3-3.5 s left at the start of start-lite-driver).
PLACED_LEASE_SECONDS = 2.8
# The live readiness cancel ran for at least 0.39 s (CANCEL sent at about 5.05 s, lease end at 5.44 s or later)
# and the native close may take up to 2 s (run_authority.c close_end). The wait is applied before the cancel,
# so the client's 1 s CANCEL deadline is not exercised here (finding 22, residual A-iii).
CANCEL_COMPLETION_SECONDS = 1.5


@pytest.fixture(params=[WINDOW_SECONDS, ADMITTED_WINDOW_SECONDS], ids=["live-window", "admitted-window"])
def long_window_runtime(request, monkeypatch):
    """The composed runtime with the sink declaring ``nonce-marker`` (``marker-never``), a readiness window
    W (policy timeout W, observe timeout 4) and the live action timeouts (``use_action_timeouts``). W is the live
    3.5 s or the admitted 2.0 s. Returns the ScheduleError when the schedule is refused at admission."""
    window = request.param
    from . import test_launcher, test_runtime_entry

    declare(monkeypatch, {"sink-binding": dict(condition="nonce-marker", cwd="sink", mode="marker-never",
                                               observe_timeout=ACTION_TIMEOUTS["observe"])})
    declared = test_launcher.compiled

    def compiled(docs):
        for binding in docs["deployment.json"]["spec"]["bindings"]:
            for action in binding["extensions"][NS]["actions"]:
                action["timeoutSeconds"] = ACTION_TIMEOUTS[action["phase"]]
        return declared(docs)

    monkeypatch.setattr(test_launcher, "compiled", compiled)
    admit = test_runtime_entry.admit_schedule

    def admit_schedule(prepared, *, policies, **kw):
        policies = tuple(ProbePolicy(p.unit_id, p.freshness_seconds, p.cadence_seconds, window, p.attempts)
                         for p in policies)
        kw.update(use_action_timeouts=True, active_seconds=20)
        return admit(prepared, policies=policies, **kw)

    monkeypatch.setattr(test_runtime_entry, "admit_schedule", admit_schedule)
    try:
        return request.getfixturevalue("runtime")
    except ScheduleError as error:  # a repair may refuse a window that cannot fit the lease
        return error


def _instrument(entry, monkeypatch, *, cancel_completion=0.0):
    """Place the sink's start step at PLACED_LEASE_SECONDS of bootstrap lease left (a wait, never a change of
    any request), record each sink readiness query and the lease left at the readiness-failure cancel, and
    optionally let that cancel complete CANCEL_COMPLETION_SECONDS after the failure."""
    facts = dict(placed=None, queries=[], cancel_left=None, renewals_before_start=None, lease=None)
    original_effect = FiniteDispatcher._effect

    def effect(self, step):
        if step.phase == "start" and "sink" in step.unit_id and facts["placed"] is None:
            gap = self.bootstrap._lease / 1e9 - PLACED_LEASE_SECONDS - time.monotonic()
            if gap > 0:
                time.sleep(gap)
            facts["placed"] = self.bootstrap._lease / 1e9 - time.monotonic()
            facts["renewals_before_start"] = self.lease_renewals
            facts["lease"] = min(self.bootstrap._lease, entry._broker.connection._lease) / 1e9
        return original_effect(self, step)

    original_query = ProcessReadiness._query

    def query(self, unit_id, deadline):
        if self._readying is not None and "sink" in unit_id:
            facts["queries"].append(time.monotonic())
        return original_query(self, unit_id, deadline)

    original_cancel = ProcessReadiness.cancel

    def cancel(self, reason="readiness-cancel"):
        if reason == "readiness-start-failed" and facts["cancel_left"] is None:
            facts["cancel_left"] = entry._broker.session._lease / 1e9 - time.monotonic()
            if cancel_completion:
                time.sleep(cancel_completion)
        return original_cancel(self, reason)

    monkeypatch.setattr(FiniteDispatcher, "_effect", effect)
    monkeypatch.setattr(ProcessReadiness, "_query", query)
    monkeypatch.setattr(ProcessReadiness, "cancel", cancel)
    return facts


def _refused(runtime):
    """RA1: the live window is refused at admission; an admitted window must not be."""
    if isinstance(runtime, ScheduleError):
        assert str(runtime) == "ML-SCHEDULE-READINESS-WINDOW", runtime
        assert WINDOW_SECONDS > readiness_window_bound(0.5)  # the fixture's operation_seconds
        return True
    return False


def test_a_declared_readiness_window_is_not_silently_cut_by_the_lease(long_window_runtime, monkeypatch, request):
    """Live (A): 2 of 3 attempts, the third dropped by the start step's lease cap. Correct: either the schedule
    is refused at admission (W cannot fit the lease), or every declared attempt is made before
    ML-PROBE-NOT-READY (Maestro renews, or spaces the attempts inside the lease it actually has).
    Finding 23 (RA1): the live window is refused at admission; the admitted window makes its 3 attempts within the
    capped window, the last one at least CANCEL_CLOSE_RESERVE before the lease."""
    if _refused(long_window_runtime):
        assert request.node.callspec.id == "live-window"
        return
    assert request.node.callspec.id == "admitted-window"
    entry, scope, work = long_window_runtime
    facts = _instrument(entry, monkeypatch)
    result = entry.start(scope)
    assert facts["placed"] is not None and 2.0 < facts["placed"] <= PLACED_LEASE_SECONDS + 0.05, facts
    assert result.dispatch is not None and result.dispatch.diagnostic == "ML-PROBE-NOT-READY", result
    assert len(facts["queries"]) == 3, facts
    assert facts["lease"] - facts["queries"][-1] >= CANCEL_CLOSE_RESERVE_SECONDS, facts
    assert facts["cancel_left"] > NATIVE_CANCEL_CLOSE_SECONDS, facts


def test_a_readiness_failure_cancel_that_takes_longer_than_the_lease_left_still_closes(long_window_runtime,
                                                                                       monkeypatch, request):
    """Live (A): the readiness cancel was issued with under a second of unrenewed lease left and did not finish
    before the lease end; the bootstrap root then killed the authority and the storage worker. Here the
    readiness-failure cancel completes CANCEL_COMPLETION_SECONDS after the failure (below the native close
    bound of 2 s). Correct: the cancel is confirmed natively, there is no persistence failure, cleanup is
    complete and the writer is failed or closed. Finding 23 (RA1): refused at admission for the live window; for
    the admitted window the cancel starts with more than the native close bound of lease left."""
    if _refused(long_window_runtime):
        assert request.node.callspec.id == "live-window"
        return
    assert request.node.callspec.id == "admitted-window"
    entry, scope, work = long_window_runtime
    errors = _record_exchanges(monkeypatch)
    facts = _instrument(entry, monkeypatch, cancel_completion=CANCEL_COMPLETION_SECONDS)
    result = entry.start(scope)
    assert facts["placed"] is not None and 2.0 < facts["placed"] <= PLACED_LEASE_SECONDS + 0.05, facts
    assert result.dispatch is not None and result.dispatch.diagnostic == "ML-PROBE-NOT-READY", result
    assert len(facts["queries"]) == 3 and facts["cancel_left"] > NATIVE_CANCEL_CLOSE_SECONDS, facts
    cancelled = entry._broker._cancel_result
    failure = result.persistence_failure
    observed = dict(
        native_epoch_confirmed=cancelled.native_epoch_confirmed, issuer_dead=cancelled.issuer_dead,
        exchange_errors=errors, persistence_failure=failure and (failure.diagnostic, failure.kind, failure.stage),
        cleanup_complete=result.cleanup_complete,
        workload_wait_unknown="ML-CLOSURE-WORKLOAD-WAIT-UNKNOWN" in result.closure.diagnostics,
        writer_failed_or_closed=entry._storage.last_writer_state in ("failed", "closed"))
    assert observed == dict(native_epoch_confirmed=True, issuer_dead=False, exchange_errors=[], persistence_failure=None,
                            cleanup_complete=True, workload_wait_unknown=False, writer_failed_or_closed=True), (
        facts, entry._storage.last_writer_state, result.closure.diagnostics, entry._session._root_result)

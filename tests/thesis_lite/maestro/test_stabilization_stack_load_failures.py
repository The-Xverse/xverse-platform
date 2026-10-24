"""S1b review findings 21 and 22: the two failures of the stack ``b049585bf`` under load 8.4-8.7 (S1c finding 45).

Reproduction before repair. Each test asserts the CORRECT behaviour, so it fails while the defect is present.
The tests never alter a request or a reply. Repaired per thesis DR-15 (S1b review finding 23): (B) by RB1
(ADR-ML3-PERSISTENCE-0001, S1a-1 revision); (A) by RA1 (ADR-ML3-PROBE-0001, S1b-1 revision), which refuses the
live W = 3.5 s at admission and caps an admitted window at run time, and RA4 (ADR-ML3-AFFA-0001, S1a-6).
Extended per thesis DR-16 (S1b review finding 25): RA2 renews before a marker start step, RA5 adds the failure
statement to the reserve (admission bound 2.75 - 2 x operation_seconds: 1.75 s in this fixture), each marker start
records W, W', L and t0 (``ReadinessWindow``) and a cut window ends ``ML-PROBE-WINDOW-CUT``; the RB1 fail-closed
side (finding 24 MEDIUM-3) is pinned in (B).

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

import os
import select
import signal
import socket
import threading
import time

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro import persistence as persistence_module
from xverse.maestro.bootstrap import BootstrapError
from xverse.maestro.dispatcher import FiniteDispatcher
from xverse.maestro.persistence import PersistenceCancelled, PersistenceClient, PersistenceError
from xverse.maestro.providers import (NATIVE_CANCEL_CLOSE_SECONDS, ProbePolicy, ProcessReadiness, cancel_close_reserve,
                                      readiness_window_bound)
from xverse.maestro.run_broker import RunBroker
from xverse.maestro.schedule_plan import ScheduleError

from .test_stabilization_s1b_broker import NS, declare
from .test_stabilization_s1b_start_failure import _delay_cancel_reply, _record_exchanges
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


def _fault_in_the_targeted_live(entry, monkeypatch, name, fault, *, cancel=True):
    """In the targeted call's ``validation`` ``_live`` (as above), at ``name`` (``check_child``: before the child
    check; ``wait_child``: before the final check), optionally cancel from another thread and then apply
    ``fault(storage)``. Returns what ``_live`` raised in the targeted call and whether the latch was cancelled
    at the fault."""
    seen, armed, targeted, placed, raised = [], threading.local(), threading.local(), [], []
    original_rpc, original_live = PersistenceClient._rpc, PersistenceClient._live

    def rpc(self, kind, body, end, **kw):
        if kind == "schedule" and isinstance(body, dict) and body.get("kind") == "tick-complete":
            seen.append(True)
        targeted.value = armed.value = len(seen) == TARGET and not placed
        try:
            return original_rpc(self, kind, body, end, **kw)
        finally:
            targeted.value = armed.value = False

    def live(self, **kw):
        try:
            return original_live(self, **kw)
        except Exception as error:
            if getattr(targeted, "value", False):
                raised.append(error)
            raise

    original_hook = getattr(persistence_module, name)

    def hook(*args, **kwargs):
        if getattr(armed, "value", False):
            armed.value = False
            storage = entry._storage
            assert not storage.latch.cancelled
            if cancel:
                thread = threading.Thread(target=entry.stop, args=("fixture-run",), kwargs=dict(reason="rb1-negative"))
                thread.start()
                thread.join(5)
                assert not thread.is_alive() and storage.latch.cancelled
            placed.append(storage.latch.cancelled)
            fault(storage)
        return original_hook(*args, **kwargs)

    monkeypatch.setattr(PersistenceClient, "_rpc", rpc)
    monkeypatch.setattr(PersistenceClient, "_live", live)
    monkeypatch.setattr(persistence_module, name, hook)
    return raised, placed


def _kill_the_storage_worker(storage):
    signal.pidfd_send_signal(storage._pidfd, signal.SIGKILL)
    assert select.select([storage._pidfd], [], [], 2)[0]


def _set_failed(storage):
    storage._failed = True  # as a concurrent _fail() would, without its SIGTERM


def _replace_the_socket(storage, kept=[]):
    replacement, other = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    kept.extend((replacement, other))
    os.dup2(replacement.fileno(), storage._pins[1].fileno())  # the channel fd now names another socket


def _refuse_at_the_root(storage):
    raise BootstrapError("ML-BOOT-CLOSED")  # the root's own refusal (bootstrap._live), with no cancel


@pytest.mark.parametrize("name, fault, cancel, expected", [
    pytest.param("check_child", _kill_the_storage_worker, True, ("ML-PERSIST-CHILD", PersistenceError),
                 id="child-killed"),
    pytest.param("wait_child", _set_failed, True, ("ML-PERSIST-CLOSED", PersistenceError), id="failed-set"),
    pytest.param("check_child", _replace_the_socket, True, ("ML-PERSIST-CHILD", PersistenceError),
                 id="socket-replaced"),
    pytest.param("check_child", _refuse_at_the_root, False, ("ML-BOOT-CLOSED", BootstrapError),
                 id="root-refusal-without-cancel"),
])
def test_rb1_a_real_storage_fault_with_or_without_a_cancel_still_fails_closed(runtime, monkeypatch, name, fault,
                                                                               cancel, expected):
    """Finding 24 MEDIUM-3 (ADR-ML3-PERSISTENCE-0001, RB1 residual note): with the latch cancelled in the RB1
    windows, a killed storage worker, ``_failed`` and a replaced socket identity are still a plain
    ``PersistenceError``, recorded as the RPC failure at ``validation``, with ``_fail()``; never
    ``PersistenceCancelled``. A root refusal without a cancel also still fails closed (the RB1 re-check needs the
    cancel)."""
    entry, scope, work = runtime
    raised, placed = _fault_in_the_targeted_live(entry, monkeypatch, name, fault, cancel=cancel)
    result = entry.start(scope)
    assert placed == [cancel], "the targeted call was never reached"
    code, kind = expected
    failure = result.persistence_failure
    assert len(raised) == 1 and type(raised[0]) is kind and str(raised[0]) == code, raised
    assert not isinstance(raised[0], PersistenceCancelled)
    assert failure is not None and (failure.diagnostic, failure.kind, failure.stage) == (code, "schedule", "validation")
    assert entry._storage._failed


# ---------------------------------------------------------------------------------------------------------------
# (A) a long readiness window inside one unrenewed bootstrap lease
# ---------------------------------------------------------------------------------------------------------------

WINDOW_SECONDS = 3.5  # the live harness's OWNED_READINESS_TIMEOUT_S
# RA1/RA5 (findings 23, 25): W = 3.5 s cannot fit a fresh lease and is refused at admission; the run is exercised
# with an admitted window below the fixture's bound 5 - (2 + 0.5 + 0.25) - 0.5 = 1.75 s.
ADMITTED_WINDOW_SECONDS = 1.5
OPERATION_SECONDS = 0.5  # the composed fixture's operation_seconds
RESERVE_SECONDS = cancel_close_reserve(OPERATION_SECONDS)  # 2.75 s
ACTION_TIMEOUTS = {"prepare": 2, "start": 5, "observe": 4, "stop": 5, "cleanup": 5}  # the live harness's budgets
# The start step is dispatched with this much bootstrap lease left: above the dispatcher's renewal margin
# (service_operation_count 4 x operation 0.5 s + 0.5 s = 2.5 s in this fixture, 1.9 s live), so it is not
# renewed, and below W, as in the live run (2.3-3.5 s left at the start of start-lite-driver).
PLACED_LEASE_SECONDS = 2.8
# A start step placed with this much lease left, with RA2 disabled, is cut but keeps W' > 0: the cap then leaves
# exactly the reserve after the last attempt (finding 25, M2).
PLACED_CUT_LEASE_SECONDS = 3.6
# The live readiness cancel ran for at least 0.39 s (CANCEL sent at about 5.05 s, lease end at 5.44 s or later)
# and the native close may take up to 2 s (run_authority.c close_end). Finding 25 (M2): the full 2 s.
CANCEL_COMPLETION_SECONDS = NATIVE_CANCEL_CLOSE_SECONDS


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


def _instrument(entry, monkeypatch, *, cancel_completion=0.0, placed=PLACED_LEASE_SECONDS, renew=True):
    """Place the sink's start step at ``placed`` seconds of bootstrap lease left (a wait, never a change of any
    request), record each sink readiness query and the lease left at the readiness-failure cancel, and optionally
    let that cancel complete ``cancel_completion`` after the failure. ``renew=False`` disables RA2 (a forced cut)."""
    facts = dict(placed=None, queries=[], cancel_left=None, renewals_before_start=None, lease=None)
    original_effect = FiniteDispatcher._effect
    if not renew:
        monkeypatch.setattr(FiniteDispatcher, "_renew_before_marker_start", lambda self, unit: None)

    def effect(self, step):
        if step.phase == "start" and "sink" in step.unit_id and facts["placed"] is None:
            gap = self.bootstrap._lease / 1e9 - placed - time.monotonic()
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
        assert WINDOW_SECONDS > readiness_window_bound(OPERATION_SECONDS)
        return True
    return False


def _sink_window(entry, result):
    """The sink's ReadinessWindow (S1b-1 revision), the same record in the facade and the dispatch result."""
    windows = [w for w in result.dispatch.readiness_windows if "sink" in w.unit_id]
    assert len(windows) == 1 and windows[0] in entry._driver.facade._windows, result.dispatch.readiness_windows
    return windows[0]


def _failure_events(work):
    reader = EvidenceStore.read_run(work.parent / "argus")
    return [e["extensions"]["xverse.maestro"] for e in reader.records()
            if e.get("extensions", {}).get("xverse.maestro", {}).get("diagnosticCode", "").startswith("ML-PROBE")]


def test_a_declared_readiness_window_is_not_silently_cut_by_the_lease(long_window_runtime, monkeypatch, request):
    """Live (A): 2 of 3 attempts, the third dropped by the start step's lease cap. Correct: either the schedule
    is refused at admission (W cannot fit the lease), or every declared attempt is made before
    ML-PROBE-NOT-READY (Maestro renews, or spaces the attempts inside the lease it actually has).
    Finding 23 (RA1): the live window is refused at admission. Finding 25 (RA2, M1): the start step, placed with
    less than its need W + reserve + operation_seconds of lease left, is renewed first and keeps W' = W; its
    window record shows it, and its 3 attempts end at least the reserve before the lease."""
    if _refused(long_window_runtime):
        assert request.node.callspec.id == "live-window"
        return
    assert request.node.callspec.id == "admitted-window"
    entry, scope, work = long_window_runtime
    facts = _instrument(entry, monkeypatch)
    result = entry.start(scope)
    assert facts["placed"] is not None and 2.0 < facts["placed"] <= PLACED_LEASE_SECONDS + 0.05, facts
    assert facts["placed"] < ADMITTED_WINDOW_SECONDS + RESERVE_SECONDS + OPERATION_SECONDS  # below the need
    assert result.dispatch is not None and result.dispatch.diagnostic == "ML-PROBE-NOT-READY", result
    assert result.dispatch.lease_renewals > facts["renewals_before_start"], facts  # RA2 renewed
    window = _sink_window(entry, result)
    assert (window.declared_seconds, window.window_seconds, window.cut) == (
        ADMITTED_WINDOW_SECONDS, ADMITTED_WINDOW_SECONDS, False), window
    assert window.lease_end - window.began >= ADMITTED_WINDOW_SECONDS + RESERVE_SECONDS, window
    assert len(facts["queries"]) == 3 and facts["queries"][0] >= window.began, facts
    assert facts["queries"][-1] - window.began >= ADMITTED_WINDOW_SECONDS - 0.25 - 0.01, (facts, window)  # all of W
    assert window.lease_end - facts["queries"][-1] >= RESERVE_SECONDS, (facts, window)
    assert facts["cancel_left"] > NATIVE_CANCEL_CLOSE_SECONDS + OPERATION_SECONDS, facts
    assert [e["diagnosticCode"] for e in _failure_events(work)] == ["ML-PROBE-NOT-READY"]


def test_a_forced_cut_window_is_recorded_and_diagnosed(long_window_runtime, monkeypatch, request):
    """Finding 25 (M1): with RA2 disabled, the same placement leaves less than the reserve after t0, so the cap
    spends W' < W. The cut is in the window record and ends ML-PROBE-WINDOW-CUT (cause deadline-exceeded) in the
    dispatch result and the Argus failure event, never ML-PROBE-NOT-READY."""
    if _refused(long_window_runtime):
        return
    entry, scope, work = long_window_runtime
    facts = _instrument(entry, monkeypatch, renew=False)
    result = entry.start(scope)
    assert facts["placed"] is not None and 2.0 < facts["placed"] <= PLACED_LEASE_SECONDS + 0.05, facts
    assert result.dispatch.lease_renewals == facts["renewals_before_start"], facts  # no renewal
    window = _sink_window(entry, result)
    assert window.cut and window.window_seconds < window.declared_seconds == ADMITTED_WINDOW_SECONDS, window
    assert window.window_seconds == pytest.approx(
        max(0.0, window.lease_end - RESERVE_SECONDS - window.began), abs=1e-9), window
    assert len(facts["queries"]) == 3, facts
    assert result.dispatch.diagnostic == "ML-PROBE-WINDOW-CUT", result
    assert [(e["diagnosticCode"], e["cause"]) for e in _failure_events(work)] == [
        ("ML-PROBE-WINDOW-CUT", "deadline-exceeded")]


def test_a_cut_window_cancel_that_takes_the_full_native_close_still_reaches_the_fence(long_window_runtime,
                                                                                      monkeypatch):
    """Finding 25 (M2, RA5): the worst case the reserve is sized for. RA2 is disabled and the start step is placed so
    that the cap binds with W' > 0, so the last attempt keeps exactly the reserve (2 s close + the failure
    statement + 0.25 s) before the lease. The readiness-failure K.CANCEL reply then takes the full 2.0 s native
    close. Correct: the root and the authority are still alive, inside their lease, when the terminal fence
    (``service_terminal``) runs; the cancel is confirmed natively and the closure is complete."""
    if _refused(long_window_runtime):
        return
    entry, scope, work = long_window_runtime
    errors = _record_exchanges(monkeypatch)
    delays = _delay_cancel_reply(monkeypatch, NATIVE_CANCEL_CLOSE_SECONDS)
    facts = _instrument(entry, monkeypatch, placed=PLACED_CUT_LEASE_SECONDS, renew=False)
    fence = []
    original_terminal = RunBroker.service_terminal

    def service_terminal(self, deadline):
        if not fence:
            root, authority = self.session, self.connection.child
            fence.append(dict(
                lease_left=root._lease / 1e9 - time.monotonic(),
                root_alive=root._root_result is None and not select.select(
                    [root._pidfd_capability.fileno()], [], [], 0)[0],
                authority_alive=authority._result is None and not select.select(
                    [authority._capability.fileno()], [], [], 0)[0]))
        return original_terminal(self, deadline)

    monkeypatch.setattr(RunBroker, "service_terminal", service_terminal)
    result = entry.start(scope)
    window = _sink_window(entry, result)
    assert window.cut and 0 < window.window_seconds < ADMITTED_WINDOW_SECONDS, window
    assert window.lease_end - facts["queries"][-1] >= RESERVE_SECONDS, (facts, window)
    assert len(delays) == 1 and delays[0] >= NATIVE_CANCEL_CLOSE_SECONDS, delays
    assert result.dispatch.diagnostic == "ML-PROBE-WINDOW-CUT", result
    assert fence and fence[0]["root_alive"] and fence[0]["authority_alive"] and fence[0]["lease_left"] > 0, (
        fence, facts, window)
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
        fence, facts, window, entry._storage.last_writer_state, result.closure.diagnostics)


def test_a_readiness_failure_cancel_that_takes_longer_than_the_lease_left_still_closes(long_window_runtime,
                                                                                       monkeypatch, request):
    """Live (A): the readiness cancel was issued with under a second of unrenewed lease left and did not finish
    before the lease end; the bootstrap root then killed the authority and the storage worker. Here the
    readiness-failure cancel completes CANCEL_COMPLETION_SECONDS after the failure (finding 25: the full native
    close bound of 2 s). Correct: the cancel is confirmed natively, there is no persistence failure, cleanup is
    complete and the writer is failed or closed. Finding 23 (RA1): refused at admission for the live window; for
    the admitted window (renewed by RA2, finding 25) the cancel starts with more than the reserve's close and
    failure-statement terms of lease left."""
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
    assert len(facts["queries"]) == 3 and facts["cancel_left"] > NATIVE_CANCEL_CLOSE_SECONDS + OPERATION_SECONDS, facts
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

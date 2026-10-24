"""Simulator-time fault triggers (ADR-ML3-SIMTIME-0001; review-simtime-faults findings 1-2).

Pure cases: the capability flag, the binding, resolution and horizon, tick-mode compatibility, schedule admission
(the D-4c refusal and the thaw check), the channel codec, and the scheduler against a fake hub over a socketpair.
The composed case runs the native Maestro dispatcher fixture with a fake hub thread: a step-hold freeze and a
remote-relay loss. Worker-side code is involved: run with the installed wheel.
"""

from __future__ import annotations

import copy
import json
import socket
import threading
import time

import pytest

import xverse.faults as faults_package
from xverse.faults import FaultError, HubChannel, SimTimeFaultScheduler, SimulationClock, resolve_simtime, resolve_schedule
from xverse.faults.boundary import BoundaryOutcome, ProcessBoundary
from xverse.faults.simtime import FRAME_MAX, HOLD, RELAY, decode_hub_frame, encode_frame
from xverse.maestro import PreparationError, prepare
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.schedule_plan import ScheduleError, admit_schedule, decode_schedule

from .support import PLANNED_TICKS, compiled_plan, fault, parameter, with_sensor
from ..maestro.test_preparation import PIN, compiled, documents as maestro_documents

DOMAIN, SOURCE, STEP = "experiment-time", "source-instance", 50_000_000
MEASURED = dict(max_step_host_s=0.05, handshake_s=0.5, hold_bound_s=1.0)


def clock(**kw):
    return SimulationClock(**{"domain": DOMAIN, "source_unit": SOURCE, "step_ns": STEP, "horizon_ns": 30_000_000_000, **kw})


def simfault(fault_id, kind, element, at, duration, parameters=None, unit="s", duration_unit=None, domain=DOMAIN):
    item = fault(fault_id, kind, element, at=None, duration=1, parameters=parameters)
    intent = item["extensions"]["io.xverse.experiment"]
    intent["trigger"] = {"kind": "time", "at": at, "unit": unit}
    intent["duration"] = {"value": duration, "unit": duration_unit or unit}
    intent["timeDomainId"] = domain
    return item


def docs_with(items):
    docs = with_sensor(maestro_documents())
    docs["scenario.json"]["spec"]["faults"] = copy.deepcopy(items)
    return docs


def prepared_with(items, binding):
    result, resources = compiled(docs_with(items))
    return prepare(result, resources, provider_descriptors=(PIN,), fault_clock=binding)


FREEZE = simfault("f-frz", "freeze", "sink-instance", 1.5, 0.5)
LOSS = simfault("f-loss", "loss", "sample-flow", 1.0, 0.25, [parameter("every", 2)])


# --- capability contract (decision 9) -----------------------------------------------------------------------------

def test_capability_flag_is_pinned():
    assert faults_package.SIMULATION_TIME_TRIGGERS is True
    assert "SIMULATION_TIME_TRIGGERS" in faults_package.__all__


# --- binding ----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("change", [dict(step_ns=0), dict(step_ns=1.5), dict(horizon_ns=1), dict(domain=""),
                                    dict(source_unit="bad unit"), dict(handshake_s=0), dict(handshake_s=float("nan")),
                                    dict(hold_bound_s=6.0), dict(max_step_host_s=0.0), dict(handshake_s=True)])
def test_binding_validation(change):
    with pytest.raises(ValueError):
        clock(**change)


def test_l8_reproduction_without_binding_and_admission_with_it():
    result, resources = compiled(docs_with([FREEZE]))
    with pytest.raises(PreparationError, match="XVERSE-FAULT-HORIZON"):
        prepare(result, resources, provider_descriptors=(PIN,))  # rc.1 behaviour kept without a binding (L-8)
    prepared = prepared_with([FREEZE, LOSS], clock())
    assert prepared.fault_clock == clock() and b'"faultClock"' in prepared.canonical_bytes


def test_plans_without_binding_keep_their_bytes():
    result, resources = compiled()
    plain = prepare(result, resources, provider_descriptors=(PIN,))
    assert plain.fault_clock is None and b"faultClock" not in plain.canonical_bytes
    bound = prepare(result, resources, provider_descriptors=(PIN,), fault_clock=clock())
    assert bound.lifecycle_digest != plain.lifecycle_digest and bound.faults == ()


def test_binding_must_name_the_admitted_domain_and_a_deployed_source():
    with pytest.raises(PreparationError, match="ML-TIME"):
        prepared_with([LOSS], clock(domain="other-domain"))
    with pytest.raises(PreparationError, match="ML-PROJECTION"):
        prepared_with([LOSS], clock(source_unit="hub-instance"))


# --- resolution and horizon (decision 2) ----------------------------------------------------------------------------

def plan_of(items):
    return compiled_plan(items, docs=docs_with([]))


def test_exact_ns_and_grid_rounding():
    items = [simfault("f-a", "freeze", "sink-instance", 1510, 10, unit="ms"), simfault("f-b", "stale", "sample-flow", 250, 1, unit="ms")]
    by_id = {e.fault_id: e for e in resolve_simtime(plan_of(items), clock())}
    a, b = by_id["f-a"], by_id["f-b"]
    assert (a.mode, a.at_ns, a.duration_ns, a.onset_step, a.clear_step) == (HOLD, 1_510_000_000, 10_000_000, 31, 32)
    assert (b.mode, b.at_ns, b.duration_ns, b.onset_step, b.clear_step) == (RELAY, 250_000_000, 1_000_000, 5, 6)


def test_horizon_is_checked_in_simulator_time():
    assert resolve_simtime(plan_of([simfault("f-h", "stale", "sample-flow", 29.5, 0.5)]), clock())
    with pytest.raises(FaultError) as caught:
        resolve_simtime(plan_of([simfault("f-h", "stale", "sample-flow", 29500, 510, unit="ms")]), clock())
    assert caught.value.code == "XVERSE-FAULT-HORIZON"


@pytest.mark.parametrize("item, code", [
    (simfault("f-c", "crash", "sink-instance", 1, 0), "XVERSE-FAULT-SIMTIME-KIND"),
    (simfault("f-d", "sensorDropout", "front-sensor", 1, 1), "XVERSE-FAULT-SIMTIME-KIND"),
    (simfault("f-u", "duplicate", "sample-flow", 1, 1, [parameter("copies", 1)]), "XVERSE-FAULT-SIMTIME-KIND"),
    (simfault("f-z", "freeze", "sample-flow", 1, 1), "XVERSE-FAULT-SIMTIME-KIND"),
    (simfault("f-s", "freeze", SOURCE, 1, 1), "XVERSE-FAULT-SIMTIME-SOURCE"),
    (simfault("f-t", "stale", "sample-flow", 3, 1, unit="tick"), "XVERSE-FAULT-SIMTIME-TRIGGER"),
    (fault("f-o", "stale", "sample-flow", at=None, order=1, duration=1), "XVERSE-FAULT-SIMTIME-TRIGGER"),
    (simfault("f-dt", "delay", "sample-flow", 1, 1, [parameter("delay-ticks", 1)]), "XVERSE-FAULT-PARAMETER"),
    (simfault("f-ar", "stale", "sample-flow", 1, 1, [parameter("arbitration", "serialize", "string")]), "XVERSE-FAULT-PARAMETER"),
])
def test_refused_entries(item, code):
    with pytest.raises(FaultError) as caught:
        resolve_simtime(plan_of([item]), clock())
    assert caught.value.code == code


def test_overlap_on_one_target_is_refused_and_disjoint_windows_are_admitted():
    with pytest.raises(FaultError) as caught:
        resolve_simtime(plan_of([simfault("f-1", "stale", "sample-flow", 1, 1), simfault("f-2", "loss", "sample-flow", 1.5, 1, [parameter("every", 2)])]), clock())
    assert caught.value.code == "XVERSE-FAULT-OVERLAP"
    disjoint = resolve_simtime(plan_of([simfault("f-1", "stale", "sample-flow", 1, 1), simfault("f-2", "stale", "sample-flow", 2.5, 1)]), clock())
    assert [(e.onset_step, e.clear_step) for e in disjoint] == [(20, 40), (50, 70)]


def test_delay_ns_and_assurance_kinds_are_relay_entries():
    items = [simfault("f-dn", "delay", "sample-flow", 1, 1, [parameter("delay-ns", 100_000_000)]),
             simfault("f-ev", "assurance.evidence-loss", "sample-flow", 3, 1)]
    by_id = {e.fault_id: e for e in resolve_simtime(plan_of(items), clock())}
    assert by_id["f-dn"].parameters.values == {"delay-ns": 100_000_000} and by_id["f-ev"].mode == RELAY
    assert by_id["f-ev"].boundary_class == "assurance" and by_id["f-ev"].executable


def test_tick_mode_refuses_delay_ns_and_keeps_delay_ticks():
    with pytest.raises(FaultError) as caught:
        resolve_schedule(compiled_plan([fault("f-x", "delay", "sample-flow", parameters=[parameter("delay-ns", 5)])]), PLANNED_TICKS)
    assert caught.value.code == "XVERSE-FAULT-PARAMETER"
    entries = resolve_schedule(compiled_plan([fault("f-x", "delay", "sample-flow", parameters=[parameter("delay-ticks", 1)])]), PLANNED_TICKS)
    assert entries[0].parameters.values == {"delay-ticks": 1}


# --- schedule admission (decision 3) ----------------------------------------------------------------------------------

def admitted(prepared):
    return admit_schedule(prepared, policies=tuple(ProbePolicy(u.unit_id, 5, 5, 0.5) for u in prepared.units),
                          ticks=(0, prepared.clock.horizon_ticks), active_seconds=20, operation_seconds=0.5,
                          request_limit=1024)


def test_admission_refuses_a_freeze_while_the_handshake_values_are_unknown():
    for partial in ({}, dict(max_step_host_s=0.05, handshake_s=0.5), dict(handshake_s=0.5, hold_bound_s=1.0)):
        with pytest.raises(ScheduleError, match="ML-SCHEDULE-FAULT-SIMTIME-UNMEASURED"):
            admitted(prepared_with([FREEZE], clock(**partial)))


def test_admission_checks_the_thaw_bound_and_the_hold_bound():
    prepared = prepared_with([FREEZE, LOSS], clock(**MEASURED))
    schedule = admitted(prepared)  # 10 steps x 0.05 + 2 x 0.5 = 1.5 <= thaw bound 5 - 2 x 0.5 = 4.0
    assert decode_schedule(prepared, json.loads(schedule.canonical_bytes)) == schedule
    with pytest.raises(ScheduleError, match="ML-SCHEDULE-FAULT-SIMTIME-THAW"):  # 10 x 0.4 + 1.0 = 5.0 > 4.0
        admitted(prepared_with([FREEZE], clock(**dict(MEASURED, max_step_host_s=0.4))))
    with pytest.raises(ScheduleError, match="ML-SCHEDULE-FAULT-SIMTIME-HOLD"):
        admitted(prepared_with([FREEZE], clock(**dict(MEASURED, hold_bound_s=0.4))))


def test_message_only_schedules_need_no_handshake_values():
    assert admitted(prepared_with([LOSS], clock())).digest


# --- channel and frames (decision 4) ----------------------------------------------------------------------------------

def hub_frame(seq, kind, **fields):
    return encode_frame({"v": 1, "kind": kind, "seq": seq, **fields})


def test_frame_codec_is_closed_and_canonical():
    data = hub_frame(1, "hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    assert decode_hub_frame(data)["step"] == 30
    for bad in (b'{"kind":"hold"}', data.replace(b'"seq":1', b'"seq": 1'), hub_frame(1, "hold", entry="x", phase="up", step=1, simNs=1),
                hub_frame(1, "teleport", entry="x"), hub_frame(0, "time", step=1, simNs=STEP), b"x" * (FRAME_MAX + 1),
                hub_frame(1, "time", step=1, simNs=STEP, extra=1), b'{"kind":"time","seq":1,"simNs":NaN,"step":1,"v":1}'):
        with pytest.raises(FaultError) as caught:
            decode_hub_frame(bad)
        assert caught.value.code == "XVERSE-FAULT-SIMTIME-PROTOCOL"
    with pytest.raises(FaultError):
        encode_frame({"v": 1, "kind": "time", "seq": 1, "pad": "x" * FRAME_MAX})


def test_channel_refuses_a_stream_socket_and_a_sequence_gap():
    stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    with pytest.raises(FaultError, match="CHANNEL"):
        HubChannel(stream)
    stream.close()
    ours, hub = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    channel = HubChannel(ours)
    assert channel.connected and channel.peer_credentials[1] >= 0
    hub.send(hub_frame(2, "time", step=1, simNs=STEP))
    with pytest.raises(FaultError, match="sequence gap"):
        channel.receive()
    channel.close()
    hub.close()


def test_listening_channel_accepts_exactly_one_peer(tmp_path):
    path = str(tmp_path / "hub.sock")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    listener.bind(path)
    listener.listen(2)
    channel = HubChannel(listener)
    assert not channel.connected
    first = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    first.connect(path)
    assert channel.connected
    second = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    second.connect(path)
    with pytest.raises(FaultError, match="second hub peer"):
        channel.connected
    channel.close()
    first.close()
    second.close()


# --- scheduler against a fake hub (decisions 4-7) ---------------------------------------------------------------------

class Ops:
    def __init__(self, refuse=()):
        self.calls, self.refuse = [], set(refuse)

    def revalidate(self):
        return True

    def fault(self, operation):
        self.calls.append(operation)
        return BoundaryOutcome(operation not in self.refuse, None if operation not in self.refuse else "XVERSE-FAULT-BOUNDARY-REFUSED")


class Listener:
    def __init__(self):
        self.seen = []

    def decision(self, entry, decision):
        self.seen.append((entry.entry_id, decision.phase, decision.outcome, decision.diagnostic, dict(decision.detail)))


class Hub:
    def __init__(self):
        self.sock = None
        self.seq = 0

    def send(self, kind, **fields):
        self.seq += 1
        self.sock.send(hub_frame(self.seq, kind, **fields))

    def frames(self):
        out = []
        self.sock.setblocking(False)
        while True:
            try:
                data = self.sock.recv(FRAME_MAX)
            except BlockingIOError:
                return out
            if not data:  # Maestro closed its end
                return out
            out.append(json.loads(data))


def stack(items, *, live=True, refuse=()):
    entries = resolve_simtime(plan_of(items), clock(**MEASURED))
    ours, theirs = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    hub = Hub()
    hub.sock = theirs
    ops = Ops(refuse)
    boundaries = {("componentInstances", "sink-instance"): ProcessBoundary("sink-instance", ops)}
    listener = Listener()
    state = {"live": live}
    scheduler = SimTimeFaultScheduler("run-1", entries, clock(**MEASURED), HubChannel(ours), boundaries,
                                      source_live=lambda: state["live"], seed=7, listener=listener)
    scheduler.start()
    return scheduler, hub, ops, listener, state


def arm(scheduler, hub, tick=0):
    scheduler.advance(tick)
    sent = hub.frames()
    assert [f["kind"] for f in sent] == ["arm"] * len(sent)
    for frame in sent:
        hub.send("armed", entry=frame["entry"])
    return sent


def test_arming_waits_for_the_live_source_and_sends_minimum_descriptors():
    scheduler, hub, ops, listener, state = stack([FREEZE, LOSS], live=False)
    scheduler.advance(0)
    assert hub.frames() == []
    state["live"] = True
    sent = arm(scheduler, hub, 1)
    by_entry = {f["entry"]: f for f in sent}
    assert by_entry["fault:f-frz"]["mode"] == "hold" and by_entry["fault:f-frz"]["onsetStep"] == 30
    assert by_entry["fault:f-loss"]["parameters"] == {"every": 2} and by_entry["fault:f-loss"]["seed"] == 7
    assert set(by_entry["fault:f-loss"]) == {"v", "kind", "seq", "entry", "fault", "faultKind", "mode", "collection", "element",
                                            "atNs", "durationNs", "onsetStep", "clearStep", "parameters", "seed", "stepNs"}


def test_step_hold_and_relay_sequence_with_both_clocks():
    scheduler, hub, ops, listener, _ = stack([FREEZE, LOSS])
    arm(scheduler, hub)
    hub.send("time", step=10, simNs=10 * STEP)
    hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    hub.send("cleared", entry="fault:f-loss", step=25, simNs=25 * STEP, items=2)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(3)
    assert ops.calls == ["freeze"]
    assert [(f["kind"], f["phase"], f["outcome"], f["step"]) for f in hub.frames()] == [("ack", "apply", "applied", 30)]
    hub.send("hold", entry="fault:f-frz", phase="clear", step=40, simNs=40 * STEP)
    scheduler.advance(4)
    assert ops.calls == ["freeze", "thaw"]
    assert hub.frames()[0]["outcome"] == "cleared"
    assert scheduler.outcomes == {"fault:f-frz": "cleared", "fault:f-loss": "cleared"}
    applies = [d for d in listener.seen if d[1] == "apply"]
    assert {d[0]: (d[4]["simulatorNs"], d[4]["simulatorStep"], d[4]["mode"]) for d in applies} == {
        "fault:f-loss": (20 * STEP, 20, "remote-relay"), "fault:f-frz": (30 * STEP, 30, "step-hold")}
    assert all(type(d[4]["hostNs"]) is int for d in listener.seen)
    assert scheduler.finish(5) == {"fault:f-frz": "cleared", "fault:f-loss": "cleared"} and not scheduler.incomplete


@pytest.mark.parametrize("items, frames, reason", [
    ([FREEZE], [("hold", dict(entry="fault:f-frz", phase="apply", step=31, simNs=31 * STEP))], "out of order"),
    ([FREEZE], [("hold", dict(entry="fault:f-frz", phase="clear", step=30, simNs=30 * STEP))], "out of order"),
    ([FREEZE], [("time", dict(step=35, simNs=35 * STEP))], "passed step"),
    ([FREEZE, LOSS], [("hold", dict(entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP))], "passed step"),
    ([FREEZE], [("applied", dict(entry="fault:f-frz", step=30, simNs=30 * STEP, items=0))], "held entry"),
    ([LOSS], [("hold", dict(entry="fault:f-loss", phase="apply", step=20, simNs=20 * STEP))], "relay entry"),
    ([FREEZE], [("time", dict(step=5, simNs=5 * STEP + 1))], "step grid"),
    ([FREEZE], [("time", dict(step=5, simNs=5 * STEP)), ("time", dict(step=4, simNs=4 * STEP))], "went back"),
    ([FREEZE], [("hold", dict(entry="fault:nobody", phase="apply", step=1, simNs=STEP))], "unknown entry"),
])
def test_protocol_violations_end_the_run(items, frames, reason):
    scheduler, hub, ops, listener, _ = stack(items)
    arm(scheduler, hub)
    for kind, fields in frames:
        hub.send(kind, **fields)
    scheduler.advance(2)
    assert scheduler.run_failed and reason in scheduler.failure_diagnostic and "SIMTIME-PROTOCOL" in scheduler.failure_diagnostic
    assert ops.calls == [] and scheduler.channel.closed
    assert hub.frames()[-1]["kind"] == "close"


def test_report_before_arming_completes_is_a_protocol_failure():
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    scheduler.advance(0)
    hub.frames()
    hub.send("time", step=1, simNs=STEP)
    scheduler.advance(1)
    assert scheduler.run_failed and "before every entry was armed" in scheduler.failure_diagnostic


def test_refused_freeze_is_acknowledged_as_refused_and_fails_the_run():
    scheduler, hub, ops, listener, _ = stack([FREEZE], refuse=("freeze",))
    arm(scheduler, hub)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(1)
    assert hub.frames()[0]["outcome"] == "refused"
    assert scheduler.run_failed and scheduler.outcomes["fault:f-frz"] == "failed-to-apply"


def test_finish_thaws_a_freeze_whose_clear_step_was_not_reached():
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    arm(scheduler, hub)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(1)
    hub.frames()
    assert scheduler.finish(2) == {"fault:f-frz": "cancelled"} and not scheduler.incomplete
    assert ops.calls == ["freeze", "thaw"]
    finals = {d[0]: d[3] for d in listener.seen if d[1] == "final"}
    assert finals == {"fault:f-frz": "XVERSE-FAULT-SIMTIME-NOT-REACHED"}
    last = hub.frames()[-1]
    assert (last["kind"], last["reason"]) == ("close", "run-finished")


def test_finish_marks_a_relay_entry_never_reported_cleared_incomplete():
    scheduler, hub, ops, listener, _ = stack([LOSS])
    arm(scheduler, hub)
    hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    scheduler.advance(1)
    assert scheduler.finish(2) == {"fault:f-loss": "incomplete-clearing"} and scheduler.incomplete
    finals = {d[0]: d[3] for d in listener.seen if d[1] == "final"}
    assert finals == {"fault:f-loss": "XVERSE-FAULT-SIMTIME-NOT-CLEARED"}


def test_cancel_thaws_and_closes():
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    arm(scheduler, hub)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(1)
    scheduler.cancel(2, "run-failed")
    assert ops.calls == ["freeze", "thaw"] and scheduler.outcomes == {"fault:f-frz": "cancelled"}
    assert scheduler.channel.closed


def test_never_applied_entries_end_cancelled_never_due():
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    arm(scheduler, hub)
    assert scheduler.finish(1) == {"fault:f-frz": "cancelled"} and not scheduler.incomplete


# --- persistence (decision 8) -------------------------------------------------------------------------------------

def test_worker_decodes_exactly_the_encoded_binding():
    from dataclasses import asdict
    from xverse.maestro.persistence import PersistenceError
    from xverse.maestro.persistence_worker import _decode_fault_clock

    binding = clock(**MEASURED)
    assert _decode_fault_clock({}) is None
    assert _decode_fault_clock({"fault_clock": json.loads(json.dumps(asdict(binding)))}) == binding
    for bad in ({"domain": DOMAIN}, dict(asdict(binding), step_ns=0), dict(asdict(binding), extra=1)):
        with pytest.raises(PersistenceError, match="ML-PERSIST-FAULT-CLOCK"):
            _decode_fault_clock({"fault_clock": bad})


# --- composed: the native dispatcher fixture with a fake hub thread ----------------------------------------------

from ..maestro import test_launcher, test_lazy_dispatcher, test_shared_dispatcher  # noqa: E402
from ..maestro.test_run_broker import broker_stack as broker_stack  # noqa: E402,F401
from ..maestro.test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary  # noqa: E402,F401
from ..maestro.test_affa_native import authority_binary as authority_binary  # noqa: E402,F401
from ..maestro.test_boundary import environment as environment  # noqa: E402,F401
from ..maestro.test_launcher import binaries as binaries  # noqa: E402,F401


class HubThread(threading.Thread):
    """A fake clock-source hub: arms, then steps the simulator, holding at each freeze point until Maestro acks."""

    def __init__(self, sock, *, delay_s=0.6, host_step_s=0.005, max_steps=200):
        super().__init__(daemon=True)
        self.sock, self.delay_s, self.host_step_s, self.max_steps = sock, delay_s, host_step_s, max_steps
        self.seq, self.received, self.error = 0, [], None

    def send(self, kind, **fields):
        self.seq += 1
        self.sock.send(hub_frame(self.seq, kind, **fields))

    def recv(self, timeout):
        self.sock.settimeout(timeout)
        frame = json.loads(self.sock.recv(FRAME_MAX))
        self.received.append(frame)
        return frame

    def run(self):
        try:
            entries = []
            first = self.recv(20)
            entries.append(first)
            self.send("armed", entry=first["entry"])
            self.sock.settimeout(0.3)
            while True:
                try:
                    frame = self.recv(0.3)
                except socket.timeout:
                    break
                entries.append(frame)
                self.send("armed", entry=frame["entry"])
            time.sleep(self.delay_s)
            done = set()
            for step in range(self.max_steps):
                sim = step * entries[0]["stepNs"]
                for e in sorted(entries, key=lambda e: e["fault"]):
                    for phase, point in (("apply", e["onsetStep"]), ("clear", e["clearStep"])):
                        key = (e["entry"], phase)
                        if point != step or key in done:
                            continue
                        done.add(key)
                        if e["mode"] == "hold":
                            self.send("hold", entry=e["entry"], phase=phase, step=step, simNs=sim)
                            ack = self.recv(5)
                            assert ack["kind"] == "ack" and ack["entry"] == e["entry"] and ack["phase"] == phase, ack
                        else:
                            self.send("applied" if phase == "apply" else "cleared", entry=e["entry"], step=step, simNs=sim,
                                      items=0)
                if len(done) == 2 * len(entries):
                    break
                time.sleep(self.host_step_s)
        except Exception as error:  # recorded for the test, never raised in the thread
            self.error = error


def test_composed_native_run_step_hold_freeze_and_relay_loss(request, monkeypatch):
    from xverse.argus import EvidenceStore
    from xverse.faults.evidence import closure_report, reconstruct

    items = [simfault("f-frz", "freeze", "sink-instance", 1.5, 0.5), simfault("f-loss", "loss", "sample-flow", 1.0, 0.25, [parameter("every", 2)])]
    base = test_launcher.documents

    def documents():
        docs = with_sensor(base())
        docs["scenario.json"]["spec"]["faults"] = copy.deepcopy(items)
        return docs

    monkeypatch.setattr(test_launcher, "documents", documents)
    prepare_original = test_launcher.prepare_lifecycle
    monkeypatch.setattr(test_launcher, "prepare_lifecycle", lambda *a, **kw: prepare_original(*a, fault_clock=clock(**MEASURED), **kw))
    ours, theirs = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    channel = HubChannel(ours)
    dispatcher = test_shared_dispatcher.FiniteDispatcher
    monkeypatch.setattr(test_shared_dispatcher, "FiniteDispatcher", lambda *a, **kw: dispatcher(*a, fault_clock_channel=channel, **kw))
    shared = test_shared_dispatcher.scheduled
    monkeypatch.setattr(test_shared_dispatcher, "scheduled", lambda request, monkeypatch, **kw: shared(request, monkeypatch, pauses=40, **kw))
    stack_, _, driver = test_lazy_dispatcher.scheduled(request, monkeypatch)
    hub = HubThread(theirs)
    hub.start()
    try:
        result = test_lazy_dispatcher.run(driver)
    finally:
        hub.join(timeout=10)
        theirs.setblocking(False)
        try:
            remaining = theirs.recv(FRAME_MAX)
        except BlockingIOError:
            remaining = b"{}"
        theirs.close()
    assert hub.error is None, hub.error
    assert result.execution_succeeded and result.diagnostic is None, result.diagnostic
    assert driver._faults.outcomes == {"fault:f-frz": "cleared", "fault:f-loss": "cleared"}
    acks = [(f["entry"], f["phase"], f["outcome"], f["step"]) for f in hub.received if f["kind"] == "ack"]
    assert acks == [("fault:f-frz", "apply", "applied", 30), ("fault:f-frz", "clear", "cleared", 40)]
    assert json.loads(remaining)["kind"] == "close"
    events = EvidenceStore.read_run(stack_[3].parent / "argus").records()
    payloads = [(r.get("extensions") or {}).get("io.xverse.faults") for r in events]
    payloads = [p for p in payloads if p]
    modes = {p["faultId"]: p["detail"]["boundaryMode"] for p in payloads if p["phase"] == "intent"}
    assert modes == {"f-frz": "step-hold", "f-loss": "remote-relay"}
    applied = {p["faultId"]: p["detail"]["simulatorStep"] for p in payloads if p["phase"] == "apply"}
    assert applied == {"f-frz": 30, "f-loss": 20}
    assert all(type(p["tick"]) is int for p in payloads)
    assert closure_report(reconstruct(events))["complete"]
    assert _unit_suspended_cleared(driver)


def _unit_suspended_cleared(driver):
    unit = next(u.unit_id for u in driver.prepared.units if u.unit_id.endswith("sink-instance"))
    return unit not in driver.facade._suspended


def test_missing_channel_is_refused_at_begin(request, monkeypatch):
    base = test_launcher.documents

    def documents():
        docs = with_sensor(base())
        docs["scenario.json"]["spec"]["faults"] = [copy.deepcopy(LOSS)]
        return docs

    monkeypatch.setattr(test_launcher, "documents", documents)
    prepare_original = test_launcher.prepare_lifecycle
    monkeypatch.setattr(test_launcher, "prepare_lifecycle", lambda *a, **kw: prepare_original(*a, fault_clock=clock(), **kw))
    _, _, driver = test_lazy_dispatcher.scheduled(request, monkeypatch)
    result = test_lazy_dispatcher.run(driver)
    assert not result.execution_succeeded and result.diagnostic == "ML-SCHEDULE-FAULT-CLOCK"


def test_dispatcher_refuses_a_channel_of_another_type():
    from xverse.maestro.dispatcher import FiniteDispatcher
    from xverse.maestro.owner import OwnerError

    with pytest.raises(OwnerError, match="ML-SCHEDULE-FAULT-CLOCK"):
        FiniteDispatcher(None, None, gates=(), fault_clock_channel=object())

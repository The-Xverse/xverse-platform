"""Simulator-time fault triggers (ADR-ML3-SIMTIME-0001 with amendment ST-2; review-simtime-faults findings 1-5).

Pure cases: the capability flag, the binding, resolution and horizon, tick-mode compatibility, schedule admission
(the D-4c refusal and the thaw check), the channel codec, and the scheduler against a fake hub over a socketpair.
The composed case runs the native Maestro dispatcher fixture with a fake hub thread: a step-hold freeze and a
remote-relay loss. Worker-side code is involved: run with the installed wheel.
"""

from __future__ import annotations

import copy
import json
import socket
import tempfile
import threading
import time

import pytest

import xverse.faults as faults_package
from xverse.faults import FaultError, HubChannel, SimTimeFaultScheduler, SimulationClock, resolve_simtime, resolve_schedule
from xverse.faults.boundary import BoundaryOutcome, ProcessBoundary
from xverse.faults.simtime import FRAME_MAX, HOLD, RELAY, check_arm_batch, decode_hub_frame, encode_frame
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


# ST-2 (L4): literals computed from a clean export of base b40acce49 (review-simtime-faults finding 5), not from
# this candidate: (lifecycle digest, sha256 of the canonical bytes).
BASE_DIGESTS = {
    "fault-less": ("f570fa42244c1550be6bc6aeb8665050826b7c45227db0b9faf1ab3cbccb4b7a",
                   "65ade2a522f8217ac23f8824219f9506307af35fe9be215eb17fc42cf6dafdac"),
    "fault-less-sensor": ("952c6b9308d82abf170a8c34e7465eb232cb606eb1d411b688df930aed123836",
                          "45b88e72ea7a2136a981f7b4a420dabfeca63923e258c9b64fb62006212a540f"),
    "stale+crash": ("3e2bd8afc9d2f010dc729c6c8c896406f5abbc40334d2cc213225bdd3a0b70c1",
                    "afbd56ad18689ff6d167e611a9befc1895ad6ba37573a03906e3759ffcdb4a94"),
    "freeze": ("dc962b8b122a094fc574878a0f60aa3bedbae453b3a8e78c3c18b4b3df456ce6",
               "f56cf29d8e5884839905cfe06ce5866cb87407ec5dea64d8e1bc99f015c3a577"),
    "delay-ticks": ("f147b3f36ce13c7f0331b42610f10d06844822e730c9aae8f27b6c873a4a590f",
                    "10478f962a6650bed21f97a0435aa67be9125a1b0b7cd72df47a23efb2d27a52"),
}
TICK_PLANS = {
    "fault-less": None,
    "fault-less-sensor": [],
    "stale+crash": [fault("f-s", "stale", "sample-flow", at=1, duration=1),
                    fault("f-c", "crash", "source-instance", at=2, duration=0, recovery="manual")],
    "freeze": [fault("f-frz", "freeze", "sink-instance", at=1, duration=1)],
    "delay-ticks": [fault("f-dl", "delay", "sample-flow", at=1, duration=1, parameters=[parameter("delay-ticks", 1)])],
}


@pytest.mark.parametrize("name", sorted(TICK_PLANS))
def test_tick_mode_plans_keep_the_base_digests(name):
    import hashlib

    items = TICK_PLANS[name]
    result, resources = compiled() if items is None else compiled(docs_with(items))
    prepared = prepare(result, resources, provider_descriptors=(PIN,))
    assert prepared.fault_clock is None and len(prepared.faults) == len(items or ())
    assert (prepared.lifecycle_digest, hashlib.sha256(prepared.canonical_bytes).hexdigest()) == BASE_DIGESTS[name]


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


def test_listening_channel_accepts_exactly_one_peer():
    # Nested whole-suite runs inherit a long pytest temp root; AF_UNIX paths are bounded.
    with tempfile.TemporaryDirectory(prefix="xv-hub-", dir="/tmp") as directory:
        path = directory + "/hub.sock"
        with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as listener:
            listener.bind(path)
            listener.listen(2)
            channel = HubChannel(listener)
            try:
                assert not channel.connected
                with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as first:
                    first.connect(path)
                    assert channel.connected
                    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as second:
                        second.connect(path)
                        with pytest.raises(FaultError, match="second hub peer"):
                            channel.connected
            finally:
                channel.close()



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


def resume(hub, ack):
    hub.send("resumed", entry=ack["entry"], phase=ack["phase"], step=ack["step"], ackSeq=ack["seq"])


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
                                            "atNs", "durationNs", "onsetStep", "clearStep", "parameters", "seed", "stepNs",
                                            "count", "index"}
    assert [(f["count"], f["index"]) for f in sent] == [(2, 1), (2, 2)]
    check_arm_batch(sent)


def test_arm_batch_check_refuses_a_wrong_count_an_index_gap_and_a_duplicate():
    scheduler, hub, *_ = stack([FREEZE, LOSS, simfault("f-st", "stale", "sample-flow", 3, 1)])
    scheduler.advance(0)
    sent = hub.frames()
    check_arm_batch(sent)
    assert [f["index"] for f in sent] == [1, 2, 3] and {f["count"] for f in sent} == {3}
    wrong_count = [dict(f, count=4) for f in sent]
    one_count_differs = [sent[0], dict(sent[1], count=2), sent[2]]
    gap = [sent[0], dict(sent[1], index=3), dict(sent[2], index=4)]
    starts_at_zero = [dict(f, index=f["index"] - 1) for f in sent]
    duplicate_index = [sent[0], sent[1], dict(sent[2], index=2)]
    duplicate_entry = [sent[0], sent[1], dict(sent[2], entry=sent[0]["entry"])]
    truncated = sent[:2]
    for bad, reason in ((wrong_count, "count"), (one_count_differs, "count"), (gap, "index"), (starts_at_zero, "index"),
                        (duplicate_index, "index"), (duplicate_entry, "repeated"), (truncated, "count")):
        with pytest.raises(FaultError, match=reason) as caught:
            check_arm_batch(bad)
        assert caught.value.code == "XVERSE-FAULT-SIMTIME-PROTOCOL"


def test_step_hold_and_relay_sequence_with_both_clocks():
    scheduler, hub, ops, listener, _ = stack([FREEZE, LOSS])
    arm(scheduler, hub)
    hub.send("time", step=10, simNs=10 * STEP)
    hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    hub.send("cleared", entry="fault:f-loss", step=25, simNs=25 * STEP, items=2)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(3)
    assert ops.calls == ["freeze"]
    acks = hub.frames()
    assert [(f["kind"], f["phase"], f["outcome"], f["step"]) for f in acks] == [("ack", "apply", "applied", 30)]
    resume(hub, acks[0])
    hub.send("hold", entry="fault:f-frz", phase="clear", step=40, simNs=40 * STEP)
    scheduler.advance(4)
    assert ops.calls == ["freeze", "thaw"]
    ack = hub.frames()[0]
    assert ack["outcome"] == "cleared"
    resume(hub, ack)
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


def test_armed_must_precede_the_onset_step_of_its_entry():
    """ST-2 (M3), replacing finding 2's R9 rule: a step below every unarmed onset is accepted, the onset is not."""
    scheduler, hub, ops, listener, _ = stack([FREEZE, LOSS])
    scheduler.advance(0)
    hub.frames()
    hub.send("time", step=1, simNs=STEP)
    hub.send("armed", entry="fault:f-loss")
    hub.send("time", step=19, simNs=19 * STEP)
    scheduler.advance(1)
    assert not scheduler.run_failed
    hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    hub.send("time", step=30, simNs=30 * STEP)
    scheduler.advance(2)
    assert scheduler.run_failed and "hub reached step 30 of unarmed fault:f-frz" in scheduler.failure_diagnostic
    assert ops.calls == [] and scheduler.channel.closed


def test_a_report_for_an_unarmed_entry_at_its_onset_is_a_protocol_failure():
    scheduler, hub, ops, listener, _ = stack([LOSS])
    scheduler.advance(0)
    hub.frames()
    hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    scheduler.advance(1)
    assert scheduler.run_failed and "unarmed fault:f-loss" in scheduler.failure_diagnostic


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
    resume(hub, hub.frames()[0])
    # ST-2a (N1): a freeze cut short is a different treatment under PAIR-1, so the run is incomplete
    assert scheduler.finish(2) == {"fault:f-frz": "cancelled"} and scheduler.incomplete and not scheduler.run_failed
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


def test_an_unreached_onset_ends_cancelled_not_reached_and_the_run_incomplete():
    """ST-2 (M3), replacing the pin of the old behaviour (never-due, run complete)."""
    scheduler, hub, ops, listener, _ = stack([FREEZE, LOSS])
    arm(scheduler, hub)
    hub.send("time", step=10, simNs=10 * STEP)
    scheduler.advance(1)
    assert scheduler.finish(2) == {"fault:f-frz": "cancelled", "fault:f-loss": "cancelled"}
    assert scheduler.incomplete and not scheduler.run_failed and ops.calls == []
    finals = {d[0]: d[3] for d in listener.seen if d[1] == "final"}
    assert finals == {"fault:f-frz": "XVERSE-FAULT-SIMTIME-NOT-REACHED", "fault:f-loss": "XVERSE-FAULT-SIMTIME-NOT-REACHED"}


@pytest.mark.parametrize("items, steps, reason", [
    ([FREEZE], None, "never armed"),  # the source never went live: nothing was armed
    ([FREEZE], (), "never armed"),  # armed frames sent by Maestro, never confirmed by the hub
    ([FREEZE], (30,), "fault:f-frz not applied although the hub reported step 30"),
    ([LOSS], (20,), "fault:f-loss not applied although the hub reported step 20"),
])
def test_finish_refuses_an_unarmed_entry_or_a_reached_onset_without_apply(items, steps, reason):
    scheduler, hub, ops, listener, state = stack(items, live=steps is not None)
    if steps is None:
        scheduler.advance(0)
        assert hub.frames() == []
    elif steps == ():
        scheduler.advance(0)
        hub.frames()
    else:
        arm(scheduler, hub)
        for step in steps:
            hub.send("time", step=step, simNs=step * STEP)
        scheduler.advance(1)
        assert not scheduler.run_failed
    outcomes = scheduler.finish(2)
    assert scheduler.run_failed and reason in scheduler.failure_diagnostic and "SIMTIME-PROTOCOL" in scheduler.failure_diagnostic
    assert set(outcomes.values()) == {"cancelled"}
    assert {d[3] for d in listener.seen if d[1] == "final"} == {"XVERSE-FAULT-CANCELLED"}
    assert scheduler.channel.closed and ops.calls == []


# --- ST-2 (M2): hold verification by ``resumed`` -------------------------------------------------------------------

def test_p1_steps_queued_behind_a_hold_without_resumed_are_refused():
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    arm(scheduler, hub)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    hub.send("time", step=31, simNs=31 * STEP)
    hub.send("time", step=35, simNs=35 * STEP)
    scheduler.advance(1)
    assert scheduler.run_failed and "hub sent time before resumed" in scheduler.failure_diagnostic
    assert ops.calls == ["freeze"] and scheduler.channel.closed
    scheduler.cancel(2, "run-failed")
    assert ops.calls == ["freeze", "thaw"] and scheduler.outcomes == {"fault:f-frz": "cancelled"}


def test_p2_back_to_back_holds_without_resumed_are_refused():
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    arm(scheduler, hub)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    hub.send("hold", entry="fault:f-frz", phase="clear", step=40, simNs=40 * STEP)
    scheduler.advance(1)
    assert scheduler.run_failed and "hub sent hold before resumed" in scheduler.failure_diagnostic
    assert ops.calls == ["freeze"] and scheduler.outcomes == {"fault:f-frz": None}


@pytest.mark.parametrize("change, reason", [
    (dict(ackSeq=99), "before resumed"), (dict(step=31), "before resumed"), (dict(phase="clear"), "before resumed"),
    (None, "no hold ack pending"),
])
def test_resumed_must_echo_the_pending_ack(change, reason):
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    arm(scheduler, hub)
    if change is None:
        hub.send("resumed", entry="fault:f-frz", phase="apply", step=30, ackSeq=1)
    else:
        hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
        scheduler.advance(1)
        ack = hub.frames()[0]
        hub.send("resumed", **(dict(entry=ack["entry"], phase=ack["phase"], step=ack["step"], ackSeq=ack["seq"]) | change))
    scheduler.advance(2)
    assert scheduler.run_failed and reason in scheduler.failure_diagnostic


def test_resumed_frame_codec():
    data = hub_frame(3, "resumed", entry="fault:f-frz", phase="apply", step=30, ackSeq=2)
    assert decode_hub_frame(data)["ackSeq"] == 2
    for bad in (hub_frame(3, "resumed", entry="fault:f-frz", phase="apply", step=30, ackSeq=0),
                hub_frame(3, "resumed", entry="fault:f-frz", phase="apply", step=30, ackSeq=2, simNs=30 * STEP),
                hub_frame(3, "resumed", entry="fault:f-frz", phase="apply", step=30)):
        with pytest.raises(FaultError):
            decode_hub_frame(bad)


# --- ST-2 (M1): channel lifetime ---------------------------------------------------------------------------------

def test_hub_end_of_file_after_every_entry_is_final_is_benign_and_recorded():
    scheduler, hub, ops, listener, _ = stack([FREEZE, LOSS])
    arm(scheduler, hub)
    hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    hub.send("cleared", entry="fault:f-loss", step=25, simNs=25 * STEP, items=2)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(1)
    resume(hub, hub.frames()[0])
    hub.send("hold", entry="fault:f-frz", phase="clear", step=40, simNs=40 * STEP)
    scheduler.advance(2)
    resume(hub, hub.frames()[0])
    hub.sock.close()  # the hub exits at its stop step
    scheduler.advance(3)
    assert not scheduler.run_failed and scheduler.hub_closed["event"] == "hub-closed"
    assert scheduler.hub_closed["simulatorStep"] == 40
    assert not [d for d in listener.seen if d[1] in ("final", "outcome")]  # finals are emitted when the scheduler ends
    scheduler.advance(4)  # nothing is read after the end-of-file
    assert scheduler.finish(5) == {"fault:f-frz": "cleared", "fault:f-loss": "cleared"}
    assert not scheduler.run_failed and not scheduler.incomplete and scheduler.channel.closed  # no close to a closed hub
    # ST-2a: hubClosed sits in the first listed entry's final detail; exactly one final per entry, no other outcome
    first = next(iter(scheduler.outcomes))
    assert first == "fault:f-loss"
    finals = [(d[0], d[2], d[4].get("hubClosed")) for d in listener.seen if d[1] in ("final", "outcome")]
    assert sorted(f[0] for f in finals) == ["fault:f-frz", "fault:f-loss"]
    assert {f[0]: f[2] for f in finals} == {first: {"simulatorStep": 40, "hostNs": scheduler.hub_closed["hostNs"]},
                                            "fault:f-frz": None}
    assert all(f[1] == "cleared" for f in finals)


def test_outstanding_resumed_at_finish_is_recorded_not_failed():
    """ST-2a (N2): the clear hold is acked and the hub never confirms it; the run is not failed (R13)."""
    scheduler, hub, ops, listener, _ = stack([FREEZE])
    arm(scheduler, hub)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(1)
    resume(hub, hub.frames()[0])
    hub.send("hold", entry="fault:f-frz", phase="clear", step=40, simNs=40 * STEP)
    scheduler.advance(2)
    ack = hub.frames()[0]
    assert scheduler.finish(3) == {"fault:f-frz": "cleared"}
    assert not scheduler.run_failed and not scheduler.incomplete
    finals = [d for d in listener.seen if d[1] == "final"]
    assert len(finals) == 1 and finals[0][4]["resumedOutstanding"] == {"phase": "clear", "step": 40, "ackSeq": ack["seq"]}


def test_outstanding_resumed_at_cancel_is_recorded():
    scheduler, hub, ops, listener, _ = stack([FREEZE, LOSS])
    arm(scheduler, hub)
    hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    hub.send("cleared", entry="fault:f-loss", step=25, simNs=25 * STEP, items=1)
    hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
    scheduler.advance(1)
    ack = hub.frames()[0]
    scheduler.cancel(2, "run-failed")
    assert ops.calls == ["freeze", "thaw"] and scheduler.outcomes == {"fault:f-frz": "cancelled", "fault:f-loss": "cleared"}
    finals = {d[0]: d[4] for d in listener.seen if d[1] == "final"}
    assert finals["fault:f-frz"]["resumedOutstanding"] == {"phase": "apply", "step": 30, "ackSeq": ack["seq"]}
    assert "resumedOutstanding" not in finals["fault:f-loss"] and len(finals) == 2


def test_each_entry_has_exactly_one_final_even_when_the_scheduler_ends_twice():
    scheduler, hub, ops, listener, _ = stack([FREEZE, LOSS])
    arm(scheduler, hub)
    hub.send("time", step=10, simNs=10 * STEP)
    scheduler.advance(1)
    scheduler.finish(2)
    scheduler.cancel(3, "run-failed")  # the dispatcher cancels after an incomplete finish
    finals = [d[0] for d in listener.seen if d[1] in ("final", "outcome")]
    assert sorted(finals) == ["fault:f-frz", "fault:f-loss"]


@pytest.mark.parametrize("pending", ["report", "resumed", "hold"])
def test_hub_end_of_file_with_anything_pending_is_a_protocol_failure(pending):
    scheduler, hub, ops, listener, _ = stack([FREEZE] if pending != "report" else [LOSS])
    arm(scheduler, hub)
    if pending == "report":
        hub.send("applied", entry="fault:f-loss", step=20, simNs=20 * STEP, items=0)
    else:
        hub.send("hold", entry="fault:f-frz", phase="apply", step=30, simNs=30 * STEP)
        scheduler.advance(1)
        ack = hub.frames()[0]
        if pending == "hold":  # resumed was sent; the clear point is still pending
            resume(hub, ack)
    hub.sock.close()
    scheduler.advance(2)
    assert scheduler.run_failed and "the hub closed the channel with" in scheduler.failure_diagnostic
    assert "SIMTIME-PROTOCOL" in scheduler.failure_diagnostic and scheduler.hub_closed is None


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
    """A fake clock-source hub: arms (until ``index == count``), then steps the simulator, holding at each freeze
    point until Maestro acks and confirming each ack with ``resumed``. With ``exit_at_stop`` it closes its end after
    its last report, as U2 does when its stop step ends the process (ST-2, M1)."""

    def __init__(self, sock, *, delay_s=0.6, host_step_s=0.005, max_steps=200, exit_at_stop=False):
        super().__init__(daemon=True)
        self.sock, self.delay_s, self.host_step_s, self.max_steps = sock, delay_s, host_step_s, max_steps
        self.exit_at_stop = exit_at_stop
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
            while not entries or entries[-1]["index"] < entries[-1]["count"]:
                frame = self.recv(20)
                assert frame["kind"] == "arm" and frame["index"] == len(entries) + 1, frame
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
                            self.send("resumed", entry=ack["entry"], phase=phase, step=step, ackSeq=ack["seq"])
                        else:
                            self.send("applied" if phase == "apply" else "cleared", entry=e["entry"], step=step, simNs=sim,
                                      items=0)
                if len(done) == 2 * len(entries):
                    break
                time.sleep(self.host_step_s)
            if self.exit_at_stop:
                self.sock.close()
        except Exception as error:  # recorded for the test, never raised in the thread
            self.error = error


@pytest.mark.parametrize("exit_at_stop", [False, True], ids=["hub-waits-for-close", "hub-exits-at-stop-step"])
def test_composed_native_run_step_hold_freeze_and_relay_loss(request, monkeypatch, exit_at_stop):
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
    hub = HubThread(theirs, exit_at_stop=exit_at_stop)
    hub.start()
    try:
        result = test_lazy_dispatcher.run(driver)
    finally:
        hub.join(timeout=10)
        remaining = b"{}"
        if not exit_at_stop:
            theirs.setblocking(False)
            try:
                remaining = theirs.recv(FRAME_MAX)
            except BlockingIOError:
                pass
        theirs.close()
    assert hub.error is None, hub.error
    assert result.execution_succeeded and result.diagnostic is None, result.diagnostic
    assert driver._faults.outcomes == {"fault:f-frz": "cleared", "fault:f-loss": "cleared"}
    acks = [(f["entry"], f["phase"], f["outcome"], f["step"]) for f in hub.received if f["kind"] == "ack"]
    assert acks == [("fault:f-frz", "apply", "applied", 30), ("fault:f-frz", "clear", "cleared", 40)]
    events = EvidenceStore.read_run(stack_[3].parent / "argus").records()
    payloads = [(r.get("extensions") or {}).get("io.xverse.faults") for r in events]
    payloads = [p for p in payloads if p]
    outcomes = [p for p in payloads if p["phase"] == "outcome"]
    assert sorted(p["faultId"] for p in outcomes) == ["f-frz", "f-loss"]  # exactly one final outcome per entry (ST-2a)
    assert {p["outcome"] for p in outcomes} == {"cleared"}
    closed = {p["faultId"]: p["detail"]["hubClosed"] for p in outcomes if "hubClosed" in p["detail"]}
    if exit_at_stop:  # ST-2 (M1), ST-2a: a benign end-of-file, in the first listed entry's final outcome detail
        assert driver._faults.hub_closed is not None and json.loads(remaining) == {}
        first = next(iter(driver._fault_entries.values())).fault_id  # the first entry in compiled listing order
        assert list(closed) == [first] and closed[first]["simulatorStep"] == 40
    else:
        assert driver._faults.hub_closed is None and closed == {} and json.loads(remaining)["kind"] == "close"
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

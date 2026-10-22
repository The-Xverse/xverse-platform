"""V01/V02: binding of the owned fixtures, stage 0, refusal order, mask and limits (FR-001-FR-007, FR-012, FR-013)."""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path

import pytest

from xverse_xdl.experiment_plan import compile_experiment_plan
from xverse_xdl.validate import validate_files
from xverse.flows import bind, binding as binding_module
from xverse.flows.provider import LOOPBACK

from .support import ROOT, SCHEMAS, compile_fixture, documents


def _codes(record):
    return [(r["flowId"], r["code"], r["detail"].get("xcomOutcome")) for r in record.refusals]


def test_v01_uniform_binds_every_flow_and_agrees_with_the_plan_block():
    plan, resources = compile_fixture(documents("uniform"))
    record = bind(plan, resources)
    assert record.activatable() and record.xcom_plan_status == "activatable" and record.xcom_plan_diagnostics == ()
    assert [b.flow_id for b in record.bindings] == ["camera-flow", "radar-flow"]
    camera = record.binding("camera-flow")
    assert (camera.policy.ordering, camera.policy.reliability, camera.policy.queue_depth) == ("fifo", "best-effort", 4)
    assert (camera.claim_delivery, camera.claim_ordering, camera.provider_id) == ("best_effort", "per_route_fifo", "local-simulated-loop")
    assert (camera.sender_domain, camera.receiver_domain, camera.mapping.offset_ns, camera.mapping.tolerance_ns) == ("experiment-time", "control-time", 1, 2)
    assert (camera.freshness_ns, camera.deadline_ns) == (6, 5)
    data = record.to_json()
    assert data["schema"] == "xverse.flows.binding/1" and data["tickPeriodNs"] == 1 and data["refusals"] == []
    assert data["cppMirrorSha256"] and data["xcomPlanSha256"] and data["xcomGraphDigest"]
    assert bind(plan, resources).sha256() == record.sha256()  # deterministic


def test_v01_distinct_binds_per_component_with_only_the_allowed_conflict():
    plan, resources = compile_fixture(documents("distinct"))
    record = bind(plan, resources)
    assert record.activatable() and record.xcom_plan_status == "inspectable"
    assert {d["code"] for d in record.xcom_plan_diagnostics} == {"XCOM-PLAN-POLICY-CONFLICT"}
    assert record.binding("camera-flow").policy.queue_depth == 4 and record.binding("radar-flow").policy.queue_depth == 2


def test_v02_existing_fixture_set_stops_at_stage_0():
    folder = ROOT / "tests" / "thesis_lite" / "xdl" / "fixtures"
    paths = sorted(p for p in folder.glob("*.xdl.yaml") if "invalid" not in p.name)
    validation = validate_files(paths, profile_schema_paths=SCHEMAS)
    assert validation.is_valid
    plan = compile_experiment_plan(validation.resources).plan
    record = bind(plan, validation.resources)
    assert [r["code"] for r in record.refusals] == ["XVERSE-FLOW-XCOM-PLAN"] and record.bindings == ()
    codes = {d["code"] for d in record.refusals[0]["detail"]["xcomPlanDiagnostics"]}
    assert {"XCOM-PLAN-CAPABILITY-UNRESOLVED", "XCOM-PLAN-POLICY-UNRESOLVED", "XCOM-PLAN-SCHEMA-UNRESOLVED"} <= codes


def test_v02_inputs_must_match_the_plan_provenance_exactly():
    plan, resources = compile_fixture(documents("uniform"))
    record = bind(plan, resources[1:])
    assert [r["code"] for r in record.refusals] == ["XVERSE-FLOW-INPUT-MISMATCH"] and record.refusals[0]["detail"]["missing"]
    tampered = copy.deepcopy(plan)
    tampered["provenance"]["resources"][0]["semanticDigest"]["value"] = "0" * 64
    assert bind(tampered, resources).refusals[0]["detail"]["mismatched"]


@pytest.mark.parametrize("change, expected", [
    (dict(intents={"camera-flow": "latest-value"}), ("camera-flow", "XVERSE-FLOW-UNSUPPORTED", None)),
    (dict(camera_policy={"ordering": "priority"}), ("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "unsupported_ordering")),
    (dict(camera_policy={"reliability": "exactly-once"}), ("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "unsupported_delivery")),
    (dict(intents={"camera-flow": "reliable"}), ("camera-flow", "XVERSE-FLOW-POLICY-CONFLICT", None)),
    (dict(camera_policy={"overflow": "drop-oldest"}), ("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "unsupported_policy")),
    (dict(camera_policy={"retry": 1}), ("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "unsupported_policy")),
    (dict(camera_policy={"deadlineMs": 5}), ("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "unsupported_policy")),
    (dict(camera_policy={"queueDepth": 9}), ("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "queue_limit_exceeded")),
])
def test_v02_refusal_order(change, expected):
    plan, resources = compile_fixture(documents("uniform", **change))
    record = bind(plan, resources)
    assert _codes(record) == [expected] and not record.activatable()


def test_v02_mask_refuses_what_loopback_cannot_honour_even_when_a_token_qualifies():
    tokens = ("xcom.delivery.reliable", "xcom.ordering.unordered")
    reliable = bind(*compile_fixture(documents("uniform", tokens=tokens, intents={"camera-flow": "reliable"},
                                               camera_policy={"reliability": "at-least-once"})))
    assert _codes(reliable) == [("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "unsupported_delivery")]
    unordered = bind(*compile_fixture(documents("uniform", tokens=tokens, intents={"camera-flow": "best-effort"},
                                                camera_policy={"ordering": "unordered"})))
    assert _codes(unordered) == [("camera-flow", "XVERSE-FLOW-UNSUPPORTED", "unsupported_ordering")]
    without_token = bind(*compile_fixture(documents("uniform", intents={"camera-flow": "reliable"}, camera_policy={"reliability": "at-least-once"})))
    assert _codes(without_token) == [("camera-flow", "XVERSE-FLOW-PROVIDER", None)]


def test_v02_route_limit_counts_only_surviving_flows(monkeypatch):
    monkeypatch.setattr(binding_module, "LOOPBACK", dataclasses.replace(LOOPBACK, max_routes=1))
    record = bind(*compile_fixture(documents("uniform")))
    assert _codes(record) == [("radar-flow", "XVERSE-FLOW-UNSUPPORTED", "route_capacity_exhausted")]
    record = bind(*compile_fixture(documents("uniform", camera_policy={"queueDepth": 9})))
    assert ("radar-flow", "XVERSE-FLOW-UNSUPPORTED", "route_capacity_exhausted") not in _codes(record)


@pytest.mark.parametrize("change, code", [
    (dict(mappings=[]), "XVERSE-FLOW-MAPPING-MISSING"),
    (dict(mappings=[{"sourceTimeDomainId": "control-time", "targetTimeDomainId": "experiment-time", "mapping": "identity",
                      "tolerance": {"value": 0, "unit": "tick"}}]), "XVERSE-FLOW-MAPPING-MISSING"),
    (dict(mappings=[{"sourceTimeDomainId": "experiment-time", "targetTimeDomainId": "control-time", "mapping": "scale:2",
                      "tolerance": {"value": 0, "unit": "tick"}}]), "XVERSE-FLOW-MAPPING-UNSUPPORTED"),
    (dict(quality={"camera-flow": {"receiverTimeDomainId": "no-such-time"}}), "XVERSE-FLOW-CLOCK-UNKNOWN"),
    (dict(quality={"camera-flow": {"freshness": {"value": -1, "unit": "tick"}}}), "XVERSE-FLOW-QUALITY-INVALID"),
    (dict(quality={"camera-flow": {"deadline": {"value": 0.5, "unit": "ns"}}}), "XVERSE-FLOW-QUALITY-INVALID"),
    (dict(quality={"camera-flow": {"deadline": {"value": 1, "unit": "minute"}}}), "XVERSE-FLOW-QUALITY-INVALID"),
])
def test_v04_time_refusals_at_binding(change, code):
    record = bind(*compile_fixture(documents("uniform", **change)))
    assert [(r["flowId"], r["code"]) for r in record.refusals] == [("camera-flow", code)]


def test_v01_ignored_quality_members_are_listed():
    quality = {"camera-flow": {"freshness": {"value": 6, "unit": "tick"}, "jitter": "low"}}
    record = bind(*compile_fixture(documents("uniform", quality=quality, mappings=[])))
    assert record.ignored_quality == {"camera-flow": ("jitter",)}


def test_v01_crosscheck_compares_field_by_field():
    policy = binding_module.FlowPolicy("fifo", "best-effort", 4, "reject", 0, 0)
    block = {"ordering": "fifo", "reliability": "best-effort", "queueDepth": 4, "overflow": "reject", "retry": 0, "deadlineMs": 0, "backpressure": "reject"}
    assert binding_module._crosscheck(block, policy) == []
    assert binding_module._crosscheck(dict(block, queueDepth=2), policy) == ["queueDepth"]


def test_v02_flow_id_hash_collision_is_refused(monkeypatch):
    monkeypatch.setattr(binding_module, "flow_hash", lambda flow_id: "0" * 16)
    record = bind(*compile_fixture(documents("uniform")))
    assert [(r["code"], r["detail"].get("reason")) for r in record.refusals] == [("XVERSE-FLOW-INPUT-MISMATCH", "flow-id-hash-collision")]

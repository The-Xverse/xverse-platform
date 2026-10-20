"""Owning-platform consumer checks against actual XDL and M3, without workloads."""

import copy
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path

import pytest

from xverse.maestro import Limits, PreparationError, ProviderDescriptor, prepare
from xverse.maestro import projection
from xverse_xdl.experiment_plan import (
    ExperimentPlanResult,
    compile_experiment_plan,
    compute_plan_digest,
)
from xverse_xdl.models import freeze
from xverse_xdl.validate import validate_files, validate_sources

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCHEMAS = tuple((ROOT / "xdl/profiles").glob("*.schema.json"))
PIN = ProviderDescriptor(
    "maestro-fixture-v1", "fixture", "sha256:" + "1" * 64, "isolated-fixture"
)
SYSTEM = "xdl://org.xverse.experiment/system/sample-loop"
SCENARIO = "xdl://org.xverse.experiment/scenario/sample-observation-run"
SOURCE = SYSTEM + "#componentInstances/source-instance"
SINK = SYSTEM + "#componentInstances/sink-instance"


def documents():
    return {path.name: json.loads(path.read_text()) for path in FIXTURES.glob("*.json")}


def compiled(docs=None):
    if docs is None:
        validation = validate_files(
            sorted(FIXTURES.glob("*.json")), profile_schema_paths=SCHEMAS
        )
    else:
        validation = validate_sources(
            [(name, json.dumps(value).encode()) for name, value in docs.items()],
            profile_schema_paths=SCHEMAS,
        )
    assert validation.is_valid, [(d.code, d.message) for d in validation.diagnostics]
    result = compile_experiment_plan(validation.resources)
    assert result.is_valid, [(d.code, d.message) for d in result.diagnostics]
    return result, validation.resources


def prepared(docs=None, **options):
    result, resources = compiled(docs)
    return prepare(
        result,
        resources,
        provider_descriptors=options.pop("provider_descriptors", (PIN,)),
        **options,
    )


def test_real_xdl_catalog_plans_and_combined_phase_edges():
    value = prepared()
    assert {u.unit_id for u in value.units} == {SOURCE, SINK}
    assert value.resource_order == (SOURCE, SINK)
    assert all(unit.plan.requires_execution_permit for unit in value.units)
    assert all(
        unit.plan.artifact_digests
        == ("sha256:6506e6f74827ef5d40ba871e29d7666487e0c50c7dffb2f0b911f6eb642f8a4b",)
        for unit in value.units
    )
    pairs = {(e.source, e.target) for e in value.graph_edges}
    # Expected graph is written from D2, not generated from implementation transitions.
    expected = {
        ((SOURCE, "dispatch"), (SOURCE, "release")),
        ((SOURCE, "release"), (SOURCE, "probe")),
        ((SOURCE, "probe"), (SOURCE, "ready")),
        ((SOURCE, "ready"), (SOURCE, "start-complete")),
        ((SOURCE, "ready"), (SINK, "dispatch")),
        ((SINK, "cleanup"), (SOURCE, "termination")),
        (
            (SCENARIO + "#steps/start-source", "complete"),
            (SCENARIO + "#steps/start-sink", "dispatch"),
        ),
    }
    assert expected <= pairs
    flow = next(e for e in value.graph_edges if e.kind == "flow")
    assert flow.pointer == SYSTEM + "#/spec/flows/0"
    rank = {node: i for i, node in enumerate(value.topological_order)}
    assert all(rank[e.source] < rank[e.target] for e in value.graph_edges)
    assert len({unit.node_id for unit in value.units}) == 2
    assert value.ready_for_execution is False


def test_preparation_has_no_execution_facade_or_success_outcome():
    import xverse.maestro as maestro

    assert not hasattr(maestro, "start")
    assert not hasattr(prepared(), "outcome")


def test_digest_snapshot_is_immutable_and_repeatable():
    result, resources = compiled()
    value = prepare(result, resources, provider_descriptors=(PIN,))
    same = prepare(
        replace(result, run=freeze({"runId": "different"})),
        tuple(reversed(resources)),
        provider_descriptors=(PIN,),
    )
    assert value.lifecycle_digest == same.lifecycle_digest
    assert value.canonical_bytes == same.canonical_bytes
    assert (
        value.lifecycle_digest
        == hashlib.sha256(projection.DIGEST_DOMAIN + value.canonical_bytes).hexdigest()
    )
    result.plan["lifecycleIntent"][0]["phase"] = "cleanup"
    assert value.canonical_bytes == same.canonical_bytes
    with pytest.raises(FrozenInstanceError):
        value.units[0].unit_id = "forged"
    with pytest.raises(TypeError):
        value.units[0].plan.selection["bindingId"] = "forged"


def test_changed_plan_and_rehashed_forgery_both_reject():
    result, resources = compiled()
    altered = copy.deepcopy(result.plan)
    altered["seed"]["value"] += 1
    with pytest.raises(PreparationError, match="ML-PLAN-DIGEST"):
        prepare(replace(result, plan=altered), resources, provider_descriptors=(PIN,))
    altered["digest"]["value"] = compute_plan_digest(altered)
    with pytest.raises(PreparationError, match="ML-PLAN-INPUT"):
        prepare(replace(result, plan=altered), resources, provider_descriptors=(PIN,))


def test_invalid_result_and_duplicate_resources_reject():
    result, resources = compiled()
    with pytest.raises(PreparationError, match="ML-PLAN"):
        prepare(ExperimentPlanResult((), None), resources)
    with pytest.raises(PreparationError, match="ML-PLAN-INPUT"):
        prepare(result, resources + (resources[0],), provider_descriptors=(PIN,))


@pytest.mark.parametrize(
    "pins", [(), (PIN, PIN), (replace(PIN, environment_identity="other"),)]
)
def test_missing_ambiguous_or_wrong_environment_provider_rejects(pins):
    with pytest.raises(PreparationError, match="ML-PROVIDER"):
        prepared(provider_descriptors=pins)


def test_provider_pin_and_bounds_are_strict():
    for digest in ("latest", "sha256:1234", "sha256:" + "G" * 64):
        with pytest.raises(ValueError):
            replace(PIN, artifact_digest=digest)
    with pytest.raises(ValueError):
        replace(PIN, provider_id="arbitrary")
    for options in (
        {"max_units": True},
        {"max_units": 17},
        {"max_steps": 129},
        {"max_steps": 0},
        {"horizon_ticks": 1.0},
        {"horizon_ticks": 10001},
    ):
        with pytest.raises(ValueError):
            Limits(**options)
    with pytest.raises(PreparationError, match="ML-BOUND"):
        prepared(limits=Limits(max_units=1))


def test_ambiguous_actual_catalog_entry_rejects(monkeypatch):
    original = projection.derive_catalog

    def duplicate(resources):
        value = original(resources)
        return replace(value, entries=value.entries + (value.entries[0],))

    monkeypatch.setattr(projection, "derive_catalog", duplicate)
    with pytest.raises(PreparationError, match="ML-CATALOG"):
        prepared()


def test_combined_cycle_rejects_even_when_xdl_order_is_valid():
    docs = documents()
    steps = docs["scenario.json"]["spec"]["steps"]
    steps[0]["extensions"]["io.xverse.experiment"]["dependsOn"] = ["start-sink"]
    steps[1]["extensions"]["io.xverse.experiment"]["dependsOn"] = []
    with pytest.raises(PreparationError, match="ML-PROJECTION-CYCLE"):
        prepared(docs)


def test_missing_executable_flow_prerequisite_rejects():
    docs = documents()
    docs["deployment.json"]["spec"]["bindings"] = docs["deployment.json"]["spec"][
        "bindings"
    ][1:]
    docs["scenario.json"]["spec"]["steps"] = docs["scenario.json"]["spec"]["steps"][1:]
    docs["scenario.json"]["spec"]["steps"][0]["extensions"]["io.xverse.experiment"][
        "dependsOn"
    ] = []
    with pytest.raises(PreparationError, match="ML-PROJECTION"):
        prepared(docs)


def test_duplicate_realization_rejects_before_graph_creation():
    docs = documents()
    binding = docs["deployment.json"]["spec"]["bindings"][1]
    binding["logicalRef"]["element"] = "source-instance"
    with pytest.raises(PreparationError, match="ML-REALIZATION"):
        prepared(docs)


def test_no_logical_node_is_launched_as_an_extra_unit():
    value = prepared()
    assert not any("#nodes/" in unit.unit_id for unit in value.units)
    docs = documents()
    binding = docs["deployment.json"]["spec"]["bindings"][0]
    binding["logicalRef"]["element"] = "source-node"
    # Direct immutable-resource compilation permits intent; Maestro rejects node realization.
    result, resources = compiled()
    deployment = next(r for r in resources if r.identity.kind == "Deployment")
    content = {
        **dict(deployment.content),
        "bindings": freeze(docs["deployment.json"]["spec"]["bindings"]),
    }
    changed = tuple(
        replace(r, content=freeze(content)) if r is deployment else r for r in resources
    )
    compiled_changed = compile_experiment_plan(changed)
    assert compiled_changed.is_valid
    with pytest.raises(PreparationError, match="ML-REALIZATION|ML-CATALOG"):
        prepare(compiled_changed, changed, provider_descriptors=(PIN,))


def test_missing_start_step_rejects():
    docs = documents()
    docs["scenario.json"]["spec"]["steps"][1]["actionKind"] = "observe"
    docs["scenario.json"]["spec"]["steps"][1]["action"]["operation"] = "observe"
    docs["scenario.json"]["spec"]["steps"][1]["extensions"]["io.xverse.experiment"][
        "phase"
    ] = "observe"
    with pytest.raises(PreparationError, match="ML-PROJECTION"):
        prepared(docs)


def test_impossible_step_duration_and_dependency_window_reject():
    docs = documents()
    first = docs["scenario.json"]["spec"]["steps"][0]
    first["schedule"]["tolerance"]["value"] = 2
    first["extensions"]["io.xverse.experiment"]["duration"]["value"] = 2
    with pytest.raises(PreparationError, match="ML-TIME"):
        prepared(docs)


def test_source_pointers_and_full_logical_identity_survive_projection():
    value = prepared()
    assert all(step.logical_id.startswith(SCENARIO + "#steps/") for step in value.steps)
    assert any(
        edge.pointer.endswith("/1/extensions/io.xverse.experiment/dependsOn")
        for edge in value.graph_edges
    )
    assert len({step.logical_id for step in value.steps}) == 2


def test_static_eligibility_requires_flow_and_step_predecessor_completion():
    value = prepared()
    assert tuple(s.step_id for s in value.eligible_steps(0, ())) == ("start-source",)
    assert tuple(s.step_id for s in value.eligible_steps(0, ("start-source",))) == (
        "start-sink",
    )
    assert value.eligible_steps(0, ("start-source", "start-sink")) == ()
    with pytest.raises(ValueError):
        value.eligible_steps(0, ("unknown",))
    with pytest.raises(ValueError):
        value.eligible_steps(0.0, ())


def extra_step(docs, *, step_id, phase, unit="source-instance", at=0):
    step = copy.deepcopy(docs["scenario.json"]["spec"]["steps"][0])
    step.update(id=step_id, actionKind=projection.OPERATIONS[phase])
    step["action"]["operation"] = projection.OPERATIONS[phase]
    step["targetRef"]["element"] = unit
    step["schedule"]["at"] = at
    payload = step["extensions"]["io.xverse.experiment"]
    payload["phase"], payload["dependsOn"] = phase, []
    payload["target"]["element"] = step_id
    docs["scenario.json"]["spec"]["steps"].append(step)


def test_implicit_start_precedes_observation_without_explicit_dependency():
    docs = documents()
    extra_step(docs, step_id="observe-source", phase="observe")
    value = prepared(docs)
    assert [step.step_id for step in value.eligible_steps(0, ())] == ["start-source"]
    assert {step.step_id for step in value.eligible_steps(0, ("start-source",))} == {
        "start-sink",
        "observe-source",
    }


def test_early_stop_cannot_outlive_a_still_required_dependent():
    docs = documents()
    extra_step(docs, step_id="stop-source", phase="stop", at=2)
    with pytest.raises(PreparationError, match="ML-TIME"):
        prepared(docs, limits=Limits(horizon_ticks=10))
    extra_step(docs, step_id="stop-sink", phase="stop", unit="sink-instance", at=1)
    value = prepared(docs, limits=Limits(horizon_ticks=10))
    assert "stop-source" not in {
        s.step_id for s in value.eligible_steps(2, ("start-source", "start-sink"))
    }
    assert "stop-source" in {
        s.step_id
        for s in value.eligible_steps(2, ("start-source", "start-sink", "stop-sink"))
    }


def test_source_json_pointers_resolve_to_original_records():
    value = prepared()
    docs = documents()
    resources = {SYSTEM: docs["system.json"], SCENARIO: docs["scenario.json"]}
    for edge in value.graph_edges:
        if not edge.pointer:
            continue
        uri, pointer = edge.pointer.split("#", 1)
        current = resources[uri]
        for part in pointer.lstrip("/").split("/"):
            current = current[int(part)] if isinstance(current, list) else current[part]
        assert current is not None


def test_unsupported_actions_do_not_reach_provider_or_graph():
    docs = documents()
    step = docs["scenario.json"]["spec"]["steps"][0]
    step["action"]["unexpectedCommand"] = "run-anything"
    result, resources = compiled()
    scenario = next(r for r in resources if r.identity.kind == "Scenario")
    content = freeze(
        {**dict(scenario.content), "steps": docs["scenario.json"]["spec"]["steps"]}
    )
    changed = tuple(
        replace(r, content=content) if r is scenario else r for r in resources
    )
    changed_result = compile_experiment_plan(changed)
    assert changed_result.is_valid
    with pytest.raises(PreparationError, match="ML-UNSUPPORTED"):
        prepare(changed_result, changed, provider_descriptors=(PIN,))


def test_pure_prepare_cannot_open_sink_launch_lock_or_read_ambient_clock(monkeypatch):
    import builtins
    import socket
    import subprocess
    import threading
    import time

    result, resources = compiled()

    def denied(*args, **kwargs):
        raise AssertionError("preparation attempted an external effect")

    for owner, attribute in (
        (builtins, "open"),
        (Path, "open"),
        (subprocess, "Popen"),
        (socket, "socket"),
        (threading, "Lock"),
        (threading, "Thread"),
        (time, "time"),
        (time, "monotonic"),
    ):
        monkeypatch.setattr(owner, attribute, denied)
    value = prepare(result, resources, provider_descriptors=(PIN,))
    assert len(value.units) == 2
    with pytest.raises(PreparationError):
        prepare(result, resources, provider_descriptors=())

"""DV01/DV02 negative controls with per-case zero effects (increment19, finding 414).

Expected codes were authored in review-affa19.md finding 414 before this module first ran, from
ML-DESIGN-2026-10-03-v2 verification-plan.md (DV01-N, DV02-N) and projection-fixtures.json
(negative_controls). The design names the ML-PROJECTION family; the implementation refines it
(ML-REALIZATION, ML-UNSUPPORTED, ML-CATALOG). Every case also runs prepare() under an effect
recorder: no file, process, socket, lock, thread or ambient-clock use, and no prepared value.
"""

import copy
from dataclasses import replace
import json

import pytest

from xverse.maestro import PreparationError, prepare
from xverse.maestro import projection
from xverse_xdl.experiment_plan import ExperimentPlanResult, compile_experiment_plan, compute_plan_digest
from xverse_xdl.models import freeze

from .test_preparation import FIXTURES, PIN, compiled, documents

ARGUS_FIXTURES = FIXTURES.parents[1] / "argus" / "fixtures"
FAULT = json.loads((ARGUS_FIXTURES / "scenario.json").read_text())["spec"]["faults"][0]
PARAMETER = {"id": "gain", "mutability": "configuration", "unitSemantics": "dimensionless",
             "value": 2.0, "valueType": "number"}


def with_content(resources, kind, **changes):
    """Replace content fields of one immutable resource without revalidating its source text."""
    target = next(r for r in resources if r.identity.kind == kind)
    content = freeze({**dict(target.content), **{k: freeze(v) for k, v in changes.items()}})
    return tuple(replace(r, content=content) if r is target else r for r in resources)


def direct(resources):
    """Compile already-normalized resources directly (XDL intent accepted, Maestro decides)."""
    result = compile_experiment_plan(resources)
    assert result.is_valid, [(d.code, d.message) for d in result.diagnostics]
    return result, resources


# Each case returns (result, resources, prepare keyword arguments).

def hybrid_realization():
    docs = documents()
    docs["deployment.json"]["spec"]["bindings"][1]["realizationClass"] = "hybrid"
    return (*compiled(docs), {})


def scheduled_fault():
    docs = documents()
    docs["scenario.json"]["spec"]["faults"] = [copy.deepcopy(FAULT)]
    return (*compiled(docs), {})


def unbound_sink():
    # Source-document route: removing a binding from a normalized resource orphans its profile
    # payload and XDL rejects the plan before Maestro (finding 416).
    docs = documents()
    bindings = docs["deployment.json"]["spec"]["bindings"]
    docs["deployment.json"]["spec"]["bindings"] = [b for b in bindings if b["id"] != "sink-binding"]
    return (*compiled(docs), {})


def step_parameters():
    docs = documents()
    docs["scenario.json"]["spec"]["steps"][1]["extensions"]["io.xverse.experiment"]["parameters"] = [PARAMETER]
    return (*compiled(docs), {})


def set_parameter_action():
    docs = documents()
    step = docs["scenario.json"]["spec"]["steps"][1]
    step["actionKind"] = "set-parameter"
    step["action"]["operation"] = "set-parameter"
    _, resources = compiled()
    return (*direct(with_content(resources, "Scenario", steps=docs["scenario.json"]["spec"]["steps"])), {})


def changed_digest():
    result, resources = compiled()
    altered = copy.deepcopy(result.plan)
    altered["seed"]["value"] += 1
    return replace(result, plan=altered), resources, {}


def rehashed_forgery():
    result, resources = compiled()
    altered = copy.deepcopy(result.plan)
    altered["seed"]["value"] += 1
    altered["digest"]["value"] = compute_plan_digest(altered)
    return replace(result, plan=altered), resources, {}


def invalid_result():
    _, resources = compiled()
    return ExperimentPlanResult((), None), resources, {}


def duplicate_resource():
    result, resources = compiled()
    return result, resources + (resources[0],), {}


def missing_prerequisite_binding():
    docs = documents()
    docs["deployment.json"]["spec"]["bindings"] = docs["deployment.json"]["spec"]["bindings"][1:]
    docs["scenario.json"]["spec"]["steps"] = docs["scenario.json"]["spec"]["steps"][1:]
    docs["scenario.json"]["spec"]["steps"][0]["extensions"]["io.xverse.experiment"]["dependsOn"] = []
    return (*compiled(docs), {})


def duplicate_realization():
    docs = documents()
    docs["deployment.json"]["spec"]["bindings"][1]["logicalRef"]["element"] = "source-instance"
    return (*compiled(docs), {})


def combined_cycle():
    docs = documents()
    steps = docs["scenario.json"]["spec"]["steps"]
    steps[0]["extensions"]["io.xverse.experiment"]["dependsOn"] = ["start-sink"]
    steps[1]["extensions"]["io.xverse.experiment"]["dependsOn"] = []
    return (*compiled(docs), {})


def node_target():
    docs = documents()
    docs["deployment.json"]["spec"]["bindings"][0]["logicalRef"]["element"] = "source-node"
    _, resources = compiled()
    return (*direct(with_content(resources, "Deployment", bindings=docs["deployment.json"]["spec"]["bindings"])), {})


def impossible_window():
    docs = documents()
    first = docs["scenario.json"]["spec"]["steps"][0]
    first["schedule"]["tolerance"]["value"] = 2
    first["extensions"]["io.xverse.experiment"]["duration"]["value"] = 2
    return (*compiled(docs), {})


def missing_start_step():
    docs = documents()
    step = docs["scenario.json"]["spec"]["steps"][1]
    step["actionKind"] = "observe"
    step["action"]["operation"] = "observe"
    step["extensions"]["io.xverse.experiment"]["phase"] = "observe"
    return (*compiled(docs), {})


def unexpected_command():
    docs = documents()
    docs["scenario.json"]["spec"]["steps"][0]["action"]["unexpectedCommand"] = "run-anything"
    _, resources = compiled()
    return (*direct(with_content(resources, "Scenario", steps=docs["scenario.json"]["spec"]["steps"])), {})


def empty_providers():
    return (*compiled(), {"provider_descriptors": ()})


def ambiguous_catalog(monkeypatch):
    original = projection.derive_catalog

    def duplicate(resources):
        value = original(resources)
        return replace(value, entries=value.entries + (value.entries[0],))

    monkeypatch.setattr(projection, "derive_catalog", duplicate)
    return (*compiled(), {})


# (case id, builder, accepted code pattern from finding 414)
CASES = [
    # Rejected by accepted catalog derivation before the projection realization check (finding 416).
    ("R1-hybrid-realization", hybrid_realization, r"^ML-CATALOG$"),
    ("R2-scheduled-fault", scheduled_fault, r"^ML-UNSUPPORTED$"),
    ("R3-unbound-sink", unbound_sink, r"^ML-PROJECTION"),
    ("R4-step-parameters", step_parameters, r"^ML-UNSUPPORTED$"),
    ("R5-set-parameter-action", set_parameter_action, r"^ML-UNSUPPORTED$"),
    ("Z-changed-digest", changed_digest, r"^ML-PLAN-DIGEST$"),
    ("Z-rehashed-forgery", rehashed_forgery, r"^ML-PLAN-INPUT$"),
    ("Z-invalid-result", invalid_result, r"^ML-PLAN$"),
    ("Z-duplicate-resource", duplicate_resource, r"^ML-PLAN-INPUT$"),
    ("Z-missing-prerequisite-binding", missing_prerequisite_binding, r"^ML-PROJECTION"),
    ("Z-duplicate-realization", duplicate_realization, r"^ML-REALIZATION$"),
    ("Z-combined-cycle", combined_cycle, r"^ML-PROJECTION-CYCLE$"),
    ("Z-node-target", node_target, r"^ML-(REALIZATION|CATALOG)$"),
    ("Z-impossible-window", impossible_window, r"^ML-TIME$"),
    ("Z-missing-start-step", missing_start_step, r"^ML-PROJECTION"),
    ("Z-unexpected-command", unexpected_command, r"^ML-UNSUPPORTED$"),
    ("Z-empty-providers", empty_providers, r"^ML-PROVIDER$"),
]


@pytest.fixture
def effects(monkeypatch):
    """Arm an effect recorder for the duration of one prepare() call."""
    import builtins
    import os
    import socket
    import subprocess
    import threading
    import time
    from pathlib import Path

    attempts = []

    def arm(m):
        for owner, name in ((builtins, "open"), (Path, "open"), (os, "open"), (os, "fork"),
                            (os, "posix_spawn"), (subprocess, "Popen"), (subprocess, "run"),
                            (socket, "socket"), (threading, "Lock"), (threading, "RLock"),
                            (threading, "Thread"), (time, "time"), (time, "monotonic"),
                            (time, "time_ns"), (time, "monotonic_ns")):
            def denied(*args, _name=f"{getattr(owner, '__name__', owner)}.{name}", **kwargs):
                attempts.append(_name)
                raise AssertionError(f"preparation attempted an external effect: {_name}")
            m.setattr(owner, name, denied)

    return attempts, arm


def code_of(error):
    return error.code if hasattr(error, "code") else str(error).split(":", 1)[0]


@pytest.mark.parametrize("case_id, build, code", CASES, ids=[c[0] for c in CASES])
def test_rejection_is_whole_and_effect_free(case_id, build, code, effects, monkeypatch):
    import re

    result, resources, options = build()
    options.setdefault("provider_descriptors", (PIN,))
    attempts, arm = effects
    outcome = None
    with monkeypatch.context() as m:
        arm(m)
        try:
            outcome = prepare(result, resources, **options)
        except PreparationError as exc:
            error = exc
        else:
            error = None
    assert attempts == [], (case_id, attempts)
    assert outcome is None and error is not None, (case_id, "prepare returned a value")
    assert re.search(code, code_of(error)), (case_id, code_of(error), str(error))


def test_ambiguous_catalog_entry_is_whole_and_effect_free(effects, monkeypatch):
    result, resources, options = ambiguous_catalog(monkeypatch)
    attempts, arm = effects
    with monkeypatch.context() as m:
        arm(m)
        with pytest.raises(PreparationError) as raised:
            prepare(result, resources, provider_descriptors=(PIN,))
    assert attempts == []
    assert code_of(raised.value) == "ML-CATALOG"


def test_original_argus_fixture_is_rejected_whole(effects):
    """Design control original-argus-fixture: the accepted Argus fixture set is not executable."""
    from xverse_xdl.validate import validate_files
    from .test_preparation import SCHEMAS

    validation = validate_files(sorted(ARGUS_FIXTURES.glob("*.json")), profile_schema_paths=SCHEMAS)
    assert validation.is_valid, [(d.code, d.message) for d in validation.diagnostics]
    result = compile_experiment_plan(validation.resources)
    assert result.is_valid, [(d.code, d.message) for d in result.diagnostics]
    attempts, arm = effects
    with pytest.MonkeyPatch.context() as m:
        arm(m)
        with pytest.raises(PreparationError) as raised:
            prepare(result, validation.resources, provider_descriptors=(PIN,))
    assert attempts == []
    assert code_of(raised.value).startswith("ML-"), str(raised.value)


def test_zero_binding_deployment_never_becomes_a_plan():
    """R6: XDL schema rejects an empty binding list, so nothing reaches Maestro (finding 416)."""
    from xverse_xdl.validate import validate_sources
    from .test_preparation import SCHEMAS

    docs = documents()
    docs["deployment.json"]["spec"]["bindings"] = []
    validation = validate_sources([(n, json.dumps(v).encode()) for n, v in docs.items()],
                                  profile_schema_paths=SCHEMAS)
    assert not validation.is_valid
    assert "XDL-SCHEMA-INVALID" in {d.code for d in validation.diagnostics}


def test_effect_recorder_detects_each_denied_effect(effects, monkeypatch, tmp_path):
    """Mutation check of the recorder itself: an attempted effect is recorded and raised."""
    import subprocess
    import time

    attempts, arm = effects
    target = tmp_path / "x"
    with monkeypatch.context() as m:
        arm(m)
        for attempt in (lambda: open(target, "w"), lambda: target.open("w"),
                        lambda: subprocess.Popen(["true"]), lambda: time.monotonic()):
            with pytest.raises(AssertionError, match="external effect"):
                attempt()
    assert attempts == ["builtins.open", "Path.open", "subprocess.Popen", "time.monotonic"]
    assert not target.exists()

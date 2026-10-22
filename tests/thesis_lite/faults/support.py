"""Fixture builders for the Phase 5 tests: the Maestro fixture graph plus declared faults."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from xverse_xdl.experiment_plan import compile_experiment_plan
from xverse_xdl.validate import validate_sources

ROOT = Path(__file__).resolve().parents[3]
MAESTRO_FIXTURES = ROOT / "tests" / "thesis_lite" / "maestro" / "fixtures"
SCHEMAS = tuple(sorted((ROOT / "xdl" / "profiles").glob("*.schema.json")))
NAMESPACE = "org.xverse.experiment"
SYSTEM_NAME = "sample-loop"
SCENARIO_NAME = "sample-observation-run"
SYSTEM_URI = f"xdl://{NAMESPACE}/system/{SYSTEM_NAME}"
PLANNED_TICKS = (0, 2, 4, 8, 16, 32)


def documents() -> dict[str, dict]:
    """Return deep copies of the Maestro fixture documents keyed by file name."""

    return {path.name: json.loads(path.read_text()) for path in sorted(MAESTRO_FIXTURES.glob("*.json"))}


def with_sensor(docs: dict[str, dict]) -> dict[str, dict]:
    """Add one sensor whose output is the source endpoint, so observation faults have a target."""

    system = docs["system.json"]["spec"]
    system.setdefault("sensors", []).append({
        "id": "front-sensor",
        "observedQuantity": "range",
        "outputEndpointId": "source-out",
        "unitSemantics": "m",
        "maturity": "prototype",
    })
    return docs


def element_ref(element: str, *, kind: str = "System", name: str = SYSTEM_NAME) -> dict:
    """Return an XDL element reference into the fixture System (or Scenario)."""

    return {"apiVersion": "xverse.io/xdl/v1alpha1", "kind": kind, "namespace": NAMESPACE, "name": name, "element": element}


def fault(
    fault_id: str,
    fault_kind: str,
    element: str,
    *,
    at: int | None = 2,
    order: int | None = None,
    duration: int = 2,
    parameters: list[dict] | None = None,
    recovery: str = "automatic",
) -> dict:
    """Return one Scenario fault with its ``io.xverse.experiment`` fault-intent payload."""

    trigger = {"kind": "declared-order", "order": order} if order is not None else {"kind": "time", "at": at, "unit": "tick"}
    intent = {
        "schemaVersion": "0.1",
        "kind": "fault-intent",
        "target": element_ref(fault_id, kind="Scenario", name=SCENARIO_NAME),
        "trigger": trigger,
        "duration": {"value": duration, "unit": "tick"},
        "parameters": parameters or [],
    }
    if order is None:  # the Profile forbids a time domain on declared-order triggers
        intent["timeDomainId"] = "experiment-time"
    return {
        "id": fault_id,
        "targetRef": element_ref(element),
        "faultKind": fault_kind,
        "activation": "scheduled",
        "recovery": recovery,
        "maturity": "prototype",
        "extensions": {"io.xverse.experiment": intent},
    }


def parameter(name: str, value, value_type: str | None = None) -> dict:
    """Return one typed parameter entry."""

    kind = value_type or ("integer" if type(value) is int else "number" if isinstance(value, float) else "string")
    return {"id": name, "valueType": kind, "value": value, "unitSemantics": "tick" if kind == "integer" else "ratio" if kind == "number" else "policy"}


def six_kind_faults() -> list[dict]:
    """Return one fault of each executable kind on a suitable target, non-overlapping."""

    return [
        fault("f-delay", "delay", "sample-flow", at=2, duration=2, parameters=[parameter("delay-ticks", 1)]),
        fault("f-loss", "loss", "sample-flow", at=8, duration=2, parameters=[parameter("every", 2)]),
        fault("f-stale", "stale", "sample-flow", at=16, duration=2),
        fault("f-crash", "crash", "source-instance", at=4, duration=0),
        fault("f-freeze", "freeze", "sink-instance", at=4, duration=4),
        fault("f-dropout", "sensorDropout", "front-sensor", at=2, duration=4),
    ]


def compiled_plan(faults: list[dict], *, docs: dict[str, dict] | None = None) -> dict:
    """Compile the fixture graph with ``faults`` declared and return the plan as a mapping."""

    docs = copy.deepcopy(docs) if docs is not None else with_sensor(documents())
    docs["scenario.json"]["spec"]["faults"] = faults
    validation = validate_sources(
        [(name, json.dumps(value).encode()) for name, value in docs.items()],
        profile_schema_paths=SCHEMAS,
    )
    assert validation.is_valid, [(d.code, d.message) for d in validation.diagnostics]
    result = compile_experiment_plan(validation.resources)
    assert result.is_valid, [(d.code, d.message) for d in result.diagnostics]
    return json.loads(json.dumps(result.plan, default=lambda value: dict(value) if hasattr(value, "items") else list(value)))

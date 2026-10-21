"""DV02 discriminating positives from projection-fixtures.json (increment19, finding 419).

The expected edges and start orders are copied from the design table ML-DESIGN-2026-10-03-v2
(discriminating_cases), not derived from the implementation: eligibility follows the combined
graph, not the compiler's declaration rank, and a self-unit flow creates no inter-unit edge.
"""

from .test_preparation import SCENARIO, SINK, SOURCE, documents, prepared

START_SOURCE = SCENARIO + "#steps/start-source"
START_SINK = SCENARIO + "#steps/start-sink"


def kinds_between(value, source, target):
    return {e.kind for e in value.graph_edges if e.source[0] == source and e.target[0] == target}


def acyclic(value):
    rank = {node: i for i, node in enumerate(value.topological_order)}
    return all(rank[e.source] < rank[e.target] for e in value.graph_edges)


def test_flow_only_reversed_steps_start_by_flow_not_declaration_rank():
    docs = documents()
    steps = docs["scenario.json"]["spec"]["steps"]
    for step in steps:
        step["extensions"]["io.xverse.experiment"]["dependsOn"] = []
    steps.reverse()
    assert [s["id"] for s in steps][:2] == ["start-sink", "start-source"]
    value = prepared(docs)
    assert ((SOURCE, "ready"), (SINK, "dispatch")) in {(e.source, e.target) for e in value.graph_edges
                                                       if e.kind == "flow"}
    assert not kinds_between(value, START_SOURCE, START_SINK) - {"flow-step"}
    assert not kinds_between(value, START_SINK, START_SOURCE)
    assert not any(e.kind == "dependsOn" for e in value.graph_edges)
    assert tuple(s.step_id for s in value.eligible_steps(0, ())) == ("start-source",)
    assert tuple(s.step_id for s in value.eligible_steps(0, ("start-source",))) == ("start-sink",)
    assert acyclic(value)


def test_step_only_reversed_instances_keep_dependency_without_inter_unit_flow_edge():
    docs = documents()
    system = docs["system.json"]["spec"]
    system["endpoints"].append({"direction": "input", "id": "source-in",
                                "interfaceId": "sample-stream", "ownerId": "source-instance"})
    system["flows"][0]["destinationEndpointIds"] = ["source-in"]
    system["componentInstances"].reverse()
    assert [c["id"] for c in system["componentInstances"]] == ["sink-instance", "source-instance"]
    value = prepared(docs)
    pairs = {(e.kind, e.source, e.target) for e in value.graph_edges}
    assert ("dependsOn", (START_SOURCE, "complete"), (START_SINK, "dispatch")) in pairs
    assert not any(kind in ("flow", "flow-step") and source[0] != target[0] and
                   SINK in (source[0], target[0]) for kind, source, target in pairs)
    assert tuple(s.step_id for s in value.eligible_steps(0, ())) == ("start-source",)
    assert tuple(s.step_id for s in value.eligible_steps(0, ("start-source",))) == ("start-sink",)
    assert acyclic(value)

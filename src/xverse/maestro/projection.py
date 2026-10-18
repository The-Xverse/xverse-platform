"""Side-effect-free preparation over accepted XDL/M3 APIs (partial U1).

This module issues no authority and exposes no execution/evidence-success API.
Provider descriptors are inert pins, never callbacks or runtime-readiness proof.
"""

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
import hashlib
import heapq
import json
import re
from urllib.parse import quote

from xverse_xdl.catalog import LifecyclePlan, build_lifecycle_plan, derive_catalog
from xverse_xdl.experiment_plan import (
    ExperimentPlanResult,
    compile_experiment_plan,
    plan_matches_digest,
    resource_semantic_digest,
)
from xverse_xdl.models import NormalizedResource, ResourceIdentity

from .time import TickDomain

PHASE_RANK = {"prepare": 0, "start": 1, "observe": 2, "stop": 3, "cleanup": 4}
OPERATIONS = {
    "prepare": "validate",
    "start": "start",
    "observe": "observe",
    "stop": "stop",
    "cleanup": "cleanup",
}
PROVIDERS = {"maestro-fixture-v1": "fixture", "maestro-process-v1": "process"}
DIGEST_DOMAIN = b"xverse.maestro.preparation.increment1\0"
Node = tuple[str, str]


class PreparationError(ValueError):
    """Stable preparation diagnostic, optionally anchored to original XDL."""

    def __init__(self, code: str, message: str, pointer: str = "") -> None:
        super().__init__(f"{code}: {message}")
        self.code, self.pointer = code, pointer


def _reject(code: str, message: str, pointer: str = "") -> None:
    raise PreparationError(code, message, pointer)


def _json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def _logical(resource: ResourceIdentity, collection: str, element: str) -> str:
    return f"{resource.uri}#{collection}/{quote(element, safe='')}"


@dataclass(frozen=True)
class Limits:
    """Proposed engineering bounds, not dissertation protocol thresholds."""

    max_units: int = 16
    max_steps: int = 128
    max_edges: int = 16384
    horizon_ticks: int = 10000

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if type(value) is not int or value < (0 if name == "horizon_ticks" else 1):
                raise ValueError(f"invalid integer bound: {name}")
        caps = {
            "max_units": 16,
            "max_steps": 128,
            "max_edges": 16384,
            "horizon_ticks": 10000,
        }
        if any(getattr(self, name) > cap for name, cap in caps.items()):
            raise ValueError("limits exceed the declared engineering caps")


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    kind: str
    artifact_digest: str
    environment_identity: str

    def __post_init__(self) -> None:
        if PROVIDERS.get(self.provider_id) != self.kind:
            raise ValueError("provider id/kind is outside the closed registry")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.artifact_digest):
            raise ValueError("provider artifact needs an exact sha256 pin")
        if (
            not isinstance(self.environment_identity, str)
            or not self.environment_identity.strip()
        ):
            raise ValueError("provider environment identity is required")


@dataclass(frozen=True)
class Unit:
    unit_id: str
    binding_id: str
    node_id: str
    compiler_rank: int
    plan: LifecyclePlan
    provider: ProviderDescriptor


@dataclass(frozen=True)
class PreparedStep:
    step_id: str
    logical_id: str
    unit_id: str
    phase: str
    action: str
    at_ticks: int
    latest_ticks: int
    duration_ticks: int
    depends_on: tuple[str, ...]
    compiler_rank: int


@dataclass(frozen=True)
class GraphEdge:
    source: Node
    target: Node
    kind: str
    pointer: str
    minimum_ticks: int = 0


@dataclass(frozen=True)
class PreparedLifecycle:
    experiment_digest: str
    resource_digests: tuple[tuple[str, str], ...]
    units: tuple[Unit, ...]
    steps: tuple[PreparedStep, ...]
    graph_nodes: tuple[Node, ...]
    graph_edges: tuple[GraphEdge, ...]
    topological_order: tuple[Node, ...]
    resource_order: tuple[str, ...]
    clock: TickDomain
    limits: Limits
    canonical_bytes: bytes
    lifecycle_digest: str

    @property
    def ready_for_execution(self) -> bool:
        return False

    def eligible_steps(
        self, tick: int, completed_steps: Iterable[str]
    ) -> tuple[PreparedStep, ...]:
        """Static eligibility only: no live readiness, permits or execution inferred."""
        from .time import ClockContext, advance_tick

        advance_tick(ClockContext(self.clock, "static", "static"), tick, tick)
        complete = frozenset(completed_steps)
        if not complete <= {step.step_id for step in self.steps}:
            raise ValueError("completed step set contains an undeclared identity")
        predecessors = {step.step_id: set(step.depends_on) for step in self.steps}
        step_completions = {
            (step.logical_id, "complete"): step.step_id for step in self.steps
        }
        incoming = {node: set() for node in self.graph_nodes}
        for edge in self.graph_edges:
            incoming[edge.target].add(edge.source)
        for step in self.steps:
            pending = list(incoming[(step.logical_id, "dispatch")])
            visited = set()
            while pending:
                node = pending.pop()
                if node in visited:
                    continue
                visited.add(node)
                if node in step_completions:
                    predecessors[step.step_id].add(step_completions[node])
                pending.extend(incoming[node])
        starts = {
            step.unit_id: step.step_id for step in self.steps if step.phase == "start"
        }
        for edge in self.graph_edges:
            if edge.kind == "flow":
                predecessors[starts[edge.target[0]]].add(starts[edge.source[0]])
        return tuple(
            sorted(
                (
                    step
                    for step in self.steps
                    if step.step_id not in complete
                    and step.at_ticks <= tick <= step.latest_ticks
                    and predecessors[step.step_id] <= complete
                ),
                key=lambda step: (
                    step.compiler_rank,
                    PHASE_RANK[step.phase],
                    step.logical_id,
                ),
            )
        )


def _order(nodes: set[Node], edges: Sequence[GraphEdge]) -> tuple[Node, ...]:
    incoming = {node: set() for node in nodes}
    outgoing = {node: set() for node in nodes}
    for edge in edges:
        incoming[edge.target].add(edge.source)
        outgoing[edge.source].add(edge.target)
    ready = [node for node, parents in incoming.items() if not parents]
    heapq.heapify(ready)
    ordered = []
    while ready:
        node = heapq.heappop(ready)
        ordered.append(node)
        for child in sorted(outgoing[node]):
            incoming[child].remove(node)
            if not incoming[child]:
                heapq.heappush(ready, child)
    if len(ordered) != len(nodes):
        _reject("ML-PROJECTION-CYCLE", "combined lifecycle dependency cycle")
    return tuple(ordered)


def prepare_lifecycle(
    result: ExperimentPlanResult,
    resources: Sequence[NormalizedResource],
    *,
    provider_descriptors: Iterable[ProviderDescriptor] = (),
    limits: Limits | None = None,
) -> PreparedLifecycle:
    """Verify, recompile and project the original closed XDL set with zero effects."""
    limits = limits if limits is not None else Limits()
    if not isinstance(limits, Limits):
        raise ValueError("limits must be a Limits value")
    if not isinstance(result, ExperimentPlanResult) or not result.is_valid:
        _reject("ML-PLAN", "a valid accepted compiler result is required")
    try:
        supplied = json.loads(_json(result.plan))
        if not plan_matches_digest(supplied):
            _reject("ML-PLAN-DIGEST", "experiment plan digest mismatch")
    except (TypeError, KeyError, ValueError) as exc:
        if isinstance(exc, PreparationError):
            raise
        raise PreparationError("ML-PLAN-DIGEST", "malformed experiment plan") from exc
    resources = tuple(resources)
    if not all(isinstance(item, NormalizedResource) for item in resources):
        _reject("ML-PLAN-INPUT", "resources must be immutable normalized XDL")
    if len({item.identity for item in resources}) != len(resources):
        _reject("ML-PLAN-INPUT", "duplicate resource identity")
    recomputed = compile_experiment_plan(
        resources, static_readiness=supplied["selection"]["staticReadiness"]
    )
    if not recomputed.is_valid or _json(recomputed.plan) != _json(supplied):
        _reject("ML-PLAN-INPUT", "normalized XDL does not reproduce the supplied plan")
    plan = recomputed.plan
    if plan["faultSchedule"]:
        _reject("ML-UNSUPPORTED", "fault execution belongs to Phase 5")
    selected = plan["selection"]
    by_uri = {item.identity.uri: item for item in resources}
    system = by_uri[selected["system"]["uri"]]
    scenario = by_uri[selected["scenario"]["uri"]]
    if selected["deployment"] is None:
        _reject("ML-PROJECTION", "an executable deployment is required")
    deployment = by_uri[selected["deployment"]["uri"]]
    domains = plan["timeDomains"]
    if len(domains) != 1 or domains[0]["clockClass"] != "simulation":
        _reject("ML-TIME", "exactly one simulation domain is supported")
    clock = TickDomain(domains[0]["id"], limits.horizon_ticks)
    descriptors = tuple(provider_descriptors)
    if any(not isinstance(item, ProviderDescriptor) for item in descriptors):
        _reject("ML-PROVIDER", "descriptors must be inert ProviderDescriptor values")
    catalog = derive_catalog(resources)
    if not catalog.is_valid:
        _reject("ML-CATALOG", "accepted catalog derivation rejected the resource set")
    ranks = {
        (item["kind"], item["id"]): item["rank"] for item in plan["dependencyOrder"]
    }
    instances = {item["id"]: item for item in system.content["componentInstances"]}
    units, instance_units, entry_ids = [], {}, set()
    binding_indices = {
        item["id"]: index for index, item in enumerate(deployment.content["bindings"])
    }
    for binding in plan["bindings"]:
        pointer = (
            f"{deployment.identity.uri}#/spec/bindings/{binding_indices[binding['id']]}"
        )
        ref = binding["logicalRef"]
        if (
            binding["collection"] != "componentInstances"
            or ref["uri"] != system.identity.uri
        ):
            _reject(
                "ML-REALIZATION",
                "only bound component instances are executable",
                pointer,
            )
        if (
            binding["realizationClass"] not in ("simulated", "virtual")
            or binding["delivery"] != "none"
            or binding["retry"]
        ):
            _reject(
                "ML-REALIZATION", "unsupported realization, delivery or retry", pointer
            )
        instance = ref["element"]
        if instance in instance_units:
            _reject("ML-REALIZATION", "duplicate executable realization", pointer)
        entries = [
            entry
            for entry in catalog.entries
            if entry.deployment == deployment.identity
            and entry.binding_id == binding["id"]
            and entry.system == system.identity
            and entry.component_instance == f"{system.identity.uri}#{instance}"
        ]
        if len(entries) != 1:
            _reject(
                "ML-CATALOG", "binding must resolve exactly one catalog entry", pointer
            )
        entry = entries[0]
        m3 = build_lifecycle_plan(entry)
        if not m3.is_plannable:
            _reject("ML-CATALOG", "selected M3 plan has planning blockers", pointer)
        if (
            tuple(sorted(item["digest"] for item in binding["artifactRefs"]))
            != m3.artifact_digests
        ):
            _reject(
                "ML-CATALOG", "artifact pins disagree with selected M3 plan", pointer
            )
        matches = [
            d
            for d in descriptors
            if d.provider_id == m3.provider_id
            and d.kind == m3.provider_kind
            and d.environment_identity == m3.environment_identity
        ]
        if len(matches) != 1:
            _reject(
                "ML-PROVIDER",
                "provider/environment must have exactly one descriptor",
                pointer,
            )
        if any(
            action.operation != OPERATIONS.get(action.phase) for action in m3.actions
        ):
            _reject("ML-CATALOG", "unsupported M3 operation", pointer)
        unit_id = _logical(system.identity, "componentInstances", instance)
        unit = Unit(
            unit_id,
            binding["id"],
            _logical(system.identity, "nodes", instances[instance]["nodeId"]),
            ranks[("component-instance", instance)],
            m3,
            matches[0],
        )
        units.append(unit)
        instance_units[instance] = unit
        entry_ids.add(entry.identity)
    if not units or len(units) > limits.max_units:
        _reject("ML-BOUND", "executable unit count is empty or exceeds its bound")
    if any(
        entry.deployment == deployment.identity and entry.identity not in entry_ids
        for entry in catalog.entries
    ):
        _reject(
            "ML-CATALOG", "an executable catalog entry was omitted by the projection"
        )
    steps = []
    declarations = {item["id"]: item for item in scenario.content["steps"]}
    step_indices = {
        item["id"]: index for index, item in enumerate(scenario.content["steps"])
    }
    for item in plan["lifecycleIntent"]:
        pointer = f"{scenario.identity.uri}#/spec/steps/{step_indices[item['stepId']]}"
        phase = item["phase"]
        ref = item["targetRef"]
        if OPERATIONS.get(phase) != item["actionKind"] or phase not in PHASE_RANK:
            _reject(
                "ML-UNSUPPORTED", "unsupported scheduled phase/action pair", pointer
            )
        declared_action = declarations[item["stepId"]].get("action", {})
        if (
            set(declared_action) != {"operation"}
            or declared_action["operation"] != item["actionKind"]
            or item["parameters"]
        ):
            _reject(
                "ML-UNSUPPORTED",
                "scheduled commands/parameters are not supported",
                pointer,
            )
        if (
            ref["uri"] != system.identity.uri
            or ref.get("element") not in instance_units
        ):
            _reject(
                "ML-PROJECTION",
                "step target must resolve one executable instance",
                pointer,
            )
        if item["timeDomainId"] != clock.domain:
            _reject(
                "ML-TIME", "step is outside the admitted simulation domain", pointer
            )
        schedule = item["schedule"]
        at = schedule["atTicks"]
        tolerance = schedule["tolerance"]["ticks"] if schedule["tolerance"] else 0
        duration = item["duration"]["ticks"] if item["duration"] else 0
        if (
            any(
                type(value) is not int or value < 0
                for value in (at, tolerance, duration)
            )
            or at + tolerance > clock.horizon_ticks
        ):
            _reject("ML-TIME", "schedule exceeds the frozen tick horizon", pointer)
        steps.append(
            PreparedStep(
                item["stepId"],
                _logical(scenario.identity, "steps", item["stepId"]),
                instance_units[ref["element"]].unit_id,
                phase,
                item["actionKind"],
                at,
                at + tolerance,
                duration,
                tuple(item["dependsOn"]),
                ranks[("step", item["stepId"])],
            )
        )
    if not steps or len(steps) > limits.max_steps:
        _reject("ML-BOUND", "scheduled step count is empty or exceeds its bound")
    units.sort(key=lambda unit: (unit.compiler_rank, unit.unit_id))
    steps.sort(
        key=lambda step: (step.compiler_rank, PHASE_RANK[step.phase], step.logical_id)
    )
    return _project(
        plan,
        resources,
        system,
        scenario,
        tuple(units),
        tuple(steps),
        clock,
        limits,
        ranks,
    )


def _project(
    plan, resources, system, scenario, units, steps, clock, limits, ranks
) -> PreparedLifecycle:
    nodes: set[Node] = set()
    edges: list[GraphEdge] = []

    def edge(source: Node, target: Node, kind="phase", pointer="", ticks=0):
        nodes.update((source, target))
        edges.append(GraphEdge(source, target, kind, pointer, ticks))

    starts, stops = {}, {}
    for unit in units:
        unit_steps = [step for step in steps if step.unit_id == unit.unit_id]
        start = [step for step in unit_steps if step.phase == "start"]
        if len(start) != 1:
            _reject("ML-PROJECTION", "each unit requires exactly one start step")
        starts[unit.unit_id] = start[0]
        for phase in ("stop", "cleanup"):
            if sum(step.phase == phase for step in unit_steps) > 1:
                _reject("ML-PROJECTION", f"duplicate {phase} step")
        stop = [step for step in unit_steps if step.phase == "stop"]
        stops[unit.unit_id] = stop[0] if stop else None
        for before, after in (
            ("dispatch", "release"),
            ("release", "probe"),
            ("probe", "ready"),
            ("ready", "start-complete"),
            ("start-complete", "termination"),
            ("termination", "stop-complete"),
            ("stop-complete", "cleanup"),
        ):
            edge((unit.unit_id, before), (unit.unit_id, after))
        edge((unit.node_id, "placement"), (unit.unit_id, "dispatch"), "placement")
    by_id = {step.step_id: step for step in steps}
    step_indices = {
        item["id"]: index for index, item in enumerate(scenario.content["steps"])
    }
    for step in steps:
        pointer = f"{scenario.identity.uri}#/spec/steps/{step_indices[step.step_id]}"
        dispatch, complete = (
            (step.logical_id, "dispatch"),
            (step.logical_id, "complete"),
        )
        edge(dispatch, complete, "duration", pointer, step.duration_ticks)
        for dep in step.depends_on:
            predecessor = by_id.get(dep)
            if (
                predecessor is None
                or predecessor.compiler_rank >= step.compiler_rank
                or PHASE_RANK[predecessor.phase] > PHASE_RANK[step.phase]
            ):
                _reject(
                    "ML-PROJECTION",
                    "dependency violates compiler order or phase order",
                    pointer,
                )
            edge(
                (predecessor.logical_id, "complete"),
                dispatch,
                "dependsOn",
                pointer + "/extensions/io.xverse.experiment/dependsOn",
            )
        unit = step.unit_id
        if step.phase == "start":
            edge(dispatch, (unit, "dispatch"))
            edge((unit, "start-complete"), complete)
        elif step.phase == "prepare":
            edge(complete, (unit, "dispatch"))
            edge(complete, (starts[unit].logical_id, "dispatch"))
        elif step.phase == "observe":
            edge((starts[unit].logical_id, "complete"), dispatch)
            edge(dispatch, (step.logical_id, "probe"))
            edge((step.logical_id, "probe"), complete)
            edge(complete, (unit, "termination"))
        elif step.phase == "stop":
            edge((starts[unit].logical_id, "complete"), dispatch)
            for observation in steps:
                if observation.unit_id == unit and observation.phase == "observe":
                    edge((observation.logical_id, "complete"), dispatch)
            edge(dispatch, (unit, "termination"))
            edge((unit, "stop-complete"), complete)
            edge(complete, (unit, "cleanup"))
        elif step.phase == "cleanup":
            edge((unit, "stop-complete"), dispatch)
            if stops[unit] is not None:
                edge((stops[unit].logical_id, "complete"), dispatch)
            edge(dispatch, (unit, "cleanup"))
            edge((unit, "cleanup"), complete)
    endpoints = {item["id"]: item for item in system.content["endpoints"]}
    instance_units = {
        unit.plan.selection["componentInstance"].split("#", 1)[1]: unit
        for unit in units
    }
    flow_pairs = set()
    for flow_index, flow in enumerate(system.content.get("flows", ())):
        pointer = f"{system.identity.uri}#/spec/flows/{flow_index}"
        source = endpoints[flow["sourceEndpointId"]]["ownerId"]
        for destination in flow["destinationEndpointIds"]:
            target = endpoints[destination]["ownerId"]
            if source == target:
                continue
            if source not in instance_units or target not in instance_units:
                _reject(
                    "ML-PROJECTION", "flow owner lacks an executable binding", pointer
                )
            a, b = instance_units[source], instance_units[target]
            if (
                ranks[("component-instance", source)]
                >= ranks[("component-instance", target)]
            ):
                _reject("ML-PROJECTION", "flow contradicts compiler rank", pointer)
            edge((a.unit_id, "ready"), (b.unit_id, "dispatch"), "flow", pointer)
            edge(
                (a.unit_id, "ready"),
                (starts[b.unit_id].logical_id, "dispatch"),
                "flow-step",
                pointer,
            )
            edge(
                (b.unit_id, "cleanup"),
                (a.unit_id, "termination"),
                "reverse-teardown",
                pointer,
            )
            if stops[a.unit_id] is not None:
                edge(
                    (b.unit_id, "cleanup"),
                    (stops[a.unit_id].logical_id, "dispatch"),
                    "reverse-stop",
                    pointer,
                )
            flow_pairs.add((a.unit_id, b.unit_id))
    if len(flow_pairs) > 128 or len(edges) > limits.max_edges:
        _reject("ML-BOUND", "projected edges exceed the frozen bound")
    order = _order(nodes, edges)
    earliest = {node: 0 for node in nodes}
    for unit in units:
        if stops[unit.unit_id] is None:
            earliest[(unit.unit_id, "termination")] = clock.horizon_ticks
    for step in steps:
        earliest[(step.logical_id, "dispatch")] = step.at_ticks
    outgoing = {node: [] for node in nodes}
    for item in edges:
        outgoing[item.source].append(item)
    for node in order:
        for item in outgoing[node]:
            earliest[item.target] = max(
                earliest[item.target], earliest[node] + item.minimum_ticks
            )
    for step in steps:
        if earliest[(step.logical_id, "complete")] > step.latest_ticks:
            _reject(
                "ML-TIME",
                "dependency completion cannot meet the step window",
                f"{scenario.identity.uri}#/spec/steps/{step_indices[step.step_id]}",
            )
    body = {
        "increment": "maestro-preparation-1",
        "executionEligible": False,
        "experimentDigest": plan["digest"]["value"],
        "resources": sorted(
            (item.identity.uri, resource_semantic_digest(item)) for item in resources
        ),
        "units": [
            {
                "unitId": unit.unit_id,
                "bindingId": unit.binding_id,
                "nodeId": unit.node_id,
                "compilerRank": unit.compiler_rank,
                "catalogDigest": unit.plan.digest,
                "provider": asdict(unit.provider),
            }
            for unit in units
        ],
        "steps": [asdict(step) for step in steps],
        "nodes": sorted(nodes),
        "edges": [asdict(item) for item in edges],
        "clock": asdict(clock),
        "limits": asdict(limits),
    }
    encoded = _json(body)
    return PreparedLifecycle(
        plan["digest"]["value"],
        tuple(body["resources"]),
        units,
        steps,
        tuple(sorted(nodes)),
        tuple(edges),
        order,
        tuple(unit.unit_id for unit in units),
        clock,
        limits,
        encoded,
        hashlib.sha256(DIGEST_DOMAIN + encoded).hexdigest(),
    )

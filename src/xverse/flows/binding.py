"""Flow binding: declared flows to flow-runtime routes with explicit per-route policies.

Implements the data model's stage 0 and steps 1-9 (design §6; contract rules 1-7). Refusals are
collected, never raised; a record with any refusal is not activatable and no route opens (gate G1).
A flow's policy is the resource-level ``io.xverse.xcom`` flow-policy of the Component owning its
source endpoint, else of the Deployment (D6-9). The X-COM core is compiled by ``xcom_plan`` from
the same digest-checked inputs; when that plan is activatable its policy block must agree with
every binding (D6-10). The route model mirrors the loopback provider (D6-7).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from xverse_xdl.experiment_plan import compute_plan_digest
from xverse_xdl.models import NormalizedResource
from xverse_xdl.xcom_plan import XcomPlanError, compile_plan, compute_digest

from . import codes as C
from .convert import COMPILE_KINDS, check_inputs, check_xcom_provenance, thaw, to_graph_entry
from .provider import LOOPBACK, MIRROR_SHA256, claims
from .timebase import TimeMapping, parse_mapping, parse_quantity_ns

SCHEMA = "xverse.flows.binding/1"
XCOM_NAMESPACE = "io.xverse.xcom"
RESOURCE_LEVEL_POINTER = f"/extensions/{XCOM_NAMESPACE}"
INTENT_FIXED = {"best-effort": {"reliability": "best-effort", "ordering": "unordered"}, "reliable": {"reliability": "at-least-once"}, "ordered": {"ordering": "fifo"}}
TOKENS = {"best_effort": "xcom.delivery.best-effort", "reliable": "xcom.delivery.reliable", "unordered": "xcom.ordering.unordered", "per_route_fifo": "xcom.ordering.per-route-fifo"}
QUALITY_MEMBERS = ("freshness", "deadline", "receiverTimeDomainId")


@dataclass(frozen=True)
class FlowPolicy:
    """Per-route policy derived from intent and payload."""

    ordering: str
    reliability: str
    queue_depth: int
    overflow: str
    retry: int
    core_deadline_ms: int

    def to_json(self) -> dict[str, Any]:
        """Return the serialized policy."""

        return {"ordering": self.ordering, "reliability": self.reliability, "queueDepth": self.queue_depth,
                "overflow": self.overflow, "retry": self.retry, "coreDeadlineMs": self.core_deadline_ms}


@dataclass(frozen=True)
class FlowBinding:
    """One bound flow (one route)."""

    flow_id: str
    source: str
    destination: str
    contract_id: str
    delivery_intent: str
    policy: FlowPolicy
    claim_delivery: str
    claim_ordering: str
    provider_id: str
    sender_domain: str
    receiver_domain: str
    mapping: TimeMapping
    freshness_ns: int
    deadline_ns: int

    def to_json(self) -> dict[str, Any]:
        """Return the serialized binding."""

        return {"flowId": self.flow_id, "source": self.source, "destination": self.destination, "contractId": self.contract_id,
                "deliveryIntent": self.delivery_intent, "policy": self.policy.to_json(),
                "claims": {"delivery": self.claim_delivery, "ordering": self.claim_ordering}, "providerId": self.provider_id,
                "senderDomain": self.sender_domain, "receiverDomain": self.receiver_domain, "mapping": self.mapping.to_json(),
                "freshnessBoundNs": self.freshness_ns, "deadlineNs": self.deadline_ns}


@dataclass(frozen=True)
class FlowBindingRecord:
    """Versioned binding record (serialization table of design §6)."""

    experiment_plan_sha256: str | None
    input_digests: Mapping[str, str]
    xcom_plan_sha256: str | None
    xcom_graph_digest: str | None
    xcom_plan_status: str | None
    xcom_plan_diagnostics: tuple[Mapping[str, str], ...]
    xcom_plan_error: str | None
    bindings: tuple[FlowBinding, ...]
    refusals: tuple[Mapping[str, Any], ...]
    ignored_payloads: tuple[str, ...] = ()
    ignored_quality: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def activatable(self) -> bool:
        """Return whether no refusal exists."""

        return not self.refusals

    def binding(self, flow_id: str) -> FlowBinding:
        """Return the binding of ``flow_id``."""

        for item in self.bindings:
            if item.flow_id == flow_id:
                return item
        raise C.FlowError(C.HARNESS, f"flow {flow_id!r} is not bound")

    def to_json(self) -> dict[str, Any]:
        """Return the serialized record."""

        return {
            "schema": SCHEMA, "experimentPlanSha256": self.experiment_plan_sha256, "inputDigests": dict(self.input_digests),
            "xcomPlanSha256": self.xcom_plan_sha256, "xcomGraphDigest": self.xcom_graph_digest, "xcomPlanStatus": self.xcom_plan_status,
            "xcomPlanDiagnostics": [dict(item) for item in self.xcom_plan_diagnostics], "xcomPlanError": self.xcom_plan_error,
            "cppMirrorSha256": MIRROR_SHA256, "tickPeriodNs": 1,
            "bindings": [item.to_json() for item in sorted(self.bindings, key=lambda b: b.flow_id)],
            "refusals": sorted((dict(item) for item in self.refusals), key=lambda r: (r["flowId"] is not None, r["flowId"] or "", r["code"])),
            "ignoredPayloads": sorted(self.ignored_payloads),
            "ignoredQuality": {key: sorted(value) for key, value in sorted(self.ignored_quality.items())},
        }

    def canonical_bytes(self) -> bytes:
        """Return the canonical JSON bytes of the record."""

        return json.dumps(self.to_json(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def sha256(self) -> str:
        """Return the SHA-256 of the canonical bytes."""

        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def flow_hash(flow_id: str) -> str:
    """Return the 16-hex-character evidence id prefix of ``flow_id`` (design §7, E2)."""

    return hashlib.sha256(flow_id.encode("utf-8")).hexdigest()[:16]


def _xcom_payloads(resource: NormalizedResource) -> list[tuple[str, Mapping[str, Any]]]:
    """Return ``(pointer, value)`` of every ``io.xverse.xcom`` payload of ``resource``."""

    entry = thaw(resource.extensions).get(XCOM_NAMESPACE) or {}
    return [(str(p.get("pointer")), p.get("value") or {}) for p in entry.get("payloads") or () if isinstance(p, Mapping)]


def _resource_flow_policy(resource: NormalizedResource | None) -> Mapping[str, Any] | None:
    """Return the resource-level flow-policy payload's ``policy`` of ``resource``."""

    if resource is None:
        return None
    for pointer, value in _xcom_payloads(resource):
        if pointer == RESOURCE_LEVEL_POINTER and value.get("kind") == "flow-policy":
            return value.get("policy") or {}
    return None


def _empty(plan_sha: str | None, digests: Mapping[str, str], refusals: list[dict[str, Any]], **xcom: Any) -> FlowBindingRecord:
    """Return a record with refusals and no bindings."""

    return FlowBindingRecord(plan_sha, digests, xcom.get("sha"), xcom.get("graph"), xcom.get("status"),
                             tuple(xcom.get("diagnostics") or ()), xcom.get("error"), (), tuple(refusals))


def bind(plan: Mapping[str, Any], resources: Sequence[NormalizedResource]) -> FlowBindingRecord:
    """Bind every flow of ``plan`` to one route; collect refusals (design §6 procedure).

    @param plan Validated experiment plan.
    @param resources The plan's contributing normalized resources (provenance-exact).
    @return The binding record.
    """

    plan_sha = compute_plan_digest(plan)
    digests, refused = check_inputs(plan, resources)
    if refused:
        return _empty(plan_sha, digests, refused)
    entries = [to_graph_entry(r) for r in resources if r.identity.kind in COMPILE_KINDS]
    try:
        xplan = compile_plan({"resources": entries})
    except XcomPlanError as error:
        return _empty(plan_sha, digests, [C.refusal(C.XCOM_PLAN, None, xcomPlanError=error.code)], error=error.code)
    diagnostics = tuple(dict(item) for item in xplan.get("diagnostics") or ())
    xcom = dict(sha=compute_digest(xplan), status=xplan.get("status"), diagnostics=diagnostics)
    graph, refused = check_xcom_provenance(xplan, entries)
    xcom["graph"] = graph
    if refused:
        return _empty(plan_sha, digests, refused, **xcom)
    other = [item for item in diagnostics if item.get("code") != "XCOM-PLAN-POLICY-CONFLICT"]
    if other:
        return _empty(plan_sha, digests, [C.refusal(C.XCOM_PLAN, None, xcomPlanDiagnostics=[dict(item) for item in diagnostics])], **xcom)
    return _bind_flows(plan, resources, xplan, plan_sha, digests, xcom)


def _bind_flows(plan: Mapping[str, Any], resources: Sequence[NormalizedResource], xplan: Mapping[str, Any],
                plan_sha: str, digests: Mapping[str, str], xcom: Mapping[str, Any]) -> FlowBindingRecord:
    """Run the hash-collision check and steps 1-9 for every flow."""

    by_kind: dict[str, list[NormalizedResource]] = {}
    for resource in resources:
        by_kind.setdefault(resource.identity.kind, []).append(resource)
    system = thaw(by_kind["System"][0].content)
    deployment_resource = (by_kind.get("Deployment") or [None])[0]
    deployment = thaw(deployment_resource.content) if deployment_resource is not None else {}
    components = {(r.identity.namespace, r.identity.name): r for r in by_kind.get("Component", ())}
    ignored = [f"{r.identity.kind}/{r.identity.name}{p}" for r in by_kind.get("Scenario", ()) for p, v in _xcom_payloads(r) if v.get("kind") == "flow-policy"]
    refusals: list[dict[str, Any]] = []
    flows = sorted(plan.get("flows") or (), key=lambda f: str(f.get("id")))
    hashes: dict[str, str] = {}
    for flow in flows:
        hashes.setdefault(flow_hash(str(flow.get("id"))), str(flow.get("id")))
        if hashes[flow_hash(str(flow.get("id")))] != str(flow.get("id")):
            refusals.append(C.refusal(C.INPUT_MISMATCH, None, reason="flow-id-hash-collision"))
            return FlowBindingRecord(plan_sha, digests, xcom.get("sha"), xcom.get("graph"), xcom.get("status"), tuple(xcom.get("diagnostics") or ()), None, (), tuple(refusals), tuple(ignored))
    endpoints = {e.get("id"): e for e in system.get("endpoints") or ()}
    instances = {i.get("id"): i for i in system.get("componentInstances") or ()}
    system_flows = {f.get("id"): f for f in system.get("flows") or ()}
    domains = {d.get("id") for d in system.get("timeDomains") or ()}
    mappings = {(m.get("sourceTimeDomainId"), m.get("targetTimeDomainId")): m for m in plan.get("timeMappings") or ()}
    deployment_policy = _resource_flow_policy(deployment_resource)
    survivors: list[tuple[str, dict[str, Any]]] = []
    ignored_quality: dict[str, tuple[str, ...]] = {}
    for flow in flows:
        flow_id = str(flow.get("id"))
        outcome = _steps_1_to_7(flow, endpoints, instances, components, deployment_policy, deployment, xplan)
        if "code" in outcome:
            refusals.append(C.refusal(outcome.pop("code"), flow_id, **outcome))
            continue
        survivors.append((flow_id, outcome))
    # Step 8: queue limit, then route count per provider over the queue survivors.
    queued: list[tuple[str, dict[str, Any]]] = []
    for flow_id, state in survivors:
        if state["policy"].queue_depth > LOOPBACK.max_queue_items:
            refusals.append(C.refusal(C.UNSUPPORTED, flow_id, xcomOutcome="queue_limit_exceeded", queueDepth=state["policy"].queue_depth))
        else:
            queued.append((flow_id, state))
    per_provider: dict[str, int] = {}
    routed: list[tuple[str, dict[str, Any]]] = []
    for flow_id, state in queued:
        count = per_provider.get(state["provider"], 0) + 1
        per_provider[state["provider"]] = count
        if count > LOOPBACK.max_routes:
            refusals.append(C.refusal(C.UNSUPPORTED, flow_id, xcomOutcome="route_capacity_exhausted", providerId=state["provider"]))
        else:
            routed.append((flow_id, state))
    # Step 9: time and quality.
    bindings: list[FlowBinding] = []
    for flow_id, state in routed:
        flow = state["flow"]
        quality = (system_flows.get(flow_id) or {}).get("quality") or {}
        extra = tuple(sorted(k for k in quality if k not in QUALITY_MEMBERS))
        if extra:
            ignored_quality[flow_id] = extra
        timed = _step_9(flow, quality, domains, mappings)
        if "code" in timed:
            refusals.append(C.refusal(timed.pop("code"), flow_id, **timed))
            continue
        bindings.append(FlowBinding(flow_id, str(flow.get("sourceEndpointId")), str((flow.get("destinationEndpointIds") or [None])[0]),
                                    str(flow.get("interfaceId")), str(flow.get("deliveryIntent")), state["policy"], state["claims"][0],
                                    state["claims"][1], state["provider"], timed["sender"], timed["receiver"], timed["mapping"],
                                    timed["freshness"], timed["deadline"]))
    if xcom.get("status") == "activatable":
        block = xplan.get("policies") or {}
        for item in bindings:
            differ = _crosscheck(block, item.policy)
            if differ:
                refusals.append(C.refusal(C.XCOM_CROSSCHECK, item.flow_id, fields=differ))  # L3
    return FlowBindingRecord(plan_sha, digests, xcom.get("sha"), xcom.get("graph"), xcom.get("status"), tuple(xcom.get("diagnostics") or ()),
                             None, tuple(bindings), tuple(refusals), tuple(ignored), ignored_quality)


def _crosscheck(block: Mapping[str, Any], policy: FlowPolicy) -> list[str]:
    """Return the fields where the plan-wide policy block differs from ``policy`` (T6)."""

    pairs = {"ordering": policy.ordering, "reliability": policy.reliability, "queueDepth": policy.queue_depth,
             "overflow": policy.overflow, "retry": policy.retry, "deadlineMs": policy.core_deadline_ms}
    return sorted(key for key, value in pairs.items() if block.get(key) != value)


def _steps_1_to_7(flow: Mapping[str, Any], endpoints: Mapping[str, Any], instances: Mapping[str, Any],
                  components: Mapping[tuple[str, str], NormalizedResource], deployment_policy: Mapping[str, Any] | None,
                  deployment: Mapping[str, Any], xplan: Mapping[str, Any]) -> dict[str, Any]:
    """Return the per-flow state or ``{code, ...detail}`` for the first failing step."""

    intent = flow.get("deliveryIntent")
    if intent not in INTENT_FIXED:
        return {"code": C.UNSUPPORTED, "reason": "delivery-intent", "deliveryIntent": intent}
    owner = (endpoints.get(flow.get("sourceEndpointId")) or {}).get("ownerId")
    instance = instances.get(owner)
    component = None
    if instance is not None:
        ref = instance.get("componentRef") or {}
        component = components.get((ref.get("namespace"), ref.get("name")))
    payload = _resource_flow_policy(component) or deployment_policy
    if payload is None:
        return {"code": C.POLICY_MISSING}
    reliability, ordering = payload.get("reliability"), payload.get("ordering")
    claimed = claims(reliability, ordering)
    if isinstance(claimed, str):
        return {"code": C.UNSUPPORTED, "xcomOutcome": claimed, "reliability": reliability, "ordering": ordering}
    for member, value in INTENT_FIXED[intent].items():
        if payload.get(member) != value:
            return {"code": C.POLICY_CONFLICT, "member": member, "intent": intent, "payload": payload.get(member)}
    if payload.get("overflow") != "reject" or payload.get("retry") != 0 or payload.get("deadlineMs") != 0:
        return {"code": C.UNSUPPORTED, "xcomOutcome": "unsupported_policy"}
    policy = FlowPolicy(ordering, reliability, int(payload.get("queueDepth")), "reject", 0, 0)
    provider = _select_provider(flow, claimed, deployment, xplan)
    if "code" in provider:
        return provider
    if claimed[0] not in LOOPBACK.delivery_mask:
        return {"code": C.UNSUPPORTED, "xcomOutcome": "unsupported_delivery", "claim": claimed[0]}
    if claimed[1] not in LOOPBACK.ordering_mask:
        return {"code": C.UNSUPPORTED, "xcomOutcome": "unsupported_ordering", "claim": claimed[1]}
    return {"flow": flow, "policy": policy, "claims": claimed, "provider": provider["id"]}


def _select_provider(flow: Mapping[str, Any], claimed: tuple[str, str], deployment: Mapping[str, Any], xplan: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``{id}`` of the single qualifying provider or ``{code, ...}`` (data model, F8/N9)."""

    providers = {p.get("providerId"): p for p in xplan.get("providers") or ()}
    candidates = set(providers)
    network = flow.get("networkId")
    if network:
        bindings = [b for b in deployment.get("networkBindings") or () if (b.get("logicalNetworkRef") or {}).get("element") == network]
        if bindings:
            profile_refs = [b.get("profileRef") for b in bindings]
            targets = {t.get("id"): t for t in deployment.get("targets") or ()}
            candidates = {b.get("id") for b in bindings} | {
                tid for tid, target in targets.items() if any(ref in (target.get("profileRefs") or ()) for ref in profile_refs)
            }
            candidates &= set(providers)
    needed = {TOKENS[claimed[0]], TOKENS[claimed[1]]}
    qualifying = sorted(pid for pid in candidates if needed <= set(providers[pid].get("capabilities") or ()))
    if len(qualifying) != 1:
        return {"code": C.PROVIDER, "candidates": sorted(candidates), "qualifying": qualifying}
    return {"id": qualifying[0]}


def _step_9(flow: Mapping[str, Any], quality: Mapping[str, Any], domains: set[str],
            mappings: Mapping[tuple[str, str], Mapping[str, Any]]) -> dict[str, Any]:
    """Return sender/receiver/mapping/bounds or ``{code, ...}``."""

    sender = flow.get("timeDomainId")
    receiver = quality.get("receiverTimeDomainId", sender)
    if sender not in domains or receiver not in domains:
        return {"code": C.CLOCK_UNKNOWN, "sender": sender, "receiver": receiver}
    if sender == receiver:
        mapping = TimeMapping(sender, receiver, 0, 0)
    else:
        declared = mappings.get((sender, receiver))
        if declared is None:
            return {"code": C.MAPPING_MISSING, "sender": sender, "receiver": receiver}
        tolerance = declared.get("tolerance") or {}
        try:
            tolerance_ns = parse_quantity_ns({"value": tolerance.get("value"), "unit": tolerance.get("unit")}, code=C.MAPPING_UNSUPPORTED)
            if "ticks" in tolerance and tolerance["ticks"] != tolerance_ns:  # 1 tick = 1 ns (finding 3)
                raise C.FlowError(C.MAPPING_UNSUPPORTED, "normalized tolerance ticks disagree")
            mapping = TimeMapping(sender, receiver, parse_mapping(declared.get("mapping")), tolerance_ns)
        except C.FlowError as error:
            return {"code": error.code, "sender": sender, "receiver": receiver}
    bounds = {}
    for member in ("freshness", "deadline"):
        if member in quality:
            try:
                bounds[member] = parse_quantity_ns(quality[member], code=C.QUALITY_INVALID)
            except C.FlowError as error:
                return {"code": error.code, "member": member}
        else:
            bounds[member] = 0
    return {"sender": sender, "receiver": receiver, "mapping": mapping, "freshness": bounds["freshness"], "deadline": bounds["deadline"]}

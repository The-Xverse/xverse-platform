"""Closed-set reference resolution and XDL semantic validation."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from .diagnostics import escape_pointer_token, make_diagnostic, pointer_from_path, sorted_diagnostics
from .loader import ParsedDocument
from .models import (
    Diagnostic, ElementIdentity, ResourceIdentity, ResolvedReference, SourceLocation,
    StaticReadiness, ValidationGate,
)
from .schema import API_VERSION, ProfileSchemaCatalog

REALIZATION_KEYS = frozenset((
    "targets", "targetClass", "artifactIds", "externalAssetRef", "secretRefs", "runtime",
    "host", "address", "credentials",
))


@dataclass(frozen=True)
class ElementRecord:
    """Indexed authored element with owning collection and source pointer."""

    collection: str
    value: dict[str, Any]
    pointer: str


@dataclass(frozen=True)
class ResourceRecord:
    """Parsed resource paired with logical identity and indexed elements."""

    document: ParsedDocument
    identity: ResourceIdentity
    elements: dict[str, ElementRecord]


@dataclass(frozen=True)
class SemanticGraph:
    """Closed validated graph with resolved references, profiles, and readiness."""

    records: tuple[ResourceRecord, ...]
    references: dict[ResourceIdentity, tuple[ResolvedReference, ...]]
    profiles: dict[str, ResourceIdentity]
    readiness: dict[str, StaticReadiness]


EXTENSION_COLLECTIONS = {
    "Component": ("interfaces", "endpoints", "parameters"),
    "System": (
        "nodes", "componentInstances", "devices", "interfaces", "endpoints", "flows",
        "networks", "parameters",
    ),
    "Deployment": ("targets", "bindings"),
    "Scenario": ("steps", "faults"),
    "Profile": (),
}


def iter_extension_containers(record: ResourceRecord) -> Iterator[tuple[dict[str, Any], str]]:
    """Yield only extension maps declared by the kind schemas."""

    resource = record.document.data
    if "extensions" in resource:
        yield resource["extensions"], "/extensions"
    spec = resource["spec"]
    for collection in EXTENSION_COLLECTIONS[record.identity.kind]:
        for index, item in enumerate(spec.get(collection, [])):
            if "extensions" in item:
                yield item["extensions"], f"/spec/{collection}/{index}/extensions"


def _iter_authored_references(record: ResourceRecord) -> Iterator[tuple[dict[str, Any], str]]:
    """Yield only ResourceRef/ElementRef positions declared by the kind schemas."""

    spec = record.document.data["spec"]
    kind = record.identity.kind
    if kind == "System":
        for index, item in enumerate(spec.get("componentInstances", [])):
            yield item["componentRef"], f"/spec/componentInstances/{index}/componentRef"
    elif kind == "Deployment":
        yield spec["systemRef"], "/spec/systemRef"
        for index, target in enumerate(spec.get("targets", [])):
            for ref_index, reference in enumerate(target.get("profileRefs", [])):
                yield reference, f"/spec/targets/{index}/profileRefs/{ref_index}"
        for index, binding in enumerate(spec.get("bindings", [])):
            yield binding["logicalRef"], f"/spec/bindings/{index}/logicalRef"
        for index, binding in enumerate(spec.get("networkBindings", [])):
            yield binding["logicalNetworkRef"], f"/spec/networkBindings/{index}/logicalNetworkRef"
            yield binding["profileRef"], f"/spec/networkBindings/{index}/profileRef"
        for index, mapping in enumerate(spec.get("timeMappings", [])):
            yield mapping["sourceTimeDomainRef"], f"/spec/timeMappings/{index}/sourceTimeDomainRef"
            yield mapping["targetTimeDomainRef"], f"/spec/timeMappings/{index}/targetTimeDomainRef"
    elif kind == "Scenario":
        yield spec["systemRef"], "/spec/systemRef"
        if "deploymentRef" in spec:
            yield spec["deploymentRef"], "/spec/deploymentRef"
        for collection in ("steps", "faults", "observers"):
            for index, item in enumerate(spec.get(collection, [])):
                yield item["targetRef"], f"/spec/{collection}/{index}/targetRef"


def _walk_typed_structure(value: Any, pointer: str = "") -> Iterator[tuple[Any, str]]:
    """Walk typed XDL structure while treating open payload objects as opaque."""

    yield value, pointer
    if isinstance(value, Mapping):
        opaque = {"extensions", "parameterValues", "quality", "limits", "action", "initialConditions"}
        for key, child in value.items():
            if key in opaque:
                continue
            yield from _walk_typed_structure(child, f"{pointer}/{escape_pointer_token(key)}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_typed_structure(child, f"{pointer}/{index}")


def _diag(
    record: ResourceRecord,
    code: str,
    gate: ValidationGate,
    pointer: str,
    message: str,
    correction: str,
    *,
    related: tuple[str, ...] = (),
) -> Diagnostic:
    """Create a source-anchored diagnostic for a semantic resource record."""

    return make_diagnostic(
        code, gate, message, correction, pointer=pointer, resource=record.identity,
        location=record.document.source_map.get(pointer, SourceLocation(record.document.source_name)),
        related=related,
    )


def _build_records(documents: tuple[ParsedDocument, ...]) -> tuple[tuple[ResourceRecord, ...], tuple[Diagnostic, ...]]:
    """Index resources and globally unique element IDs, reporting collisions."""

    records: list[ResourceRecord] = []
    identities: dict[ResourceIdentity, ResourceRecord] = {}
    diagnostics: list[Diagnostic] = []
    for document in documents:
        identity = ResourceIdentity.from_mapping(document.data)
        elements: dict[str, ElementRecord] = {}
        provisional = ResourceRecord(document, identity, elements)
        if identity in identities:
            diagnostics.append(_diag(
                provisional, "XDL-REFERENCE-DUPLICATE-RESOURCE", ValidationGate.REFERENCE, "",
                f"resource identity {identity.uri} is supplied more than once",
                "Supply exactly one revision of each resource identity.", related=(identity.uri,),
            ))
        else:
            identities[identity] = provisional
        spec = document.data.get("spec", {})
        if isinstance(spec, dict):
            for collection, values in spec.items():
                if not isinstance(values, list):
                    continue
                for index, value in enumerate(values):
                    if not isinstance(value, dict) or not isinstance(value.get("id"), str):
                        continue
                    element_id = value["id"]
                    pointer = f"/spec/{escape_pointer_token(collection)}/{index}/id"
                    if element_id in elements:
                        previous = elements[element_id]
                        diagnostics.append(_diag(
                            provisional, "XDL-REFERENCE-DUPLICATE-ELEMENT", ValidationGate.REFERENCE,
                            pointer, f"element ID {element_id!r} also appears in {previous.collection}",
                            "Use an element ID that is unique across the complete resource.",
                            related=(f"{identity.uri}#{element_id}",),
                        ))
                    else:
                        elements[element_id] = ElementRecord(collection, value, pointer.rsplit("/", 1)[0])
        records.append(provisional)
    return tuple(sorted(records, key=lambda item: item.identity)), sorted_diagnostics(diagnostics)


def _resolve_references(
    records: tuple[ResourceRecord, ...],
) -> tuple[dict[ResourceIdentity, tuple[ResolvedReference, ...]], tuple[Diagnostic, ...]]:
    """Resolve only schema-declared references against the supplied closed set."""

    catalog = {record.identity: record for record in records}
    result: dict[ResourceIdentity, tuple[ResolvedReference, ...]] = {}
    diagnostics: list[Diagnostic] = []
    for record in records:
        resolved: list[ResolvedReference] = []
        for value, pointer in _iter_authored_references(record):
            target_identity = ResourceIdentity(
                str(value["apiVersion"]), str(value["kind"]), str(value["namespace"]), str(value["name"]),
            )
            target = catalog.get(target_identity)
            if target is None:
                diagnostics.append(_diag(
                    record, "XDL-REFERENCE-UNRESOLVED-RESOURCE", ValidationGate.REFERENCE, pointer,
                    f"resource reference {target_identity.uri} is not in the supplied set",
                    "Supply the exact referenced resource in this validation run.",
                    related=(target_identity.uri,),
                ))
                continue
            element_identity = None
            collection = None
            if "element" in value:
                element_id = str(value["element"])
                element = target.elements.get(element_id)
                if element is None:
                    diagnostics.append(_diag(
                        record, "XDL-REFERENCE-UNRESOLVED-ELEMENT", ValidationGate.REFERENCE,
                        f"{pointer}/element", f"element {target_identity.uri}#{element_id} does not exist",
                        "Correct the element ID or supply the resource revision that owns it.",
                        related=(f"{target_identity.uri}#{element_id}",),
                    ))
                    continue
                element_identity = ElementIdentity(target_identity, element_id)
                collection = element.collection
            resolved.append(ResolvedReference(pointer, target_identity, element_identity, collection))
        result[record.identity] = tuple(sorted(resolved, key=lambda item: item.pointer))
    return result, sorted_diagnostics(diagnostics)


def _ids(spec: dict[str, Any], collection: str) -> set[str]:
    """Return string IDs declared by a named specification collection."""

    return {item["id"] for item in spec.get(collection, []) if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _reference_identity(value: Mapping[str, Any]) -> ResourceIdentity:
    """Convert a resource-reference mapping to logical identity."""

    return ResourceIdentity(
        str(value.get("apiVersion", "")), str(value.get("kind", "")),
        str(value.get("namespace", "")), str(value.get("name", "")),
    )


def _check_member(
    diagnostics: list[Diagnostic], record: ResourceRecord, value: str | None, allowed: set[str],
    pointer: str, label: str,
) -> None:
    """Append a stable diagnostic when a referenced member is absent."""

    if value is not None and value not in allowed:
        diagnostics.append(_diag(
            record, f"XDL-SEMANTIC-{label.upper().replace(' ', '-')}", ValidationGate.SEMANTIC,
            pointer, f"{label} {value!r} does not resolve", f"Reference a declared {label} ID.",
        ))


def _validate_component(record: ResourceRecord, diagnostics: list[Diagnostic]) -> None:
    """Validate Component endpoint ownership and interface direction rules."""

    spec = record.document.data["spec"]
    interfaces = {item["id"]: item for item in spec.get("interfaces", [])}
    for index, endpoint in enumerate(spec.get("endpoints", [])):
        base = f"/spec/endpoints/{index}"
        _check_member(diagnostics, record, endpoint.get("interfaceId"), set(interfaces), f"{base}/interfaceId", "interface")
        if endpoint.get("ownerId") != record.identity.name:
            diagnostics.append(_diag(
                record, "XDL-SEMANTIC-ENDPOINT-OWNER", ValidationGate.SEMANTIC, f"{base}/ownerId",
                "Component endpoint owner must equal the Component resource name",
                f"Use ownerId {record.identity.name!r}.",
            ))
        interface = interfaces.get(endpoint.get("interfaceId"))
        if interface and interface["direction"] != "bidirectional" and endpoint["direction"] != interface["direction"]:
            diagnostics.append(_diag(
                record, "XDL-SEMANTIC-ENDPOINT-DIRECTION", ValidationGate.SEMANTIC, f"{base}/direction",
                "endpoint direction is incompatible with its Interface",
                "Match the Interface direction or declare the Interface bidirectional.",
            ))


def _validate_system(record: ResourceRecord, diagnostics: list[Diagnostic]) -> None:
    """Validate System membership, ownership, flow, and network relationships."""

    spec = record.document.data["spec"]
    collections = {name: _ids(spec, name) for name in (
        "nodes", "componentInstances", "devices", "sensors", "actuators", "interfaces",
        "endpoints", "networks", "timeDomains",
    )}
    endpoints = {item["id"]: item for item in spec.get("endpoints", [])}
    interfaces = {item["id"]: item for item in spec.get("interfaces", [])}
    owners = collections["nodes"] | collections["componentInstances"] | collections["devices"]
    for value, pointer in _walk_typed_structure(spec, "/spec"):
        if isinstance(value, dict) and REALIZATION_KEYS.intersection(value):
            diagnostics.append(_diag(
                record, "XDL-SEMANTIC-REALIZATION-LEAKAGE", ValidationGate.SEMANTIC, pointer,
                f"logical System contains realization fields {sorted(REALIZATION_KEYS.intersection(value))}",
                "Move realization data to a Deployment resource.",
            ))
    for index, instance in enumerate(spec.get("componentInstances", [])):
        if instance["componentRef"]["kind"] != "Component":
            diagnostics.append(_diag(
                record, "XDL-SEMANTIC-COMPONENT-REFERENCE", ValidationGate.SEMANTIC,
                f"/spec/componentInstances/{index}/componentRef/kind",
                "componentInstance componentRef must reference a Component",
                "Use kind Component and supply that exact Component resource.",
            ))
        _check_member(diagnostics, record, instance.get("nodeId"), collections["nodes"],
                      f"/spec/componentInstances/{index}/nodeId", "node")
    for index, device in enumerate(spec.get("devices", [])):
        _check_member(diagnostics, record, device.get("nodeId"), collections["nodes"],
                      f"/spec/devices/{index}/nodeId", "node")
    for index, endpoint in enumerate(spec.get("endpoints", [])):
        base = f"/spec/endpoints/{index}"
        _check_member(diagnostics, record, endpoint.get("ownerId"), owners, f"{base}/ownerId", "endpoint owner")
        _check_member(diagnostics, record, endpoint.get("interfaceId"), collections["interfaces"],
                      f"{base}/interfaceId", "interface")
        interface = interfaces.get(endpoint.get("interfaceId"))
        if interface and interface["direction"] != "bidirectional" and endpoint["direction"] != interface["direction"]:
            diagnostics.append(_diag(
                record, "XDL-SEMANTIC-ENDPOINT-DIRECTION", ValidationGate.SEMANTIC, f"{base}/direction",
                "endpoint direction is incompatible with its Interface",
                "Match the Interface direction or declare the Interface bidirectional.",
            ))
    for index, sensor in enumerate(spec.get("sensors", [])):
        base = f"/spec/sensors/{index}"
        _check_member(diagnostics, record, sensor.get("deviceId"), collections["devices"], f"{base}/deviceId", "device")
        _check_member(diagnostics, record, sensor.get("outputEndpointId"), collections["endpoints"],
                      f"{base}/outputEndpointId", "endpoint")
    for index, actuator in enumerate(spec.get("actuators", [])):
        base = f"/spec/actuators/{index}"
        _check_member(diagnostics, record, actuator.get("deviceId"), collections["devices"], f"{base}/deviceId", "device")
        _check_member(diagnostics, record, actuator.get("inputEndpointId"), collections["endpoints"],
                      f"{base}/inputEndpointId", "endpoint")
    for index, flow in enumerate(spec.get("flows", [])):
        base = f"/spec/flows/{index}"
        source = endpoints.get(flow.get("sourceEndpointId"))
        destinations = [endpoints.get(item) for item in flow.get("destinationEndpointIds", [])]
        if source is None:
            _check_member(diagnostics, record, flow.get("sourceEndpointId"), collections["endpoints"],
                          f"{base}/sourceEndpointId", "endpoint")
        elif source.get("direction") not in {"output", "bidirectional"}:
            diagnostics.append(_diag(record, "XDL-SEMANTIC-FLOW-DIRECTION", ValidationGate.SEMANTIC,
                                     f"{base}/sourceEndpointId", "flow source is not output-capable",
                                     "Use an output or bidirectional endpoint."))
        for destination_index, destination_id in enumerate(flow.get("destinationEndpointIds", [])):
            destination = destinations[destination_index]
            if destination is None:
                _check_member(diagnostics, record, destination_id, collections["endpoints"],
                              f"{base}/destinationEndpointIds/{destination_index}", "endpoint")
            elif destination.get("direction") not in {"input", "bidirectional"}:
                diagnostics.append(_diag(record, "XDL-SEMANTIC-FLOW-DIRECTION", ValidationGate.SEMANTIC,
                                         f"{base}/destinationEndpointIds/{destination_index}",
                                         "flow destination is not input-capable",
                                         "Use an input or bidirectional endpoint."))
        interface_id = flow.get("interfaceId")
        _check_member(diagnostics, record, interface_id, collections["interfaces"], f"{base}/interfaceId", "interface")
        attached = ([source] if source else []) + [item for item in destinations if item]
        if any(item.get("interfaceId") != interface_id for item in attached):
            diagnostics.append(_diag(record, "XDL-SEMANTIC-FLOW-INTERFACE", ValidationGate.SEMANTIC,
                                     f"{base}/interfaceId", "flow and endpoint interfaces differ",
                                     "Use one compatible interface for the flow and all attached endpoints."))
        if "networkId" in flow:
            _check_member(diagnostics, record, flow["networkId"], collections["networks"],
                          f"{base}/networkId", "network")
        if "timeDomainId" in flow:
            _check_member(diagnostics, record, flow["timeDomainId"], collections["timeDomains"],
                          f"{base}/timeDomainId", "time domain")
    for index, link in enumerate(spec.get("links", [])):
        base = f"/spec/links/{index}"
        _check_member(diagnostics, record, link.get("networkId"), collections["networks"], f"{base}/networkId", "network")
        for participant_index, endpoint_id in enumerate(link.get("participantEndpointIds", [])):
            _check_member(diagnostics, record, endpoint_id, collections["endpoints"],
                          f"{base}/participantEndpointIds/{participant_index}", "endpoint")
    for index, model in enumerate(spec.get("models", [])):
        for port in ("inputs", "outputs"):
            for port_index, interface_id in enumerate(model.get(port, [])):
                _check_member(diagnostics, record, interface_id, collections["interfaces"],
                              f"/spec/models/{index}/{port}/{port_index}", "interface")
    if "defaultTimeDomainId" in spec:
        _check_member(diagnostics, record, spec["defaultTimeDomainId"], collections["timeDomains"],
                      "/spec/defaultTimeDomainId", "time domain")


def _validate_deployment(
    record: ResourceRecord, catalog: dict[ResourceIdentity, ResourceRecord], diagnostics: list[Diagnostic],
    readiness: dict[str, StaticReadiness],
) -> None:
    """Validate Deployment system, target, binding, artifact, and time mappings."""

    spec = record.document.data["spec"]
    system_ref = spec["systemRef"]
    system_identity = ResourceIdentity(system_ref["apiVersion"], system_ref["kind"], system_ref["namespace"], system_ref["name"])
    system = catalog.get(system_identity)
    if system_identity.kind != "System":
        diagnostics.append(_diag(record, "XDL-SEMANTIC-DEPLOYMENT-SYSTEM", ValidationGate.SEMANTIC,
                                 "/spec/systemRef/kind", "Deployment systemRef must reference a System",
                                 "Use kind System."))
    target_ids = _ids(spec, "targets")
    artifact_by_id = {item["id"]: item for item in spec.get("artifacts", [])}
    resource_ids = _ids(spec, "resources")
    targets = {item["id"]: item for item in spec.get("targets", [])}
    for index, target in enumerate(spec.get("targets", [])):
        for resource_index, resource_id in enumerate(target.get("offeredResourceIds", [])):
            _check_member(diagnostics, record, resource_id, resource_ids,
                          f"/spec/targets/{index}/offeredResourceIds/{resource_index}", "resource")
        for profile_index, profile_ref in enumerate(target.get("profileRefs", [])):
            if profile_ref["kind"] != "Profile":
                diagnostics.append(_diag(
                    record, "XDL-SEMANTIC-PROFILE-REFERENCE", ValidationGate.SEMANTIC,
                    f"/spec/targets/{index}/profileRefs/{profile_index}/kind",
                    "target profileRefs entries must reference Profile resources",
                    "Use kind Profile and supply that exact Profile resource.",
                ))
    binding_error = False
    for index, binding in enumerate(spec.get("bindings", [])):
        base = f"/spec/bindings/{index}"
        logical = binding["logicalRef"]
        logical_identity = ResourceIdentity(logical["apiVersion"], logical["kind"], logical["namespace"], logical["name"])
        if logical_identity != system_identity:
            diagnostics.append(_diag(record, "XDL-SEMANTIC-BINDING-SYSTEM", ValidationGate.SEMANTIC,
                                     f"{base}/logicalRef", "binding logicalRef is outside the selected System",
                                     "Reference an element owned by systemRef."))
            binding_error = True
        before = len(diagnostics)
        _check_member(diagnostics, record, binding.get("targetId"), target_ids, f"{base}/targetId", "target")
        for item_index, artifact_id in enumerate(binding.get("artifactIds", [])):
            _check_member(diagnostics, record, artifact_id, set(artifact_by_id),
                          f"{base}/artifactIds/{item_index}", "artifact")
            artifact = artifact_by_id.get(artifact_id)
            if artifact is not None and not artifact.get("digest"):
                diagnostics.append(_diag(record, "XDL-BINDING-ARTIFACT-INTEGRITY", ValidationGate.BINDING,
                                         f"/spec/artifacts/{list(artifact_by_id).index(artifact_id)}/digest",
                                         f"artifact {artifact_id!r} has no immutable digest",
                                         "Supply a pinned digest before declaring static readiness."))
                binding_error = True
        for item_index, resource_id in enumerate(binding.get("resourceIds", [])):
            _check_member(diagnostics, record, resource_id, resource_ids,
                          f"{base}/resourceIds/{item_index}", "resource")
        target = targets.get(binding.get("targetId"))
        if binding.get("realizationClass") == "physical" and target is not None and not target.get("externalAssetRef"):
            diagnostics.append(_diag(record, "XDL-SEMANTIC-PHYSICAL-ASSET", ValidationGate.SEMANTIC,
                                     f"{base}/targetId", "physical binding target lacks externalAssetRef",
                                     "Provide an indirect external asset reference on the target."))
            binding_error = True
        binding_error = binding_error or len(diagnostics) > before
    if system:
        time_domains = _ids(system.document.data["spec"], "timeDomains")
        for index, simulator in enumerate(spec.get("simulators", [])):
            _check_member(diagnostics, record, simulator.get("artifactId"), set(artifact_by_id),
                          f"/spec/simulators/{index}/artifactId", "artifact")
            _check_member(diagnostics, record, simulator.get("timeDomainId"), time_domains,
                          f"/spec/simulators/{index}/timeDomainId", "time domain")
        for index, network_binding in enumerate(spec.get("networkBindings", [])):
            logical_ref = network_binding["logicalNetworkRef"]
            logical_identity = _reference_identity(logical_ref)
            logical_element = system.elements.get(str(logical_ref.get("element", "")))
            if logical_identity != system_identity or logical_element is None or logical_element.collection != "networks":
                diagnostics.append(_diag(
                    record, "XDL-SEMANTIC-NETWORK-REFERENCE", ValidationGate.SEMANTIC,
                    f"/spec/networkBindings/{index}/logicalNetworkRef",
                    "logicalNetworkRef must select a network in the Deployment's System",
                    "Reference an element in systemRef's networks collection.",
                ))
            if network_binding["profileRef"]["kind"] != "Profile":
                diagnostics.append(_diag(
                    record, "XDL-SEMANTIC-PROFILE-REFERENCE", ValidationGate.SEMANTIC,
                    f"/spec/networkBindings/{index}/profileRef/kind",
                    "network profileRef must reference a Profile",
                    "Use kind Profile and supply that exact Profile resource.",
                ))
        for index, time_mapping in enumerate(spec.get("timeMappings", [])):
            for field in ("sourceTimeDomainRef", "targetTimeDomainRef"):
                time_ref = time_mapping[field]
                time_identity = _reference_identity(time_ref)
                time_element = system.elements.get(str(time_ref.get("element", "")))
                if time_identity != system_identity or time_element is None or time_element.collection != "timeDomains":
                    diagnostics.append(_diag(
                        record, "XDL-SEMANTIC-TIME-DOMAIN-REFERENCE", ValidationGate.SEMANTIC,
                        f"/spec/timeMappings/{index}/{field}",
                        f"{field} must select a time domain in the Deployment's System",
                        "Reference an element in systemRef's timeDomains collection.",
                    ))
    readiness[record.identity.uri] = StaticReadiness.NOT_READY if binding_error else StaticReadiness.READY


def _validate_scenario(
    record: ResourceRecord, catalog: dict[ResourceIdentity, ResourceRecord], diagnostics: list[Diagnostic],
) -> None:
    """Validate Scenario selection, target, observer, and time-domain consistency."""

    spec = record.document.data["spec"]
    system_ref = spec["systemRef"]
    system_identity = ResourceIdentity(system_ref["apiVersion"], system_ref["kind"], system_ref["namespace"], system_ref["name"])
    system = catalog.get(system_identity)
    if system_identity.kind != "System":
        diagnostics.append(_diag(record, "XDL-SEMANTIC-SCENARIO-SYSTEM", ValidationGate.SEMANTIC,
                                 "/spec/systemRef/kind", "Scenario systemRef must reference a System",
                                 "Use kind System."))
        return
    deployment_identity = None
    if "deploymentRef" in spec:
        deployment_ref = spec["deploymentRef"]
        deployment_identity = ResourceIdentity(
            deployment_ref["apiVersion"], deployment_ref["kind"], deployment_ref["namespace"], deployment_ref["name"]
        )
    if deployment_identity is not None and deployment_identity.kind != "Deployment":
        diagnostics.append(_diag(record, "XDL-SEMANTIC-SCENARIO-DEPLOYMENT", ValidationGate.SEMANTIC,
                                 "/spec/deploymentRef/kind", "Scenario deploymentRef must reference a Deployment",
                                 "Use kind Deployment."))
    elif deployment_identity is not None:
        deployment = catalog.get(deployment_identity)
        if deployment is not None:
            selected_system = _reference_identity(deployment.document.data["spec"]["systemRef"])
            if selected_system != system_identity:
                diagnostics.append(_diag(
                    record, "XDL-SEMANTIC-SCENARIO-DEPLOYMENT-SYSTEM", ValidationGate.SEMANTIC,
                    "/spec/deploymentRef", "Scenario deploymentRef realizes a different System",
                    "Select a Deployment whose systemRef exactly matches the Scenario systemRef.",
                ))
    time_domains = _ids(system.document.data["spec"], "timeDomains") if system else set()
    selected_targets = {system_identity}
    if deployment_identity is not None:
        selected_targets.add(deployment_identity)
    for collection in ("steps", "observers"):
        for index, item in enumerate(spec.get(collection, [])):
            _check_member(diagnostics, record, item.get("timeDomainId"), time_domains,
                          f"/spec/{collection}/{index}/timeDomainId", "time domain")
            target = item.get("targetRef", {})
            target_identity = ResourceIdentity(
                str(target.get("apiVersion", "")), str(target.get("kind", "")),
                str(target.get("namespace", "")), str(target.get("name", "")),
            )
            if target_identity not in selected_targets:
                diagnostics.append(_diag(
                    record, "XDL-SEMANTIC-SCENARIO-TARGET", ValidationGate.SEMANTIC,
                    f"/spec/{collection}/{index}/targetRef",
                    "Scenario target is outside the selected System/Deployment graph",
                    "Target an element owned by systemRef or deploymentRef.",
                ))
    for index, fault in enumerate(spec.get("faults", [])):
        target = fault.get("targetRef", {})
        target_identity = ResourceIdentity(
            str(target.get("apiVersion", "")), str(target.get("kind", "")),
            str(target.get("namespace", "")), str(target.get("name", "")),
        )
        if target_identity not in selected_targets:
            diagnostics.append(_diag(
                record, "XDL-SEMANTIC-SCENARIO-TARGET", ValidationGate.SEMANTIC,
                f"/spec/faults/{index}/targetRef",
                "Scenario fault target is outside the selected System/Deployment graph",
                "Target an element owned by systemRef or deploymentRef.",
            ))
    used_time_domains = {
        item["timeDomainId"] for collection in ("steps", "observers")
        for item in spec.get(collection, []) if "timeDomainId" in item
    }
    mapped_pairs: set[frozenset[str]] = set()
    for index, mapping in enumerate(spec.get("timeMappings", [])):
        source = mapping["sourceTimeDomainId"]
        target = mapping["targetTimeDomainId"]
        _check_member(diagnostics, record, source, time_domains,
                      f"/spec/timeMappings/{index}/sourceTimeDomainId", "time domain")
        _check_member(diagnostics, record, target, time_domains,
                      f"/spec/timeMappings/{index}/targetTimeDomainId", "time domain")
        if source != target:
            mapped_pairs.add(frozenset((source, target)))
    missing_pairs = [
        (source, target) for source, target in combinations(sorted(used_time_domains), 2)
        if frozenset((source, target)) not in mapped_pairs
    ]
    for source, target in missing_pairs:
        diagnostics.append(_diag(
            record, "XDL-SEMANTIC-TIME-MAPPING", ValidationGate.SEMANTIC,
            "/spec/timeMappings", f"Scenario has no mapping between {source!r} and {target!r}",
            "Declare a mapping and tolerance for every pair of used time domains.",
            related=(source, target),
        ))
    observers = _ids(spec, "observers")
    for index, metric in enumerate(spec.get("metrics", [])):
        for observer_index, observer_id in enumerate(metric.get("observerIds", [])):
            _check_member(diagnostics, record, observer_id, observers,
                          f"/spec/metrics/{index}/observerIds/{observer_index}", "observer")


def _validate_profiles(
    records: tuple[ResourceRecord, ...], profile_schemas: ProfileSchemaCatalog,
    diagnostics: list[Diagnostic],
) -> dict[str, ResourceIdentity]:
    """Validate profile ownership and extension payloads against local schemas."""

    profiles: dict[str, ResourceIdentity] = {}
    profile_records: dict[str, ResourceRecord] = {}
    for record in records:
        if record.identity.kind != "Profile":
            continue
        namespace = record.document.data["spec"]["extensionNamespace"]
        if namespace in profiles:
            diagnostics.append(_diag(
                record, "XDL-SEMANTIC-DUPLICATE-PROFILE-NAMESPACE", ValidationGate.SEMANTIC,
                "/spec/extensionNamespace", f"extension namespace {namespace!r} has multiple owners",
                "Supply exactly one Profile resource for each extension namespace.",
            ))
        else:
            profiles[namespace] = record.identity
            profile_records[namespace] = record
    for record in records:
        for extensions, pointer in iter_extension_containers(record):
            for namespace, payload in extensions.items():
                extension_pointer = f"{pointer}/{escape_pointer_token(namespace)}"
                profile_record = profile_records.get(namespace)
                if profile_record is None:
                    diagnostics.append(_diag(
                        record, "XDL-SEMANTIC-PROFILE-MISSING", ValidationGate.SEMANTIC,
                        extension_pointer, f"extension namespace {namespace!r} has no supplied Profile",
                        "Supply exactly one compatible Profile resource.",
                    ))
                    continue
                profile_spec = profile_record.document.data["spec"]
                if API_VERSION not in profile_spec["compatibleApiVersions"]:
                    diagnostics.append(_diag(
                        record, "XDL-SEMANTIC-PROFILE-INCOMPATIBLE", ValidationGate.SEMANTIC,
                        extension_pointer, f"Profile {profile_record.identity.uri} is incompatible with {API_VERSION}",
                        "Use a Profile revision that lists the resource API version.",
                    ))
                    continue
                schema_id = profile_spec["schemaRef"]
                if schema_id not in profile_schemas.schemas:
                    diagnostics.append(_diag(
                        record, "XDL-SEMANTIC-PROFILE-SCHEMA-MISSING", ValidationGate.SEMANTIC,
                        extension_pointer, f"Profile schema {schema_id!r} was not supplied locally",
                        "Pass the exact local Profile schema explicitly.",
                    ))
                    continue
                try:
                    schema_errors = profile_schemas.validate(schema_id, payload)
                except Exception as error:  # authored schemas must fail closed, never crash validation
                    diagnostics.append(_diag(
                        record, "XDL-SEMANTIC-PROFILE-SCHEMA-RESOLUTION", ValidationGate.SEMANTIC,
                        extension_pointer, str(error),
                        "Supply every Profile schema dependency in the explicit local schema set.",
                    ))
                    continue
                for error in schema_errors:
                    error_pointer = extension_pointer + pointer_from_path(error.absolute_path)
                    diagnostics.append(_diag(
                        record, "XDL-SEMANTIC-EXTENSION-SCHEMA", ValidationGate.SEMANTIC,
                        error_pointer, error.message,
                        "Correct the extension payload to match its declared Profile schema.",
                    ))
    return profiles


def validate_semantics(
    documents: tuple[ParsedDocument, ...], profile_schemas: ProfileSchemaCatalog,
) -> tuple[SemanticGraph | None, tuple[Diagnostic, ...]]:
    """Build and validate a closed semantic graph.

    @param documents Schema-valid parsed XDL documents.
    @param profile_schemas Explicit offline schemas for extension payloads.
    @return A graph plus sorted diagnostics, or ``None`` when semantic errors block normalization.
    """

    records, diagnostics = _build_records(documents)
    if diagnostics:
        return None, diagnostics
    references, ref_diagnostics = _resolve_references(records)
    if ref_diagnostics:
        return None, ref_diagnostics
    catalog = {record.identity: record for record in records}
    found: list[Diagnostic] = []
    readiness: dict[str, StaticReadiness] = {}
    profiles = _validate_profiles(records, profile_schemas, found)
    for record in records:
        kind = record.identity.kind
        if kind == "Component":
            _validate_component(record, found)
        elif kind == "System":
            _validate_system(record, found)
        elif kind == "Deployment":
            _validate_deployment(record, catalog, found, readiness)
        elif kind == "Scenario":
            _validate_scenario(record, catalog, found)
    semantic_errors = tuple(item for item in found if item.gate in {ValidationGate.SEMANTIC, ValidationGate.REFERENCE})
    if semantic_errors:
        return None, sorted_diagnostics(found)
    return SemanticGraph(records, references, profiles, readiness), sorted_diagnostics(found)

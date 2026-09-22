"""Deterministic catalog derivation and side-effect-free M3 lifecycle planning."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import Any

from .diagnostics import make_diagnostic, sorted_diagnostics
from .models import (
    Diagnostic, FrozenMap, NormalizedResource, ResourceIdentity, Severity, ValidationGate, freeze,
)

RUNTIME_PROFILE_NAMESPACE = "io.xverse.runtime.compatibility"
_PHASE_ORDER = ("prepare", "start", "observe", "stop", "cleanup")
_SENSITIVE_ARGUMENT = re.compile(
    r"(?i)(?:^--?(?:password|passwd|secret|token|api[-_]?key)(?:$|[:=])|"
    r"(?:password|passwd|secret|token|api[-_]?key)\s*[:=])"
)
_SENSITIVE_ENVIRONMENT = re.compile(r"(?i)(?:password|passwd|secret|token|credential|api_?key)")


@dataclass(frozen=True)
class ProcessAction:
    """Fully resolved, shell-free process invocation selected by an XDL binding."""

    executable: str
    arguments: tuple[str, ...]
    working_directory: str
    environment_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Enforce absolute paths, unique names, and credential-free arguments."""

        if not PurePath(self.executable).is_absolute():
            raise ValueError("process executable must be absolute")
        if not PurePath(self.working_directory).is_absolute():
            raise ValueError("process working directory must be absolute")
        if len(set(self.environment_names)) != len(self.environment_names):
            raise ValueError("process environment names must be unique")
        if any(_SENSITIVE_ENVIRONMENT.search(name) for name in self.environment_names):
            raise ValueError("M3 process actions must not request secret-like environment names")
        if any(_SENSITIVE_ARGUMENT.search(argument) for argument in self.arguments):
            raise ValueError("process arguments must not contain credential-like assignments")


@dataclass(frozen=True)
class PlanAction:
    """One ordered lifecycle phase in a deterministic execution plan."""

    action_id: str
    phase: str
    operation: str
    timeout_seconds: float
    condition: str | None = None


@dataclass(frozen=True)
class CatalogEntry:
    """Derived compatibility selection anchored to exact XDL revisions and artifacts."""

    identity: str
    deployment: ResourceIdentity
    deployment_revision: str
    binding_id: str
    system: ResourceIdentity
    system_revision: str
    component_instance: str
    component: ResourceIdentity
    component_revision: str
    profile: ResourceIdentity
    profile_revision: str
    environment_identity: str
    provider_id: str
    provider_kind: str
    realization_class: str
    target_id: str
    target_class: str
    external_asset_ref: str | None
    artifact_digests: tuple[str, ...]
    interface_ids: tuple[str, ...]
    time_domain_ids: tuple[str, ...]
    scenario_revisions: FrozenMap
    lifecycle: FrozenMap
    profile_payload: FrozenMap
    provenance: FrozenMap
    planning_blockers: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogBuildResult:
    """Deterministically ordered catalog entries and derivation diagnostics."""

    entries: tuple[CatalogEntry, ...]
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Return whether catalog derivation produced no error diagnostic."""

        return not any(item.severity is Severity.ERROR for item in self.diagnostics)


@dataclass(frozen=True)
class LifecyclePlan:
    """Inspectable, side-effect-free lifecycle plan requiring a separate permit."""

    catalog_identity: str
    environment_identity: str
    provider_id: str
    provider_kind: str
    selection: FrozenMap
    resource_revisions: FrozenMap
    artifact_digests: tuple[str, ...]
    actions: tuple[PlanAction, ...]
    process_action: ProcessAction | None
    blockers: tuple[str, ...]
    digest: str
    requires_execution_permit: bool = field(default=True, compare=True)

    @property
    def is_plannable(self) -> bool:
        """Return whether no declared planning blocker prevents authorization."""

        return not self.blockers

    @property
    def execution_eligible(self) -> bool:
        """Remain false because a plan alone never authorizes execution."""

        return False


def _identity(value: Mapping[str, Any]) -> ResourceIdentity:
    """Extract a resource identity from a reference-like mapping."""

    return ResourceIdentity(
        str(value.get("apiVersion", "")), str(value.get("kind", "")),
        str(value.get("namespace", "")), str(value.get("name", "")),
    )


def _diagnostic(
    code: str, resource: NormalizedResource, pointer: str, message: str, correction: str,
) -> Diagnostic:
    """Create a policy diagnostic anchored to a normalized resource."""

    return make_diagnostic(
        code, ValidationGate.POLICY, message, correction, pointer=pointer, resource=resource.identity,
    )


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Return *value* as a mapping or an empty mapping for malformed data."""

    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> Sequence[Any]:
    """Return a non-text sequence or an empty tuple for malformed data."""

    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else ()


def derive_catalog(resources: Sequence[NormalizedResource]) -> CatalogBuildResult:
    """Derive compatibility entries from an explicit normalized XDL resource set."""

    ordered = tuple(sorted(resources, key=lambda item: item.identity))
    resource_index = {item.identity: item for item in ordered}
    runtime_profiles = tuple(
        item for item in ordered
        if item.identity.kind == "Profile"
        and item.content.get("extensionNamespace") == RUNTIME_PROFILE_NAMESPACE
    )
    diagnostics: list[Diagnostic] = []
    entries: list[CatalogEntry] = []
    has_runtime_payload = False
    runtime_payload_anchor: NormalizedResource | None = None

    for resource in ordered:
        extension = resource.extensions.get(RUNTIME_PROFILE_NAMESPACE)
        if not extension:
            continue
        has_runtime_payload = True
        runtime_payload_anchor = runtime_payload_anchor or resource
        for occurrence in _as_sequence(_as_mapping(extension).get("payloads")):
            pointer = str(_as_mapping(occurrence).get("pointer", ""))
            if not pointer.startswith("/spec/bindings/"):
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-PROFILE-PLACEMENT", resource, pointer,
                    "runtime compatibility payload is outside a Deployment binding",
                    "Attach io.xverse.runtime.compatibility only to a Deployment binding.",
                ))

    if len(runtime_profiles) != 1:
        if has_runtime_payload:
            assert runtime_payload_anchor is not None
            anchor = runtime_payload_anchor
            diagnostics.append(_diagnostic(
                "XVERSE-CATALOG-PROFILE-OWNER", anchor, "/spec/bindings",
                f"expected one runtime compatibility Profile, found {len(runtime_profiles)}",
                "Supply exactly one compatible Profile owning io.xverse.runtime.compatibility.",
            ))
        return CatalogBuildResult((), sorted_diagnostics(diagnostics))
    runtime_profile = runtime_profiles[0]

    for deployment in (item for item in ordered if item.identity.kind == "Deployment"):
        content = deployment.content
        system_identity = _identity(_as_mapping(content.get("systemRef")))
        system = resource_index.get(system_identity)
        bindings = _as_sequence(content.get("bindings"))
        artifacts = {
            str(_as_mapping(item).get("id")): _as_mapping(item)
            for item in _as_sequence(content.get("artifacts"))
        }
        targets = {
            str(_as_mapping(item).get("id")): _as_mapping(item)
            for item in _as_sequence(content.get("targets"))
        }
        for binding_index, raw_binding in enumerate(bindings):
            binding = _as_mapping(raw_binding)
            extensions = _as_mapping(binding.get("extensions"))
            raw_payload = extensions.get(RUNTIME_PROFILE_NAMESPACE)
            if raw_payload is None:
                continue
            base = f"/spec/bindings/{binding_index}"
            payload = _as_mapping(raw_payload)
            binding_id = str(binding.get("id", ""))
            logical_ref = _as_mapping(binding.get("logicalRef"))
            logical_identity = _identity(logical_ref)
            instance_id = str(logical_ref.get("element", ""))
            instance: Mapping[str, Any] = {}
            if system is not None:
                instance = _as_mapping(_as_mapping(system.elements.get("componentInstances", {})).get(instance_id))
            component_identity = _identity(_as_mapping(instance.get("componentRef")))
            component = resource_index.get(component_identity)
            local_errors = False
            for condition, code, pointer, message, correction in (
                (system is None or logical_identity != system_identity, "XVERSE-CATALOG-SYSTEM", f"{base}/logicalRef", "binding does not resolve to its Deployment System", "Use the exact Deployment systemRef and supplied System."),
                (not instance, "XVERSE-CATALOG-INSTANCE", f"{base}/logicalRef/element", "binding does not resolve to a System componentInstance", "Reference an exact componentInstances element."),
                (component is None, "XVERSE-CATALOG-COMPONENT", f"{base}/logicalRef", "componentInstance does not resolve to a supplied Component", "Supply the exact referenced Component."),
            ):
                if condition:
                    diagnostics.append(_diagnostic(code, deployment, pointer, message, correction))
                    local_errors = True
            actions = tuple(_as_mapping(item) for item in _as_sequence(payload.get("actions")))
            phases = tuple(str(item.get("phase", "")) for item in actions)
            operations = tuple(str(item.get("operation", "")) for item in actions)
            action_ids = tuple(str(item.get("id", "")) for item in actions)
            if len(set(action_ids)) != len(action_ids):
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-LIFECYCLE-ACTION-ID", deployment,
                    f"{base}/extensions/{RUNTIME_PROFILE_NAMESPACE}/actions",
                    "runtime lifecycle action IDs are not unique",
                    "Assign a unique stable ID to every lifecycle action.",
                ))
                local_errors = True
            if tuple(sorted(phases, key=lambda item: _PHASE_ORDER.index(item) if item in _PHASE_ORDER else 99)) != _PHASE_ORDER or set(phases) != set(_PHASE_ORDER):
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-LIFECYCLE-PHASES", deployment, f"{base}/extensions/{RUNTIME_PROFILE_NAMESPACE}/actions",
                    "runtime lifecycle must declare each required phase exactly once",
                    "Declare prepare, start, observe, stop, and cleanup once each.",
                ))
                local_errors = True
            process = _as_mapping(payload.get("process"))
            sensitive_arguments = tuple(
                str(item) for item in _as_sequence(process.get("arguments"))
                if _SENSITIVE_ARGUMENT.search(str(item))
            )
            if sensitive_arguments:
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-SENSITIVE-ARGUMENT", deployment,
                    f"{base}/extensions/{RUNTIME_PROFILE_NAMESPACE}/process/arguments",
                    "process arguments contain a credential-like assignment",
                    "Remove credential values and keep secret-dependent execution blocked outside M3.",
                ))
                local_errors = True
            if any(phase != operation and not (phase == "prepare" and operation == "validate") for phase, operation in zip(phases, operations)):
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-LIFECYCLE-OPERATION", deployment, f"{base}/extensions/{RUNTIME_PROFILE_NAMESPACE}/actions",
                    "runtime lifecycle operation does not match its phase",
                    "Use validate for prepare and the phase name for all other operations.",
                ))
                local_errors = True
            observe = next((item for item in actions if item.get("phase") == "observe"), {})
            if not str(observe.get("condition", "")).strip():
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-READINESS", deployment,
                    f"{base}/extensions/{RUNTIME_PROFILE_NAMESPACE}/actions",
                    "observe action has no explicit readiness condition",
                    "Declare an observable condition; a delay alone cannot establish readiness.",
                ))
                local_errors = True
            digest_values: list[str] = []
            for artifact_id in _as_sequence(binding.get("artifactIds")):
                artifact = artifacts.get(str(artifact_id), {})
                digest = str(artifact.get("digest", ""))
                if not digest:
                    diagnostics.append(_diagnostic(
                        "XVERSE-CATALOG-ARTIFACT-PIN", deployment, f"{base}/artifactIds",
                        f"artifact {artifact_id!r} lacks an immutable digest",
                        "Select only an explicitly supplied digest-pinned artifact.",
                    ))
                    local_errors = True
                else:
                    digest_values.append(digest)
            if not digest_values:
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-ARTIFACT-PIN", deployment, f"{base}/artifactIds",
                    "compatibility binding has no immutable artifact identity",
                    "Reference at least one explicitly supplied digest-pinned artifact.",
                ))
                local_errors = True
            target = targets.get(str(binding.get("targetId", "")), {})
            realization_class = str(binding.get("realizationClass", ""))
            external_asset_ref = str(target.get("externalAssetRef", "")).strip() or None
            ownership = str(_as_mapping(binding.get("lifecycle")).get("ownership", "")).strip()
            if realization_class in {"physical", "hybrid"} and (not external_asset_ref or not ownership):
                diagnostics.append(_diagnostic(
                    "XVERSE-CATALOG-EXTERNAL-ASSET", deployment, base,
                    f"{realization_class} binding lacks an external asset or ownership boundary",
                    "Declare externalAssetRef on the target and ownership on the binding lifecycle.",
                ))
                local_errors = True
            if local_errors:
                continue
            assert system is not None and component is not None
            declared_blockers = tuple(
                str(item) for item in _as_sequence(payload.get("planningBlockers"))
            )
            secret_blockers = ("XVERSE-PLAN-SECRET-DEPENDENCY",) if binding.get("secretRefs") else ()
            blockers = tuple(sorted(set(declared_blockers + secret_blockers)))
            evidence = _as_mapping(payload.get("evidence"))
            lifecycle = {
                "actions": actions,
                "core": binding.get("lifecycle", FrozenMap()),
                "evidence": evidence,
            }
            provider = _as_mapping(payload.get("provider"))
            scenarios = {
                item.identity.uri: item.revision for item in ordered
                if item.identity.kind == "Scenario"
                and _identity(_as_mapping(item.content.get("systemRef"))) == system.identity
                and (
                    "deploymentRef" not in item.content
                    or _identity(_as_mapping(item.content.get("deploymentRef"))) == deployment.identity
                )
            }
            entries.append(CatalogEntry(
                identity=f"{deployment.identity.uri}#binding/{binding_id}",
                deployment=deployment.identity,
                deployment_revision=deployment.revision,
                binding_id=binding_id,
                system=system.identity,
                system_revision=system.revision,
                component_instance=f"{system.identity.uri}#{instance_id}",
                component=component.identity,
                component_revision=component.revision,
                profile=runtime_profile.identity,
                profile_revision=runtime_profile.revision,
                environment_identity=str(payload.get("environmentId", "")),
                provider_id=str(provider.get("id", "")),
                provider_kind=str(provider.get("kind", "")),
                realization_class=realization_class,
                target_id=str(binding.get("targetId", "")),
                target_class=str(target.get("targetClass", "")),
                external_asset_ref=external_asset_ref,
                artifact_digests=tuple(sorted(digest_values)),
                interface_ids=tuple(sorted(str(item.get("id")) for item in _as_sequence(component.content.get("interfaces")) if isinstance(item, Mapping))),
                time_domain_ids=tuple(sorted(
                    str(item.get("id")) for item in _as_sequence(system.content.get("timeDomains"))
                    if isinstance(item, Mapping)
                )),
                scenario_revisions=freeze(scenarios),
                lifecycle=freeze(lifecycle),
                profile_payload=freeze(payload),
                provenance=deployment.provenance,
                planning_blockers=blockers,
            ))
    entries.sort(key=lambda item: item.identity)
    return CatalogBuildResult(tuple(entries), sorted_diagnostics(diagnostics))


def build_lifecycle_plan(entry: CatalogEntry) -> LifecyclePlan:
    """Resolve a deterministic inspectable plan without consulting or consuming a permit."""

    payload = entry.profile_payload
    action_values = tuple(_as_mapping(item) for item in _as_sequence(payload.get("actions")))
    action_values = tuple(sorted(action_values, key=lambda item: _PHASE_ORDER.index(str(item["phase"]))))
    actions = tuple(PlanAction(
        action_id=str(item["id"]), phase=str(item["phase"]), operation=str(item["operation"]),
        timeout_seconds=float(item["timeoutSeconds"]),
        condition=str(item["condition"]) if "condition" in item else None,
    ) for item in action_values)
    process_action = None
    if entry.provider_kind == "process":
        process = _as_mapping(payload.get("process"))
        process_action = ProcessAction(
            executable=str(process["executable"]),
            arguments=tuple(str(item) for item in _as_sequence(process.get("arguments"))),
            working_directory=str(process["workingDirectory"]),
            environment_names=tuple(sorted(str(item) for item in _as_sequence(process.get("environmentNames")))),
        )
    digest_input = {
        "catalogIdentity": entry.identity,
        "environmentIdentity": entry.environment_identity,
        "provider": {"id": entry.provider_id, "kind": entry.provider_kind},
        "selection": {
            "deployment": entry.deployment.uri,
            "bindingId": entry.binding_id,
            "system": entry.system.uri,
            "componentInstance": entry.component_instance,
            "component": entry.component.uri,
            "profile": entry.profile.uri,
            "targetId": entry.target_id,
            "targetClass": entry.target_class,
            "realizationClass": entry.realization_class,
            "externalAssetRef": entry.external_asset_ref,
            "interfaceIds": list(entry.interface_ids),
            "timeDomainIds": list(entry.time_domain_ids),
            "scenarios": dict(entry.scenario_revisions),
        },
        "resourceRevisions": {
            entry.deployment.uri: entry.deployment_revision,
            entry.system.uri: entry.system_revision,
            entry.component.uri: entry.component_revision,
            entry.profile.uri: entry.profile_revision,
        },
        "actions": [
            {"id": item.action_id, "phase": item.phase, "operation": item.operation,
             "timeoutSeconds": item.timeout_seconds, "condition": item.condition}
            for item in actions
        ],
        "process": None if process_action is None else {
            "executable": process_action.executable,
            "arguments": list(process_action.arguments),
            "workingDirectory": process_action.working_directory,
            "environmentNames": list(process_action.environment_names),
            "inheritedHandles": "closed",
            "implicitShell": False,
        },
        "artifactDigests": list(entry.artifact_digests),
        "blockers": list(entry.planning_blockers),
    }
    encoded = json.dumps(digest_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return LifecyclePlan(
        catalog_identity=entry.identity,
        environment_identity=entry.environment_identity,
        provider_id=entry.provider_id,
        provider_kind=entry.provider_kind,
        selection=freeze(digest_input["selection"]),
        resource_revisions=freeze({
            entry.deployment.uri: entry.deployment_revision,
            entry.system.uri: entry.system_revision,
            entry.component.uri: entry.component_revision,
            entry.profile.uri: entry.profile_revision,
        }),
        artifact_digests=entry.artifact_digests,
        actions=actions,
        process_action=process_action,
        blockers=entry.planning_blockers,
        digest=f"sha256:{hashlib.sha256(encoded).hexdigest()}",
    )


def catalog_entry_public_data(entry: CatalogEntry) -> dict[str, Any]:
    """Return a deterministic public-safe projection with explicit evidence classes."""

    maturity = str(entry.provenance.get("maturity", "unknown"))
    limitations = tuple(str(item) for item in _as_sequence(entry.provenance.get("limitations")))
    return {
        "identity": entry.identity,
        "observedFacts": {
            "artifacts": list(entry.artifact_digests),
            "resourceRevisions": {
                entry.component.uri: entry.component_revision,
                entry.deployment.uri: entry.deployment_revision,
                entry.profile.uri: entry.profile_revision,
                entry.system.uri: entry.system_revision,
            },
        },
        "operatorDeclarations": {
            "environmentIdentity": entry.environment_identity,
            "providerId": entry.provider_id,
            "realizationClass": entry.realization_class,
        },
        "architecturalTargets": list(limitations) if maturity == "architectural-target" else [],
        "unknowns": list(entry.planning_blockers),
        "withheld": ["externalAssetRef"] if entry.external_asset_ref else [],
        "maturity": maturity,
        "limitations": list(limitations),
    }

"""Admission of binding inputs (detailed design §3; contract rules 1 and 3).

``check_inputs`` matches the experiment plan's provenance exactly against the normalized input
resources and compares each digest as ``sha256(bytes.fromhex(resource_semantic_digest(r)))``.
``to_graph_entry`` converts a normalized resource into the graph-entry shape ``compile_plan``
accepts, and ``check_xcom_provenance`` verifies the compiled ``xcom_plan`` provenance against those
entries (a drift guard on ``xcom_plan._canonical_resource``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from typing import Any

from xverse_xdl.experiment_plan import resource_semantic_digest
from xverse_xdl.models import NormalizedResource
from xverse_xdl.xcom_plan import canonical_plan_bytes

from .codes import INPUT_MISMATCH, refusal

COMPILE_KINDS = ("System", "Deployment", "Scenario", "Component")


def thaw(value: Any) -> Any:
    """Return a plain ``dict``/``list`` copy of a frozen structure."""

    if isinstance(value, Mapping):
        return {str(key): thaw(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw(item) for item in value]
    return value


def _key(api_version: str, kind: str, namespace: str, name: str, version: str) -> tuple[str, ...]:
    """Return the identity-and-version key."""

    return (api_version, kind, namespace, name, version)


def key_text(key: Sequence[str]) -> str:
    """Return ``apiVersion/kind/namespace/name@version``."""

    return f"{key[0]}/{key[1]}/{key[2]}/{key[3]}@{key[4]}"


def resource_key(resource: NormalizedResource) -> tuple[str, ...]:
    """Return the key of a normalized resource."""

    identity = resource.identity
    return _key(identity.api_version, identity.kind, identity.namespace, identity.name, resource.revision)


def check_inputs(plan: Mapping[str, Any], resources: Sequence[NormalizedResource]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Match plan provenance and inputs exactly and compare digests.

    @return ``(inputDigests, refusals)``; any refusal is a single ``INPUT-MISMATCH``.
    """

    provenance: dict[tuple[str, ...], str] = {}
    duplicates: list[str] = []
    for entry in (plan.get("provenance") or {}).get("resources") or ():
        key = _key(entry.get("apiVersion"), entry.get("kind"), entry.get("namespace"), entry.get("name"), entry.get("version"))
        if key in provenance:
            duplicates.append(key_text(key))
        provenance[key] = str((entry.get("semanticDigest") or {}).get("value"))
    inputs: dict[tuple[str, ...], NormalizedResource] = {}
    for resource in resources:
        key = resource_key(resource)
        if key in inputs:
            duplicates.append(key_text(key))
        inputs[key] = resource
    missing = sorted(key_text(key) for key in provenance.keys() - inputs.keys())
    extra = sorted(key_text(key) for key in inputs.keys() - provenance.keys())
    digests: dict[str, str] = {}
    mismatched: list[str] = []
    for key, resource in inputs.items():
        value = hashlib.sha256(bytes.fromhex(resource_semantic_digest(resource))).hexdigest()
        digests[key_text(key)] = value
        if key in provenance and provenance[key] != value:
            mismatched.append(key_text(key))
    if duplicates or missing or extra or mismatched:
        return digests, [refusal(INPUT_MISMATCH, None, duplicates=sorted(duplicates), missing=missing, extra=extra, mismatched=sorted(mismatched))]
    return digests, []


def to_graph_entry(resource: NormalizedResource) -> dict[str, Any]:
    """Return the ``compile_plan`` graph entry of ``resource``."""

    identity = resource.identity
    entry: dict[str, Any] = {
        "identity": {"apiVersion": identity.api_version, "kind": identity.kind, "namespace": identity.namespace, "name": identity.name},
        "revision": resource.revision,
        "content": thaw(resource.content),
    }
    extensions = thaw(resource.extensions)
    if extensions:
        entry["extensions"] = extensions
    return entry


def _sorted_payloads(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``entry`` with each extension namespace's payloads sorted by pointer."""

    value = dict(entry)
    extensions = value.get("extensions")
    if isinstance(extensions, Mapping):
        normalized: dict[str, Any] = {}
        for namespace, item in extensions.items():
            if isinstance(item, Mapping) and isinstance(item.get("payloads"), (list, tuple)):
                item = dict(item, payloads=sorted(item["payloads"], key=lambda p: str(p.get("pointer")) if isinstance(p, Mapping) else ""))
            normalized[str(namespace)] = item
        value["extensions"] = normalized
    return value


def check_xcom_provenance(xplan: Mapping[str, Any], entries: Sequence[Mapping[str, Any]]) -> tuple[str | None, list[dict[str, Any]]]:
    """Verify the compiled plan's provenance against the converted entries.

    @return ``(graphDigest value, refusals)``.
    """

    by_key = {
        (e["identity"]["apiVersion"], e["identity"]["kind"], e["identity"]["namespace"], e["identity"]["name"], e["revision"]): e
        for e in entries
    }
    provenance = xplan.get("provenance") or {}
    problems: list[str] = []
    for record in provenance.get("resources") or ():
        key = (record.get("apiVersion"), record.get("kind"), record.get("namespace"), record.get("name"), record.get("version"))
        entry = by_key.get(key)
        if entry is None:
            problems.append(f"unknown {key_text(key)}")
            continue
        expected = hashlib.sha256(canonical_plan_bytes(_sorted_payloads(entry))).hexdigest()
        if (record.get("sourceDigest") or {}).get("value") != expected:
            problems.append(f"digest {key_text(key)}")
    graph = (provenance.get("graphDigest") or {}).get("value")
    if problems:
        return graph, [refusal(INPUT_MISMATCH, None, xcomProvenance=sorted(problems))]
    return graph, []

"""XDL1-SR-018-U: metamorphic equivalence unit cases (encodings, order, volatile data)."""

from __future__ import annotations

import dataclasses
import json

from xverse_xdl import experiment_plan as ep
from xverse_xdl.experiment_plan import compile_experiment_sources
from xverse_xdl.loader import SourceInput, load_sources
from xverse_xdl.models import freeze

from tests.thesis_lite.xdl import support as S


def _codes(result):
    return [item.code for item in result.diagnostics]


def _permuted_payload_resource(resource):
    """Return the same normalized resource with its payload attachment order reversed."""

    groups: dict[str, object] = {}
    for namespace, entry in resource.extensions.items():
        groups[str(namespace)] = {
            "profile": entry.get("profile"),
            "payloads": tuple(reversed(tuple(entry.get("payloads")))),
        }
    return dataclasses.replace(resource, extensions=freeze(groups))


def test_yaml_and_json_equal_plan_bytes_and_digest():
    documents, diagnostics = load_sources(S.yaml_sources())
    assert not diagnostics
    json_sources = tuple(
        SourceInput(path.name.replace(".xdl.yaml", ".xdl.json"), json.dumps(document.data).encode("utf-8"))
        for path, document in zip(S.FIXTURE_PATHS, documents)
    )
    yaml_result = compile_experiment_sources(S.yaml_sources(), profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    json_result = compile_experiment_sources(json_sources, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert yaml_result.is_valid and json_result.is_valid, _codes(yaml_result) + _codes(json_result)
    assert ep.canonical_plan_bytes(yaml_result.plan) == ep.canonical_plan_bytes(json_result.plan)
    assert yaml_result.plan["digest"] == json_result.plan["digest"]
    assert (
        yaml_result.plan["provenance"]["inputSemanticDigest"]
        == json_result.plan["provenance"]["inputSemanticDigest"]
    )
    assert dict(yaml_result.run["sourceByteDigests"]) != dict(json_result.run["sourceByteDigests"])


def test_resource_order_permutation_equal_plan_bytes():
    forward = S.compile_declared(S.declared())
    reverse = S.compile_declared(list(reversed(S.declared())))
    assert forward.is_valid and reverse.is_valid
    assert ep.canonical_plan_bytes(forward.plan) == ep.canonical_plan_bytes(reverse.plan)
    assert forward.plan["digest"] == reverse.plan["digest"]


def test_payload_order_permutation_equal_plan_bytes():
    declared = S.declared()
    base = S.compile_declared(declared)
    normalized = [S.normalize(resource) for resource in declared]
    normalized[4] = _permuted_payload_resource(normalized[4])
    permuted = ep.compile_experiment_plan(tuple(normalized))
    assert base.is_valid and permuted.is_valid, _codes(permuted)
    assert ep.canonical_plan_bytes(base.plan) == ep.canonical_plan_bytes(permuted.plan)
    assert base.plan["digest"] == permuted.plan["digest"]


def test_volatile_run_envelope_does_not_change_plan_digest():
    first = S.compile_declared(S.declared(), run_id="run-a", generated_at="2026-10-01T00:00:00Z")
    second = S.compile_declared(S.declared(), run_id="run-b", generated_at="2026-10-02T12:30:00Z")
    assert first.is_valid and second.is_valid
    assert ep.canonical_plan_bytes(first.plan) == ep.canonical_plan_bytes(second.plan)
    assert first.run["planDigest"] == second.run["planDigest"]
    assert first.run["runId"] != second.run["runId"]
    assert first.run["generatedAt"] != second.run["generatedAt"]


def test_resource_revision_change_keeps_unrelated_identity():
    base = S.compile_declared(S.declared())
    deployment = S.deployment_resource()
    deployment["spec"]["artifacts"][0]["digest"] = "sha256:" + "cd" * 32
    changed = S.declared(deployment=deployment)
    extra = S.component_resource()
    extra["metadata"]["name"] = "unrelated-component"
    extra["metadata"]["version"] = "0.2.0"
    changed.append(extra)
    updated = S.compile_declared(changed)
    assert base.is_valid and updated.is_valid, _codes(updated)
    identity_fields = ("apiVersion", "kind", "namespace", "name", "uri", "version")
    for resource in ("system", "deployment", "scenario"):
        base_identity = {key: base.plan["selection"][resource][key] for key in identity_fields}
        changed_identity = {key: updated.plan["selection"][resource][key] for key in identity_fields}
        assert base_identity == changed_identity
    assert base.plan["components"] == updated.plan["components"]
    assert (
        base.plan["bindings"][0]["artifactRefs"][0]["digest"]
        != updated.plan["bindings"][0]["artifactRefs"][0]["digest"]
    )
    assert base.plan["digest"] != updated.plan["digest"]

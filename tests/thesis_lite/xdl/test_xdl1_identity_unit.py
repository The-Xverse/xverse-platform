"""XDL1-SR-011-U / XDL1-SR-014-U / XDL1-SR-018-U canonical identity unit cases."""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json

from xverse_xdl import experiment_plan as ep

from tests.thesis_lite.xdl import support as S


def _codes(result):
    return [item.code for item in result.diagnostics]


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def test_plan_digest_self_consistent():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    plan = result.plan
    first = ep.canonical_plan_bytes(plan)
    assert ep.compute_plan_digest(plan) == plan["digest"]["value"]
    assert ep.canonical_plan_bytes(plan) == first
    assert plan["digest"]["algorithm"] == "sha256"
    assert len(plan["digest"]["value"]) == 64


def test_plan_matches_digest_for_emitted_plan():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    assert ep.plan_matches_digest(result.plan) is True
    assert ep.experiment_plan_status(result.plan) == "resolved"
    assert result.plan["status"] == "resolved"


def test_plan_body_excludes_volatile_fields():
    result = S.compile_declared(
        S.declared(), run_id="run-2026-10-01", generated_at="2026-10-01T00:00:00Z"
    )
    assert result.is_valid, _codes(result)
    keys = set(_walk_keys(result.plan))
    assert not ({"runId", "generatedAt", "sourceByteDigests"} & keys)
    assert result.run["runId"] == "run-2026-10-01"
    assert result.run["generatedAt"] == "2026-10-01T00:00:00Z"
    assert result.run["planDigest"] == result.plan["digest"]["value"]


def test_expected_input_digest_mismatch_rejected():
    uri = "xdl://org.xverse.experiment/scenario/sample-observation-run"
    result = S.compile_declared(
        S.declared(), expected_input_semantic_digests={uri: "0" * 64}
    )
    assert result.plan is None
    assert "XDL1-PLAN-INPUT-MUTATED" in _codes(result)


def test_post_hash_mutation_detected(monkeypatch):
    real = ep.resource_semantic_digest
    seen: dict[str, int] = {}

    def mutated(resource):
        key = resource.identity.uri
        seen[key] = seen.get(key, 0) + 1
        value = real(resource)
        return value if seen[key] == 1 else hashlib.sha256(key.encode("utf-8")).hexdigest()

    monkeypatch.setattr(ep, "resource_semantic_digest", mutated)
    result = S.compile_declared(S.declared())
    assert result.plan is None
    assert "XDL1-PLAN-INPUT-MUTATED" in _codes(result)


def test_digest_selfcheck_failure_rejected(monkeypatch):
    real = ep.canonical_plan_bytes
    calls = {"count": 0}

    def tampered(plan):
        calls["count"] += 1
        value = real(plan)
        return value if calls["count"] == 1 else value + b" "

    monkeypatch.setattr(ep, "canonical_plan_bytes", tampered)
    result = S.compile_declared(S.declared())
    assert result.plan is None
    assert "XDL1-PLAN-DIGEST-SELFCHECK" in _codes(result)


def test_resource_semantic_digest_stable():
    resource = S.normalize(S.system_resource())
    first = ep.resource_semantic_digest(resource)
    second = ep.resource_semantic_digest(resource)
    reordered = S.normalize({
        "spec": S.system_resource()["spec"],
        "kind": S.system_resource()["kind"],
        "apiVersion": S.system_resource()["apiVersion"],
        "metadata": S.system_resource()["metadata"],
    })
    third = ep.resource_semantic_digest(reordered)
    assert first == second == third
    assert len(first) == 64
    assert all(character in "0123456789abcdef" for character in first)


def test_resource_semantic_digest_excludes_source_map():
    declared = S.scenario_resource()
    first = S.normalize(declared)
    second = dataclasses.replace(
        first,
        source_map=S.freeze({"": {"source": "other-name.yaml", "line": 42, "column": 3}}),
    )
    assert ep.resource_semantic_digest(first) == ep.resource_semantic_digest(second)


def test_input_semantic_digest_uses_contributing_set_only():
    base = S.compile_declared(S.declared())
    extra = S.component_resource()
    extra["metadata"]["name"] = "unrelated-component"
    resources = S.declared()
    resources.append(extra)
    extended = S.compile_declared(resources)
    assert base.is_valid and extended.is_valid
    assert (
        base.plan["provenance"]["inputSemanticDigest"]
        == extended.plan["provenance"]["inputSemanticDigest"]
    )
    uris = [item["uri"] for item in extended.plan["provenance"]["resources"]]
    assert "xdl://org.xverse.experiment/component/unrelated-component" not in uris


def test_unrelated_extra_resource_does_not_change_plan():
    base = S.compile_declared(S.declared())
    extra = S.profile_resource()
    extra["metadata"]["name"] = "unrelated-profile"
    extra["spec"] = {
        "extensionNamespace": "io.xverse.other",
        "compatibleApiVersions": [S.API],
        "schemaRef": "https://example.invalid/other/schema.json",
        "documentationRef": "https://example.invalid/other/",
        "conflictPolicy": "reject",
    }
    resources = S.declared()
    resources.append(extra)
    extended = S.compile_declared(resources)
    assert base.is_valid and extended.is_valid
    assert ep.canonical_plan_bytes(base.plan) == ep.canonical_plan_bytes(extended.plan)
    assert base.plan["digest"] == extended.plan["digest"]


def test_provenance_resources_sorted_and_complete():
    result = S.compile_declared(S.declared())
    assert result.is_valid, _codes(result)
    entries = result.plan["provenance"]["resources"]
    keys = [
        (item["apiVersion"], item["kind"], item["namespace"], item["name"], item["version"])
        for item in entries
    ]
    assert keys == sorted(keys)
    assert [item["kind"] for item in entries] == [
        "Component", "Deployment", "Profile", "Scenario", "System",
    ]
    for item in entries:
        assert item["semanticDigest"]["algorithm"] == "sha256"
        assert len(item["semanticDigest"]["value"]) == 64
    assert json.loads(json.dumps(result.plan)) == result.plan

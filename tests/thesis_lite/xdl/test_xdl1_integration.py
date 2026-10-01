"""XDL1-INTEGRATION: real-consumer integration cases over the asset repository.

These cases exercise the accepted loader/schema registry/semantics/normalizer, the additive
compiler and CLI, and the accepted derived catalog, lifecycle-plan and C++ X-COM
activation-plan consumers in one platform checkout. They start no process, open no socket and
retrieve no artifact. Whole-system integration is executed only by the trusted
target-repository measure over the pinned revision.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys

from xverse_xdl import xcom_plan
from xverse_xdl.catalog import build_lifecycle_plan, derive_catalog
from xverse_xdl.experiment_plan import compile_experiment_files
from xverse_xdl.normalize import canonical_json
from xverse_xdl.validate import validate_files
from tests.helpers import EXAMPLE_PATHS, PROFILE_SCHEMA

from tests.thesis_lite.xdl import support as S

RUNTIME_SCHEMA = S.ROOT / "xdl" / "profiles" / "runtime-compatibility-v0.1.schema.json"
RUNTIME_SCHEMA_V2 = S.ROOT / "xdl" / "profiles" / "runtime-compatibility-v0.2.schema.json"
SD0001_PATHS = tuple(sorted((S.ROOT / "xdl" / "candidates" / "sd0001").glob("*.xdl.yaml")))


def _codes(result):
    return [item.code for item in result.diagnostics]


def run_cli(*arguments: str):
    return subprocess.run(
        [sys.executable, "-m", "xverse_xdl", *arguments],
        cwd=S.ROOT, text=True, capture_output=True, check=False,
    )


def _xcom_graph() -> dict:
    api = xcom_plan.API_VERSION
    namespace = "org.xverse.examples"

    def identity(kind: str, name: str) -> dict:
        return {
            "apiVersion": api, "kind": kind, "namespace": namespace, "name": name,
            "uri": f"xdl://{namespace}/{kind.lower()}/{name}",
        }

    component = {
        "identity": identity("Component", "signal-source"),
        "revision": "0.1.0",
        "content": {
            "capabilities": ["produce-samples"],
            "interfaces": [{"id": "sample-stream", "direction": "output", "payloadSchema": "urn:x:1"}],
            "endpoints": [{
                "id": "samples-out", "ownerId": "signal-source",
                "interfaceId": "sample-stream", "direction": "output",
            }],
        },
    }
    system = {
        "identity": identity("System", "sample-loop"),
        "revision": "0.1.0",
        "content": {
            "nodes": [{"id": "producer-node", "roles": ["compute"]}, {"id": "observer-node", "roles": ["compute"]}],
            "componentInstances": [{
                "id": "source-instance",
                "componentRef": {
                    "apiVersion": api, "kind": "Component",
                    "namespace": namespace, "name": "signal-source",
                },
                "nodeId": "producer-node",
            }],
            "interfaces": [{"id": "sample-stream", "direction": "bidirectional", "payloadSchema": "urn:x:1"}],
            "endpoints": [
                {"id": "samples-out", "ownerId": "source-instance", "interfaceId": "sample-stream", "direction": "output"},
                {"id": "samples-in", "ownerId": "observer-node", "interfaceId": "sample-stream", "direction": "input"},
            ],
            "flows": [{
                "id": "sample-flow", "sourceEndpointId": "samples-out",
                "destinationEndpointIds": ["samples-in"], "interfaceId": "sample-stream",
                "deliveryIntent": "ordered",
            }],
        },
    }
    return {"resources": [component, system]}


def test_real_loader_schema_registry_and_compiler_resolve_neutral_experiment():
    validation = validate_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert validation.is_valid, _codes(validation)
    assert len(validation.resources) == len(S.FIXTURE_PATHS)
    result = compile_experiment_files(S.FIXTURE_PATHS, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.is_valid, _codes(result)
    assert result.plan["status"] == "resolved"
    assert result.plan["selection"]["scenario"]["name"] == "sample-observation-run"
    assert result.plan["provenance"]["resources"]


def test_real_cli_experiment_compile_end_to_end_over_fixture_files():
    arguments = (
        "experiment", "compile", "--format", "json",
        "--profile-schema", str(S.PROFILE_SCHEMA_PATH), *(str(path) for path in S.FIXTURE_PATHS),
    )
    completed = run_cli(*arguments)
    assert completed.returncode == 0, completed.stderr
    value = json.loads(completed.stdout)
    assert value["valid"] is True and value["plan"] is not None
    text = run_cli(
        "experiment", "compile",
        "--profile-schema", str(S.PROFILE_SCHEMA_PATH), *(str(path) for path in S.FIXTURE_PATHS),
    )
    assert text.returncode == 0
    assert text.stdout.startswith(f"resolved plan {value['plan']['digest']['value']}")


def test_existing_loader_and_normalizer_compatible_on_accepted_examples():
    result = validate_files(EXAMPLE_PATHS, profile_schema_paths=(PROFILE_SCHEMA,))
    assert result.is_valid, _codes(result)
    assert len(result.resources) == len(EXAMPLE_PATHS)
    first = canonical_json(result.resources)
    second = canonical_json(result.resources)
    assert first == second
    assert not any(code.startswith("XDL1-PLAN-") for code in _codes(result))


def test_existing_catalog_consumer_compatible_on_normalized_resources():
    validation = validate_files(
        SD0001_PATHS, profile_schema_paths=(RUNTIME_SCHEMA, RUNTIME_SCHEMA_V2)
    )
    assert validation.is_valid, _codes(validation)
    catalog = derive_catalog(validation.resources)
    assert catalog.is_valid, _codes(catalog)
    assert len(catalog.entries) == 1
    first = repr(catalog.entries[0])
    second = repr(derive_catalog(validation.resources).entries[0])
    assert first == second


def test_existing_xcom_activation_plan_consumer_compatible():
    plan = xcom_plan.compile_plan(_xcom_graph())
    assert xcom_plan.plan_matches_digest(plan) is True
    assert plan["digest"]["value"] == xcom_plan.compute_digest(plan)
    assert plan["digest"] == xcom_plan.compile_plan(_xcom_graph())["digest"]
    assert plan["generator"] == {"task": xcom_plan.TASK_ID, "version": xcom_plan.GENERATOR_VERSION}


def test_existing_lifecycle_plan_api_compatible_without_execution():
    validation = validate_files(
        SD0001_PATHS, profile_schema_paths=(RUNTIME_SCHEMA, RUNTIME_SCHEMA_V2)
    )
    entry = derive_catalog(validation.resources).entries[0]
    plan = build_lifecycle_plan(entry)
    assert plan.requires_execution_permit is True
    assert plan.actions
    assert plan.blockers
    assert build_lifecycle_plan(entry) == plan


def test_legacy_cli_validate_normalize_and_version_behaviour_preserved():
    version = run_cli("version", "--format", "json")
    assert version.returncode == 0
    assert json.loads(version.stdout)["supportedApiVersions"] == ["xverse.io/xdl/v1alpha1"]
    validate = run_cli(
        "validate", "--format", "json", "--profile-schema", str(PROFILE_SCHEMA),
        *(str(path) for path in EXAMPLE_PATHS),
    )
    assert validate.returncode == 0
    assert json.loads(validate.stdout)["valid"] is True
    forward = run_cli(
        "normalize", "--profile-schema", str(PROFILE_SCHEMA), *(str(path) for path in EXAMPLE_PATHS)
    )
    reverse = run_cli(
        "normalize", "--profile-schema", str(PROFILE_SCHEMA),
        *(str(path) for path in reversed(EXAMPLE_PATHS)),
    )
    assert forward.returncode == 0 and reverse.returncode == 0
    assert forward.stdout == reverse.stdout


def test_rejected_compile_leaves_consumers_and_files_unchanged():
    paths = tuple(path for path in S.FIXTURE_PATHS if path.name != "scenario.xdl.yaml") + (
        S.FIXTURE_DIR / "invalid-scenario.xdl.yaml",
    )
    digests = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    result = compile_experiment_files(paths, profile_schema_paths=S.PROFILE_SCHEMA_REFS)
    assert result.plan is None
    assert result.diagnostics
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths} == digests
    still_valid = validate_files(EXAMPLE_PATHS, profile_schema_paths=(PROFILE_SCHEMA,))
    assert still_valid.is_valid

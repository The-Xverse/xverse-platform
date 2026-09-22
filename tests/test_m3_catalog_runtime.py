from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.helpers import PROFILE_SCHEMA, ROOT, parsed_examples
from xverse_xdl.catalog import (
    RUNTIME_PROFILE_NAMESPACE, build_lifecycle_plan, catalog_entry_public_data, derive_catalog,
)
from xverse_xdl.lifecycle import (
    EvidenceRecord,
    EvidenceWriteError,
    ExecutionPermit,
    FileEvidenceJournal,
    FixtureProvider,
    IsolationAttestation,
    InMemoryEvidenceJournal,
    LifecycleController,
    LifecycleError,
    OwnedResourceHandle,
    ProcessAction,
    ProcessProvider,
)
from xverse_xdl.models import freeze
from xverse_xdl.validate import validate_files, validate_mappings


RUNTIME_SCHEMA = ROOT / "xdl" / "profiles" / "runtime-compatibility-v0.1.schema.json"
RUNTIME_SCHEMA_V02 = ROOT / "xdl" / "profiles" / "runtime-compatibility-v0.2.schema.json"
SD0001_ROOT = ROOT / "xdl" / "candidates" / "sd0001"
SD0001_PATHS = tuple(sorted(SD0001_ROOT.glob("*.xdl.yaml")))
SD0001_BLOCKERS = (
    "XVERSE-PLAN-ARTIFACT-RETENTION-UNAPPROVED",
    "XVERSE-PLAN-ENVIRONMENT-UNPINNED",
    "XVERSE-PLAN-INTERFACE-CONTRACT-UNVERIFIED",
    "XVERSE-PLAN-OWNER-UNASSIGNED",
    "XVERSE-PLAN-READINESS-UNVERIFIED",
    "XVERSE-PLAN-RESOURCE-LIMITS-UNAPPROVED",
    "XVERSE-PLAN-VENDOR-BINARY-DISPOSITION",
)
SD0001_FILE_DIGESTS = {
    "component.xdl.yaml": "fca3fbd7aeda202bbb974d22e3d87b07b373342539203f8cfd68a35cf6657280",
    "deployment.xdl.yaml": "4a9f1f19f3e9fc310d67606fb8fb048c41b62d93fc1d1837513fb5d77e58f626",
    "runtime-profile.xdl.yaml": "11711aae1955f77386ddce58483c088519a9be8405c8f494e0d3d02e7e6c456d",
    "system.xdl.yaml": "970d0562433ccac9359269ef664940d912805c8f7e7b789c5e36edd88ddfffc6",
}


def runtime_profile() -> dict:
    return {
        "apiVersion": "xverse.io/xdl/v1alpha1",
        "kind": "Profile",
        "metadata": {
            "namespace": "io.xverse.runtime",
            "name": "compatibility-runtime",
            "version": "0.1.0",
            "provenance": {
                "source": "xverse-public-test",
                "revision": "m3-fixture-v1",
                "maturity": "prototype",
                "limitations": ["fixture only"],
            },
        },
        "spec": {
            "extensionNamespace": RUNTIME_PROFILE_NAMESPACE,
            "compatibleApiVersions": ["xverse.io/xdl/v1alpha1"],
            "schemaRef": "https://xverse.io/profiles/runtime-compatibility/v0.1/schema.json",
            "documentationRef": "https://xverse.io/docs/profiles/runtime-compatibility/v0.1/",
            "conflictPolicy": "reject",
        },
    }


def runtime_payload(provider: str = "fixture") -> dict:
    payload = {
        "schemaVersion": "0.1.0",
        "environmentId": "isolated-fixture",
        "provider": {"id": f"{provider}-provider", "kind": provider},
        "actions": [
            {"id": "prepare", "phase": "prepare", "operation": "validate", "timeoutSeconds": 1},
            {"id": "start", "phase": "start", "operation": "start", "timeoutSeconds": 2},
            {"id": "observe", "phase": "observe", "operation": "observe", "condition": "running", "timeoutSeconds": 1},
            {"id": "stop", "phase": "stop", "operation": "stop", "timeoutSeconds": 2},
            {"id": "cleanup", "phase": "cleanup", "operation": "cleanup", "timeoutSeconds": 1},
        ],
        "evidence": {"maturity": "prototype", "limitations": ["fixture lifecycle only"]},
    }
    if provider == "process":
        payload["process"] = {
            "executable": sys.executable,
            "arguments": ["-c", "import time; time.sleep(30)"],
            "workingDirectory": "/tmp/xverse-fixture",
            "environmentNames": [],
            "inheritedHandles": "closed",
            "implicitShell": False,
        }
    return payload


def graph(*, provider: str = "fixture", realization: str = "simulated") -> dict[str, dict]:
    resources = parsed_examples()
    resources["RuntimeProfile"] = runtime_profile()
    binding = resources["Deployment"]["spec"]["bindings"][0]
    binding["realizationClass"] = realization
    binding["extensions"] = {RUNTIME_PROFILE_NAMESPACE: runtime_payload(provider)}
    if realization == "physical":
        resources["Deployment"]["spec"]["targets"][0]["externalAssetRef"] = "urn:xverse:fixture:asset"
    return resources


def validate_graph(resources: dict[str, dict]):
    return validate_mappings(
        tuple(resources.values()), profile_schema_paths=(PROFILE_SCHEMA, RUNTIME_SCHEMA)
    )


def catalog_entry(*, provider: str = "fixture"):
    validation = validate_graph(graph(provider=provider))
    if not validation.is_valid:
        raise AssertionError(validation.diagnostics)
    catalog = derive_catalog(validation.resources)
    if not catalog.is_valid:
        raise AssertionError(catalog.diagnostics)
    return catalog.entries[0]


def permit_for(plan, *, permit_id: str = "permit-one", expires_delta: int = 60):
    now = datetime.now(timezone.utc)
    return ExecutionPermit(
        permit_id=permit_id,
        nonce="nonce-one",
        plan_digest=plan.digest,
        catalog_identity=plan.catalog_identity,
        environment_identity=plan.environment_identity,
        permitted_actions=tuple(action.action_id for action in plan.actions),
        approval_evidence_ref="urn:xverse:test:approval",
        issuer_label="local-test-reviewer",
        operation_classes=tuple(sorted({action.operation for action in plan.actions})),
        exclusions=("legacy-execution",),
        public_safety_classification="public-safe",
        not_before=now - timedelta(seconds=10),
        expires_at=now + timedelta(seconds=expires_delta),
    )


class CatalogTests(unittest.TestCase):
    def test_derives_exact_entry_and_deterministic_plan(self):
        validation = validate_graph(graph())
        self.assertTrue(validation.is_valid, validation.diagnostics)
        forward = derive_catalog(validation.resources)
        reverse = derive_catalog(tuple(reversed(validation.resources)))
        self.assertTrue(forward.is_valid, forward.diagnostics)
        self.assertEqual(forward.entries, reverse.entries)
        entry = forward.entries[0]
        self.assertEqual(entry.binding_id, "source-binding")
        self.assertEqual(entry.component.name, "signal-source")
        self.assertEqual(entry.profile.name, "compatibility-runtime")
        self.assertEqual(build_lifecycle_plan(entry), build_lifecycle_plan(entry))
        plan = build_lifecycle_plan(entry)
        self.assertEqual(plan.selection["bindingId"], "source-binding")
        self.assertIn("experiment-time", plan.selection["timeDomainIds"])
        self.assertTrue(plan.is_plannable)
        self.assertEqual(plan.blockers, ())
        projection = catalog_entry_public_data(entry)
        self.assertEqual(
            set(("observedFacts", "operatorDeclarations", "architecturalTargets", "unknowns", "withheld")),
            set(projection).intersection({"observedFacts", "operatorDeclarations", "architecturalTargets", "unknowns", "withheld"}),
        )

    def test_three_realization_classes_are_catalog_valid(self):
        for realization in ("simulated", "virtual", "physical"):
            with self.subTest(realization=realization):
                result = validate_graph(graph(realization=realization))
                self.assertTrue(result.is_valid, result.diagnostics)
                self.assertTrue(derive_catalog(result.resources).is_valid)

    def test_sd0001_candidate_is_exact_deterministic_and_blocked(self):
        self.assertEqual(
            {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in SD0001_PATHS
            },
            SD0001_FILE_DIGESTS,
        )
        validation = validate_files(
            SD0001_PATHS,
            profile_schema_paths=(PROFILE_SCHEMA, RUNTIME_SCHEMA_V02),
        )
        self.assertTrue(validation.is_valid, validation.diagnostics)
        catalog = derive_catalog(validation.resources)
        self.assertTrue(catalog.is_valid, catalog.diagnostics)
        self.assertEqual(len(catalog.entries), 1)
        entry = catalog.entries[0]
        self.assertEqual(
            entry.identity,
            "xdl://io.xverse.compat.legacy/deployment/sd0001-gateway-candidate"
            "#binding/gateway-process-binding",
        )
        self.assertEqual(entry.provider_id, "zenoh-someip-gateway-provider")
        self.assertEqual(entry.provider_kind, "process")
        self.assertEqual(entry.component_revision, "0.1.0")
        self.assertEqual(entry.system_revision, "0.1.0")
        self.assertEqual(entry.deployment_revision, "0.1.0")
        self.assertEqual(entry.profile_revision, "0.2.0")
        self.assertEqual(
            entry.artifact_digests,
            ("sha256:6ce98220d1c4997a20d2b85464e7e1550e8347d68c572bfb63586c150f41f946",),
        )
        self.assertEqual(
            entry.interface_ids,
            ("someip-egress", "someip-ingress", "zenoh-egress", "zenoh-ingress"),
        )
        self.assertEqual(entry.planning_blockers, SD0001_BLOCKERS)
        plan = build_lifecycle_plan(entry)
        self.assertEqual(plan, build_lifecycle_plan(entry))
        self.assertFalse(plan.is_plannable)
        self.assertFalse(plan.execution_eligible)
        self.assertEqual(plan.blockers, SD0001_BLOCKERS)
        self.assertEqual(
            plan.digest,
            "sha256:ccab18b9980cae1be7537cd13be9f3cbd5b2a0e6a3ddae33a3a98a8560a699cf",
        )
        self.assertEqual(catalog_entry_public_data(entry)["unknowns"], list(SD0001_BLOCKERS))

    def test_runtime_v02_rejects_malformed_declared_blocker(self):
        resources = graph()
        resources["RuntimeProfile"]["metadata"]["version"] = "0.2.0"
        resources["RuntimeProfile"]["spec"]["schemaRef"] = (
            "https://xverse.io/profiles/runtime-compatibility/v0.2/schema.json"
        )
        payload = resources["Deployment"]["spec"]["bindings"][0]["extensions"][
            RUNTIME_PROFILE_NAMESPACE
        ]
        payload["schemaVersion"] = "0.2.0"
        payload["planningBlockers"] = ["owner missing"]
        result = validate_mappings(
            tuple(resources.values()), profile_schema_paths=(PROFILE_SCHEMA, RUNTIME_SCHEMA_V02)
        )
        self.assertFalse(result.is_valid)
        self.assertIn("XDL-SEMANTIC-EXTENSION-SCHEMA", {item.code for item in result.diagnostics})

    def test_runtime_payload_outside_binding_is_rejected(self):
        resources = graph()
        payload = resources["Deployment"]["spec"]["bindings"][0].pop("extensions")
        resources["Deployment"]["extensions"] = payload
        result = validate_graph(resources)
        self.assertTrue(result.is_valid, result.diagnostics)
        catalog = derive_catalog(result.resources)
        self.assertIn("XVERSE-CATALOG-PROFILE-PLACEMENT", {d.code for d in catalog.diagnostics})

    def test_secret_dependency_blocks_plan_without_hiding_entry(self):
        resources = graph()
        resources["Deployment"]["spec"]["bindings"][0]["secretRefs"] = ["urn:secret:test"]
        result = validate_graph(resources)
        self.assertTrue(result.is_valid, result.diagnostics)
        entry = derive_catalog(result.resources).entries[0]
        plan = build_lifecycle_plan(entry)
        self.assertIn("XVERSE-PLAN-SECRET-DEPENDENCY", plan.blockers)

    def test_shared_digest_does_not_merge_catalog_identity(self):
        resources = graph()
        second = copy.deepcopy(resources["Deployment"])
        second["metadata"]["name"] = "second-deployment"
        resources["SecondDeployment"] = second
        validation = validate_graph(resources)
        self.assertTrue(validation.is_valid, validation.diagnostics)
        entries = derive_catalog(validation.resources).entries
        self.assertEqual(len(entries), 2)
        self.assertNotEqual(entries[0].identity, entries[1].identity)
        self.assertEqual(entries[0].artifact_digests, entries[1].artifact_digests)

    def test_profile_schema_rejects_relative_command_and_missing_phase(self):
        resources = graph(provider="process")
        payload = resources["Deployment"]["spec"]["bindings"][0]["extensions"][RUNTIME_PROFILE_NAMESPACE]
        payload["process"]["executable"] = "python"
        payload["actions"].pop()
        result = validate_graph(resources)
        self.assertFalse(result.is_valid)
        self.assertIn("XDL-SEMANTIC-EXTENSION-SCHEMA", {d.code for d in result.diagnostics})

    def test_graph_without_runtime_payload_has_empty_valid_catalog(self):
        result = validate_mappings(tuple(parsed_examples().values()), profile_schema_paths=(PROFILE_SCHEMA,))
        self.assertTrue(result.is_valid, result.diagnostics)
        catalog = derive_catalog(result.resources)
        self.assertTrue(catalog.is_valid, catalog.diagnostics)
        self.assertEqual(catalog.entries, ())

    def test_at_least_twelve_malformed_or_unsafe_cases_fail_closed(self):
        def payload(resources):
            return resources["Deployment"]["spec"]["bindings"][0]["extensions"][RUNTIME_PROFILE_NAMESPACE]

        def relative_executable(resources):
            payload(resources)["provider"] = {"id": "process-provider", "kind": "process"}
            payload(resources)["process"] = runtime_payload("process")["process"]
            payload(resources)["process"]["executable"] = "python"

        def relative_cwd(resources):
            payload(resources)["provider"] = {"id": "process-provider", "kind": "process"}
            payload(resources)["process"] = runtime_payload("process")["process"]
            payload(resources)["process"]["workingDirectory"] = "relative"

        def inherited_handles(resources):
            payload(resources)["provider"] = {"id": "process-provider", "kind": "process"}
            payload(resources)["process"] = runtime_payload("process")["process"]
            payload(resources)["process"]["inheritedHandles"] = "open"

        def implicit_shell(resources):
            payload(resources)["provider"] = {"id": "process-provider", "kind": "process"}
            payload(resources)["process"] = runtime_payload("process")["process"]
            payload(resources)["process"]["implicitShell"] = True

        def missing_phase(resources):
            payload(resources)["actions"].pop()

        def duplicate_phase(resources):
            payload(resources)["actions"][-1]["phase"] = "stop"

        def mismatched_operation(resources):
            payload(resources)["actions"][-1]["operation"] = "start"

        def root_placement(resources):
            extensions = resources["Deployment"]["spec"]["bindings"][0].pop("extensions")
            resources["Deployment"]["extensions"] = extensions

        def missing_digest(resources):
            del resources["Deployment"]["spec"]["artifacts"][0]["digest"]

        def missing_component(resources):
            resources["System"]["spec"]["componentInstances"][0]["componentRef"]["name"] = "missing"

        def physical_without_asset(resources):
            resources["Deployment"]["spec"]["bindings"][0]["realizationClass"] = "physical"

        def hybrid_without_asset(resources):
            resources["Deployment"]["spec"]["bindings"][0]["realizationClass"] = "hybrid"

        def secret_dependency(resources):
            resources["Deployment"]["spec"]["bindings"][0]["secretRefs"] = ["urn:secret:test"]

        def sensitive_argument(resources):
            payload(resources)["provider"] = {"id": "process-provider", "kind": "process"}
            payload(resources)["process"] = runtime_payload("process")["process"]
            payload(resources)["process"]["arguments"] = ["--api-key=value"]

        def no_artifact(resources):
            resources["Deployment"]["spec"]["bindings"][0].pop("artifactIds")

        def missing_readiness(resources):
            payload(resources)["actions"][2].pop("condition")

        mutations = (
            relative_executable, relative_cwd, inherited_handles, implicit_shell, missing_phase,
            duplicate_phase, mismatched_operation, root_placement, missing_digest, missing_component,
            physical_without_asset, hybrid_without_asset, secret_dependency, sensitive_argument,
            no_artifact, missing_readiness,
        )
        self.assertGreaterEqual(len(mutations), 12)
        for mutate in mutations:
            with self.subTest(case=mutate.__name__):
                resources = graph()
                mutate(resources)
                validation = validate_graph(resources)
                unsafe = not validation.is_valid
                if validation.resources:
                    catalog = derive_catalog(validation.resources)
                    unsafe = unsafe or not catalog.is_valid
                    if catalog.entries:
                        unsafe = unsafe or bool(build_lifecycle_plan(catalog.entries[0]).blockers)
                self.assertTrue(unsafe, f"{mutate.__name__} was accepted")


class FailingJournal(InMemoryEvidenceJournal):
    def __init__(self, fail_kind: str):
        super().__init__()
        self.fail_kind = fail_kind

    def append(self, record):
        if record.kind == self.fail_kind:
            raise EvidenceWriteError("injected evidence failure")
        super().append(record)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_lifecycle_plan(catalog_entry())

    def test_fixture_start_observe_stop_and_idempotency(self):
        journal = InMemoryEvidenceJournal()
        provider = FixtureProvider()
        controller = LifecycleController(journal)
        permit = permit_for(self.plan)
        first = controller.start(self.plan, permit, provider, execution_id="execution-one")
        second = controller.start(self.plan, permit, provider, execution_id="execution-one")
        self.assertEqual(first.handle, second.handle)
        self.assertEqual(provider.start_count, 1)
        self.assertEqual(controller.observe("execution-one", provider).status, "running")
        stopped = controller.stop("execution-one", provider)
        repeated = controller.stop("execution-one", provider)
        self.assertEqual(stopped.status, "stopped")
        self.assertEqual(repeated.status, "stopped")
        self.assertEqual(provider.stop_count, 1)

    def test_invalid_and_replayed_permits_fail_closed(self):
        journal = InMemoryEvidenceJournal()
        controller = LifecycleController(journal)
        provider = FixtureProvider()
        expired = permit_for(self.plan, expires_delta=-1)
        with self.assertRaisesRegex(LifecycleError, "expired"):
            controller.start(self.plan, expired, provider, execution_id="expired")
        valid = permit_for(self.plan, permit_id="single-use")
        controller.start(self.plan, valid, provider, execution_id="first")
        with self.assertRaisesRegex(LifecycleError, "consumed"):
            controller.start(self.plan, valid, provider, execution_id="second")
        replayed_nonce = permit_for(self.plan, permit_id="different-id")
        with self.assertRaisesRegex(LifecycleError, "consumed"):
            controller.start(self.plan, replayed_nonce, provider, execution_id="third")
        mismatched = ExecutionPermit(
            **{**valid.__dict__, "permit_id": "mismatch", "nonce": "nonce-two", "plan_digest": "sha256:bad"}
        )
        with self.assertRaisesRegex(LifecycleError, "digest mismatch"):
            controller.start(self.plan, mismatched, provider, execution_id="mismatch")
        with self.assertRaisesRegex(ValueError, "non-empty"):
            ExecutionPermit(**{**valid.__dict__, "permit_id": ""})

    def test_provider_kind_is_part_of_exact_runtime_identity(self):
        class WrongKindProvider(FixtureProvider):
            """Fixture with a deliberately mismatched provider kind."""

            provider_kind = "process"

        provider = WrongKindProvider()
        controller = LifecycleController(InMemoryEvidenceJournal())
        with self.assertRaisesRegex(LifecycleError, "provider identity does not match"):
            controller.start(
                self.plan, permit_for(self.plan), provider, execution_id="wrong-provider-kind",
            )
        self.assertEqual(provider.start_count, 0)

    def test_intent_failure_blocks_mutation_and_outcome_failure_safe_stops(self):
        provider = FixtureProvider()
        before = LifecycleController(FailingJournal("intent"))
        with self.assertRaisesRegex(LifecycleError, "EVIDENCE-INTENT"):
            before.start(self.plan, permit_for(self.plan), provider, execution_id="before")
        self.assertEqual(provider.start_count, 0)

        failed_journal = FailingJournal("outcome")
        after = LifecycleController(failed_journal)
        result = after.start(self.plan, permit_for(self.plan, permit_id="after"), provider, execution_id="after")
        self.assertEqual(result.status, "evidence-incomplete")
        self.assertEqual(after.stop("after", provider).status, "evidence-incomplete")
        self.assertEqual(provider.stop_count, 1)
        restarted = LifecycleController(failed_journal)
        with self.assertRaisesRegex(LifecycleError, "incomplete evidence"):
            restarted.start(
                self.plan, permit_for(self.plan, permit_id="new-after-failure"),
                provider, execution_id="blocked-after-restart",
            )

    def test_concurrent_start_creates_one_resource(self):
        journal = InMemoryEvidenceJournal()
        first_controller = LifecycleController(journal)
        second_controller = LifecycleController(journal)
        provider = FixtureProvider(start_barrier=threading.Barrier(2))
        permit = permit_for(self.plan)
        outcomes = []

        def run(controller):
            try:
                outcomes.append(controller.start(self.plan, permit, provider, execution_id="same"))
            except Exception as error:  # expected exclusive-mutation rejection is captured for assertion
                outcomes.append(error)

        first = threading.Thread(target=run, args=(first_controller,))
        second = threading.Thread(target=run, args=(second_controller,))
        first.start()
        provider.wait_until_starting()
        second.start()
        second.join(timeout=1)
        provider.release_start()
        first.join()
        second.join(timeout=1)
        self.assertEqual(provider.start_count, 1)
        self.assertEqual(sum(isinstance(value, LifecycleError) for value in outcomes), 1)

    def test_restart_requires_handle_revalidation(self):
        provider = FixtureProvider()
        journal = InMemoryEvidenceJournal()
        first = LifecycleController(journal)
        started = first.start(self.plan, permit_for(self.plan), provider, execution_id="execution-one")
        restarted = LifecycleController(journal)
        self.assertTrue(restarted.reconcile(self.plan, "execution-one", provider))
        self.assertEqual(restarted.observe("execution-one", provider).status, "running")
        unknown_provider = FixtureProvider()
        self.assertFalse(LifecycleController(journal).reconcile(self.plan, "execution-one", unknown_provider))

    def test_file_journal_is_durable_and_public_projection_redacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.jsonl"
            controller = LifecycleController(FileEvidenceJournal(path))
            provider = FixtureProvider()
            started = controller.start(self.plan, permit_for(self.plan), provider, execution_id="durable")
            loaded = FileEvidenceJournal(path)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            self.assertTrue(loaded.permit_consumed("permit-one"))
            intent = next(item for item in loaded.records if item.kind == "intent")
            self.assertEqual(intent.permit_issuer_label, "local-test-reviewer")
            self.assertIn("start", intent.permit_operation_classes)
            self.assertEqual(intent.permit_public_safety_classification, "public-safe")
            outcome = next(item for item in loaded.records if item.kind == "outcome")
            self.assertEqual(outcome.handle_provider_kind, "fixture")
            loaded.append(EvidenceRecord(
                kind="observation", sequence=len(loaded.records) + 1,
                timestamp=datetime.now(timezone.utc).isoformat(), execution_id="durable",
                action_id="observe", catalog_identity=self.plan.catalog_identity,
                plan_digest=self.plan.digest, permit_id="permit-one", permit_nonce="nonce-one",
                status="running", environment_identity=self.plan.environment_identity,
                resource_revisions=self.plan.resource_revisions,
                artifact_digests=self.plan.artifact_digests,
                selection=self.plan.selection,
                details=freeze({"path": str(path), "host": "10.0.0.1", "note": "safe"}),
            ))
            rendered = json.dumps(loaded.public_records())
            self.assertNotIn(str(path), rendered)
            self.assertNotIn("10.0.0.1", rendered)
            self.assertNotIn("nonce-one", rendered)
            self.assertNotIn(started.handle.opaque_id, rendered)
            self.assertIn("safe", rendered)
            second_view = FileEvidenceJournal(path)
            loaded.append(EvidenceRecord(
                kind="observation", sequence=0, timestamp=datetime.now(timezone.utc).isoformat(),
                execution_id="durable", action_id="observe", catalog_identity=self.plan.catalog_identity,
                plan_digest=self.plan.digest, permit_id=None, permit_nonce=None, status="running",
                environment_identity=self.plan.environment_identity,
                resource_revisions=self.plan.resource_revisions, artifact_digests=self.plan.artifact_digests,
                selection=self.plan.selection,
            ))
            second_view.append(EvidenceRecord(
                kind="observation", sequence=0, timestamp=datetime.now(timezone.utc).isoformat(),
                execution_id="durable", action_id="observe", catalog_identity=self.plan.catalog_identity,
                plan_digest=self.plan.digest, permit_id=None, permit_nonce=None, status="running",
                environment_identity=self.plan.environment_identity,
                resource_revisions=self.plan.resource_revisions, artifact_digests=self.plan.artifact_digests,
                selection=self.plan.selection,
            ))
            self.assertEqual([item.sequence for item in FileEvidenceJournal(path).records], list(range(1, 7)))

    def test_process_action_rejects_secret_environment_and_arguments(self):
        with self.assertRaisesRegex(ValueError, "secret-like environment"):
            ProcessAction("/bin/true", (), "/tmp", ("API_KEY",))
        with self.assertRaisesRegex(ValueError, "credential-like"):
            ProcessAction("/bin/true", ("--password", "value"), "/tmp", ())

    def test_process_provider_enforces_execution_root_and_closes_owned_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            provider = ProcessProvider(
                root, allowed_executables=(sys.executable,), explicit_environment={},
                isolation_attestation=IsolationAttestation(
                    "test-isolation", str(root), "isolated", True, "disabled",
                ),
            )
            action = ProcessAction(
                executable=str(Path(sys.executable).resolve()),
                arguments=("-c", "import time; time.sleep(30)"),
                working_directory=str(root),
                environment_names=(),
            )
            handle = provider.start(action, "process-execution", "start")
            self.assertEqual(provider.observe(handle), "running")
            self.assertEqual(provider.stop(handle, timeout_seconds=2), "stopped")
            outside = ProcessAction(
                executable=str(Path(sys.executable).resolve()), arguments=("-c", "pass"),
                working_directory="/", environment_names=(),
            )
            with self.assertRaisesRegex(ValueError, "execution root"):
                provider.start(outside, "outside", "start")

    def test_forged_handle_cannot_observe_or_stop_owned_fixture(self):
        provider = FixtureProvider()
        started = provider.start(None, "execution-one", "start", 1)
        forged = OwnedResourceHandle(
            started.opaque_id, "different-execution", started.action_id,
            started.provider_id, started.provider_kind, started.resource_identity,
        )
        with self.assertRaisesRegex(PermissionError, "does not own"):
            provider.observe(forged, 1)
        with self.assertRaisesRegex(PermissionError, "does not own"):
            provider.stop(forged, 1)

    def test_runtime_error_has_stable_diagnostic_context(self):
        blocked = self.plan.__class__(**{**self.plan.__dict__, "blockers": ("blocked",)})
        with self.assertRaises(LifecycleError) as caught:
            LifecycleController(InMemoryEvidenceJournal()).start(
                blocked, permit_for(blocked), FixtureProvider(), execution_id="blocked",
            )
        diagnostic = caught.exception.diagnostic
        self.assertEqual(diagnostic.code, "XVERSE-RUNTIME-PLAN-BLOCKED")
        self.assertEqual(diagnostic.phase, "start")
        self.assertEqual(diagnostic.selected_identity, blocked.catalog_identity)

    def test_declared_readiness_condition_is_evaluated(self):
        class WarmingProvider(FixtureProvider):
            def observe(self, handle, timeout_seconds):
                super().observe(handle, timeout_seconds)
                return "warming"

        provider = WarmingProvider()
        controller = LifecycleController(InMemoryEvidenceJournal())
        controller.start(self.plan, permit_for(self.plan), provider, execution_id="warming")
        self.assertEqual(controller.observe("warming", provider).status, "not-ready")


if __name__ == "__main__":
    unittest.main()

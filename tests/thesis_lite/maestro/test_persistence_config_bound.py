"""C1: the bound on the sealed persistence configuration (review-c1 findings 1-2; ADR-ML3-BOOTSTRAP-0001
amendment C1).

The size cases are an offline dry run: each builds the encoded ``PersistenceInput`` for n units through the
admissions a run uses (validation, experiment plan, preparation, permits, schedule, coverage, collection and
broker artifact) and starts no process. Two shapes:

- ``bench``: the S1a size-probe shape (``tools/bench/persistence_scaling``), for comparison with S1a finding 3;
- ``phase8``: a conservative stand-in for the Phase 8 units, modelled on the Phase 7 live blueprint at rc.1
  (``automotive/thesis-lite-carla-closed-loop``). Every unit declares the S1b controls (TERM grace, private
  stderr, nonce-marker readiness), the four Phase 7 action budgets, three environment names and the argument
  vector of the CARLA adapter, the longest Phase 7 unit. The run declares two concurrent freezes (CC-1), a
  600-tick horizon and the retained-inputs artifact. The XDL flows, endpoints and sensors that WP-12 adds are
  not modelled (review-c1 finding 1, residual).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import time

from xverse.maestro.admission import PermitApproval, PermitBinding, permit_digest
from xverse.maestro.artifacts import ArtifactDeclaration
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.coverage import ArtifactExpectation, admit_coverage
from xverse.maestro.persistence import encode_configuration
from xverse.maestro.projection import Limits, ProviderDescriptor, prepare_lifecycle
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.public_blobs import admit_broker_artifact
from xverse.maestro.schedule_plan import admit_schedule
from xverse.maestro.time import HostDeadline
from xverse_xdl.experiment_plan import compile_experiment_plan
from xverse_xdl.lifecycle import ExecutionPermit
from xverse_xdl.validate import validate_sources

from tools.bench.persistence_scaling.bench_persistence import _process, build_documents
from ..faults.support import fault
from .test_bootstrap_launcher import pin
from .test_preparation import SCHEMAS

RUN_ID = "c1-config-bound"
PY = Path(sys.base_prefix, "bin", "python3.13").resolve()
NS = "io.xverse.runtime.compatibility"
# The Phase 8 units of the WP-11 allocation (thesis 002 design/wp11-unit-allocation.md §4), plus the open
# seventh unit (chassis and brake on their own).
PHASE8_UNITS = ("carla-adapter", "vehicle-loop", "front-zone", "adas-hpc", "vc-functional", "vc-assurance",
                "chassis-brake")
# Path lengths of the Phase 7 live environment (blueprint units.py at rc.1), so the stand-in carries the same bytes.
CACHE = "/media/jefferson/11c42dee-73a3-4c2b-ab42-a0440011d9e0/.x-verse-build/cache"
COMPAT = "/home/jefferson/xverse-platform-worktrees/xverse-compat-phase8-stand-in"
RUN_DIR = "/dev/shm/xverse-lite-phase8-stand-in/runs/lite-20261024T000000-phase8-stand-in"
STOP_GRACE_S, STDERR_MAX, OWNED_READINESS_S = 0.6, 256 * 1024, 1.7
RETAINED_MAX = 4 * 1024 * 1024


def _phase8_arguments(name, work):
    """The Phase 7 CARLA adapter's argument vector (blueprint units.py, the longest unit), for unit ``name``."""

    return ["-s", "-B", "-m", "xverse_compat_carla.main", "--protocol", "2",
            "--connect", f"unix:/run/user/1000/xverse-lite/{RUN_ID}.sock", "--connect-timeout-s", "20",
            "--source", "live:127.0.0.1:2000:scenario", "--scenario", COMPAT + "/xdl/descriptors/aeb-sim/live-scenario.json",
            "--descriptors", COMPAT + "/xdl/descriptors/aeb-sim/carla-sensors.json",
            "--carla-site", CACHE + "/xverse-compat-carla-0.9.15-cp310/lib/python3.10/site-packages",
            "--owned-registry", RUN_DIR + f"/{name}/owned-actors.json",
            "--marker", str(work / f"{name}-binding.marker"), "--linger"]


def _phase8(docs, names, work, horizon):
    """Move the bench documents to the Phase 8 stand-in shape (module docstring)."""

    profile = docs["runtime-profile.json"]
    profile["metadata"]["version"] = "0.2.0"
    profile["spec"]["schemaRef"] = "https://xverse.io/profiles/runtime-compatibility/v0.2/schema.json"
    for binding in docs["deployment.json"]["spec"]["bindings"]:
        name = binding["id"].removesuffix("-binding")
        payload = binding["extensions"][NS]
        payload["schemaVersion"] = "0.2.0"
        for action in payload["actions"]:
            action["timeoutSeconds"] = {"prepare": 2, "start": 5, "observe": 4, "stop": 5, "cleanup": 5}[action["phase"]]
            if action["phase"] == "observe":
                action["condition"] = "nonce-marker"
        cwd = work / name
        cwd.mkdir(mode=0o700, exist_ok=True)
        payload["process"] = {"executable": str(PY), "arguments": _phase8_arguments(name, work),
                              "workingDirectory": str(cwd), "environmentNames": ["HOME", "PATH", "PYTHONPATH"],
                              "inheritedHandles": "closed", "implicitShell": False,
                              "stop": {"graceSeconds": STOP_GRACE_S},
                              "stderr": {"capture": "run-scoped-private", "maximumBytes": STDERR_MAX}}
    # CC-1: two concurrent freezes, inside the observe-to-stop window of every unit.
    docs["scenario.json"]["spec"]["faults"] = [
        fault(f"f-freeze-{name}", "freeze", name + "-instance", at=horizon // 2 + 2, duration=10, recovery="automatic")
        for name in names[2:4]]
    return docs


def configuration(tmp_path, count, *, shape="bench", horizon=300, operation=0.2):
    """The encoded persistence configuration for ``count`` units; an offline dry run (no process starts)."""

    phase8 = shape == "phase8"
    names = list(PHASE8_UNITS[:count]) if phase8 else [f"u{i}" for i in range(count)]
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    artifact = (str(PY), "sha256:" + "1" * 64)
    docs = build_documents(names, horizon, artifact)
    for binding in docs["deployment.json"]["spec"]["bindings"]:
        _process(binding["extensions"][NS], work, binding["id"].removesuffix("-binding"))
    if phase8:
        docs = _phase8(docs, names, work, horizon)
    validation = validate_sources([(name, json.dumps(value).encode()) for name, value in docs.items()],
                                  profile_schema_paths=SCHEMAS)
    assert validation.is_valid, [(d.code, d.message) for d in validation.diagnostics]
    result = compile_experiment_plan(validation.resources)
    assert result.is_valid, [(d.code, d.message) for d in result.diagnostics]
    resources = validation.resources
    helper_pin = pin(b"c1-offline-helper")
    prepared = prepare_lifecycle(result, resources,
                                 provider_descriptors=(ProviderDescriptor("maestro-process-v1", "process", helper_pin,
                                                                          "isolated-fixture"),),
                                 limits=Limits(horizon_ticks=horizon))
    now = datetime.now(timezone.utc)
    bindings, approvals = [], []
    for index, unit in enumerate(prepared.units):
        plan = unit.plan
        permit = ExecutionPermit(
            permit_id=f"c1-permit-{index}", nonce=f"c1-nonce-{index}-{time.time_ns()}", plan_digest=plan.digest,
            catalog_identity=plan.catalog_identity, environment_identity=plan.environment_identity,
            permitted_actions=tuple(a.action_id for a in plan.actions),
            approval_evidence_ref="urn:xverse:author:2026-10-22:live-integration-authorization",
            issuer_label="author-delegated-live-integration",
            operation_classes=tuple(sorted({a.operation for a in plan.actions})), exclusions=("legacy-execution",),
            public_safety_classification="public-safe", not_before=now - timedelta(seconds=30),
            expires_at=now + timedelta(seconds=150))
        binding = PermitBinding(unit.unit_id, f"c1-execution-{index}", 1, permit)
        bindings.append(binding)
        approvals.append(PermitApproval(permit.approval_evidence_ref, permit.issuer_label, RUN_ID, unit.unit_id,
                                        binding.execution_id, 1, prepared.lifecycle_digest, plan.digest,
                                        unit.provider.provider_id, unit.provider.kind, helper_pin,
                                        plan.environment_identity, plan.artifact_digests, permit_digest(permit),
                                        now - timedelta(seconds=30), now + timedelta(seconds=150)))
    timeout = OWNED_READINESS_S if phase8 else 1
    schedule = admit_schedule(prepared, policies=tuple(ProbePolicy(u.unit_id, 5, 5, timeout) for u in prepared.units),
                              ticks=tuple(range(horizon + 1)), active_seconds=55, operation_seconds=operation,
                              service_operation_count=4, per_unit_seconds=2, poll_seconds=0.05, request_limit=8192,
                              event_limit=8192, use_action_timeouts=True)
    declarations = tuple(ArtifactDeclaration(u.unit_id, 1, u.binding_id + ".marker", "outputs/" + u.binding_id + ".txt")
                         for u in prepared.units)
    st = work.stat()
    coverage = admit_coverage(prepared, result, resources, run_id=RUN_ID, host_session="host-session",
                              contexts=[(b.unit_id, b.generation, b.execution_id) for b in bindings],
                              health_policies={p.unit_id: (p.cadence_seconds, p.freshness_seconds)
                                               for p in schedule.policies},
                              active_start=time.monotonic(), active_end=time.monotonic() + schedule.active_seconds,
                              source_digests=(pin(schedule.canonical_bytes),),
                              artifacts=[*(ArtifactExpectation(d.destination, True, 256, d.unit_id, 1)
                                           for d in declarations),
                                         ArtifactExpectation("collection-result.json", maximum_bytes=16384),
                                         *([ArtifactExpectation("retained-inputs.json", maximum_bytes=RETAINED_MAX)]
                                           if phase8 else [])])
    collection = admit_collection(coverage, expected_digest=coverage.digest, source_root=str(work),
                                  source_identity=(st.st_dev, st.st_ino), declarations=declarations,
                                  metadata_path="collection-result.json", operation_seconds=1,
                                  per_unit_teardown_seconds=2, collection_seconds=3, terminal_seconds=2,
                                  drain_seconds=2)
    return encode_configuration(prepared, result, resources, run_id=RUN_ID, bindings=bindings, approvals=approvals,
                                session="host-session",
                                generation_deadline=HostDeadline("host-session", time.monotonic() + 120),
                                journal_path=tmp_path / "m3.jsonl", evidence_root=tmp_path / "argus-maestro",
                                schedule=schedule, coverage=coverage, collection=collection,
                                broker_artifact=admit_broker_artifact(coverage, expected_digest=coverage.digest))

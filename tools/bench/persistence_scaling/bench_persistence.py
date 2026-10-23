"""S1 persistence scaling benchmark (S1-T01, S1-T02; FR-001, FR-002). Bench-only: it lives outside the pytest
collection of the platform suite and is run explicitly by ``run-bench.sh``.

One test = one Maestro run through the owned trusted-host harness (``_OriginalRuntimeRun``, as in the
platform's own real-child runtime tests; not RuntimeService, not M1). The units are owned dummy processes:
each writes its completion marker and then sleeps until Maestro stops it, so the run exercises only Maestro's
lifecycle, schedule, health and persistence paths. No simulator, network or legacy artifact is involved.

Configuration (environment variables): ``XVERSE_BENCH_OUT`` (output directory, required),
``XVERSE_BENCH_UNITS`` (default 4), ``XVERSE_BENCH_HORIZON`` (Maestro ticks, default 300),
``XVERSE_BENCH_OPERATION_S`` (default 0.38), ``XVERSE_BENCH_ACTIVE_S`` (default 55; the whole run must close within
90 s of entry, finding 1),
``XVERSE_BENCH_CANCEL_AFTER_S`` (optional: cancel the run from another thread after this many seconds).

Outputs: ``rpc.jsonl`` (client side, one line per persistence round trip), ``load.jsonl`` (1 s samples of
/proc/loadavg), ``run.json`` (outcome and budgets) and a copy of the Maestro Argus root and M3 journal.
The worker-side trace is written by ``xverse_bench_trace`` when the bench venv has it installed.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time

from xverse.maestro import persistence as persistence_module
from xverse.maestro.admission import PermitApproval, PermitBinding, permit_digest
from xverse.maestro.artifacts import ArtifactDeclaration
from xverse.maestro.bootstrap import BootstrapAdmission, encode_bootstrap, seal_helper_image
from xverse.maestro.bootstrap_launcher import OriginalBootstrapRegistry
from xverse.maestro.collection_plan import admit_collection
from xverse.maestro.coverage import ArtifactExpectation, admit_coverage
from xverse.maestro.persistence import encode_configuration
from xverse.maestro.prbc import BoundaryDescriptor
from xverse.maestro.projection import Limits, ProviderDescriptor, prepare_lifecycle
from xverse.maestro.providers import ProbePolicy
from xverse.maestro.public_blobs import admit_broker_artifact
from xverse.maestro.run_broker import UnitAdmission
from xverse.maestro.runtime_entry import RuntimeScope, _OriginalRuntimeRun
from xverse.maestro.schedule_plan import admit_schedule
from xverse.maestro.time import HostDeadline
from xverse_xdl.experiment_plan import compile_experiment_plan
from xverse_xdl.lifecycle import ExecutionPermit
from xverse_xdl.validate import validate_sources

from tests.thesis_lite.maestro.test_bootstrap_launcher import pin
from tests.thesis_lite.maestro.test_preparation import SCHEMAS, documents as fixture_documents

RUN_ID = "persistence-bench"
POLL = 0.05
PY = Path(sys.base_prefix, "bin", "python3.13").resolve()  # a real ELF interpreter (Maestro seals it)
DUMMY = ("import json,pathlib,sys,time;pathlib.Path(sys.argv[1]).write_text(json.dumps({'code':0}));"
         "time.sleep(3600)")
ENVIRONMENT_DIGEST = pin(b"owned-environment")


def _digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_documents(names, horizon, artifact):
    docs = fixture_documents()
    text = json.dumps(docs)
    for old, new in (("source", names[0]), ("sink", names[1])):
        for suffix in ("-instance", "-binding"):
            text = text.replace(f'"{old}{suffix}"', f'"{new}{suffix}"').replace(f'/{old}{suffix}"', f'/{new}{suffix}"').replace(
                f'/{old}{suffix}#', f'/{new}{suffix}#')
    docs = json.loads(text)
    system = docs["system.json"]["spec"]
    template_instance = next(i for i in system["componentInstances"] if i["id"] == names[0] + "-instance")
    template_node = system["nodes"][1]
    deployment = docs["deployment.json"]["spec"]
    template_binding = next(b for b in deployment["bindings"] if b["id"] == names[0] + "-binding")
    for name in names[2:]:
        system["componentInstances"].append(dict(copy.deepcopy(template_instance), id=name + "-instance", nodeId=name + "-node"))
        system["nodes"].append(dict(copy.deepcopy(template_node), id=name + "-node"))
        binding = copy.deepcopy(template_binding)
        binding["id"] = name + "-binding"
        binding["logicalRef"]["element"] = name + "-instance"
        binding["extensions"]["io.xverse.experiment"]["target"]["element"] = name + "-binding"
        deployment["bindings"].append(binding)
    deployment["artifacts"] = [dict(id="python313", artifactKind="executable", version="1.0.0", digest=artifact[1],
                                    sourceRef=Path(artifact[0]).as_uri(), maturity="prototype")]
    for binding in deployment["bindings"]:
        binding["artifactIds"] = ["python313"]
        payload = binding["extensions"]["io.xverse.runtime.compatibility"]
        payload["provider"] = {"id": "maestro-process-v1", "kind": "process"}
        for action in payload["actions"]:
            action["timeoutSeconds"] = {"prepare": 2, "start": 5, "observe": 2, "stop": 5, "cleanup": 5}[action["phase"]]
    scenario = docs["scenario.json"]["spec"]
    template = scenario["steps"][0]
    scenario["steps"] = []
    plan = []
    for index, name in enumerate(names):
        before = [f"start-{names[index - 1]}"] if index else []
        plan += [(f"prepare-{name}", name, "prepare", 0, []), (f"start-{name}", name, "start", 0, [f"prepare-{name}"] + before),
                 (f"observe-{name}", name, "observe", horizon // 2, [f"start-{name}"])]
    for offset, name in enumerate(reversed(names)):
        tick = horizon - len(names) + 1 + offset
        plan += [(f"stop-{name}", name, "stop", tick, [f"observe-{name}"]), (f"cleanup-{name}", name, "cleanup", tick, [f"stop-{name}"])]
    for step_id, unit, phase, tick, deps in plan:
        step = copy.deepcopy(template)
        step["id"] = step_id
        step["targetRef"]["element"] = unit + "-instance"
        step["actionKind"] = "validate" if phase == "prepare" else phase
        step["action"]["operation"] = step["actionKind"]
        step["schedule"]["at"] = tick
        ext = step["extensions"]["io.xverse.experiment"]
        ext["target"]["element"] = step_id
        ext["phase"] = phase
        ext["dependsOn"] = deps
        scenario["steps"].append(step)
    return docs


def _process(payload, work, name):
    payload["process"] = {"executable": str(PY), "arguments": ["-I", "-c", DUMMY, str(work / f"{name}-binding.marker")],
                          "workingDirectory": str(work), "environmentNames": ["PATH"], "inheritedHandles": "closed",
                          "implicitShell": False}


def test_persistence_scaling(environment, binaries, authority_binary, run_bootstrap_binary, tmp_path):
    out = Path(os.environ["XVERSE_BENCH_OUT"])
    out.mkdir(parents=True, exist_ok=True)
    count = int(os.environ.get("XVERSE_BENCH_UNITS", "4"))
    horizon = int(os.environ.get("XVERSE_BENCH_HORIZON", "300"))
    operation = float(os.environ.get("XVERSE_BENCH_OPERATION_S", "0.38"))
    active_s = float(os.environ.get("XVERSE_BENCH_ACTIVE_S", "55"))
    cancel_after = os.environ.get("XVERSE_BENCH_CANCEL_AFTER_S")
    names = [f"u{i}" for i in range(count)]
    record = {"runId": RUN_ID, "units": count, "horizon": horizon, "operationS": operation, "activeS": active_s,
              "cancelAfterS": cancel_after, "startedWallNs": time.time_ns(), "monotonicStartNs": time.monotonic_ns(),
              "harness": "owned trusted-host Maestro harness (_OriginalRuntimeRun); bench-only dummy units; not M1",
              "interpreter": sys.executable, "xverseFile": persistence_module.__file__}
    stop_sampling = threading.Event()
    load_lines = []

    def sample_load():
        while not stop_sampling.wait(1.0):
            load_lines.append({"monotonicNs": time.monotonic_ns(), "load": open("/proc/loadavg").read().split()[:3]})

    sampler = threading.Thread(target=sample_load, daemon=True)
    sampler.start()
    rpc_log = (out / "rpc.jsonl").open("w", buffering=1)
    original_rpc = persistence_module.PersistenceClient._rpc

    def timed_rpc(self, kind, body, deadline, **kwargs):
        start = time.monotonic_ns()
        error = None
        try:
            return original_rpc(self, kind, body, deadline, **kwargs)
        except Exception as exc:  # recorded, then re-raised unchanged
            error = getattr(exc, "args", [None])[0] if exc.args else type(exc).__name__
            raise
        finally:
            rpc_log.write(json.dumps({"kind": kind, "bodyKind": body.get("kind") if isinstance(body, dict) else None,
                                      "startNs": start, "durationNs": time.monotonic_ns() - start, "error": error}) + "\n")

    persistence_module.PersistenceClient._rpc = timed_rpc
    factory, _, _ = environment
    lifetime = active_s + 90
    manager, _ = factory(seconds=lifetime, run_id=RUN_ID, operation=2)
    work = tmp_path / "work"
    work.mkdir()
    artifact = (str(PY), _digest(PY))
    docs = build_documents(names, horizon, artifact)
    for binding in docs["deployment.json"]["spec"]["bindings"]:
        _process(binding["extensions"]["io.xverse.runtime.compatibility"], work, binding["id"].removesuffix("-binding"))
    validation = validate_sources([(name, json.dumps(value).encode()) for name, value in docs.items()], profile_schema_paths=SCHEMAS)
    assert validation.is_valid, [(d.code, d.message) for d in validation.diagnostics]
    result = compile_experiment_plan(validation.resources)
    assert result.is_valid, [(d.code, d.message) for d in result.diagnostics]
    resources = validation.resources
    helper_pin = "sha256:" + hashlib.sha256(authority_binary.read_bytes()).hexdigest()
    prepared = prepare_lifecycle(result, resources, provider_descriptors=(ProviderDescriptor("maestro-process-v1", "process", helper_pin,
                                                                                            "isolated-fixture"),),
                                 limits=Limits(horizon_ticks=horizon))
    now = datetime.now(timezone.utc)
    bindings, approvals = [], []
    for index, unit in enumerate(prepared.units):
        unit_plan = unit.plan
        permit = ExecutionPermit(
            permit_id=f"bench-permit-{index}", nonce=f"bench-nonce-{index}-{time.time_ns()}", plan_digest=unit_plan.digest,
            catalog_identity=unit_plan.catalog_identity, environment_identity=unit_plan.environment_identity,
            permitted_actions=tuple(a.action_id for a in unit_plan.actions),
            approval_evidence_ref="urn:xverse:bench:s1-persistence-scaling", issuer_label="bench-owned-fixture",
            operation_classes=tuple(sorted({a.operation for a in unit_plan.actions})), exclusions=("legacy-execution",),
            public_safety_classification="public-safe", not_before=now - timedelta(seconds=30),
            expires_at=now + timedelta(seconds=lifetime + 60))
        binding = PermitBinding(unit.unit_id, f"bench-execution-{index}", 1, permit)
        bindings.append(binding)
        approvals.append(PermitApproval(permit.approval_evidence_ref, permit.issuer_label, RUN_ID, unit.unit_id, binding.execution_id, 1,
                                        prepared.lifecycle_digest, unit_plan.digest, unit.provider.provider_id, unit.provider.kind, helper_pin,
                                        unit_plan.environment_identity, unit_plan.artifact_digests, permit_digest(permit),
                                        now - timedelta(seconds=30), now + timedelta(seconds=lifetime + 60)))
    schedule = admit_schedule(prepared, policies=tuple(ProbePolicy(u.unit_id, 5, 5, 1) for u in prepared.units),
                              ticks=tuple(range(horizon + 1)), active_seconds=active_s, operation_seconds=operation,
                              service_operation_count=4, per_unit_seconds=2, poll_seconds=POLL, request_limit=8192, event_limit=8192,
                              use_action_timeouts=True)
    record["admission"] = {k: getattr(schedule, k) for k in ("active_seconds", "terminal_reserve_seconds") if hasattr(schedule, k)}
    declarations = tuple(ArtifactDeclaration(u.unit_id, 1, u.binding_id + ".marker", "outputs/" + u.binding_id + ".txt")
                         for u in prepared.units)
    st = work.stat()
    coverage = admit_coverage(prepared, result, resources, run_id=RUN_ID, host_session="host-session",
                              contexts=[(b.unit_id, b.generation, b.execution_id) for b in bindings],
                              health_policies={p.unit_id: (p.cadence_seconds, p.freshness_seconds) for p in schedule.policies},
                              active_start=time.monotonic(), active_end=time.monotonic() + schedule.active_seconds,
                              source_digests=(pin(schedule.canonical_bytes),),
                              artifacts=[*(ArtifactExpectation(d.destination, True, 256, d.unit_id, 1) for d in declarations),
                                         ArtifactExpectation("collection-result.json", maximum_bytes=16384),
                                         # retained public inputs grow ~1.7 KB per event; the 1 MiB default bounds a run to
                                         # ~600 events (finding 8). Coverage admission allows up to 16 MiB in total.
                                         *([ArtifactExpectation("retained-inputs.json", maximum_bytes=int(retained_max))]
                                           if (retained_max := os.environ.get("XVERSE_BENCH_RETAINED_MAX")) else [])])
    collection = admit_collection(coverage, expected_digest=coverage.digest, source_root=str(work), source_identity=(st.st_dev, st.st_ino),
                                  declarations=declarations, metadata_path="collection-result.json", operation_seconds=1,
                                  per_unit_teardown_seconds=2, collection_seconds=3, terminal_seconds=2, drain_seconds=2)
    config = encode_configuration(prepared, result, resources, run_id=RUN_ID, bindings=bindings, approvals=approvals, session="host-session",
                                  generation_deadline=manager._admission.teardown_deadline, journal_path=tmp_path / "m3.jsonl",
                                  evidence_root=tmp_path / "argus-maestro", schedule=schedule, coverage=coverage, collection=collection,
                                  broker_artifact=admit_broker_artifact(coverage, expected_digest=coverage.digest))
    record["configBytes"] = len(config.private_bytes)  # bootstrap refuses more than 65 536 (ML-BOOT-PERSISTENCE)
    images = tuple(seal_helper_image(p, digest=pin(p.read_bytes()), argv0=sys.executable if p == Path(sys.executable).resolve() else str(p))
                   for p in (binaries["launcher"], binaries["bound-gate"], Path(sys.executable).resolve(), authority_binary))
    supervisor = seal_helper_image(run_bootstrap_binary, digest=pin(run_bootstrap_binary.read_bytes()), argv0=str(run_bootstrap_binary))
    boot = encode_bootstrap(BootstrapAdmission(config.run_id, config.prepared.lifecycle_digest, "bootstrap-approval", ENVIRONMENT_DIGEST,
                                               supervisor.digest, manager._admission.teardown_deadline,
                                               HostDeadline("host-session", time.monotonic() + 4.8), images[:3], images[3], manager._root_fd))
    launcher = OriginalBootstrapRegistry(1).reserve(boot, supervisor, manager)
    admissions = tuple(UnitAdmission(BoundaryDescriptor(config.run_id, u.unit_id, 1, "work-" + str(i), 0), (("PATH", "/usr/bin"),), 1)
                       for i, u in enumerate(config.prepared.units))
    entry = _OriginalRuntimeRun(config, launcher, admissions, controller_sessions=1)
    active = HostDeadline(config.session, config.coverage.data(config.coverage.digest)["end"] - .01)
    reserve = config.schedule.terminal_reserve_seconds + config.collection.collection_seconds + config.collection.terminal_seconds
    terminal = HostDeadline(config.session, active.monotonic_seconds + reserve + 1 + .01)
    # the run-closure cap: closure at most 90 s after entry (runtime_entry.py:112, closure15 unit contract; finding 1)
    closure = HostDeadline(config.session, min(terminal.monotonic_seconds + 3, time.monotonic() + 89.5, config.generation_ns / 1e9))
    startup_s = float(os.environ.get("XVERSE_BENCH_STARTUP_S", "2"))  # within the 4.8 s bootstrap lease
    scope = RuntimeScope(HostDeadline("host-session", time.monotonic() + startup_s), active, terminal, closure)
    record["budgets"] = {"terminalReserveS": config.schedule.terminal_reserve_seconds, "reserveS": reserve,
                         "closureFromNowS": round(closure.monotonic_seconds - time.monotonic(), 2)}
    canceller = None
    if cancel_after:
        def cancel():
            time.sleep(float(cancel_after))
            record["cancelRequestedMonotonicNs"] = time.monotonic_ns()
            record["cancelEpoch"] = entry.stop(RUN_ID, reason="bench-cancel")
            record["cancelReturnedMonotonicNs"] = time.monotonic_ns()
        canceller = threading.Thread(target=cancel, daemon=True)
        canceller.start()
    outcome = None
    try:
        outcome = entry.start(scope)
    finally:
        if canceller is not None:
            canceller.join(timeout=5)
        stop_sampling.set()
        sampler.join(timeout=2)
        persistence_module.PersistenceClient._rpc = original_rpc
        rpc_log.close()
        record["endedWallNs"] = time.time_ns()
        record["monotonicEndNs"] = time.monotonic_ns()
        if outcome is not None:
            record.update(executionSucceeded=outcome.execution_succeeded, cleanupComplete=outcome.cleanup_complete,
                          diagnostics=list(outcome.diagnostics), dispatchDiagnostic=outcome.dispatch.diagnostic if outcome.dispatch else None,
                          normalUnitRecordsComplete=outcome.closure.normal_unit_records_complete,
                          nativeUnits=[asdict(u) for u in outcome.closure.native_units],
                          persistenceFailure=str(getattr(outcome, "persistence_failure", None)),
                          closureDiagnostics=[str(d) for d in getattr(outcome.closure, "diagnostics", ())],
                          closureWriters=str(getattr(outcome.closure, "writers", None)),
                          dispatchTerminal=(outcome.dispatch.terminal.public_data()
                                            if outcome.dispatch and outcome.dispatch.terminal is not None else None))
        (out / "load.jsonl").write_text("".join(json.dumps(line) + "\n" for line in load_lines))
        (out / "run.json").write_text(json.dumps(record, indent=2, sort_keys=True, default=str) + "\n")
        for name in ("argus-maestro", "m3.jsonl"):
            source = tmp_path / name
            if source.is_dir():
                shutil.copytree(source, out / name, dirs_exist_ok=True)
            elif source.exists():
                shutil.copy2(source, out / name)
        if outcome is not None:
            entry.dispose()
        else:
            launcher.dispose()
        for image in (*images, supervisor):
            os.close(image.descriptor)

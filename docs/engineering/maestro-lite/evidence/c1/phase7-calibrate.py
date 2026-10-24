"""Offline calibration: the Phase 7 live blueprint configuration (rc.1 blueprints 99df3a4) at 4 units, freeze-vcu
case and nominal, horizon 400 and 600. No process starts; the blueprint module is imported read-only."""
import json, os, sys, tempfile, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, ".")
BP = "/home/jefferson/xverse-blueprints/automotive/thesis-lite-carla-closed-loop"
sys.path.insert(0, BP)
import test_live_closed_loop as lt
from units import units
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
from xverse_xdl.lifecycle import ExecutionPermit
from tests.thesis_lite.maestro.test_bootstrap_launcher import pin
out = []
for case, horizon in (("nominal", 400), ("freeze-vcu", 400), ("freeze-vcu", 600)):
    with tempfile.TemporaryDirectory(dir="/dev/shm") as t:
        t = Path(t); run_dir = t / "run"; run_dir.mkdir(); work = t / "work"; work.mkdir()
        defs = units(compat=Path("/home/jefferson/xverse-compat"), run_dir=run_dir, work=work,
                     socket_path=f"/run/user/{os.getuid()}/xverse-lite/{lt.RUN_ID}.sock", plan=run_dir / "experiment-plan.json",
                     episode_s=9.5)
        artifacts = {"python310": ("/usr/bin/python3.10", "sha256:" + "1" * 64), "python313": (defs[0].executable, "sha256:" + "2" * 64)}
        docs = lt.build_documents(defs, artifacts, horizon)
        if case == "freeze-vcu":
            from tests.thesis_lite.faults.support import fault
            docs["scenario.json"]["spec"]["faults"] = [lt._rename(fault("f-freeze-vcu", "freeze", "legacy-vcu-instance", at=lt.FREEZE_AT,
                                                                        duration=lt.FREEZE_TICKS, recovery="automatic"))]
        result, resources = lt.compile_documents(docs)
        helper_pin = pin(b"c1-offline-helper")
        prepared = prepare_lifecycle(result, resources, provider_descriptors=(ProviderDescriptor("maestro-process-v1", "process", helper_pin, "isolated-fixture"),),
                                     limits=Limits(horizon_ticks=horizon))
        now = datetime.now(timezone.utc); bindings, approvals = [], []
        for index, unit in enumerate(prepared.units):
            p = unit.plan; legacy = "legacy-vcu" in unit.unit_id
            permit = ExecutionPermit(permit_id=f"live-permit-{index}", nonce=f"live-nonce-{index}-{time.time_ns()}", plan_digest=p.digest,
                catalog_identity=p.catalog_identity, environment_identity=p.environment_identity, permitted_actions=tuple(a.action_id for a in p.actions),
                approval_evidence_ref="urn:xverse:author:2026-10-22:live-integration-authorization", issuer_label="author-delegated-live-integration",
                operation_classes=tuple(sorted({a.operation for a in p.actions})), exclusions=() if legacy else ("legacy-execution",),
                public_safety_classification="public-safe", not_before=now - timedelta(seconds=30), expires_at=now + timedelta(seconds=150))
            b = PermitBinding(unit.unit_id, f"live-execution-{index}", 1, permit); bindings.append(b)
            approvals.append(PermitApproval(permit.approval_evidence_ref, permit.issuer_label, lt.RUN_ID, unit.unit_id, b.execution_id, 1,
                prepared.lifecycle_digest, p.digest, unit.provider.provider_id, unit.provider.kind, helper_pin, p.environment_identity,
                p.artifact_digests, permit_digest(permit), now - timedelta(seconds=30), now + timedelta(seconds=150)))
        rt = {u.unit_id: 1 if "legacy-vcu" in u.unit_id else lt.OWNED_READINESS_TIMEOUT_S for u in prepared.units}
        schedule = admit_schedule(prepared, policies=tuple(ProbePolicy(u.unit_id, 5, 5, rt[u.unit_id]) for u in prepared.units),
            ticks=tuple(range(horizon + 1)), active_seconds=55, operation_seconds=0.38, service_operation_count=4, per_unit_seconds=2,
            poll_seconds=lt.POLL, request_limit=8192, event_limit=8192, use_action_timeouts=True)
        owned = [u for u in prepared.units if "legacy-vcu" not in u.unit_id]
        decl = tuple(ArtifactDeclaration(u.unit_id, 1, u.binding_id + ".marker", "outputs/" + u.binding_id + ".txt") for u in owned)
        st = work.stat()
        cov = admit_coverage(prepared, result, resources, run_id=lt.RUN_ID, host_session="host-session",
            contexts=[(b.unit_id, b.generation, b.execution_id) for b in bindings],
            health_policies={p.unit_id: (p.cadence_seconds, p.freshness_seconds) for p in schedule.policies},
            active_start=time.monotonic(), active_end=time.monotonic() + schedule.active_seconds, source_digests=(pin(schedule.canonical_bytes),),
            artifacts=[*(ArtifactExpectation(d.destination, True, 256, d.unit_id, 1) for d in decl),
                       ArtifactExpectation("collection-result.json", maximum_bytes=16384),
                       ArtifactExpectation("retained-inputs.json", maximum_bytes=lt.RETAINED_MAX)])
        col = admit_collection(cov, expected_digest=cov.digest, source_root=str(work), source_identity=(st.st_dev, st.st_ino), declarations=decl,
            metadata_path="collection-result.json", operation_seconds=1, per_unit_teardown_seconds=2, collection_seconds=3, terminal_seconds=2, drain_seconds=2)
        c = encode_configuration(prepared, result, resources, run_id=lt.RUN_ID, bindings=bindings, approvals=approvals, session="host-session",
            generation_deadline=HostDeadline("host-session", time.monotonic() + 120), journal_path=t / "m3.jsonl", evidence_root=t / "argus-maestro",
            schedule=schedule, coverage=cov, collection=col, broker_artifact=admit_broker_artifact(cov, expected_digest=cov.digest))
        out.append(dict(case=case, horizon=horizon, units=4, bytes=len(c.private_bytes)))
        print(out[-1], flush=True)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))

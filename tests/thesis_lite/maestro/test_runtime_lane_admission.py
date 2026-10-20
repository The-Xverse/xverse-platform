"""Bounded lane admission with real pins (IR-ML3-04, finding 382): preflight accepts, execution stays closed.

Reads the lane admission proposal named by MAESTRO_LANE_PROPOSAL (skipped when absent, so the full
platform run does not depend on retained evidence paths). Real pins: helper artifact digests must
equal the binaries this harness compiles (reproducible build), the nine runtime-case receipt files
retained by runtime-lane-20261020a and crash-matrix-20261020b are read through RuntimeEvidenceFiles,
the environment/implementation/design pins and both review digests come from the proposal. Asserts:
validate_run_admission and verify_runtime_evidence accept the real pins with ready_for_execution
false; RuntimeService.inspect refuses with READINESS-BLOCKED because execution is not approved and
blocking findings remain; no process, boundary entry, journal or evidence store is created.
Not M1, not acceptance.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import pytest
from xverse.maestro.runtime_admission import FacilityAttestation, RunAuthorization, RUNTIME_CASES, FENCE_PROPERTIES, HELPER_ROLES, admission_digest, validate_run_admission
from xverse.maestro.runtime_evidence import RuntimeEvidenceFiles, verify_runtime_evidence
from xverse.maestro.runtime_service import ApprovedRuntime, RuntimeReadiness, ReadinessFiles, RuntimeSubmission, RuntimeService, readiness_digest
from xverse.maestro.time import HostDeadline
from . import test_runtime_entry
from .test_runtime_entry import runtime as runtime
from .test_boundary import environment as environment
from .test_launcher import binaries as binaries, deadline
from .test_affa_native import authority_binary as authority_binary
from .test_run_bootstrap import run_bootstrap_binary as run_bootstrap_binary
from .test_bootstrap_launcher import pin

SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
PROPOSAL = os.environ.get("MAESTRO_LANE_PROPOSAL")
pytestmark = pytest.mark.skipif(not PROPOSAL, reason="MAESTRO_LANE_PROPOSAL not set: lane admission evidence runs under its own driver")


@pytest.fixture
def proposal():
    path = Path(PROPOSAL).resolve(strict=True)
    data = json.loads(path.read_bytes())
    root = path.parents[5]  # docs/engineering/maestro-lite/evidence/affa17/<file>
    return data, root, path


@pytest.fixture
def lane_runtime(proposal, request, monkeypatch):
    data, _, _ = proposal
    monkeypatch.setattr(test_runtime_entry, "ENVIRONMENT_DIGEST", data["facility"]["environment"]["digest"])
    return request.getfixturevalue("runtime")


def test_real_pins_are_admitted_read_only_and_execution_stays_closed(proposal, lane_runtime, tmp_path, monkeypatch):
    from xverse.argus import EvidenceStore
    from xverse_xdl.lifecycle import FileEvidenceJournal
    from xverse.maestro.prbc import ProcessBoundaryOps
    data, root, proposal_path = proposal
    entry, scope, work = lane_runtime
    config, launcher, _ = entry._pins[:3]
    boot = launcher.config
    facility_data = data["facility"]
    # Reproducible build: the helpers this harness compiled are the lane's retained binaries.
    compiled = dict(zip(HELPER_ROLES, (boot.admission.supervisor_artifact_digest, *(i.digest for i in (*boot.admission.images, boot.admission.authority_image)))))
    expected = {role: "sha256:" + facility_data["helpers"][role]["binary_sha256"] for role in HELPER_ROLES}
    assert compiled == expected, dict(compiled=compiled, expected=expected)
    assert boot.admission.environment_digest == facility_data["environment"]["digest"]
    receipt_paths = {case: root / facility_data["runtime_case_receipts"][case]["path"] for case in RUNTIME_CASES}
    facility = FacilityAttestation(facility_data["environment"]["digest"], facility_data["implementation"]["digest"], facility_data["design"]["digest"],
                                   os.uname().release, tuple((role, compiled[role]) for role in HELPER_ROLES),
                                   tuple((case, "sha256:" + facility_data["runtime_case_receipts"][case]["sha256"]) for case in RUNTIME_CASES), FENCE_PROPERTIES)
    assert admission_digest(facility) == facility_data["facility_digest"]
    now = datetime.now(timezone.utc)
    authorization = RunAuthorization(boot.admission.approval_ref, config.run_id, "sha256:" + config.prepared.lifecycle_digest,
                                     pin(config.private_bytes), pin(boot.private_bytes), admission_digest(facility),
                                     now - timedelta(seconds=60), now + timedelta(seconds=30), boot.admission.generation)
    readiness_data = data["readiness"]
    ready = RuntimeReadiness(readiness_data["approval_ref"], admission_digest(authorization), admission_digest(facility),
                             facility.design_digest, facility.implementation_digest, facility.environment_digest,
                             readiness_data["source_review"]["digest"], readiness_data["verification_review"]["digest"], 18, RUNTIME_CASES,
                             readiness_data["source_dispositions_approved"], readiness_data["verification_complete"],
                             readiness_data["independent_review_recorded"], readiness_data["execution_approved"], tuple(readiness_data["blocking_findings"]))
    assert ready.execution_approved is False and ready.blocking_findings
    directory = tmp_path / "lane-admission"; directory.mkdir()
    (directory / "authorization").write_bytes(authorization.canonical_bytes())
    (directory / "facility").write_bytes(facility.canonical_bytes())
    (directory / "readiness").write_bytes(ready.canonical_bytes())
    fds = {}
    opened = []
    def open_ro(name, path):
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC); opened.append(fd); fds[name] = fd; return fd
    try:
        open_ro("authorization", directory / "authorization"); open_ro("facility", directory / "facility"); open_ro("readiness", directory / "readiness")
        for case in RUNTIME_CASES:
            open_ro(case, receipt_paths[case])
        open_ro("source_review", Path(readiness_data["source_review"]["path"]))
        open_ro("verification_review", root / readiness_data["verification_review"]["path"])
        evidence = RuntimeEvidenceFiles(fds["authorization"], fds["facility"], tuple((case, fds[case]) for case in RUNTIME_CASES))
        reviews = ReadinessFiles(fds["readiness"], fds["source_review"], fds["verification_review"])
        pins = dict(expected_authorization_digest=admission_digest(authorization), expected_facility_digest=admission_digest(facility),
                    expected_design_digest=facility.design_digest, expected_implementation_digest=facility.implementation_digest,
                    expected_environment_digest=facility.environment_digest)
        def forbidden(*a, **kw):
            pytest.fail("lane admission preflight attempted a process, boundary, journal or store effect")
        with monkeypatch.context() as patch:
            patch.setattr(subprocess, "Popen", forbidden); patch.setattr(ProcessBoundaryOps, "create_frozen", forbidden)
            patch.setattr(EvidenceStore, "open_run", forbidden); patch.setattr(FileEvidenceJournal, "__init__", forbidden)
            admission = validate_run_admission(config, boot, authorization, facility, now=datetime.now(timezone.utc),
                                               host_now=HostDeadline(config.session, time.monotonic()), **pins)
            assert not admission.ready_for_execution
            result = verify_runtime_evidence(config, boot, authorization, facility, evidence, launcher.boundaries, deadline=deadline(2), **pins)
            assert not result.ready_for_execution and result.receipt_digests == facility.runtime_case_receipts
            assert result.kernel_identity == os.uname().release
            policy = ApprovedRuntime(config.run_id, admission_digest(authorization), admission_digest(facility), readiness_digest(ready),
                                     facility.design_digest, facility.implementation_digest, facility.environment_digest)
            service = RuntimeService((policy,))
            submission = RuntimeSubmission(entry, authorization, facility, evidence, ready, reviews)
            with pytest.raises(ValueError, match="READINESS-BLOCKED"):
                service.inspect(submission, deadline=deadline(2))
            # Default-closed service refuses registration before readiness; an execution-enabled service
            # still refuses on the unapproved readiness statement.
            with pytest.raises(ValueError, match="SERVICE-DISABLED"):
                service.register(submission, deadline=deadline(2))
            with pytest.raises(ValueError, match="READINESS-BLOCKED"):
                RuntimeService((policy,), execution_enabled=True).register(submission, deadline=deadline(2))
        assert not launcher.boundaries._entries and not launcher._birth_attempted
        output = os.environ.get("MAESTRO_BOUNDARY_RECEIPTS")
        if output:
            target = Path(output); target.mkdir(parents=True, exist_ok=True)
            (target / ("lane-admission-" + tmp_path.name + ".json")).write_text(json.dumps(dict(
                proposal=str(proposal_path), proposal_sha256=hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
                facility_digest=admission_digest(facility), readiness_digest=readiness_digest(ready), helpers=compiled,
                receipts=[list(r) for r in result.receipt_digests], kernel_identity=result.kernel_identity,
                ready_for_execution=False, service_inspect="READINESS-BLOCKED", service_register_default="SERVICE-DISABLED", service_register_enabled="READINESS-BLOCKED",
                blocking_findings=list(ready.blocking_findings), source_sha256=SOURCE_SHA256,
                admitted_m1_run=False, lane_activated=False, accepted=False), indent=2))
    finally:
        for fd in opened:
            os.close(fd)

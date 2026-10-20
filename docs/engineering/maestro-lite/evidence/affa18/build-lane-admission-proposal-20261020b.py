"""IR-ML3-04 lane admission proposal v2 for increment18 (changed authority helper, findings 395-397); NOT an activation.

Usage: PYTHONPATH=<candidate>/src python3 -I build-lane-admission-proposal-20261020.py

Builds the FacilityAttestation and RuntimeReadiness values of a bounded trusted runtime lane from
retained evidence: helper artifact digests from the compiled helpers retained by runtime-lane-20261020a,
the seven lane receipts and two per-case indexes of the composed-case receipts (crash-matrix-20261020b),
the environment (platform-environment-20261020d), implementation (git archive of src/xverse/maestro at
HEAD), design (ML-DESIGN-2026-10-03-v2 manifest), kernel identity, the author-confirmed source-parent
register v4 as the source review and the independent helper-bytes review as the verification review.
Validates the values through the product's own canonical_bytes/admission_digest/readiness_digest, and
writes the proposal JSON plus the two composed-case index files. execution_approved stays False; no
persistence, bootstrap, boundary or process is created; validate_run_admission is NOT called.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

from xverse.maestro.runtime_admission import FacilityAttestation, FENCE_PROPERTIES, HELPER_ROLES, RUNTIME_CASES, admission_digest
from xverse.maestro.runtime_service import RuntimeReadiness, readiness_digest

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
THESIS = Path("/home/jefferson/distributed_safety_critical_thesis")
LANE = BASE / "runtime-lane-20261020c" / "source-harness"
CRASH = BASE / "crash-matrix-20261020d" / "source-harness" / "test_composed_authority_interruptions"
OUT = BASE / "lane-admission-proposal-20261020b.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pin = lambda p: "sha256:" + sha(p)
read = lambda p: json.loads(Path(p).read_bytes())

# Helper artifacts: the exact binaries the lane run compiled and retained (source hashes recorded alongside).
actual = LANE / "test_runtime_actual"
bound_gate = next(actual.glob("catalog-native-bound-gate-*.bin"))
launcher = next(actual.glob("catalog-native-launcher-*.bin"))
supervisor = read(actual / "run-bootstrap-native.json")
authority = read(actual / "affa-native.json")
python_path = Path(os.path.realpath(sys.executable))
helpers = dict(
    supervisor=dict(source="src/xverse/maestro/native/bootstrap.c", source_sha256=supervisor["source_sha256"], binary_sha256=supervisor["binary_sha256"], retained=str((actual / "run-bootstrap-native.json").relative_to(ROOT))),
    catalog=dict(source="src/xverse/maestro/native/catalog_launcher.c", source_sha256=sha(ROOT / "src/xverse/maestro/native/catalog_launcher.c"), binary_sha256=sha(launcher), retained=str(launcher.relative_to(ROOT))),
    gate=dict(source="src/xverse/maestro/native/lease_guard.c", source_sha256=sha(ROOT / "src/xverse/maestro/native/lease_guard.c"), binary_sha256=sha(bound_gate), retained=str(bound_gate.relative_to(ROOT))),
    python=dict(source=str(python_path), binary_sha256=sha(python_path), retained=None),
    authority=dict(source="src/xverse/maestro/native/run_authority.c", source_sha256=authority["source_sha256"], binary_sha256=authority["binary_sha256"], retained=str((actual / "affa-native.json").relative_to(ROOT))),
)
for role in ("supervisor", "catalog", "gate", "authority"):
    assert helpers[role]["source_sha256"] == sha(ROOT / helpers[role]["source"]), role  # helper sources unchanged since the lane run
helper_artifacts = tuple((role, "sha256:" + helpers[role]["binary_sha256"]) for role in HELPER_ROLES)

# Runtime case receipts: seven lane receipts; two composed cases get a per-case index of their parametrized receipts.
receipts = {}
for case in RUNTIME_CASES:
    direct = actual / ("runtime-actual-" + case + ".json")
    if direct.is_file():
        receipts[case] = dict(path=str(direct.relative_to(ROOT)), sha256=sha(direct), kind="lane-receipt")
    else:
        prefix = "composed-authority-" + case[:29]
        members = sorted(p for p in CRASH.glob("composed-authority-*.json") if p.name.startswith(prefix))
        assert members, case
        index = dict(case=case, kind="composed-case-index", evidence="crash-matrix-20261020d", members=[dict(path=str(p.relative_to(ROOT)), sha256=sha(p), window=read(p)["window"], fault=read(p)["fault"]) for p in members])
        index_path = BASE / ("lane-case-index-" + case + "-20261020b.json")
        with index_path.open("x") as stream:
            json.dump(index, stream, indent=2); stream.write("\n")
        receipts[case] = dict(path=str(index_path.relative_to(ROOT)), sha256=sha(index_path), kind="composed-case-index", members=len(members))
runtime_case_receipts = tuple((case, "sha256:" + receipts[case]["sha256"]) for case in RUNTIME_CASES)

implementation = subprocess.run(["git", "archive", "--format=tar", "HEAD", "src/xverse/maestro"], cwd=ROOT, capture_output=True, check=True).stdout
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
design = THESIS / "specs/024-maestro-lite-lifecycle/engineering/successors/ML-DESIGN-2026-10-03-v2/design-manifest.json"
environment = BASE / "platform-environment-20261020f" / "preparation.json"
source_review = THESIS / "specs/024-maestro-lite-lifecycle/engineering/successors/ML-SOURCE-PARENT-2026-10-20-v4/source-parent-register.json"
verification_review = BASE / "helper-change-twopass-independent-review-20261020.json"
assert verification_review.is_file(), "independent review of the changed helper bytes required before the readiness statement"
helper_review = read(verification_review)

facility = FacilityAttestation(pin(environment), "sha256:" + hashlib.sha256(implementation).hexdigest(), pin(design), os.uname().release,
                               helper_artifacts, runtime_case_receipts, FENCE_PROPERTIES)
facility_digest = admission_digest(facility)
blocking = tuple(["ML-CAPA-359-UNKNOWN", "ML-CAPA-135/286/287/318/324/330/331/332/337-UNKNOWN", "IR-ML3-04-ACTIVATION-NOT-APPROVED", "M1-NOT-ADMITTED", "INCREMENT18-ACCEPTANCE-OPEN", "ML-CAPA-381-F02-NATIVE-DEFERRED"]
                 + ["HELPER-REVIEW-" + f["id"] + "-" + f["severity"] for f in helper_review.get("findings", []) if f.get("severity") in ("HIGH", "MEDIUM")])
readiness = RuntimeReadiness("PROPOSAL-NOT-AN-APPROVAL-2026-10-20", "sha256:" + "0" * 64, facility_digest, facility.design_digest, facility.implementation_digest,
                             facility.environment_digest, pin(source_review), pin(verification_review), 18, RUNTIME_CASES,
                             source_dispositions_approved=True, verification_complete=False, independent_review_recorded=True,
                             execution_approved=False, blocking_findings=blocking)
rd = readiness_digest(readiness)
proposal = dict(schema_version=1, revision="ML3-AFFA18-2026-10-20-lane-admission-proposal-v2", status="PROPOSAL; not an activation; no admission performed",
    candidate_git_head=head, kernel_identity=os.uname().release,
    facility=dict(environment=dict(path=str(environment.relative_to(ROOT)), digest=facility.environment_digest),
                  implementation=dict(method="git archive --format=tar HEAD src/xverse/maestro", head=head, digest=facility.implementation_digest),
                  design=dict(path=str(design), digest=facility.design_digest), helpers=helpers, runtime_case_receipts=receipts,
                  enforced_properties=list(FENCE_PROPERTIES), facility_digest=facility_digest),
    readiness=dict(approval_ref=readiness.approval_ref, authorization_digest="placeholder; a RunAuthorization exists only for a prepared run",
                   source_review=dict(path=str(source_review), digest=readiness.source_review_digest, meaning="author-confirmed source-parent register v4"),
                   verification_review=dict(path=str(verification_review.relative_to(ROOT)), digest=readiness.verification_review_digest, meaning="independent review of the changed authority helper bytes (separate agent session); unchanged helpers keep the increment17 full-bytes review"),
                   source_parent_count=18, runtime_cases=list(RUNTIME_CASES), source_dispositions_approved=True, verification_complete=False,
                   independent_review_recorded=True, execution_approved=False, blocking_findings=list(blocking), readiness_digest=rd),
    helper_review_counts=helper_review.get("counts"),
    what_this_is_not=["not validate_run_admission (needs a prepared run's persistence/bootstrap)", "not verify_runtime_evidence (needs an empty original boundary root)",
                      "not RuntimeService.register/start", "not M1", "not acceptance"],
    next_step="author decision on activating a bounded lane admission test that supplies these pins to validate_run_admission/verify_runtime_evidence inside the component harness; execution_approved stays False")
with OUT.open("x") as stream:
    json.dump(proposal, stream, indent=2); stream.write("\n")
print(json.dumps(dict(output=OUT.name, sha256=sha(OUT), facility_digest=facility_digest, readiness_digest=rd, blocking=len(blocking))))

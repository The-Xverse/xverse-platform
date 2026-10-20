"""Endpoint reconciliation proposal: map the 62 declared ML3 endpoints onto the current composition.

Usage: python3 -I build-endpoint-reconciliation-20261020.py

Author decision AD-2026-10-20-b (agent proposal under the author's proceed instruction). Every declared
endpoint receives a proposed current qualified interface identity or a superseded-with-rationale
record; every proposed target is resolved against the current candidate AST (module-level class,
function, or class method). Confidence: `mapped` (same symbol or a renamed module), `mapped_candidate`
(semantic correspondence judged from the current module contracts; review required),
`superseded_no_equivalent` (no current interface carries the declared responsibility as one symbol).
This closes no obligation: the independent review the change spec requires remains pending.
"""
import ast
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
GAP = BASE / "endpoint-reconciliation-gap-20261020.json"
MATRIX = Path("/home/jefferson/distributed_safety_critical_thesis/specs/024-maestro-lite-lifecycle/review/ml3-successor-change-spec-2026-10-03-v1/validation-matrix.json")
OUT = BASE / "endpoint-reconciliation-proposal-20261020.json"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())

# declared endpoint -> (proposed target or None, confidence, rationale, alternatives)
M = {
 "src/xverse/maestro/admission.py::Admission": ("src/xverse/maestro/admission.py::PermitSession", "mapped_candidate", "The admission session validates permits and claims the durable start intent; the declared class became the session object.", []),
 "src/xverse/maestro/admission.py::admission_digest": ("src/xverse/maestro/runtime_admission.py::admission_digest", "mapped", "Same symbol, moved to the runtime admission module.", ["src/xverse/maestro/evidence_scope.py::runtime_admission_digest"]),
 "src/xverse/maestro/admission.py::bind_identities": ("src/xverse/maestro/runtime_admission.py::validate_run_admission", "mapped_candidate", "Identity binding of run, facility and pins is performed by the joint read-only preflight.", ["src/xverse/maestro/runtime_admission.py::AdmissionPins"]),
 "src/xverse/maestro/admission.py::consume_permit_once": ("src/xverse/maestro/admission.py::PermitSession.claim_start_intent", "mapped_candidate", "Single durable claim of the start intent is the current once-only consumption.", ["src/xverse/maestro/admission.py::PermitSession.claims_closed"]),
 "src/xverse/maestro/admission.py::fence_capability_required": ("src/xverse/maestro/prbc.py::ProcessBoundaryOps.bind_authority", "mapped_candidate", "The fence capability requirement is enforced where the boundary binds its authority, not in permit validation.", ["src/xverse/maestro/affa_client.py::AuthorityConnection"]),
 "src/xverse/maestro/affa.py::FenceAuthority": ("src/xverse/maestro/affa_client.py::AuthorityConnection", "mapped_candidate", "The authority transport to the native AF17 helper replaced the in-process fence authority.", ["src/xverse/maestro/owner.py::GateConnection"]),
 "src/xverse/maestro/affa.py::ReleaseEpoch": ("src/xverse/maestro/affa_client.py::AuthorityEpochAdvance", "mapped_candidate", "Release epochs are advanced through the authority connection.", ["src/xverse/maestro/prbc.py::ProcessBoundaryOps.admit_epoch"]),
 "src/xverse/maestro/affa.py::cancel": ("src/xverse/maestro/affa_client.py::AuthorityConnection.revoke", "mapped_candidate", "Authority cancellation is revocation on the connection.", ["src/xverse/maestro/owner.py::ReleaseOwner.cancel"]),
 "src/xverse/maestro/affa.py::consume_ticket": ("src/xverse/maestro/owner.py::ReleaseOwner.release", "mapped_candidate", "Ticket consumption happens at the owner's Release; replayed tickets are fenced (REJECTED reason 4).", []),
 "src/xverse/maestro/affa.py::issue_ticket": ("src/xverse/maestro/run_broker.py::RunUnitIssuer.stage", "mapped_candidate", "Issuance is the broker's per-unit Stage over the catalog launcher.", ["src/xverse/maestro/launcher.py::CatalogLauncher.stage"]),
 "src/xverse/maestro/api.py::assess_lifecycle": ("src/xverse/maestro/coverage.py::assess_preclosure", "mapped_candidate", "Lifecycle assessment is the pre-closure coverage assessment.", ["src/xverse/maestro/coverage.py::verify_closed"]),
 "src/xverse/maestro/api.py::collect": ("src/xverse/maestro/runtime_service.py::RuntimeService.collect", "mapped_candidate", "Public collect entry on the candidate host admission facade.", ["src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRegistry.collect"]),
 "src/xverse/maestro/api.py::prepare": ("src/xverse/maestro/projection.py::prepare_lifecycle", "mapped_candidate", "Side-effect-free preparation is the projection entry.", []),
 "src/xverse/maestro/api.py::reconcile": ("src/xverse/maestro/recovery.py::IssuerRecovery.reconcile", "mapped_candidate", "Reconciliation of surviving issuers inside the original supervisor.", ["src/xverse/maestro/controller.py::ControllerSession.reconcile"]),
 "src/xverse/maestro/api.py::restart": ("src/xverse/maestro/runtime_service.py::RuntimeService.restart", "mapped_candidate", "Public restart entry on the facade.", ["src/xverse/maestro/dispatcher.py::FiniteDispatcher.restart"]),
 "src/xverse/maestro/api.py::start": ("src/xverse/maestro/runtime_service.py::RuntimeService.start", "mapped_candidate", "Public start entry on the facade; admitted public start remains gated.", ["src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRegistry.start"]),
 "src/xverse/maestro/api.py::stop": ("src/xverse/maestro/runtime_service.py::RuntimeService.stop", "mapped_candidate", "Public stop entry on the facade.", ["src/xverse/maestro/runtime_entry.py::_OriginalRuntimeRegistry.stop"]),
 "src/xverse/maestro/artifacts.py::collect_declared_artifacts": ("src/xverse/maestro/artifacts.py::CollectionAdmission.collect", "mapped_candidate", "Declared-file collection is the admission's collect method.", ["src/xverse/maestro/collection_runtime.py::collect_outputs"]),
 "src/xverse/maestro/artifacts.py::confined_read": ("src/xverse/maestro/artifacts.py::CollectionSource.bind", "mapped_candidate", "Confined reading binds a declared source before collection.", ["src/xverse/maestro/public_blobs.py::read_public_blob"]),
 "src/xverse/maestro/broker.py::Broker": ("src/xverse/maestro/run_broker.py::RunBroker", "mapped", "Renamed module and class with the same broker role.", []),
 "src/xverse/maestro/broker.py::IssueRegistry": ("src/xverse/maestro/run_broker.py::RunBroker.issuers", "mapped_candidate", "The issued inventory is exposed by the broker rather than a separate registry class.", ["src/xverse/maestro/bootstrap_launcher.py::OriginalBootstrapRegistry"]),
 "src/xverse/maestro/broker.py::revalidate_handle": ("src/xverse/maestro/run_broker.py::RunUnitIssuer.revalidate_issued", "mapped", "Same operation on the per-unit issuer.", ["src/xverse/maestro/launcher.py::CatalogLauncher.revalidate_issued"]),
 "src/xverse/maestro/broker.py::teardown_reverse": ("src/xverse/maestro/teardown.py::ReverseTeardown.run", "mapped", "Reverse teardown moved to its own module.", []),
 "src/xverse/maestro/coverage.py::OfflineVerifier": ("src/xverse/maestro/coverage.py::verify_closed", "mapped_candidate", "Offline verification of a closed run is a function, not a class.", ["src/xverse/maestro/coverage.py::OfflineCoverageResult"]),
 "src/xverse/maestro/coverage.py::PreClosureAssessor": ("src/xverse/maestro/coverage.py::assess_preclosure", "mapped", "Same responsibility as a function.", []),
 "src/xverse/maestro/coverage.py::derive_obligations": ("src/xverse/maestro/coverage.py::admit_coverage", "mapped_candidate", "Obligations are derived at coverage admission.", ["src/xverse/maestro/coverage.py::CoverageAdmission"]),
 "src/xverse/maestro/evidence.py::JournalAdapter": ("src/xverse/maestro/lifecycle_evidence.py::OutcomeJournal", "mapped_candidate", "The storage-worker outcome journal is the current journal adapter.", ["src/xverse/maestro/schedule_evidence.py::ScheduleJournal"]),
 "src/xverse/maestro/evidence.py::emit_annotation": ("src/xverse/maestro/lifecycle_evidence.py::OutcomeJournal.record", "mapped_candidate", "Annotations are recorded through the outcome journal.", ["src/xverse/maestro/teardown_evidence.py::TeardownJournal.record"]),
 "src/xverse/maestro/evidence.py::mirror_acknowledgement": ("src/xverse/maestro/public_blobs.py::publish_broker", "mapped_candidate", "Public mirroring of broker facts is the public-blob publication.", ["src/xverse/maestro/evidence.py::publish_export"]),
 "src/xverse/maestro/fence.py::BoundaryDescriptor": ("src/xverse/maestro/prbc.py::BoundaryDescriptor", "mapped", "Same symbol, owned by the boundary module.", []),
 "src/xverse/maestro/launcher.py::TrustedLauncher": ("src/xverse/maestro/launcher.py::CatalogLauncher", "mapped", "Renamed class with the catalog-selected frozen birth role.", ["src/xverse/maestro/bootstrap_launcher.py::OriginalBootstrapLauncher"]),
 "src/xverse/maestro/lifecycle.py::Coordinator": ("src/xverse/maestro/dispatcher.py::FiniteDispatcher", "mapped", "The finite dispatcher is the lifecycle coordinator.", []),
 "src/xverse/maestro/lifecycle.py::HealthCadence": ("src/xverse/maestro/providers.py::ProbePolicy", "mapped", "Cadence is a probe policy field set.", []),
 "src/xverse/maestro/lifecycle.py::ReadinessObservation": ("src/xverse/maestro/providers.py::ReadinessObservation", "mapped", "Same symbol in the providers module.", []),
 "src/xverse/maestro/lifecycle.py::await_readiness": ("src/xverse/maestro/providers.py::ProcessReadiness.check_health", "mapped_candidate", "Readiness is awaited through health checks on the readiness object.", ["src/xverse/maestro/providers.py::ProcessReadiness.start"]),
 "src/xverse/maestro/lifecycle.py::mutation_lock": (None, "superseded_no_equivalent", "The single original dispatcher serializes lifecycle mutations by construction; no lock symbol exists and none is proposed.", ["src/xverse/maestro/dispatcher.py::FiniteDispatcher"]),
 "src/xverse/maestro/prbc.py::CleanupOnlyCapability": ("src/xverse/maestro/prbc.py::ProcessBoundaryOps.force_cleanup", "mapped_candidate", "Cleanup-only authority is exercised as forced cleanup on the boundary.", ["src/xverse/maestro/run_closure.py::RunClosure.close"]),
 "src/xverse/maestro/prbc.py::create_frozen": ("src/xverse/maestro/prbc.py::ProcessBoundaryOps.create_frozen", "mapped", "Same operation as a method.", ["src/xverse/maestro/prbc.py::BoundaryOps.create_frozen"]),
 "src/xverse/maestro/prbc.py::observe_empty_membership": ("src/xverse/maestro/prbc.py::ProcessBoundaryOps.release_empty", "mapped_candidate", "Empty membership is observed as the precondition of release_empty.", ["src/xverse/maestro/prbc.py::ProcessBoundaryOps.residual_membership"]),
 "src/xverse/maestro/prbc.py::register_capability": ("src/xverse/maestro/prbc.py::ProcessBoundaryOps.bind_authority", "mapped_candidate", "Capability registration is authority binding on the boundary.", []),
 "src/xverse/maestro/prbc.py::residual_membership": ("src/xverse/maestro/prbc.py::ProcessBoundaryOps.residual_membership", "mapped", "Same operation as a method.", []),
 "src/xverse/maestro/prbc.py::terminate_exact_scope": ("src/xverse/maestro/prbc.py::ProcessBoundaryOps.terminate", "mapped", "Same operation as a method.", []),
 "src/xverse/maestro/projection.py::build_combined_graph": ("src/xverse/maestro/projection.py::prepare_lifecycle", "mapped_candidate", "The combined graph is built inside preparation; GraphEdge/PreparedStep are its values.", ["src/xverse/maestro/projection.py::GraphEdge"]),
 "src/xverse/maestro/projection.py::freeze_phase_action_map": ("src/xverse/maestro/projection.py::PreparedStep", "mapped_candidate", "Frozen phase/action mapping is carried per prepared step.", ["src/xverse/maestro/projection.py::prepare_lifecycle"]),
 "src/xverse/maestro/projection.py::lifecycle_digest": ("src/xverse/maestro/coverage.py::digest", "mapped_candidate", "The lifecycle digest is computed by the coverage module over the admitted lifecycle.", ["src/xverse/maestro/evidence_scope.py::runtime_admission_digest"]),
 "src/xverse/maestro/projection.py::select_binding_plan": ("src/xverse/maestro/providers.py::ProcessReadiness.bind", "mapped_candidate", "Provider binding is selected when readiness binds units.", []),
 "src/xverse/maestro/results.py::CollectionResult": ("src/xverse/maestro/artifacts.py::CollectionResult", "mapped", "Same symbol in the artifacts module.", []),
 "src/xverse/maestro/results.py::WriterStateReport": ("src/xverse/maestro/writer_closure.py::WriterClosure", "mapped_candidate", "Writer state is reported as the writer closure observation.", ["src/xverse/maestro/terminal_writer.py::TerminalWriterObservation"]),
 "src/xverse/maestro/results.py::in_memory_incomplete": ("src/xverse/maestro/writer_closure.py::unresolved", "mapped_candidate", "The incomplete in-memory state is the unresolved closure.", []),
 "src/xverse/maestro/results.py::terminal_report": ("src/xverse/maestro/terminal_runtime.py::finish_run", "mapped_candidate", "The terminal report is produced by finishing the run.", ["src/xverse/maestro/terminal_runtime.py::TerminalReceipt"]),
 "src/xverse/maestro/supervisor.py::Supervisor": ("src/xverse/maestro/supervisor.py::WorkerMonitor", "mapped", "Renamed class with the direct-child monitoring role.", []),
 "src/xverse/maestro/supervisor.py::Watchdog": ("src/xverse/maestro/supervisor.py::WorkerMonitor.watch", "mapped_candidate", "Watchdog behaviour is the monitor's watch under WatchLimits.", ["src/xverse/maestro/supervisor.py::WatchLimits"]),
 "src/xverse/maestro/supervisor.py::cancellation_latch": ("src/xverse/maestro/supervisor.py::CancellationLatch", "mapped", "Same concept as a class.", []),
 "src/xverse/maestro/supervisor.py::close_start_latch": ("src/xverse/maestro/admission.py::PermitSession.claims_closed", "mapped_candidate", "Closing the start latch corresponds to closing the start-intent claims.", ["src/xverse/maestro/run_closure.py::RunClosure.close"]),
 "src/xverse/maestro/time.py::host_monotonic": ("src/xverse/maestro/time.py::HostDeadline", "mapped_candidate", "Host-monotonic deadlines are the value type; no bare clock sampler is exported by design.", ["src/xverse/maestro/time.py::compare_host_deadline"]),
}

def resolve(target):
    if target is None: return None
    module, _, symbol = target.partition("::")
    path = ROOT / module
    if not path.is_file(): return False
    if not symbol: return True
    tree = ast.parse(path.read_text())
    cls, _, meth = symbol.partition(".")
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == cls:
            if not meth: return True
            return isinstance(node, ast.ClassDef) and any(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name == meth for m in node.body)
    return False

gap = read(GAP); matrix = read(MATRIX)
rows = []
for e in gap["endpoints"]:
    declared = e["endpoint"]
    if e["status"] == "present":
        target, confidence, rationale, alts = declared, "present", "Declared endpoint resolves unchanged.", []
    else:
        target, confidence, rationale, alts = M[declared]
    rows.append(dict(declared_endpoint=declared, gap_status=e["status"], units=e["units"], proposed_target=target,
                     confidence=confidence, rationale=rationale, alternatives=alts, proposed_target_resolves=resolve(target),
                     alternatives_resolve={a: resolve(a) for a in alts},
                     proposed_target_file_sha256=sha(ROOT / target.partition("::")[0]) if target else None))
assert len(rows) == 62 and all(r["proposed_target_resolves"] is not False for r in rows), [r for r in rows if r["proposed_target_resolves"] is False]
by_declared = {r["declared_endpoint"]: r for r in rows}
obligations = []
for s in matrix["symbol_reconciliation"]:
    # The gap record keyed endpoints by the change spec's own `proposed_endpoint` (its trusted-AST form);
    # three captured `declared_endpoint` rows differ only in that respect and are retained here verbatim.
    r = by_declared[s["proposed_endpoint"]]
    obligations.append(dict(unit_id=s["unit_id"], declared_endpoint=s["proposed_endpoint"], captured_declared_endpoint=s["declared_endpoint"],
                            captured_declared_resolves=resolve(s["declared_endpoint"]), proposed_target=r["proposed_target"],
                            confidence=r["confidence"], obligation_disposition="superseded_pending_review" if r["proposed_target"] is None else "re-bound_pending_review",
                            closed=False))
counts = {}
for r in rows: counts[r["confidence"]] = counts.get(r["confidence"], 0) + 1
record = dict(schema_version=1, revision="ML3-AFFA17-2026-10-20-endpoint-reconciliation-proposal-v1",
    author_decision=dict(id="AD-2026-10-20-b", record="author-decisions-proposed-20261020.json", record_sha256=sha(BASE / "author-decisions-proposed-20261020.json"),
                         mode="agent_proposal_under_proceed_instruction", author_approved=False),
    gap_record=dict(path=str(GAP.relative_to(ROOT)), sha256=sha(GAP)),
    change_spec_matrix=dict(path=str(MATRIX), sha256=sha(MATRIX), symbol_rows=len(matrix["symbol_reconciliation"])),
    candidate_git_head="46e0ebfd332dd833322d764191a7cfe1e008bec1", dirty_increment17=True,
    method="hand-authored semantic correspondence from the current module contracts (module docstrings and public symbols), each proposed target resolved against the current AST; no obligation closed",
    counts=dict(endpoints=len(rows), **counts, obligations=len(obligations), obligations_closed=0),
    endpoints=rows, obligations=obligations,
    authority_limits=dict(semantic_mapping_assigned=False, semantic_mapping_proposed=True, independent_review=False, accepted=False, trace_rebound=False))
with OUT.open("x") as stream:
    json.dump(record, stream, indent=2); stream.write("\n")
print(json.dumps(dict(output=str(OUT.relative_to(ROOT)), sha256=sha(OUT), counts=record["counts"],
                      unresolved_alternatives=[a for r in rows for a, ok in r["alternatives_resolve"].items() if not ok])))

# Endpoint reconciliation: independent review (2026-10-20)

Reviewer: separate agent session (Claude, independent of the mapping author).  
Reviewed proposal: `evidence/affa17/endpoint-reconciliation-proposal-20261020.json` (sha256 `80ad3bea9c75e930265fdcc5edff4ebbc98875a0b3cc2d960ff2b9d0db8556d7`).  
Method: for each of the 62 rows the proposed target and every listed alternative were read at the function/class-body level in `src/xverse/maestro/`; line references are to the worktree source as read.

Machine-readable record: `endpoint-reconciliation-independent-review-20261020.json`.

## Verdict counts

| Verdict | Rows |
| --- | --- |
| AGREE | 32 |
| AGREE_WITH_NOTE | 20 |
| PREFER_ALTERNATIVE | 1 |
| DISAGREE | 9 |
| CANNOT_JUDGE | 0 |
| Total | 62 |

## Rows not plainly agreed

### DISAGREE (9)

- **src/xverse/maestro/admission.py::fence_capability_required** (ML-SR-024-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/prbc.py::ProcessBoundaryOps.bind_authority`  
  Preferred: `src/xverse/maestro/runtime_admission.py::validate_run_admission`  
  bind_authority (prbc.py:310-332) binds an already created AF17 connection; it does not require one, and _creation_epoch tolerates an unbound authority (prbc.py:430). The admission-time requirement that the fence capability exist is enforced in runtime admission: FacilityAttestation must declare exactly FENCE_PROPERTIES (runtime_admission.py:27-30, 82-83) and the authority helper image must be pinned (198, 215-217) inside validate_run_admission, which matches the declared module role (admission) and unit ML-SR-024.

- **src/xverse/maestro/affa.py::issue_ticket** (ML-SR-009-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/run_broker.py::RunUnitIssuer.stage`  
  Preferred: `src/xverse/maestro/run_broker.py::RunBroker.release`  
  RunUnitIssuer.stage issues the native handle via K.STAGE (run_broker.py:1126-1163), not a ticket. The ticket is issued by the ARM exchange inside RunBroker.release (run_broker.py:537: ticket = issuer._native(K.ARM, deadline)); the native side generates it at run_authority.c:424-428 and AuthorityConnection._exchange retains ARMED tickets (affa_client.py:374-379). CatalogLauncher.stage likewise returns a handle, not a ticket.

- **src/xverse/maestro/artifacts.py::confined_read** (ML-SR-021-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/artifacts.py::CollectionSource.bind`  
  Preferred: `src/xverse/maestro/artifacts.py::CollectionAdmission._read`  
  CollectionSource.bind only pins the source root and constructs a CollectionAdmission (artifacts.py:159-177); it reads nothing. The confined read is CollectionAdmission._read (artifacts.py:333-372: dir_fd + O_NOFOLLOW open, regular-file and size checks, identity re-check after read), reached publicly through collect/collect_next. read_public_blob reads a sealed memfd, not a declared file.

- **src/xverse/maestro/evidence.py::mirror_acknowledgement** (ML-SR-016-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/public_blobs.py::publish_broker`  
  Preferred: `src/xverse/maestro/owner.py::_persist_intent`  
  publish_broker writes the broker projection as a public artifact (public_blobs.py:163-173); it has no relation to the Argus mirror of an M3 intent. The append+flush-before-ticket acknowledgement of ML-SR-016 is _persist_intent (owner.py:404-481: append_event -> ordinal -> flush_buffer -> flush_digest in the _Claim), and its verification against the stored mirror is OutcomeJournal._mirrors (lifecycle_evidence.py:118-145). publish_export is also unrelated (a declared export write).

- **src/xverse/maestro/lifecycle.py::mutation_lock** (ML-SR-011-U; proposal confidence `superseded_no_equivalent`)  
  Proposed: `none (superseded_no_equivalent)`  
  Preferred: `src/xverse/maestro/dispatcher.py::FiniteDispatcher.run`  
  The claim that no lock symbol exists is not supported by the code. A nonblocking mutation lock set exists: FiniteDispatcher.run acquires self._lock, facade._lock and owner._lock with acquire(False) and raises ML-SCHEDULE-CONFLICT (dispatcher.py:1205-1215); ReverseTeardown._mutation_locks names the same set plus the broker lock (teardown.py:308-311) and is acquired nonblocking in run/phase (354-357, 486-489); ReleaseOwner, RunBroker and ProcessReadiness use the same pattern (owner.py:775, 834; run_broker.py:523; providers.py:377). CancellationLatch is documented as independent of that lock (supervisor.py:52), which is exactly ML-SR-011. Propose binding to FiniteDispatcher.run as the coordinator acquisition site, citing ReverseTeardown._mutation_locks as the symbol enumerating the lock set.

- **src/xverse/maestro/prbc.py::observe_empty_membership** (ML-SR-013-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/prbc.py::ProcessBoundaryOps.release_empty`  
  Preferred: `src/xverse/maestro/prbc.py::ProcessBoundaryOps.terminate`  
  release_empty requires state already 'empty' and removes the directory (prbc.py:739-769); it does not observe emptiness. The empty-membership observation is terminate (prbc.py:714-737, docstring 'force/empty observation', sets state 'empty' at 733), and ReverseTeardown._stop reads emptiness from terminate's record (teardown.py:227-234). residual_membership (the listed alternative) returns raw members and is already bound by row 44.

- **src/xverse/maestro/prbc.py::register_capability** (ML-SR-012-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/prbc.py::ProcessBoundaryOps.bind_authority`  
  Preferred: `src/xverse/maestro/prbc.py::ProcessBoundaryOps.create_frozen`  
  bind_authority binds the AF17 epoch authority connection (prbc.py:310-332), which is not capability registration. The per-boundary capability (C1) is registered inside create_frozen (prbc.py:676-678: entry.c1 = object(); self._caps[key] = entry.c1, 'retained before any future child insertion') and checked by _authority (prbc.py:461-475), matching ML-SR-012 full-handle ordinary authority.

- **src/xverse/maestro/projection.py::lifecycle_digest** (ML-SR-001-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/coverage.py::digest`  
  Preferred: `src/xverse/maestro/projection.py::prepare_lifecycle`  
  coverage.digest is a generic canonical-JSON sha256 helper (coverage.py:40-41) used for schedule and payload digests; it does not compute the lifecycle digest. The lifecycle digest is computed by prepare_lifecycle (projection.py:639-652: sha256(DIGEST_DOMAIN + canonical body)) and carried as PreparedLifecycle.lifecycle_digest (projection.py:153); admit_coverage merely embeds that value (coverage.py:210). runtime_admission_digest is a different digest.

- **src/xverse/maestro/projection.py::select_binding_plan** (ML-SR-002-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/providers.py::ProcessReadiness.bind`  
  Preferred: `src/xverse/maestro/projection.py::prepare_lifecycle`  
  ProcessReadiness.bind registers a launcher/handle pair in the readiness view at runtime (providers.py:259-287) and has nothing to do with catalog plan selection. ML-SR-002 (exactly one admissible catalog plan per executable binding) is enforced in prepare_lifecycle: each binding must resolve exactly one catalog entry, build_lifecycle_plan must be plannable and artifact pins must agree (projection.py:316-338).

### PREFER_ALTERNATIVE (1)

- **src/xverse/maestro/lifecycle.py::await_readiness** (ML-SR-007-U, ML-SR-008-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/providers.py::ProcessReadiness.check_health`  
  Preferred: `src/xverse/maestro/providers.py::ProcessReadiness.start`  
  check_health is the cadence scan over already released units (providers.py:446-473). Awaiting readiness is ProcessReadiness.start: it checks live prerequisites via DependencyGuard (399-402), releases, then loops bounded probe attempts until ready (404-418), which is ML-SR-007 start-step completion; check_health remains the ML-SR-008 cadence endpoint.

### AGREE_WITH_NOTE (20)

- **src/xverse/maestro/admission.py::Admission** (ML-SR-005-U, ML-SR-024-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/admission.py::PermitSession`  
  PermitSession (admission.py:514-584) validates the whole permit set, rejects durably consumed permits (admission.py:561-566) and owns the start-intent claims, so it carries the ML-SR-005 admission role; the ML-SR-024 run/facility/pin binding lives in runtime_admission.py::validate_run_admission (runtime_admission.py:163-245), which row 4 already binds.

- **src/xverse/maestro/affa.py::FenceAuthority** (ML-SR-009-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/affa_client.py::AuthorityConnection`  
  AuthorityConnection (affa_client.py:68-459) is the original-process handle to the native AF17 authority: it holds epoch history, issued tickets, _starts_closed/_revoked and revoke. The authority logic itself runs in native/run_authority.c; GateConnection (owner.py:75-146) remains the legacy per-unit RG06 gate for the non-broker path.

- **src/xverse/maestro/affa.py::ReleaseEpoch** (ML-SR-009-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/affa_client.py::AuthorityEpochAdvance`  
  AuthorityEpochAdvance (affa_client.py:46-65) is the retained ADVANCED receipt consumed by ProcessBoundaryOps.admit_epoch (prbc.py:334-366). The monotonic epoch value itself is exposed as ProcessBoundaryOps.release_epoch (prbc.py:368-371) and AuthorityConnection.epoch (affa_client.py:138-144); a re-bound ML-SR-009 trace should cite those alongside the receipt.

- **src/xverse/maestro/affa.py::cancel** (ML-SR-009-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/affa_client.py::AuthorityConnection.revoke`  
  revoke (affa_client.py:408-447) is the fail-closed cancellation: it sets _revoked/_starts_closed, latches cancel and SIGKILLs the authority child. The protocol-level cancel is RunBroker.cancel issuing K.CANCEL (run_broker.py:888-903, native reason 5/6) with revoke as fallback (905-918); ReleaseOwner.cancel only cascades (owner.py:761-769).

- **src/xverse/maestro/affa.py::consume_ticket** (ML-SR-010-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/owner.py::ReleaseOwner.release`  
  ReleaseOwner.release delegates to RunBroker.release when a broker is bound (owner.py:824-827), and RunBroker.release performs ARM then RELEASE with the ticket (run_broker.py:537-549); the native helper consumes it exactly once (native/run_authority.c:430-434, ticket_state 1->2). The legacy path consumes the RG06 ticket inside ReleaseOwner.release itself (owner.py:850-876).

- **src/xverse/maestro/api.py::assess_lifecycle** (ML-SR-017-U, ML-SR-023-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/coverage.py::assess_preclosure`  
  assess_preclosure (coverage.py:823-826) is the pure provisional assessment over _Assessment. ML-SR-017 requires a dual provisional/offline assessment, so verify_closed (coverage.py:847-942) should be cited with it rather than treated as a mere alternative.

- **src/xverse/maestro/api.py::collect** (ML-SR-021-U, ML-SR-022-U, ML-SR-023-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/runtime_service.py::RuntimeService.collect`  
  RuntimeService.collect (runtime_service.py:242-244) resolves to _OriginalRuntimeRun.collect, which returns the retained dispatch collection without new effects (runtime_entry.py:199-203), satisfying the idempotent retained collect of ML-SR-022. The actual collection work is collection_runtime.collect_outputs (collection_runtime.py:212-293).

- **src/xverse/maestro/api.py::reconcile** (ML-SR-014-U, ML-SR-023-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/recovery.py::IssuerRecovery.reconcile`  
  IssuerRecovery.reconcile (recovery.py:301-484) revalidates surviving launchers/handles and persists a snapshot. The public entry is RuntimeService.replace_controller -> FiniteDispatcher.replace_controller -> ControllerSession.reconcile (controller.py:277-305), which wraps IssuerRecovery.

- **src/xverse/maestro/broker.py::IssueRegistry** (ML-SR-010-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/run_broker.py::RunBroker.issuers`  
  RunBroker.issuers (run_broker.py:488-491) exposes the current issuer per unit; the registry state is _issuers/_generation_issuers with log pins (run_broker.py:365-370, 444-448). OriginalBootstrapRegistry is a run registry, not an issue registry.

- **src/xverse/maestro/coverage.py::derive_obligations** (ML-SR-017-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/coverage.py::admit_coverage`  
  admit_coverage derives the obligation templates at admission (coverage.py:217: body['templates']=_templates(body)); the derivation helper is _templates (coverage.py:103-128) and CoverageAdmission.data re-verifies them (146-147).

- **src/xverse/maestro/evidence.py::JournalAdapter** (ML-SR-016-U, ML-SR-018-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/lifecycle_evidence.py::OutcomeJournal`  
  OutcomeJournal adapts both the M3 journal (permits._journal) and the Argus writer (lifecycle_evidence.py:61-79, 99-116, 274-298). ScheduleJournal and TeardownJournal are sibling adapters for schedule and teardown records.

- **src/xverse/maestro/evidence.py::emit_annotation** (ML-SR-004-U, ML-SR-016-U, ML-SR-019-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/lifecycle_evidence.py::OutcomeJournal.record`  
  OutcomeJournal.record emits v2.0 annotations through its inner mirror() (lifecycle_evidence.py:300-321). Annotation emission is distributed: ScheduleJournal._append/_payload (schedule_evidence.py:177, 252) cover ML-SR-004 scheduling annotations, evidence.record_validation (evidence.py:90-118) the validation annotation, and TeardownJournal.record the teardown ones.

- **src/xverse/maestro/launcher.py::TrustedLauncher** (ML-SR-010-U; proposal confidence `mapped`)  
  Proposed: `src/xverse/maestro/launcher.py::CatalogLauncher`  
  CatalogLauncher (launcher.py:322-723) validates the recipe against the owner and stages the frozen birth. In the broker path the per-unit issuer role is RunUnitIssuer over the native authority (run_broker.py:950+); OriginalBootstrapLauncher launches the supervisor, not units.

- **src/xverse/maestro/prbc.py::CleanupOnlyCapability** (ML-SR-010-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/prbc.py::ProcessBoundaryOps.force_cleanup`  
  force_cleanup is where the separate cleanup-only authority is exercised: _authority(entry, reservation=True) accepts the reservation capability when no C1 exists (prbc.py:461-475, 780, 797). The capability itself is represented by BoundaryAdmission.cleanup_approval_ref/reservation_approval_ref (prbc.py:85-86) and _Entry.reservation, with no public capability class; RunClosure.close is a broader orchestration and not preferred.

- **src/xverse/maestro/projection.py::build_combined_graph** (ML-SR-002-U, ML-SR-003-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/projection.py::prepare_lifecycle`  
  The combined graph is built inside prepare_lifecycle through the inner _project/edge helpers and _order (projection.py:211-229, 459-465); GraphEdge is only the value type.

- **src/xverse/maestro/projection.py::freeze_phase_action_map** (ML-SR-004-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/projection.py::PreparedStep`  
  PreparedStep carries the frozen per-step phase/action pair (projection.py:117-128). The phase-to-operation map is the module constant OPERATIONS enforced at projection.py:27-33, 352-355, and deterministic eligibility is PreparedLifecycle.eligible_steps (159-208); a re-bound ML-SR-004 trace should cite those.

- **src/xverse/maestro/results.py::WriterStateReport** (ML-SR-018-U, ML-SR-020-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/writer_closure.py::WriterClosure`  
  WriterClosure (writer_closure.py:11-25) reports before/after writer state, abort usability and durable reader status, matching ML-SR-018. TerminalWriterObservation (terminal_writer.py:8-26) is the terminal-report variant with finalize fields; both should be cited for ML-SR-020.

- **src/xverse/maestro/supervisor.py::Watchdog** (ML-SR-009-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/supervisor.py::WorkerMonitor.watch`  
  WorkerMonitor.watch/_watch apply operation/term/kill deadlines with TERM then KILL (supervisor.py:232-370). The native lease watchdog ('independent-watchdog' fence property, runtime_admission.py:29; native/lease_guard.c) is a separate mechanism not covered by this row.

- **src/xverse/maestro/supervisor.py::close_start_latch** (ML-SR-019-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/admission.py::PermitSession.claims_closed`  
  claims_closed (admission.py:673-675) exposes the latched state; the closing transition on journal failure is _claims_closed = True in revalidate_start_intent/public_start_intent/claim_start_intent/_claim_selected (admission.py:635, 664, 703, 821) and claim_start_intent refuses with ML-PERMIT-CLOSED (681-685). In the owner/persistence path the same closure is ReleaseOwner._closed plus cancel on intent failure (owner.py:803-806) and PersistenceClient._fail (persistence.py:746-757); a re-bound ML-SR-019 trace should cite claim_start_intent with the flag.

- **src/xverse/maestro/time.py::host_monotonic** (ML-SR-015-U; proposal confidence `mapped_candidate`)  
  Proposed: `src/xverse/maestro/time.py::HostDeadline`  
  HostDeadline (time.py:50-59) is the session-bound monotonic value type and compare_host_deadline its comparator; the module samples no clock by design (time.py:1). Callers sample time.monotonic() directly (for example owner.py:57), so no sampler endpoint exists to bind.

## Scope statement

This review assesses semantic correspondence only and closes no obligation, assigns no acceptance and verifies no runtime behaviour.

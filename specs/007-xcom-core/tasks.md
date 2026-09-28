# Tasks: X-COM core communication and validation

**Input**: Design documents from `specs/007-xcom-core/`

**Execution rule**: ADR-0020 requires repository-owned Spec Kit work products and exact-candidate
evidence for all future production software changes; SESN is not used. Codex implements only the authorized
bounded slice, records review findings before a later repair pass, and presents the complete software and
evidence bundle for explicit user acceptance before another feature begins.

## Phase 1: Governance and specification

- [X] T001 Record the platform-first delivery decision in Constitution 2.0.0 and ADR-0018.
- [X] T002 Record X-COM observation/stimulation ownership in ADR-0019.
- [X] T003 Complete the specification, requirements checklist, and clarification record.
- [X] T004 Complete research, data model, contracts, plan, tasks, analysis, and REF-002 traceability.
- [X] T005 Conduct and record a separate architecture review of this design package.
- [X] T006 Obtain user acceptance of the design and explicit implementation authorization; record
  the later execution-workflow amendment in ACC015 and ADR-0020.

## Phase 2: Repository-owned engineering baseline

- [X] T007 Establish separate, bounded task ownership for the C++ core, XDL compiler, observation,
  stimulation, integration/evidence, and independent-review work; bind every slice to its exact baseline
  and authorization.
- [X] T008 Maintain and review stakeholder/system/software requirements and bidirectional
  requirement/design/code/test/measure traceability.
- [X] T009 Maintain and review architecture, boundaries, component/sequence diagrams, and cross-language
  contracts.
- [X] T010 Maintain and review unit design, ownership, lifetime, thread-safety, failure semantics, bounds,
  and Doxygen plan.
- [X] T011 Pin and admit the compiler, build, `nlohmann/json`, gRPC/Protocol Buffers, static-analysis,
  sanitizer, and Doxygen environment with licenses, hashes, generated-code provenance, and a
  reproducible/offline strategy.

## Phase 3: Core communication foundation (US1)

- [X] T012 Add CMake/CTest targets and warning-as-error rules under `src/xverse/xcom/`.
- [X] T013 Implement immutable contract, item, origin, time, correlation, diagnostic, and policy types.
- [X] T014 Implement bounded endpoint/route lifecycle and exact generation-bound ownership handles.
- [X] T015 Implement explicit provider composition and the owned loopback provider.
- [X] T016 Add unit and negative tests for interaction kinds, capabilities, policy, ownership, lifecycle,
  queue bounds, deterministic diagnostics, and recovery.

## Phase 4: XDL-derived activation plan (US1)

- [X] T017 Define and validate `io.xverse.xcom` Profile v0.1 and the canonical activation-plan v1
  schema and digest/provenance contract.
- [X] T018 Implement deterministic Profile-aware plan compilation in `src/xverse_xdl/xcom_plan.py`.
- [X] T019 Implement bounded C++ plan decoding and independent version/digest/capability checks.
- [X] T020 Add ordering-equivalence, malformed-plan, drift, bound, and regression tests.

## Phase 5: Observation boundary (US2)

- [X] T021 Implement immutable observation records, filters, payload policy, and tap handles.
- [X] T022 Implement bounded best-effort drop/coalesce and explicit lossless-validation modes.
- [X] T023 Implement the synthetic sink and prove failure/disconnect isolation and visible counters.
- [X] T024 Test metadata-only zero-payload behavior, controlled payload views, redaction/truncation state,
  ordering, saturation, degraded validity, and safe detach.

## Phase 6: Validation stimulation boundary (US3)

- [X] T025 Implement the explicit time-authority interface, local validation permit
  validation/consumption, and bounded session lifecycle.
- [X] T026 Specify and implement bounded durable stimulation intent/outcome journaling without
  unrestricted payload logs, including journal-before-emission ordering, atomic/partial-write behavior,
  finite capacity and retention, disk-full/I/O failure, restart recovery, and evidence-incomplete outcomes.
- [X] T027 Implement the fail-closed pre-emission guard for schema, target, direction, action, time, quota,
  loop, service ownership, permit/session identity, revocation, and expiry; rejection must not mutate
  operational state or emit a normal-route item.
- [X] T028 Implement guarded signal/message injection, service invocation, and exclusive generation-bound
  service emulation, plus drain, close, revoke, expiry, and evidence-incomplete lifecycle completion.
- [ ] T029 Test the complete permit/action mismatch matrix, journal-before-emission and journal
  failure/recovery, zero emission after every rejection, persistent synthetic provenance, unmapped clocks,
  quotas, loop bounds, lease conflicts, drain/terminal behavior, and deterministic concurrency.

## Phase 7: External-tool gateway and conformance (US4)

- [ ] T030 Define the versioned gRPC/Protocol Buffers tool API under
  `proto/xverse/xcom/v1/tool_gateway.proto` with additive evolution rules.
- [ ] T031 Implement a local-IPC-only gateway with no TCP listener, bounded messages/streams, deadlines,
  flow control, safe logs, and disconnect cleanup.
- [ ] T032 Implement a separate-process synthetic client and generated-client contract tests for
  observation and every allowed stimulation action.
- [ ] T033 Build reusable provider, observer, stimulation-tool, and gateway contract suites.
- [ ] T034 Add a second minimal synthetic provider implementation to prove replaceability and version
  rejection; verify adapter failures do not affect unrelated routes.

## Phase 8: Evidence, documentation, and acceptance

- [ ] T035 Run full C++ unit/contract/integration/negative/concurrency/sanitizer/static checks and all
  existing Python tests; retain repository-owned manifests, bounded logs, tool/environment identity,
  commands, outcomes, and hashes bound to the exact candidate revision.
- [ ] T036 Run controlled benchmarks and record environment, uncertainty, baseline, disabled/enabled
  tap results, and explicit non-production limitations.
- [ ] T037 Add complete Doxygen comments and generate warning-free reference documentation.
- [ ] T038 Validate Spec Kit plus REF-002 requirements/design/code/test traceability and public-safe
  logs/evidence; do not promote allocated or deferred SADS targets without proof.
- [ ] T039 Conduct an independent read-only review in a separate context, record every finding before
  repair, and disposition findings without weakening required acceptance criteria; any repair creates a
  successor candidate and repeats affected verification and review.
- [ ] T040 Assemble and inspect the complete repository-owned exact-candidate work-product and evidence
  bundle, including traceability, dependency/generated-code provenance, command results, manifests, hashes,
  maintenance guidance, and limitations.
- [ ] T041 Present the implemented software and inspected evidence bundle to the user and record explicit
  acceptance or rework.

## Dependencies and execution order

T001–T004 precede architecture review. T005–T006 and the ACC015/ADR-0020 workflow amendment gate all
future software work. T007–T011 precede production code. T012–T016 establish the core. T017–T020 bind it
to XDL. Observation and stimulation may be implemented as separately owned tasks after the core, but both
precede conformance and final integration. T025 must have an accepted successor before T026. Within the
stimulation slice, T026 and the T027 pre-emission guard precede every T028 action path; T029 closes the
slice. T035–T041 require all selected implementation tasks. No later platform or legacy feature begins
before T041.

Tasks modifying overlapping C++ headers or build files must be dependency-ordered. Parallel tasks may own
only disjoint paths. Every implementation and verification result must identify its exact baseline or
candidate revision. No task may execute a legacy binary or external network peer.

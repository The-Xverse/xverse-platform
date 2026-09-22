# Tasks: X-COM core communication and validation

**Input**: Design documents from `specs/007-xcom-core/`

**Execution rule**: All production software artifacts are generated through SESN. Codex supplies this
package, reviews every SESN result, and does not manually repair generated production code. The user
validates the complete software and assurance bundle before another feature begins.

## Phase 1: Governance and specification

- [X] T001 Record the platform-first delivery decision in Constitution 2.0.0 and ADR-0018.
- [X] T002 Record X-COM observation/stimulation ownership in ADR-0019.
- [X] T003 Complete the specification, requirements checklist, and clarification record.
- [X] T004 Complete research, data model, contracts, plan, tasks, analysis, and REF-002 traceability.
- [X] T005 Conduct and record a separate architecture review of this design package.
- [X] T006 Obtain user acceptance of the design and explicit implementation authorization.

## Phase 2: SESN engineering baseline

- [ ] T007 Submit a bounded SESN feature with separate C++ core, XDL compiler, observation, stimulation,
  integration/evidence, and independent-review tasks.
- [ ] T008 Generate and review SWE.1 requirements and bidirectional requirement/test traceability.
- [ ] T009 Generate and review SWE.2 architecture, boundaries, and component/sequence diagrams.
- [ ] T010 Generate and review SWE.3 unit design, ownership, lifetime, thread-safety, and Doxygen plan.
- [ ] T011 Pin the compiler, build, `nlohmann/json`, gRPC/Protocol Buffers, static-analysis, sanitizer,
  and Doxygen environment with licenses, hashes, generated-code provenance, and a reproducible/offline
  strategy.

## Phase 3: Core communication foundation (US1)

- [ ] T012 Add CMake/CTest targets and warning-as-error rules under `src/xverse/xcom/`.
- [ ] T013 Implement immutable contract, item, origin, time, correlation, diagnostic, and policy types.
- [ ] T014 Implement bounded endpoint/route lifecycle and exact generation-bound ownership handles.
- [ ] T015 Implement explicit provider composition and the owned loopback provider.
- [ ] T016 Add unit and negative tests for interaction kinds, capabilities, policy, ownership, lifecycle,
  queue bounds, deterministic diagnostics, and recovery.

## Phase 4: XDL-derived activation plan (US1)

- [ ] T017 Define and validate `io.xverse.xcom` Profile v0.1 and the canonical activation-plan v1
  schema and digest/provenance contract.
- [ ] T018 Implement deterministic Profile-aware plan compilation in `src/xverse_xdl/xcom_plan.py`.
- [ ] T019 Implement bounded C++ plan decoding and independent version/digest/capability checks.
- [ ] T020 Add ordering-equivalence, malformed-plan, drift, bound, and regression tests.

## Phase 5: Observation boundary (US2)

- [ ] T021 Implement immutable observation records, filters, payload policy, and tap handles.
- [ ] T022 Implement bounded best-effort drop/coalesce and explicit lossless-validation modes.
- [ ] T023 Implement the synthetic sink and prove failure/disconnect isolation and visible counters.
- [ ] T024 Test metadata-only zero-payload behavior, controlled payload views, redaction/truncation state,
  ordering, saturation, degraded validity, and safe detach.

## Phase 6: Validation stimulation boundary (US3)

- [ ] T025 Implement the explicit time-authority interface, local validation permit
  validation/consumption, and bounded session lifecycle.
- [ ] T026 Implement durable stimulation intent/outcome journaling without unrestricted payload logs.
- [ ] T027 Implement signal/message injection, service invocation, and exclusive lease-bound service
  emulation.
- [ ] T028 Implement schema/target/action/time/quota checks, loop protection, service-ownership exclusion,
  revocation, expiry, drain, and evidence-incomplete handling.
- [ ] T029 Test that every rejected or unauthorized request emits zero normal-route items and every
  accepted item preserves synthetic provenance; test unmapped clocks and lease conflicts.

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
  existing Python tests.
- [ ] T036 Run controlled benchmarks and record environment, uncertainty, baseline, disabled/enabled
  tap results, and explicit non-production limitations.
- [ ] T037 Add complete Doxygen comments and generate warning-free reference documentation.
- [ ] T038 Validate Spec Kit plus REF-002 requirements/design/code/test traceability and public-safe
  logs/evidence; do not promote allocated or deferred SADS targets without proof.
- [ ] T039 Have SESN run the independent Astra review and disposition every finding without weakening
  required acceptance criteria.
- [ ] T040 Export and inspect the complete SESN report and artifact bundle.
- [ ] T041 Present the generated software/evidence to the user and record acceptance or rework.

## Dependencies and execution order

T001–T004 precede architecture review. T005–T006 gate all software work. T007–T011 precede production
code. T012–T016 establish the core. T017–T020 bind it to XDL. Observation and stimulation may be
implemented as separate SESN tasks after the core but both precede conformance and final integration.
T035–T041 require all selected implementation tasks. No later platform or legacy feature begins before
T041.

Tasks modifying overlapping C++ headers or build files must be dependency-ordered in SESN. Parallel
tasks may own only disjoint paths. No task may execute a legacy binary or external network peer.

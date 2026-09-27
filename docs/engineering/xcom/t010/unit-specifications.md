# T010 Unit Specifications — Designed Unit Contracts and Validator Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T010 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `abb81681e0d844edaecbaf2843f1c2a7deb1e40f` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Implementation artifacts | `docs/engineering/xcom/t010/unit-design.json`, `docs/engineering/xcom/t010/design-units.md`, `scripts/validate_xcom_unit_design.py` |

## 2. Scope, language, and conventions

T010 is a documentation/governance task. It has two unit sets:

- **Designed units** (`XCOM-DU-001`–`030`) — the capability-007 implementation units whose ownership,
  lifetime, thread-safety, failure semantics, bounds, and Doxygen obligations T010 specifies. Their full
  catalogues are `detailed-design.md` §5–§10; §4 below is the per-unit specification summary.
- **T010 work-product units** (`U-*`) — the offline validator units T010 itself implements. §3 specifies
  them.

Conventions:

- All identifiers are stable ASCII tokens; all ordering is declared and deterministic.
- The model is a JSON document plus a derived Markdown projection; the validator is a Python 3.11-compatible
  script under `scripts/` (the only executable artifact, and not under `src/`, `tests/`, or `xdl/`).
- Designed-unit languages follow the accepted plan: C++20 for the data plane/boundary/edge units, Python 3.11
  for the XDL compiler and the offline tooling, JSON for schema/model artifacts, Protocol Buffers for the tool
  API, Markdown for documentation/evidence units.
- "Lifetime" for the T010 work-product units is the process lifetime of a single validator invocation; the
  model has no runtime state.
- **Thread-safety (T010 work-product units)**: T010 units are offline and single-threaded. Concurrency is not
  applicable; the validator must not spawn threads or subprocesses. This is an explicit design decision, not a
  gap. Thread-safety for the *designed* units is first-class content (§4).
- **Doxygen (T010 work-product units)**: not applicable to T010's own artifacts; T010 owns the Doxygen plan
  for the designed C++ units (§4, `detailed-design.md` §10, FR-029) and adds no public C/C++ interface.

**Resource and concurrency bounds (all T010 work-product units).** Inputs are read-only, repository-relative,
each ≤ 1 MiB and ≤ 4 MiB total, including the `docs/engineering/xcom/task-ownership.json`,
`docs/engineering/xcom/t008/requirements-register.json`, and
`docs/engineering/xcom/t009/architecture-model.json` dependencies. No network, no subprocess, no filesystem
writes. Wall-clock bound ≤ 60 s, single-threaded, deterministic output.

## 3. T010 work-product units

### U-MODEL — Unit-design model, canonical serialization, and projection

- **Responsibility.** Hold the top-level model, validate its fixed field set, closed vocabularies, and counts,
  and produce the byte-stable JSON and Markdown projections (including the per-family unit tables, the
  ownership/lifetime/thread-safety/bounds/failure catalogues, and the Doxygen plan section).
- **Interface.** `load(path) -> Model`; `serialize(Model) -> bytes`; `project_markdown(Model) -> str`.
- **Invariants.** `schema_version == 1`; fixed top-level/per-record field sets and key order; every unit and
  invariant `id` a non-empty string; the `units` and `invariants` arrays sorted by `id` with unique ids; the
  fixed vocabularies equal their declared sets; `counts` matches the entries; two serializations byte-identical;
  output ends in exactly one trailing newline; no timestamp/host/absolute path.
- **Failure semantics.** Malformed JSON, a missing top-level field, a non-string or unhashable `id`, an
  unsorted or duplicate-id array, a vocabulary mismatch, or a count mismatch yields `SCHEMA_INVALID` (2),
  never a partial output or an uncaught type error. Serialization/projection failure yields
  `DETERMINISM_INVALID` (11).
- **Lifetime/ownership.** Immutable value model; owned by the validator invocation.
- **Requirements.** T010-SR-001, T010-SR-014.
- **Planned evidence.** CHK-01, CHK-02, CHK-16, ORD-01, DET-01, DET-02, NEG-01..NEG-05, NEG-40.

### U-UNIT — Unit identity, ownership, lifetime, and artifact anchoring

- **Responsibility.** Validate each unit's identity, family/kind/language/scope/maturity, owning slice and
  task set, artifact paths and their tree status, requirement links, governing ADRs, and its ownership and
  lifetime contract.
- **Interface.** `validate_units(model, tree, task_ownership, requirement_register) -> Result`.
- **Invariants.** Ids unique and patterned `XCOM-DU-###`; the required id set exactly present; family/kind/
  language/scope/maturity closed; `owning_slice`/`owning_tasks` consistent with the T007 register; every unit
  has ≥ 1 artifact path tagged `established`/`planned`; `established` paths exist and `planned` paths are
  absent; ownership/lifetime models closed with non-empty rationales; `view_lifetime` present and non-`n/a`
  iff the unit exposes a view; mutating units declare an issued-handle or platform-owned rule;
  `requirement_links` non-empty and each resolving in the T008 register; `governing_adrs` ⊆ `adr_vocabulary`.
- **Failure semantics.** Duplicate id, wrong pattern, unknown token, missing mandatory field, or no artifact
  path → `IDENTITY_INVALID` (3); a missing/contradictory ownership or lifetime declaration → `OWNERSHIP_INVALID`
  (4); a path-status inconsistency → `PATH_INVALID` (13); a dangling requirement link → `BINDING_INVALID` (10).
- **Lifetime/ownership.** Pure except bounded tree/path checks and the register read.
- **Requirements.** T010-SR-002, T010-SR-003, T010-SR-011.
- **Planned evidence.** CHK-03, CHK-04, CHK-15, NEG-06..NEG-09, NEG-12..NEG-16, NEG-20, NEG-37, NEG-42, NEG-43.

### U-THREAD — Thread-safety and concurrency contract

- **Responsibility.** Validate each unit's thread-safety model, shared mutable state, synchronization
  mechanism or message-passing/process boundary, and borrowed-view lifetime consistency.
- **Interface.** `validate_thread_safety(model) -> Result`.
- **Invariants.** `thread_safety.model` closed with a non-empty rationale; `shared_state` non-empty only for
  `internally-synchronized`/`externally-synchronized`/`message-passing` and empty for `immutable-value`,
  `read-only-static`, `single-thread-owner`, `offline-single-threaded`, and `process-isolated`; `synchronization`
  non-null for the three synchronizing models and null for the five non-synchronizing models;
  `internally-synchronized` requires a named mechanism; `message-passing` requires a capacity bound and a
  declared policy.
- **Failure semantics.** A missing model, unknown model token, a non-empty `shared_state` on a
  non-synchronizing model (including `single-thread-owner`/`immutable-value`), a non-null `synchronization` on a
  non-synchronizing model, an `internally-synchronized` model without a mechanism, a message-passing unit
  without a capacity bound, or a `process-isolated` unit declaring shared state → `THREAD_INVALID` (5). The
  exposed-view lifetime field is
  validated by `U-UNIT` under the ownership/lifetime contract (`OWNERSHIP_INVALID`, 4).
- **Lifetime/ownership.** Pure.
- **Requirements.** T010-SR-004.
- **Planned evidence.** CHK-05, NEG-10, NEG-17..NEG-19, NEG-18b, NEG-19b.

### U-BOUND — Finite resource bounds and overflow policy

- **Responsibility.** Validate that every unit declares finite bounds with kinds, sources, optional values,
  and the overflow policy set required by its bound kinds.
- **Interface.** `validate_bounds(model) -> Result`.
- **Invariants.** ≥ 1 bound per unit; kinds closed (no `unbounded` member); at most one bound per
  `(kind, resource)`; `configured == true`; `value` null or a non-negative integer; a `retry` bound is `0`
  unless the plan explicitly permits one; a `thread-count` bound ≥ 1; `overflow_policies` non-empty and equal
  to `["n/a"]` iff no capacity/quota/depth/rate bound exists.
- **Failure semantics.** Missing bound, negative/non-integer value, capacity/quota/depth/rate bound without an
  overflow policy set, `["n/a"]` alongside such a bound, or a permitted non-zero retry → `BOUNDS_INVALID` (6).
- **Lifetime/ownership.** Pure.
- **Requirements.** T010-SR-005.
- **Planned evidence.** CHK-06, NEG-21..NEG-24.

### U-FAIL — Failure semantics and outcome honesty

- **Responsibility.** Validate each unit's condition → outcome mapping, the unknown-outcome rule, the
  evidence-incomplete obligation, and the synthetic-provenance classification.
- **Interface.** `validate_failure(model) -> Result`.
- **Invariants.** `failure_semantics` non-empty with outcomes from the closed vocabulary; a unit with an
  asynchronous, journaled, externally observable, or tool-driven path maps `unknown` to a non-success outcome
  and declares `evidence-incomplete`; a rejection mutates no operational state; synthetic provenance is
  preserved through routing/observation.
- **Failure semantics.** Missing failure semantics, unknown outcome token, `unknown → accepted/delivered`, or a
  journal/write unit without `evidence-incomplete` → `FAILURE_INVALID` (7).
- **Lifetime/ownership.** Pure.
- **Requirements.** T010-SR-006.
- **Planned evidence.** CHK-07, NEG-11, NEG-25..NEG-27.

### U-DOXY — Doxygen plan and per-unit documentation obligation

- **Responsibility.** Validate the Doxygen plan and every unit's documentation obligation.
- **Interface.** `validate_doxygen(model) -> Result`.
- **Invariants.** The plan declares the admitted configuration, `WARN_AS_ERROR`, the mandatory file block, the
  mandatory public tags (including the ownership/lifetime/thread-safety/failure aliases), one group per family,
  the coverage rule, and the known gaps with owning tasks; every `cpp` unit is `required = true` with a group
  from the plan, the mandatory tags, and equal public/documented element counts; every non-`cpp` unit is
  `required = false` with a reason; no gap is reported as closed.
- **Failure semantics.** A `cpp` unit missing a mandatory tag or group, a plan without the warning-as-error
  rule, an element-coverage mismatch, or a non-`cpp` unit claiming an obligation → `DOXYGEN_INVALID` (8).
- **Lifetime/ownership.** Pure.
- **Requirements.** T010-SR-007.
- **Planned evidence.** CHK-08, NEG-28..NEG-30.

### U-COVER — Cross-resolution, coverage, and exemptions

- **Responsibility.** Resolve unit→component/contract references into the T009 model and prove requirement and
  component coverage in both directions, including the validity of declared exemptions.
- **Interface.** `validate_coverage(model, architecture_model, requirement_register) -> Result`.
- **Invariants.** Every `component_refs`/`contract_refs` id resolves; every non-exempt T009 component is
  covered by ≥ 1 unit; every non-exempt `XCOM-SW-*` requirement is covered by ≥ 1 unit; every exemption is
  real (its target is genuinely uncovered), reasoned, and task-owned; the required unit set is exactly present.
- **Failure semantics.** A dangling component/contract reference, an uncovered non-exempt component or
  requirement, a duplicate/invalid exemption, or a missing/extra required unit → `BINDING_INVALID` (10).
- **Lifetime/ownership.** Bounded reads of two dependency files; otherwise pure.
- **Requirements.** T010-SR-008, T010-SR-009.
- **Planned evidence.** CHK-09, CHK-10, NEG-37, NEG-39, NEG-44..NEG-46.

### U-GOV — Governance, neutrality, maturity, and REF-002 non-promotion

- **Responsibility.** Validate governing-ADR references, REF-002 non-promotion, dependency direction, core
  domain neutrality, and maturity/reconciliation honesty.
- **Interface.** `validate_governance(model, task_ownership) -> Result`.
- **Invariants.** Every governing ADR ∈ `adr_vocabulary`; `ref002.disposition == "unchanged"` with an empty
  `promoted` list; no `implemented` record for a deferred/allocated/unreconciled target; `implemented`
  requires a 40-hex accepted revision and `partial`-unreconciled requires a reason; the dependency-direction,
  neutrality, and safety invariants are present and enforced; no core-layer unit names a domain primitive.
- **Failure semantics.** Unknown ADR, promoted REF-002 target, unproven `implemented`, unreconciled `partial`
  without a reason, reverse dependency, or core domain primitive → `GOVERNANCE_INVALID` (9).
- **Lifetime/ownership.** Pure except the bounded register read.
- **Requirements.** T010-SR-010.
- **Planned evidence.** CHK-11, NEG-31..NEG-34.

### U-BIND — Baseline, authorization, and fail-closed dependencies

- **Responsibility.** Verify the exact baseline, the closed authorization/ADR sets, and the presence,
  readability, size, and well-formedness of the three dependencies; enforce the public-safety content rule.
- **Interface.** `validate_binding(model, deps) -> Result`; `scan_public_safety(text) -> Result`.
- **Invariants.** `baseline_revision` 40 lowercase hex; the candidate-revision rule present;
  `authorization_records` equals the T007 closed set; `adr_vocabulary` closed; every artifact path tagged
  `established`/`planned`; the three dependency files present, readable, ≤ 1 MiB each, ≤ 4 MiB total, and
  well-formed; no credential, secret, private address, private-key marker, proprietary excerpt, unrestricted
  payload, or absolute host path in the model, projection, or output.
- **Failure semantics.** Malformed baseline, unknown authorization reference, dangling link, unavailable or
  malformed dependency → `BINDING_INVALID` (10), never a pass; prohibited content →
  `PUBLIC_SAFETY_INVALID` (12); unreadable or over-bound input → `IO_ERROR` (14).
- **Lifetime/ownership.** Bounded reads of three dependency files; otherwise pure.
- **Requirements.** T010-SR-011, T010-SR-013.
- **Planned evidence.** CHK-12, CHK-13, CHK-14, NEG-35, NEG-36, NEG-38, NEG-41.

### U-SAFE — Work-product boundary preservation

- **Responsibility.** Enforce the work-product boundary rule and the review/acceptance separation of the T010
  candidate.
- **Interface.** `validate_boundary(paths) -> Result` (invoked by the gate and the implementation record).
- **Invariants.** The candidate diff contains no `src/`, `tests/`, `xdl/`, or `proto/` path; no `Doxyfile`,
  CMake, or build file change; no accepted ADR/contract or other task's work product edit; no requirement or
  test weakened; the T007 ownership validator still passes after the consistency update; no acceptance or
  integration claim and no other task checkbox marked.
- **Failure semantics.** A prohibited path or weakened artifact is reported by the deterministic gate and the
  implementation record (`CHK-18`); T010 never converts either into a pass.
- **Lifetime/ownership.** Pure.
- **Requirements.** T010-SR-012, T010-STK-008.
- **Planned evidence.** CHK-18, BND-01, BND-06, deterministic gate.

### U-VALIDATE — Validator driver and self-test

- **Responsibility.** Provide the CLI, run all checks in precedence order, provide the controlled self-test,
  and emit a bounded deterministic report.
- **Interface.** CLI `--self-test`, `--verify`, `--check-human`; `run_all(model, deps) -> Result`.
- **Invariants.** Deterministic exit and output for identical input; lowest numeric exit class when several
  apply; no network, subprocess, or write; bounded reads and runtime; the self-test covers every NEG case with
  a passing positive fixture, and every check function (`_check_model_schema`, `_check_counts`,
  `_check_ordering`, `_check_identity`, `_check_ownership`, `_check_thread_safety`, `_check_bounds`,
  `_check_failure`, `_check_doxygen`, `_check_coverage`, `_check_governance`, `_check_dependencies`,
  `_check_binding`, `_check_paths`, `_check_determinism`, `_scan_public_safety`) is independently
  exercised.
- **Failure semantics.** Distinct nonzero exit per class (`detailed-design.md` §12.1); unreadable or over-bound
  input → `IO_ERROR` (14).
- **Lifetime/ownership.** One invocation; single-threaded; no shared state.
- **Requirements.** T010-SR-014.
- **Planned evidence.** CHK-16, CHK-17, CHK-18, `--self-test`, DET-02..DET-04.

## 4. Designed-unit specification summary

Each unit's normative contract is its model record; the catalogues are `detailed-design.md` §5–§10. This
section gives the per-unit specification summary. Status abbreviations: `ownership/lifetime` uses the model
vocabulary; `TS` is the thread-safety model.

### 4.1 CORE — contract, item, diagnostic, lifecycle, provider units

| Unit | Responsibility | Requirements | Ownership / lifetime | TS | Key failure outcomes | Bounds | Doxygen | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-001` | Typed value and bounded payload view | XCOM-SW-CORE-002, -004 | caller-owns-value / invocation-scoped | immutable-value | rejected, failed, unknown→failed | bytes (view size), capacity (elements) | `xcom_core`, mandatory tags, view lifetime documented | T013 unit/negative tests |
| `XCOM-DU-002` | Versioned contract and logical-identity descriptor | XCOM-SW-CORE-001, -003 | platform-owns-shared / plan-scoped | immutable-value | rejected, failed | bytes (descriptor) | `xcom_core`, mandatory tags | T012 unit/negative tests |
| `XCOM-DU-003` | Item identity, origin, timestamps, correlation/causation | XCOM-SW-CORE-002, -003, -010 | caller-owns-value / invocation-scoped | immutable-value | rejected, failed, unknown→failed | bytes, capacity | `xcom_core`, provenance + lifetime documented | T013 unit/negative tests |
| `XCOM-DU-004` | Stable diagnostic codes and deterministic ordering | XCOM-SW-CORE-006, -010 | caller-owns-value / invocation-scoped | immutable-value | rejected, failed | bytes | `xcom_core`, severity/phase/reason/correction documented | T013 unit/negative tests |
| `XCOM-DU-005` | Result/outcome type and core type aggregate | XCOM-SW-CORE-003, -004 | caller-owns-value / invocation-scoped | immutable-value | rejected, failed, unknown→failed | bytes | `xcom_core`, outcome semantics documented | T013 unit/negative tests |
| `XCOM-DU-006` | Endpoint/route lifecycle with generation-bound handles | XCOM-SW-CORE-003, -004, -005 | provider-issued-handle / endpoint-generation | internally-synchronized | rejected (stale/foreign handle), failed, unknown→failed | capacity (endpoints/routes), retry 0 | `xcom_core`, handle/generation + thread-safety documented | T014 unit/negative/concurrency tests |
| `XCOM-DU-007` | Provider boundary and explicit composition | XCOM-SW-CORE-005, -007, -008 | provider-issued-handle / process-scoped | externally-synchronized | rejected (capability/version), failed | capacity (providers), retry 0 | `xcom_core`, composition thread-safety documented | T015/T033/T034 contract tests |
| `XCOM-DU-008` | Owned loopback provider | XCOM-SW-CORE-007, -009 | provider-issued-handle / process-scoped | single-thread-owner | rejected (policy violation), failed | capacity (in-flight queue), retry 0 | `xcom_core`, deterministic-loopback contract documented | T016 loopback/negative tests |

### 4.2 XDL — Profile compiler, activation-plan schema, bounded decode

| Unit | Responsibility | Requirements | Ownership / lifetime | TS | Key failure outcomes | Bounds | Doxygen | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-009` | Deterministic Profile-aware plan compilation (Python) | XCOM-SW-XDL-001, -002 | caller-owns-value / process-scoped | offline-single-threaded | rejected, failed, unknown→failed | bytes (input), capacity (nodes/edges) | n/a (Python tooling; docstrings covered by `check_doxygen.py`) | `tests/test_xcom_plan.py` |
| `XCOM-DU-010` | Canonical activation-plan v1 schema and digest contract | XCOM-SW-XDL-001 | task-owns-artifact / static-immutable | read-only-static | rejected | bytes (schema) | n/a (JSON artifact) | schema validation + T020 tests |
| `XCOM-DU-011` | Bounded activation-plan decode with independent version/digest checks | XCOM-SW-XDL-003, XCOM-SW-CORE-003 | caller-owns-value / plan-scoped | immutable-value | rejected, failed, unknown→failed | bytes, capacity, depth | `xcom_xdl`, digest/bounds/lifetime documented | T019/T020 decode/bound/drift tests |

### 4.3 OBS — observation record, payload policy, bounded queue, sink

| Unit | Responsibility | Requirements | Ownership / lifetime | TS | Key failure outcomes | Bounds | Doxygen | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-012` | Immutable observation record and payload-view policy | XCOM-SW-OBS-001, -002, -005 | platform-owns-shared / route-scoped | immutable-value | rejected (policy absent/over bound, truncation recorded) | bytes (view size), capacity (record) | `xcom_obs`, metadata-only default + view lifetime documented | T021/T024 tests |
| `XCOM-DU-013` | Bounded observer queue, drop/coalesce counters, synthetic sink | XCOM-SW-OBS-003, -004 | platform-owns-shared / route-scoped | message-passing | drop/coalesce surfaced in counters; isolated observer failure; unknown→failed | capacity (queue depth), quota (coalesce window), retry 0 | `xcom_obs`, counters + saturation + isolation documented | T022/T023/T024 tests |

### 4.4 STIM — time authority, session, journal, guard, actions

| Unit | Responsibility | Requirements | Ownership / lifetime | TS | Key failure outcomes | Bounds | Doxygen | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-014` | Explicit time authority with clock-domain mapping and tolerance | XCOM-SW-STIM-006 | platform-owns-shared / session-scoped | externally-synchronized | rejected (unmapped/out-of-tolerance), expired | timeout (read), deadline (tolerance) | `xcom_stim`, clock-domain + thread-safety documented | accepted T025 tests + T029 |
| `XCOM-DU-015` | Validation permit and bounded session lifecycle | XCOM-SW-STIM-001, -002 | session-issued-handle / session-scoped | internally-synchronized | rejected, expired, quota rejected | capacity, rate, quota, deadline | `xcom_stim`, permit/handle + lifetime documented | accepted T025 tests + T029 |
| `XCOM-DU-016` | Durable stimulation intent/outcome journal | XCOM-SW-STIM-007 | platform-owns-shared / session-scoped | internally-synchronized | evidence-incomplete (write/fsync/disk), unknown→evidence-incomplete | bytes, capacity (retention) | `xcom_stim`, journal ordering + partial-write + recovery documented | T026/T029 journal tests |
| `XCOM-DU-017` | Fail-closed pre-emission guard | XCOM-SW-STIM-004, -005, -006 | session-issued-handle / session-scoped | internally-synchronized | rejected (all mismatches, zero emission, no state mutation) | quota, depth (loop window), rate | `xcom_stim`, rejection matrix + no-mutation rule documented | T027/T029 guard tests |
| `XCOM-DU-018` | Guarded injection and exclusive service-emulation lease | XCOM-SW-STIM-001, -003, -008, -009 | session-issued-handle / endpoint-generation | internally-synchronized | rejected/cancelled/expired, evidence-incomplete, unknown→evidence-incomplete | capacity (leases), depth (drain), deadline | `xcom_stim`, synthetic provenance + lease lifecycle documented | T028/T029 action tests |

### 4.5 GW — tool API, local-IPC gateway, synthetic client

| Unit | Responsibility | Requirements | Ownership / lifetime | TS | Key failure outcomes | Bounds | Doxygen | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-019` | Versioned gRPC/Protocol Buffers tool API with additive evolution | XCOM-SW-GW-001 | task-owns-artifact / static-immutable | read-only-static | rejected (unknown field/version) | bytes, capacity (streams) | n/a (proto; generated-code policy is `DOX-GAP-02`) | T030 proto/evolution tests |
| `XCOM-DU-020` | Local-IPC-only gateway session with deadlines and flow control | XCOM-SW-GW-001, -002 | gateway-issued-handle / session-scoped | internally-synchronized | rejected, expired, failed, evidence-incomplete | capacity, bytes, deadline, timeout, rate | `xcom_gw`, no-TCP + bounds + disconnect-documented | T031/T032/T033 tests |
| `XCOM-DU-021` | Separate-process synthetic tool client | XCOM-SW-GW-002, -003 | gateway-issued-handle / process-scoped | externally-synchronized | expired, failed, evidence-incomplete | deadline, timeout, bytes | `xcom_gw`, client lifecycle + disconnect documented | T032 contract tests |

### 4.6 INTG — documentation, traceability, evidence, benchmark

| Unit | Responsibility | Requirements | Ownership / lifetime | TS | Key failure outcomes | Bounds | Doxygen | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-022` | Doxygen documentation, aliases, and warning gate | XCOM-SW-INTG-002 | task-owns-artifact / document-scoped | offline-single-threaded | failed (missing docstring/Doxygen warning/unavailable tool) | bytes, thread-count 1, timeout | n/a (owns the plan and gate; `DOX-GAP-01`/`03`) | T037 Doxygen + self-test |
| `XCOM-DU-023` | Requirements/traceability validation | XCOM-SW-INTG-002, XCOM-SW-ENB-001 | task-owns-artifact / document-scoped | offline-single-threaded | failed (dangling link/unavailability) | bytes, thread-count 1 | n/a (Python tooling) | T038 traceability validation |
| `XCOM-DU-024` | Public-safe evidence bundle and manifests | XCOM-SW-INTG-001 | task-owns-artifact / document-scoped | offline-single-threaded | failed (prohibited content/absent evidence) | bytes, thread-count 1 | n/a (evidence documents) | T035/T038/T040 public-safety scans |
| `XCOM-DU-025` | Controlled disabled-tap benchmark evidence | XCOM-SW-INTG-003 | task-owns-artifact / document-scoped | offline-single-threaded | failed (environment/uncertainty missing) | bytes, deadline (run), timeout | `xcom_intg`, benchmark harness contract documented | T036 benchmark run |

### 4.7 ENB — enabler models, admission, review

| Unit | Responsibility | Requirements | Ownership / lifetime | TS | Key failure outcomes | Bounds | Doxygen | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `XCOM-DU-026` | Requirement register and REF-002 disposition model | XCOM-SW-ENB-001, -002 | task-owns-artifact / document-scoped | offline-single-threaded | failed (schema/promotion defect) | bytes, thread-count 1 | n/a (JSON work product) | T008 validator + self-test |
| `XCOM-DU-027` | Architecture, boundary, and contract model | XCOM-SW-ENB-001 | task-owns-artifact / document-scoped | offline-single-threaded | failed (schema/resolution defect) | bytes, thread-count 1 | n/a (JSON work product) | T009 validator + self-test |
| `XCOM-DU-028` | Unit-design model and Doxygen plan | XCOM-SW-ENB-001 | task-owns-artifact / document-scoped | offline-single-threaded | rejected/failed (schema/coverage defect) | bytes, thread-count 1 | n/a (JSON work product) | T010 validator + self-test |
| `XCOM-DU-029` | Dependency admission and build lock | XCOM-SW-ENB-004 | task-owns-artifact / document-scoped | offline-single-threaded | failed (unadmitted version/hash/license) | bytes, thread-count 1 | n/a (admission documents) | T011 preflight + review |
| `XCOM-DU-030` | Independent review and acceptance record | XCOM-SW-ENB-003 | task-owns-artifact / document-scoped | offline-single-threaded | failed (unresolved BLOCKER/MAJOR) | bytes, thread-count 1 | n/a (review records) | T039 review, T041 acceptance |

## 5. Requirement-to-unit trace

| Requirement | Units |
| --- | --- |
| T010-SR-001 | U-MODEL |
| T010-SR-002 | U-UNIT |
| T010-SR-003 | U-UNIT |
| T010-SR-004 | U-THREAD |
| T010-SR-005 | U-BOUND |
| T010-SR-006 | U-FAIL |
| T010-SR-007 | U-DOXY |
| T010-SR-008 | U-COVER |
| T010-SR-009 | U-COVER |
| T010-SR-010 | U-GOV |
| T010-SR-011 | U-UNIT, U-BIND |
| T010-SR-012 | U-SAFE |
| T010-SR-013 | U-BIND |
| T010-SR-014 | U-MODEL, U-VALIDATE |

## 6. Cross-cutting contract summary

| Dimension | Declared rule | Model field(s) | Enforcing check |
| --- | --- | --- | --- |
| Ownership | one owning slice/task set per unit; only an exact issued handle mutates an active resource | `owning_slice`, `owning_tasks`, `ownership_model`, `ownership_rationale` | CHK-03, CHK-04 |
| Lifetime | a closed lifetime model per unit; bounded view lifetime when a view is exposed | `lifetime_model`, `lifetime_rationale`, `exposes_view`, `view_lifetime` | CHK-04 |
| Thread-safety | a closed thread-safety model; non-empty shared state implies `internally-synchronized`/`externally-synchronized`/`message-passing`; `synchronization` non-null exactly for those three models | `thread_safety.model`, `shared_state`, `synchronization` | CHK-05 |
| Bounds | ≥ 1 finite bound per unit with kind, source, and null-or-integral value | `bounds[]`, `overflow_policies` | CHK-06 |
| Failure | classified condition → outcome; unknown never success; evidence-incomplete where required | `failure_semantics[]` | CHK-07 |
| Doxygen | mandatory file block and public tags; equal public/documented element counts; plan gaps explicit | `doxygen`, `doxygen_plan` | CHK-08 |
| Traceability | requirement/component/contract links resolve; coverage total modulo real exemptions | `requirement_links`, `component_refs`, `contract_refs`, `coverage` | CHK-09, CHK-10 |

No T010 work-product unit publishes a C/C++ interface, so T010 owes no Doxygen unit contract for its own
artifacts; the Doxygen obligations for the designed production units are specified in §4 and owned by the
implementation slices as executed through `XCOM-DU-022` and T037.

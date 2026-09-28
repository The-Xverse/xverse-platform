# T007 Requirements — Bounded Task Ownership and Exact Baseline/Authorization Binding

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T007 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Predecessor tasks | T005 (separate architecture review, review 012) and T006 (user acceptance ACC001–ACC015, ADR-0020) |
| Successor tasks | T008–T011 (remaining engineering-baseline enablers) then the six implementation/review slices T012–T041 |
| Requirement ID families | `T007-STK-###` (stakeholder), `T007-SR-###` (software) |
| Authority | the T007 entry in `specs/007-xcom-core/tasks.md`; `specs/007-xcom-core/spec.md` FR-030 and FR-035; Constitution 2.1.0 articles X and the capability acceptance gates; ADR-0018, ADR-0019, ADR-0020; ACC012/ACC015 |
| Classification | Public-safe engineering work product |

### 1.1 Authority statement

This document specifies only the bounded T007 slice. T007 **establishes task ownership and the
baseline/authorization binding**. It adds **no** C++ core, XDL compiler, observation, stimulation,
gateway, integration, or test implementation, and it approves, completes, or integrates **no** other
task. It is a repository-owned work-product task: it may change documentation and governance artifacts
only, and the deterministic gate (see `verification-plan.md` §2) rejects any T007 change under `src/`,
`tests/`, or `xdl/`.

The register T007 defines is the ownership authority that T008 (requirements/traceability), T009
(architecture), T010 (unit design, ownership, lifetime, thread-safety, failure semantics, bounds, and
Doxygen plan), and every implementation/review slice consume. T007 does not weaken any accepted
requirement, test, ADR, or safety boundary.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the constitution,
or an accepted ADR is resolved in favour of the accepted source. A material gap is reported rather than
guessed. Unresolved gaps are recorded in §9.

## 2. Scope

### 2.1 In scope (bounded T007)

A repository-owned **task-ownership register** that:

1. **Names the six bounded work slices** required by T007 — C++ core, XDL compiler, observation,
   stimulation, integration/evidence, and independent-review — plus the engineering-baseline enabler
   tasks T008–T011.
2. **Assigns every capability-007 task T007–T041** to exactly one slice (or to the engineering-baseline
   enabler group) with no gaps and no double ownership.
3. **Binds each slice to an exact baseline revision** (`923a6db65aafbcdbf33a1461e93622777e902deb`)
   and to an **exact authorization record** (ACC001–ACC015, ADR-0018/0019/0020, and the capability
   specification status).
4. **Declares path ownership**: exclusive paths per slice, shared build/specification paths that require
   serialized dependency-ordered writers, and prohibited paths/actions (legacy repositories, network
   peers, TCP listeners, legacy execution).
5. **Declares the dependency order and gates** so no successor task starts before its predecessor is
   verified and accepted, and no slice weakens another.
6. **Maps each slice to its required evidence and acceptance gate**, including the separate read-only
   review and explicit user acceptance required by ADR-0020.
7. **Records honest reconciliation state** for tasks whose source already exists in the baseline but is
   not accepted (T012–T016, T021–T024), never treating source presence as acceptance proof.
8. **Defines a deterministic, public-safe serialization and validator** so the register is machine
   checkable and reproducible offline.

### 2.2 Explicit exclusions (must remain absent from the T007 candidate)

No production or test source is created or modified; no `src/`, `tests/`, or `xdl/` path is changed; no
compilation, linking, runtime execution, benchmark, or dependency retrieval occurs; no legacy repository
is read or written; no external network peer, package manager, or TCP listener is used; no accepted ADR
or test is weakened; no other task is marked complete; no software candidate is accepted or integrated;
no SESN artifact is created, rewritten, or extended.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T007 |
| --- | --- | --- |
| Stakeholder/system/software requirements and bidirectional traceability | T008 | allocated (register binds T008 to the traceability slice) |
| Architecture, boundaries, component/sequence diagrams, cross-language contracts | T009 | allocated |
| Unit design, ownership, lifetime, thread-safety, failure semantics, bounds, Doxygen plan | T010 | allocated |
| Compiler/build/`nlohmann/json`/gRPC/Protocol Buffers/static-analysis/sanitizer/Doxygen environment admission | T011 | allocated |
| Core, XDL, observation, stimulation, gateway implementation | T012–T034 | allocated to their slices |
| Full verification, benchmarks, Doxygen, traceability, evidence bundle | T035–T038, T040 | allocated to integration/evidence |
| Independent read-only review and explicit user acceptance | T039, T041 | allocated to independent-review |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths.** T007 changes documentation only. The T007 candidate adds
`docs/engineering/xcom/t007/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`,
the canonical register `docs/engineering/xcom/task-ownership.{md,json}`, and
`scripts/validate_xcom_task_ownership.py`; in the implementation stage it also updates the T007 entry in
`specs/007-xcom-core/tasks.md`. The **affected product source paths are none**: no `src/`, `tests/`, or
`xdl/` path is created or changed (T007-SR-013). The paths T007 *governs* are enumerated in
`architecture.md` §5.

**Negative cases.** T007-SR-002..011 each name the negative case(s) that must fail: missing/extra slice
(NEG-01/NEG-02), unassigned/double-assigned task (NEG-03/NEG-04), invalid baseline (NEG-05), unknown
authorization (NEG-06), duplicate exclusive path (NEG-07), undeclared shared path (NEG-08), dependency
cycle (NEG-09), reversed enabler→core ordering (NEG-10), missing evidence/gate (NEG-11), missing
prohibition in a slice (NEG-12), unproven `accepted` label (NEG-13), broken T-CORE→T-XDL /
T-{XDL,OBS,STIM}→T-INTG / T-INTG→T-REVIEW ordering (NEG-14/NEG-15/NEG-16), missing minimum top-level
prohibition (NEG-17), overlapping exclusive directory prefixes (NEG-18), empty exclusive set (NEG-19), and
an unreserved per-task artifact (NEG-20).

**Concurrency and resource bounds.** T007 has no runtime concurrency: the register is a static document
and the validator is offline and single-threaded, so no concurrency case is defined. Applicable resource
bounds are input ≤ 1 MiB per file and ≤ 4 MiB total, no network/subprocess, wall clock ≤ 60 s, and
byte-stable deterministic output. Production concurrency/resource bounds belong to the implementation
slices. See `verification-plan.md` §6.

## 3. Terminology and measurement

| Term | Meaning in T007 |
| --- | --- |
| Slice | A bounded work boundary with one or more owning tasks and an exclusive path set. |
| Enabler | An engineering-baseline task (T008–T011) that precedes all implementation slices. |
| Ownership register | The canonical human- and machine-readable ownership artifact T007 produces. |
| Exclusive path | A path pattern owned by exactly one slice. |
| Shared path | A build/specification path that several slices must edit; access is serialized and dependency-ordered. |
| Baseline binding | The exact Git revision a slice's authorized work is based on. |
| Authorization binding | The exact accepted decision record(s) that permit the slice's bounded work. |
| Reconciliation | Comparing an existing baseline artifact against an accepted candidate revision without assuming acceptance. |
| Unreconciled | Source is present in the baseline but no accepted exact-candidate evidence exists. |
| Deterministic serialization | A byte-stable canonical ordering that yields identical output across runs and hosts. |

Measurements are discrete and observable: slice/task counts, disjointness results, dependency-edge
counts, validator exit status, and byte-level register contents. No availability, throughput, timing, or
probability figure is asserted; none is derivable from the accepted capability and none is invented.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-030, FR-035, FR-026, FR-027, FR-028 | normative behaviour and safety boundary |
| Task entry | `specs/007-xcom-core/tasks.md` T007–T041 and the dependency-order section | authorized bounded scope and slice tasks |
| Accepted plan | `specs/007-xcom-core/plan.md` (delivery phases, project structure, decision gates) | slice decomposition and path layout |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles X and the capability acceptance gates | traceability and acceptance obligations |
| ADRs | ADR-0018 (platform-first), ADR-0019 (X-COM observation/stimulation ownership), ADR-0020 (repository-owned workflow) | sequencing, ownership, evidence, and review |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC001–ACC015 | exact authorization references |
| Reviews | `docs/reviews/012-xcom-core-design-review.md`, `docs/reviews/015-…`, `docs/reviews/016-…` | design review and open reconciliation finding A12/XCOM-NOSESN-08 |
| REF-002 register | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` | dispositions and traceability duty |
| Baseline provenance | `git log` for `src/xverse/xcom/**`, `tests/xcom/**`, `scripts/validate_xcom_*.py` | existing-artifact reconciliation only |

## 5. Stakeholder requirements

### T007-STK-001 — Separate, bounded ownership for every work slice

**Statement.** Capability 007 must have explicit, separate ownership for the C++ core, XDL compiler,
observation, stimulation, integration/evidence, and independent-review work, such that every task has
exactly one accountable slice and no workstream is left unnamed.

**Acceptance criteria (observable).**

- AC-1: The register names exactly the six required slices and the engineering-baseline enabler group.
- AC-2: Every task T007–T041 appears under exactly one slice/enabler group.
- AC-3: No task is unassigned and no task is assigned twice.
- AC-4: A reviewer can determine, from the register alone, which slice owns a given path and task.

**Source anchors.** `tasks.md` T007; `plan.md` "Delivery phases" and "Project Structure".

### T007-STK-002 — Exact baseline and authorization binding

**Statement.** Every slice must be bound to its exact baseline revision and to the exact accepted
authorization record that permits its bounded work, so no work proceeds on an unspecified revision or an
inferred authorization.

**Acceptance criteria (observable).**

- AC-1: Every slice records `authorized_baseline = 923a6db65aafbcdbf33a1461e93622777e902deb`.
- AC-2: Every slice records at least one resolvable authorization reference (ACC item and/or ADR).
- AC-3: The register states that each candidate must record its own exact revision and its accepted
  predecessor revision.
- AC-4: Missing or unresolvable baseline/authorization binding is rejected by the validator.

**Source anchors.** `tasks.md` "Every implementation and verification result must identify its exact
baseline or candidate revision"; ADR-0020 §Decision; ACC014/ACC015; Constitution art. X.

### T007-STK-003 — Dependency order and gates are preserved

**Statement.** The register must preserve the accepted dependency order — T007–T011 before production
code, T012–T016 establishing the core, T017–T020 binding it to XDL, observation/stimulation after the
core, and T039 review after the implementation slices — so a successor never starts before its
predecessor is verified and accepted.

**Acceptance criteria (observable).**

- AC-1: The dependency graph is acyclic and has a declared deterministic topological order.
- AC-2: T007–T011 precede all of T012–T041 in that order.
- AC-3: T039 (independent review) follows the implementation slices it reviews.
- AC-4: A dependency cycle or an ordering violation is rejected by the validator.
- AC-5: Every declared precedence pair is enforced by reachability, not merely by prose:
  `T-ENABLER → T-CORE`, `T-CORE → {T-XDL, T-OBS, T-STIM}`, `{T-XDL, T-OBS, T-STIM} → T-INTG`,
  `T-INTG → T-REVIEW`, and `T025 → T026`; reordering any pair while keeping the declared dependency
  lists consistent with the edge list still fails validation.

**Source anchors.** `tasks.md` "Dependencies and execution order"; ADR-0020 §Consequences.

### T007-STK-004 — Path ownership prevents conflicting edits

**Statement.** Exclusive path ownership must be disjoint across slices, and any path that several slices
must edit (build files, shared specifications) must be declared shared and subject to a serialized,
dependency-ordered writer rule, so overlapping C++ headers or build files cannot be edited concurrently
without an order.

**Acceptance criteria (observable).**

- AC-1: No path pattern appears in the exclusive set of two slices.
- AC-2: Every multi-slice path appears in the declared shared set.
- AC-3: The shared set carries an explicit serialization/ordering rule.
- AC-4: A path claimed by two exclusive sets, or a shared path not declared shared, is rejected.
- AC-5: Exclusive patterns are compared as directory prefixes (a trailing `/` marks a directory), so a
  parent pattern such as `tests/xcom/` cannot be added beside another slice's `tests/xcom/<slice>/`
  without failing validation.
- AC-6: Every slice declares a non-empty `paths_exclusive` set, and every task's per-task work-product
  directory `docs/engineering/xcom/<task>/` (including `internal-review.json` and
  `acceptance-decision.md`) and queue package `reports/xcom-queue/<task>-package.json` has exactly one
  owning slice, whose declared dependencies are satisfied before that task's run produces the artifact.

**Source anchors.** `tasks.md` "Tasks modifying overlapping C++ headers or build files must be
dependency-ordered. Parallel tasks may own only disjoint paths."; `plan.md` project structure.

### T007-STK-005 — Honest maturity and reconciliation

**Statement.** The register must distinguish accepted, unreconciled, allocated, and deferred work, and
must not treat the presence of source in the baseline as acceptance evidence or as implementation proof.

**Acceptance criteria (observable).**

- AC-1: Existing baseline artifacts for T012–T016 and T021–T024 are labelled `unreconciled` with the
  reason that their task checkboxes are open and no accepted candidate revision is recorded.
- AC-2: The accepted T025 successor is labelled with its accepted revision/commit and remains distinct
  from unreconciled work.
- AC-3: No slice is labelled `accepted` without an exact accepted candidate revision.
- AC-4: An acceptance claim without a recorded revision is rejected by the validator.

**Source anchors.** `spec.md` "Maturity"; Constitution arts. IX and X; `analysis.md` A12;
`docs/reviews/016-…` XCOM-NOSESN-08.

### T007-STK-006 — Public-safe, deterministic, reproducible register

**Statement.** The register and its validation must be deterministic and public-safe: byte-stable across
runs, free of credentials, private addresses, proprietary source excerpts, sensitive deployment values,
and absolute host paths, and reproducible offline with no network access.

**Acceptance criteria (observable).**

- AC-1: Serializing the same register twice yields byte-identical output.
- AC-2: The validator performs no network access and reads only repository-relative files.
- AC-3: A public-safety scan finds no credential, private address, or absolute host path in the register.
- AC-4: Validation is bounded in file size and runtime.

**Source anchors.** `spec.md` FR-027; Constitution art. X; ADR-0020 §Decision.

### T007-STK-007 — Independent review and user acceptance remain separate

**Statement.** The register must preserve the separate read-only review and explicit user acceptance
gates; T007 must not accept, complete, or integrate any candidate, including its own.

**Acceptance criteria (observable).**

- AC-1: The independent-review slice owns review artifacts and is ordered after the slices it reviews.
- AC-2: The register states that a passing internal review retains no unresolved finding.
- AC-3: T007 leaves every other task checkbox and every software candidate untouched.
- AC-4: T007 does not mark T007 itself complete in the plan stage.

**Source anchors.** ADR-0020 §Decision; ACC012/ACC015; `tasks.md` T039–T041.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names below are
fixed by `detailed-design.md`; the requirements state their observable contract.

### 6.1 Register model and content

#### T007-SR-001 — Canonical register model and serialization (refines T007-STK-006)

**Statement.** The register must exist as a canonical, schema-versioned model with a deterministic
serialization: a fixed top-level field set, a fixed per-slice field set, stable ordering (slices by
declared order, tasks and paths sorted), and a recorded `schema_version`.

**Acceptance criteria.** A declared top-level schema and per-slice schema are implemented; two
serializations are byte-identical; the `schema_version` is present and stable.

**Verification intent.** Determinism check CHK-09; structural check CHK-01.

#### T007-SR-002 — Exactly the six named slices plus the enabler group (refines T007-STK-001)

**Statement.** The register must define exactly these slice ids: `T-CORE`, `T-XDL`, `T-OBS`, `T-STIM`,
`T-INTG`, `T-REVIEW`, each with a title, owning task list, and purpose, plus one declared
engineering-baseline enabler group (`T-ENABLER`) covering T008–T011.

**Acceptance criteria.** All six slice ids and the enabler group are present exactly once; an extra or
missing slice fails validation.

**Verification intent.** Structural check CHK-02; negative cases NEG-01 (missing slice) and NEG-02
(extra/renamed slice).

#### T007-SR-003 — Complete, single-owner task assignment (refines T007-STK-001)

**Statement.** Every task from T007 through T041 must be assigned to exactly one slice or to the enabler
group, with no gap and no duplicate.

**Acceptance criteria.** The union of assignments equals the task set T007–T041; intersection of any two
assignments is empty; each task's owning slice is resolvable.

**Verification intent.** Structural check CHK-03; negative cases NEG-03 (unassigned task) and NEG-04
(double assignment).

### 6.2 Binding

#### T007-SR-004 — Exact baseline binding (refines T007-STK-002)

**Statement.** Every slice must record an exact 40-hex `authorized_baseline`, must record that
successor candidates bind their own exact revision and accepted predecessor revision, and the register
must reject a non-40-hex or empty baseline.

**Acceptance criteria.** Every slice baseline equals the run baseline; a malformed baseline fails
validation; the candidate-revision rule is stated once and referenced by every slice.

**Verification intent.** Structural check CHK-04; negative case NEG-05 (missing/invalid baseline).

#### T007-SR-005 — Exact authorization binding (refines T007-STK-002)

**Statement.** Every slice must record at least one authorization reference from the accepted set
(ACC001–ACC015, ADR-0018, ADR-0019, ADR-0020) and the register must reject an empty or unresolvable
reference.

**Acceptance criteria.** Every slice lists ≥ 1 resolvable authorization reference; an empty or unknown
reference fails validation.

**Verification intent.** Structural check CHK-04; negative case NEG-06 (unknown authorization ref).

### 6.3 Paths and dependencies

#### T007-SR-006 — Path-ownership classification and disjointness (refines T007-STK-004)

**Statement.** Every slice must declare `paths_exclusive` (owned only by that slice) and may declare
`paths_shared`; exclusive path patterns must be pairwise disjoint across slices under directory-prefix
semantics, every exclusive set must be non-empty, every task's per-task work-product directory and queue
package report must be reserved to exactly one slice, and shared patterns must appear in the declared
`shared_paths` list.

**Acceptance criteria.** No path pattern is in two exclusive sets; no exclusive directory prefix contains
another slice's exclusive pattern; no exclusive set is empty; every task's
`docs/engineering/xcom/<task>/` and `reports/xcom-queue/<task>-package.json` has exactly one owner; every
multi-slice pattern is in the shared list; a violation fails validation.

**Verification intent.** Disjointness check CHK-05; ownership check CHK-15; negative cases NEG-07
(duplicate exclusive path), NEG-08 (undeclared shared path), NEG-18 (overlapping directory prefixes),
NEG-19 (empty exclusive set), and NEG-20 (unreserved per-task artifact).

#### T007-SR-007 — Serialized shared-path rule (refines T007-STK-004)

**Statement.** The register must declare the shared build/specification paths (root `CMakeLists.txt`,
`src/xverse/xcom/CMakeLists.txt`, `cmake/*`, `specs/007-xcom-core/*`) and state that only one slice edits
a shared path at a time, in dependency order, under the owning task's candidate and evidence.

**Acceptance criteria.** The shared list is non-empty and names the build/specification paths; the
serialization rule is stated; a shared path missing from the list fails validation.

**Verification intent.** Structural check CHK-08.

#### T007-SR-008 — Acyclic dependency graph and deterministic order (refines T007-STK-003)

**Statement.** Slices and tasks must declare dependencies forming a directed acyclic graph; the register
must expose a deterministic topological order; T007–T011 must precede T012–T041; T039 must follow the
implementation slices it reviews.

**Acceptance criteria.** No cycle; a stable topological order exists; the declared precedence pairs in
T007-STK-003 AC-5 hold by reachability and a reordered graph still fails validation; a cycle or ordering
violation fails validation.

**Verification intent.** Dependency check CHK-06; negative cases NEG-09 (cycle), NEG-10 (reversed
enabler→core), NEG-14 (T-XDL only on T-ENABLER), NEG-15 (T-INTG only on T-ENABLER), and NEG-16
(T-REVIEW only on T-ENABLER), each keeping the declared dependency lists consistent with the edge list.

### 6.4 Evidence, safety, reconciliation

#### T007-SR-009 — Evidence and acceptance gate mapping (refines T007-STK-007)

**Statement.** Every slice must map to a required-evidence list and an acceptance gate, and the
`T-REVIEW` slice must own the separate read-only review and explicit user acceptance gates.

**Acceptance criteria.** Every slice has ≥ 1 evidence item and a named gate; `T-REVIEW` names the review
and user-acceptance gates; a missing gate fails validation.

**Verification intent.** Structural check CHK-07; negative case NEG-11 (missing evidence/gate).

#### T007-SR-010 — Prohibited-action and safety boundary per slice (refines T007-STK-007)

**Statement.** Every slice must declare prohibited actions including, at minimum, no legacy-repository
modification, no legacy execution, no external network peer, and no TCP listener; the register must
declare these four as top-level global invariants in `global_prohibitions` and reject a register whose
top-level list omits any of them or a slice that omits them.

**Acceptance criteria.** The top-level `global_prohibitions` is a superset of the four minimum
prohibitions; each slice lists the four minimum prohibitions; the global invariant is stated; an omission
at either level fails validation.

**Verification intent.** Safety check CHK-10; negative cases NEG-12 (missing prohibition in a slice) and
NEG-17 (missing minimum prohibition in the top-level list).

#### T007-SR-011 — Reconciliation state (refines T007-STK-005)

**Statement.** The register must record, per slice, the reconciliation status of its tasks using a
closed vocabulary (`accepted`, `unreconciled`, `allocated`, `deferred`) and must justify each
non-`allocated` status with a recorded revision or task-list state; the register must not label
`accepted` any task without an exact accepted revision.

**Acceptance criteria.** T012–T016 and T021–T024 are `unreconciled` with the open-checkbox reason; T025
is `accepted` with its accepted revision; no unproven `accepted` label exists; an unproven acceptance
fails validation.

**Verification intent.** Reconciliation check CHK-11; negative case NEG-13 (unproven `accepted`).

#### T007-SR-012 — Deterministic validator with self-test (refines T007-STK-006)

**Statement.** A repository-owned validator script must check the register against T007-SR-002..011,
provide a self-test over controlled positive and negative fixtures, be deterministic, offline, and
bounded, and expose a distinct nonzero exit per failure class.

**Acceptance criteria.** The validator passes the real register; its self-test exercises every negative
case; it performs no network access; file and runtime bounds hold; the same input yields the same exit
and output.

**Verification intent.** Validator/self-test cases described in `verification-plan.md` §4–§5.

### 6.5 Boundary

#### T007-SR-013 — Docs-only boundary for the T007 candidate (refines T007-STK-001, T007-STK-007)

**Statement.** The T007 candidate must change only work-product/governance documentation and must not
change, create, or delete any path under `src/`, `tests/`, or `xdl/`, and must not modify an accepted ADR
or weaken an existing requirement or test.

**Acceptance criteria.** `git diff --name-only <baseline>` for the T007 candidate contains no `src/`,
`tests/`, or `xdl/` path; no accepted ADR text is edited; `git diff --check` is clean.

**Verification intent.** Boundary check CHK-12 and the deterministic gate in `verification-plan.md` §2.

#### T007-SR-014 — Public-safe register content (refines T007-STK-006)

**Statement.** The register, the human-readable projection, and the validator output and retained
evidence must contain no credentials, secrets, private addresses, proprietary source excerpts,
unrestricted payloads, or absolute host paths. The documented external deterministic-gate invocation
path in `verification-plan.md` §2 is workflow infrastructure, not register content, and is out of scope
of this content rule.

**Acceptance criteria.** A public-safety scan of the register, projection, and validator output finds
none of the prohibited content classes; the scan is reproducible.

**Verification intent.** Public-safety check CHK-13.

## 7. Capability 007 requirement links

| Capability anchor | T007 disposition and link | Remaining work |
| --- | --- | --- |
| FR-030 requirement→design→code→test traceability, unit/contract/integration/performance evidence, separate architecture review | **Implemented (governance)**: T007-STK-001–004, T007-SR-001–012 establish ownership, baseline/authorization binding, path ownership, dependency order, and evidence/review gate mapping. | T008–T010 own the requirement/design/unit work products; T035–T041 produce the software evidence and review. |
| FR-035 REF-002 accounting | **Implemented for this slice**: dispositions in §8; no REF-002 disposition is promoted. | Per-slice dispositions remain with their owning tasks. |
| FR-026 normal use requires no discovery/secrets/legacy access | **Partial (constraint)**: T007-SR-010 declares the prohibition per slice. | Enforced at runtime by the implementation slices and verified by T035/T038. |
| FR-028 owned loopback/synthetic fixtures only | **Partial (constraint)**: T007-SR-010 prohibits legacy execution and external peers. | Enforced by each slice's candidate and evidence. |
| Constitution art. X reproducibility/traceability | **Implemented (governance)**: T007-SR-004, SR-005, SR-011, SR-012, SR-014. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T007 is a governance/ownership task and implements **no** direct REF-002 communication requirement
XVE-SYS-0139–0158. It changes no disposition; every capability-007 disposition recorded in
`specs/007-xcom-core/reference-traceability.md` remains exactly as accepted. T007 adds only
traceability-governance duty.

| REF-002 group | Disposition in T007 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — no new disposition; the capability-007 allocation/deferment table remains authoritative | T007 declares ownership and evidence gates only; it implements and demonstrates nothing. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may establish contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open item is the reconciliation of already-present source
(§9 A-1), which the register records rather than resolves.

## 9. Assumptions and open items

1. **A-1 (open reconciliation)** — `src/xverse/xcom/**`, `tests/xcom/**`, and the
   `scripts/validate_xcom_*.py` validators contain SESN-era artifacts for T012–T016 and T021–T024, but
   those task checkboxes are open and no accepted exact-candidate revision is recorded (analysis A12;
   review-016 XCOM-NOSESN-08). T007 records them as `unreconciled`; it does not relabel, delete, or
   extend them. Reconciliation against exact accepted revisions remains open and is owned by the
   applicable slices.
2. **A-2** — The accepted T025 successor is merged at `4b01586b438a8587d231ee8828d896c206c06a96`
   (implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a`), per `docs/reviews/016-…` and
   `docs/engineering/xcom/t025/acceptance-decision.md`; the register cites it as the accepted
   stimulation predecessor.
3. **A-3** — Slice, path, and status identifiers are candidate-chosen names fixed by
   `detailed-design.md`; no accepted text is contradicted.
4. **A-4** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch,
   tag, or ambient state is a valid binding.
5. **A-5** — The deterministic gate for T007 is a work-product gate that runs no C++/Python test suite;
   the T007 verification is static validation of the register and the docs-only boundary
   (`verification-plan.md` §2).

## 10. Requirement index

| Requirement | Refines | Primary units |
| --- | --- | --- |
| T007-STK-001 | — | U-REGISTER, U-SLICE, U-PATHS |
| T007-STK-002 | — | U-BIND |
| T007-STK-003 | — | U-DEPS |
| T007-STK-004 | — | U-PATHS |
| T007-STK-005 | — | U-RECON |
| T007-STK-006 | — | U-REGISTER, U-VALIDATE, U-SAFE |
| T007-STK-007 | — | U-EVID, U-SAFE |
| T007-SR-001 | STK-006 | U-REGISTER |
| T007-SR-002 | STK-001 | U-SLICE |
| T007-SR-003 | STK-001 | U-SLICE, U-REGISTER |
| T007-SR-004 | STK-002 | U-BIND |
| T007-SR-005 | STK-002 | U-BIND |
| T007-SR-006 | STK-004 | U-PATHS |
| T007-SR-007 | STK-004 | U-PATHS |
| T007-SR-008 | STK-003 | U-DEPS |
| T007-SR-009 | STK-007 | U-EVID |
| T007-SR-010 | STK-007 | U-SAFE |
| T007-SR-011 | STK-005 | U-RECON |
| T007-SR-012 | STK-006 | U-VALIDATE |
| T007-SR-013 | STK-001, STK-007 | build/gate integration (docs-only boundary) |
| T007-SR-014 | STK-006 | U-SAFE |

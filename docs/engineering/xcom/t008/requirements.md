# T008 Requirements — Stakeholder/System/Software Requirements and Bidirectional Traceability

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T008 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| Predecessor task | T007 (bounded task ownership and exact baseline/authorization binding; reviewed terminal package `957a607`) |
| Successor tasks | T009–T011 (remaining engineering-baseline enablers), then implementation slices T012–T034, integration/evidence T035–T040, and review/acceptance T039/T041 |
| Requirement ID families | `T008-STK-###` (stakeholder), `T008-SR-###` (software) |
| Authority | the T008 entry in `specs/007-xcom-core/tasks.md`; `specs/007-xcom-core/spec.md` FR-027, FR-028, FR-030, FR-035 and SC-009/SC-010; Constitution 2.1.0 articles IX and X and the capability acceptance gates; ADR-0018, ADR-0019, ADR-0020; ACC012/ACC014/ACC015; the T007 ownership register `docs/engineering/xcom/task-ownership.{md,json}` |
| Classification | Public-safe engineering work product |

### 1.1 Authority statement

This document specifies only the bounded T008 slice. T008 **maintains the capability-007 stakeholder,
system, and software requirements and their bidirectional requirement/design/code/test/measure
traceability**. It authors the requirement register and the traceability matrix from the already-accepted
Spec Kit package; it does **not** invent a new specification, change an accepted functional requirement or
success criterion, weaken an existing requirement or test, or approve any other task.

T008 is a repository-owned work-product task. Its candidate may change documentation/governance artifacts
and add one offline validator script under `scripts/`, but the deterministic gate rejects any T008 change
under `src/`, `tests/`, or `xdl/` (T008-SR-011). The register T008 produces is the traceability authority
that T009 (architecture), T010 (unit design), the implementation slices, T035–T038 (integration/evidence),
and T039/T041 (review/acceptance) consume.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the constitution, an
accepted ADR, or the T007 ownership register is resolved in favour of the accepted source. A material gap
is reported rather than guessed. Unresolved gaps are recorded in §9.

## 2. Scope

### 2.1 In scope (bounded T008)

Keep T008 strictly inside the T008 task entry, which places it in the engineering-baseline enabler group.

1. **Maintain the capability-007 requirements** as a canonical, schema-versioned register with three
   explicit levels — stakeholder (`XCOM-STK-###`), system (`XCOM-SYS-FR-###` for spec FR-001–FR-035 and
   `XCOM-SYS-SC-###` for spec SC-001–SC-011), and software (`XCOM-SW-<FAMILY>-###`) — each requirement
   uniquely identified, testable, source-anchored, and maturity-labelled.
2. **Preserve the accepted specification exactly.** System requirements correspond one-to-one with the
   accepted FR-001–FR-035 and SC-001–SC-011; the register elaborates and links them, and MUST NOT add,
   remove, renumber, relax, or restate an accepted requirement with changed meaning.
3. **Provide bidirectional requirement/design/code/test/measure traceability** for every requirement:
   refinements downward (stakeholder → system → software → design unit → source/test/measure/evidence)
   and coverage upward (every unit, test, and measure resolves back to at least one requirement).
4. **Record the REF-002 SADS disposition register** for XVE-SYS-0139–0158 exactly as accepted in
   `specs/007-xcom-core/reference-traceability.md` and `docs/architecture/sads-requirements-traceability.json`,
   promoting no allocated or deferred target to `implemented`.
5. **Preserve honest maturity** across `implemented`/`partial`/`allocated`/`deferred`/`superseded`/
   `conflicting`/`needs_clarification`, never treating source presence as acceptance, and keeping the
   T007 `unreconciled`/`allocated`/`accepted` reconciliation state consistent with the register.
6. **Provide a deterministic, public-safe, offline validator** with a controlled self-test, and re-run it
   plus the T007 ownership validator before the candidate is presented.
7. **Maintain consistency with the T007 ownership register** by declaring T008's new artifacts to the
   owning `T-ENABLER` slice and re-validating, without weakening the accepted register.

### 2.2 Explicit exclusions (must remain absent from the T008 candidate)

No production or test source is created or modified; no `src/`, `tests/`, or `xdl/` path is changed; no
compilation, linking, runtime execution, benchmark, or dependency retrieval occurs; no legacy repository
is read or written; no external network peer, package manager, or TCP listener is used; no accepted ADR,
accepted requirement, or existing test is rewritten or weakened; no other task is marked complete; no
software candidate is accepted or integrated; no SESN artifact is created, rewritten, or extended; no
target REF-002 SADS requirement is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T008 |
| --- | --- | --- |
| Architecture, boundaries, component/sequence diagrams, cross-language contracts | T009 | allocated; T008 links requirements to the accepted architecture, it does not redesign it |
| Unit design, ownership, lifetime, thread-safety, failure semantics, bounds, Doxygen plan | T010 | allocated; T008 records planned design-unit IDs only |
| Compiler/build/`nlohmann/json`/gRPC/Protocol Buffers/static-analysis/sanitizer/Doxygen admission | T011 | allocated; environment identity is a T011 deliverable, not a T008 claim |
| Core, XDL, observation, stimulation, gateway implementation | T012–T034 | allocated; T008 records planned code/test links, not implementation evidence |
| Full verification, benchmarks, Doxygen, traceability validation, evidence bundle | T035–T038, T040 | allocated; T008 supplies the register and matrix they validate and extend |
| Independent read-only review and explicit user acceptance | T039, T041 | allocated; T008 does not accept, complete, or integrate any candidate |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths.** T008 changes documentation/governance and adds one offline validator. The T008
candidate adds
`docs/engineering/xcom/t008/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`
(plan stage), `docs/engineering/xcom/t008/requirements-register.{json,md}`,
`docs/engineering/xcom/t008/traceability-matrix.{json,md}`,
`scripts/validate_xcom_requirements_traceability.py`, and `docs/engineering/xcom/t008/implementation.md`
(implementation stage). In the implementation stage it also updates the T008 checkbox in
`specs/007-xcom-core/tasks.md` and records T008's new script path in
`docs/engineering/xcom/task-ownership.{json,md}`. The **affected product source paths are none**: no
`src/`, `tests/`, or `xdl/` path is created or changed (T008-SR-011). The product paths T008 *links to*
are enumerated in `architecture.md` §5.

**Negative cases.** T008-SR-001..010 each name the negative case(s) that must fail: schema perturbation
(NEG-01), duplicate/unknown requirement id or level (NEG-02/NEG-03), missing or duplicated system FR
(NEG-04/NEG-05), missing system SC (NEG-06), orphan stakeholder (NEG-07), orphan system requirement
(NEG-08), circular refinement (NEG-09), missing REF-002 ID (NEG-10), promoted allocated/deferred REF-002
target (NEG-11), dangling traceability target (NEG-12), unknown link relation (NEG-13), forward-only link
without its reverse (NEG-14), `implemented` requirement without code/test/measure (NEG-15), `implemented`
requirement without an exact revision (NEG-16), unreconciled source present without reason (NEG-17),
malformed baseline (NEG-18), tampered markdown projection (NEG-19), prohibited public content
(NEG-20), a missing matrix top-level field (NEG-21), an established artifact with a non-SHA revision
binding (NEG-22), a planned artifact with a SHA revision binding (NEG-23), a truncated or reworded system
requirement statement (NEG-24), a duplicated link id (NEG-25), a duplicated artifact id (NEG-26), an
out-of-order requirement array (NEG-27), and an unavailable T007 ownership register (NEG-28). Each fixture
isolates one check or one declared ordering/uniqueness rule.

**Concurrency and resource bounds.** T008 has no runtime concurrency: the register and matrix are static
documents and the validator is offline and single-threaded. No concurrency case is defined. Applicable
resource bounds are input ≤ 1 MiB per file and ≤ 4 MiB total, no network/subprocess, wall clock ≤ 60 s,
and byte-stable deterministic output. Production concurrency/resource bounds belong to the implementation
slices. See `verification-plan.md` §6.

## 3. Terminology and measurement

| Term | Meaning in T008 |
| --- | --- |
| Requirement level | One of `stakeholder`, `system`, `software`, in the accepted three-level structure. |
| Register | The canonical, schema-versioned requirement model T008 produces. |
| Traceability matrix | The canonical link model connecting requirements to design/code/test/measure/evidence. |
| Refinement | A parent→child requirement relation (`refines`) forming an acyclic hierarchy. |
| Bidirectional traceability | Every parent reaches ≥1 child and every child reaches ≥1 parent, with no orphan requirement, unit, test, or measure. |
| Measure | A named verification measure (unit/contract/integration/negative/concurrency/sanitizer/static/benchmark/doxygen/traceability/review) with a status and candidate binding. |
| Artifact | A linked design unit, source path/symbol, test, measure, or evidence record with a locator, status, and revision binding. |
| Maturity | Closed vocabulary `implemented`/`partial`/`allocated`/`deferred`/`superseded`/`conflicting`/`needs_clarification`. |
| Reconciliation | Comparing an existing baseline artifact against an accepted exact-candidate revision without assuming acceptance. |
| Unreconciled | Source is present in the baseline but no accepted exact-candidate evidence exists. |
| Deterministic serialization | A byte-stable canonical ordering that yields identical output across runs and hosts. |

Measurements are discrete and observable: requirement counts per level and family, refinement-closure
results, traceability-link counts, orphan counts, REF-002 disposition counts, validator exit status, and
byte-level register/matrix contents. No availability, throughput, timing, or probability figure is
asserted; none is derivable from the accepted capability and none is invented.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-001–FR-035, SC-001–SC-011, user stories, edge cases, key entities | normative requirements the register maintains one-to-one |
| Task entry | `specs/007-xcom-core/tasks.md` T008 and the dependency-order section | authorized bounded scope and successor ordering |
| Accepted plan | `specs/007-xcom-core/plan.md` delivery phases, project structure, decision gates | level structure, families, and artifact layout |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles IX and X and the capability acceptance gates | maturity, traceability, and evidence obligations |
| ADRs | ADR-0018 (platform-first), ADR-0019 (X-COM observation/stimulation ownership), ADR-0020 (repository-owned workflow) | sequencing, ownership, evidence, review, and acceptance |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC001–ACC015 | exact authorization references |
| Ownership register | `docs/engineering/xcom/task-ownership.{md,json}`, `docs/engineering/xcom/t007/**`, `scripts/validate_xcom_task_ownership.py` | slice/path ownership, baseline/authorization binding, reconciliation vocabulary the register must stay consistent with |
| REF-002 registers | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md`, `docs/architecture/sads-requirements-traceability.json` | the accepted dispositions and shared-requirement ownership T008 records, not re-decides |
| Contracts and data model | `specs/007-xcom-core/{data-model.md,contracts/*.md}` | design-side trace targets and requirement intent |
| Reviews and analysis | `specs/007-xcom-core/analysis.md` A12; `docs/reviews/016-*` XCOM-NOSESN-08; the T007 terminal package | open reconciliation finding and workflow continuity |
| Baseline provenance | `git log` for `src/xverse/xcom/**`, `tests/xcom/**`, `scripts/validate_xcom_*.py` | existing-artifact anchoring only; never acceptance proof |

## 5. Stakeholder requirements

### T008-STK-001 — One authoritative, level-structured requirement register

**Statement.** Capability 007 must have a single authoritative register of stakeholder, system, and
software requirements in which every requirement is uniquely identified, testable, source-anchored, and
elaborated from — never substituted for — the accepted specification.

**Acceptance criteria (observable).**

- AC-1: The register declares exactly the levels `stakeholder`, `system`, and `software` with the family
  prefixes `XCOM-STK-`, `XCOM-SYS-FR-`, `XCOM-SYS-SC-`, and `XCOM-SW-<FAMILY>-`.
- AC-2: Every requirement id is unique across the register.
- AC-3: Every requirement has a non-empty title, statement, applicability, verification intent, and at
  least one acceptance criterion.
- AC-4: Every system requirement anchors to an accepted `FR-###`/`SC-###` identity; the accepted FR/SC
  text is not changed.

**Source anchors.** `tasks.md` T008; `plan.md` "Delivery phases" 1; Constitution art. X;
ACC012/ACC014.

### T008-STK-002 — Exact baseline and authorization binding

**Statement.** The register, the traceability matrix, and every claimed implementation link must be bound
to the exact baseline revision and to the exact accepted authorization that permits the work, so no
requirement or link rests on an unspecified revision or an inferred authorization.

**Acceptance criteria (observable).**

- AC-1: The register and matrix each record `baseline_revision = 957a60723f99c3a31efba1cbd137c454c4acb462`
  and a candidate-revision rule.
- AC-2: Every link that claims an implemented/verified relationship records an exact revision binding; a
  planned link is labelled `planned`.
- AC-3: Missing or malformed baseline binding is rejected by the validator.
- AC-4: No requirement or link cites an authorization record outside the accepted set (ACC001–ACC015,
  ADR-0018, ADR-0019, ADR-0020).

**Source anchors.** ADR-0020 §Decision; ACC012/ACC014/ACC015; Constitution art. X; T007-STK-002.

### T008-STK-003 — Complete bidirectional requirement/design/code/test/measure traceability

**Statement.** Every requirement must trace forward to its design unit, source, test, and verification
measure and every design unit, test, and measure must trace back to at least one requirement, so no
requirement, unit, test, or measure is orphaned in either direction.

**Acceptance criteria (observable).**

- AC-1: Every stakeholder requirement is refined by ≥1 system requirement and every system requirement
  by ≥1 software requirement; the refinement graph is acyclic.
- AC-2: Every requirement that is labelled `implemented` links to ≥1 source, ≥1 test, and ≥1 measure.
- AC-3: No declared design unit, test, or measure is unreferenced (orphan) in the matrix.
- AC-4: Every link resolves to a requirement in the register or to an artifact declared in the matrix.
- AC-5: A forward-only link without its reverse, a dangling target, or an orphan artifact fails validation.

**Source anchors.** `spec.md` FR-030; `tasks.md` T008; Constitution art. X; ACC012/ACC015; `plan.md`
"Decision gates" software acceptance.

### T008-STK-004 — REF-002 SADS disposition completeness without promotion

**Statement.** All twenty direct REF-002 communication IDs XVE-SYS-0139–0158 must appear exactly once
with an explicit capability-007 disposition copied from the accepted reference traceability, and no
allocated or deferred target may be reported as implemented.

**Acceptance criteria (observable).**

- AC-1: The register contains exactly the IDs XVE-SYS-0139–0158, once each.
- AC-2: Each disposition is drawn from the accepted capability-007 table in
  `specs/007-xcom-core/reference-traceability.md` and `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md`.
- AC-3: Applied requirements are linked to the system requirements that cover them; deferred targets carry
  a recorded reason and no implementation link.
- AC-4: A missing ID or an allocated/deferred target promoted to `implemented` fails validation.

**Source anchors.** `spec.md` FR-035; ACC013; `reference-traceability.md`; Constitution capability gates.

### T008-STK-005 — Honest maturity and reconciliation

**Statement.** The register must distinguish implemented, partial, allocated, deferred, superseded,
conflicting, and needs-clarification work, must not treat the presence of source in the baseline as
acceptance evidence, and must stay consistent with the T007 reconciliation state.

**Acceptance criteria (observable).**

- AC-1: Every requirement and artifact uses only the closed maturity vocabulary.
- AC-2: Requirements covered by T012–T016 and T021–T024 source are labelled `partial` with an
  `unreconciled` reason, never `implemented`.
- AC-3: `implemented` requires an exact accepted or candidate revision binding plus code, test, and
  measure links; an unproven `implemented` label fails validation.
- AC-4: The T007 register's reconciliation statements for those tasks remain consistent with the T008
  register; a contradiction fails validation.

**Source anchors.** `spec.md` "Maturity"; Constitution arts. IX and X; `analysis.md` A12; `docs/reviews/016-*`
XCOM-NOSESN-08; T007-STK-005.

### T008-STK-006 — Public-safe, deterministic, reproducible register and validator

**Statement.** The register, the traceability matrix, and their validation must be deterministic and
public-safe: byte-stable across runs, free of credentials, private addresses, proprietary source excerpts,
sensitive deployment values, and absolute host paths, and reproducible offline with no network access.

**Acceptance criteria (observable).**

- AC-1: Serializing the same model twice yields byte-identical output; the markdown projections match.
- AC-2: The validator performs no network access and reads only repository-relative files.
- AC-3: A public-safety scan finds no credential, private address, private-key marker, or absolute host
  path in the register, matrix, projections, or validator output.
- AC-4: Validation is bounded in file size and runtime.

**Source anchors.** `spec.md` FR-027; Constitution art. X; ADR-0020 §Decision; T007-STK-006.

### T008-STK-007 — Accepted architecture, safety boundaries, and ownership preserved

**Statement.** T008 must preserve the accepted architecture, ADRs, REF-002 dispositions, safety
boundaries, task ownership, and dependency order; it must not implement another task, weaken a requirement
or test, or change a product source path.

**Acceptance criteria (observable).**

- AC-1: The T008 candidate diff contains no `src/`, `tests/`, or `xdl/` path.
- AC-2: No accepted ADR, accepted requirement, or existing test is rewritten or weakened.
- AC-3: No later task's source, test, or work product is created or completed by T008.
- AC-4: The T007 ownership register still validates after T008's consistency update.

**Source anchors.** ADR-0018/0019/0020; ACC011/ACC014/ACC015; `tasks.md` dependency-order section;
T007-STK-004/T007-STK-007.

### T008-STK-008 — Independent review and explicit acceptance remain separate

**Statement.** T008 must preserve the separate read-only review and explicit user acceptance gates and
must not accept, complete, or integrate any candidate, including its own.

**Acceptance criteria (observable).**

- AC-1: T008 leaves the T008 and all other task checkboxes unchanged in the plan stage and marks only its
  own checkbox in the implementation stage.
- AC-2: T008 records no acceptance or integration claim for any candidate.
- AC-3: The review of T008's requirement and traceability work is a separate pass recorded in
  `internal-review.json`; external Codex review remains deferred until the `xcom-t007-t010-t017-t020`
  backlog completes.

**Source anchors.** ADR-0020 §Decision; ACC012/ACC015; `tasks.md` T039/T041.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names below are fixed
by `detailed-design.md`; the requirements state their observable contract.

### 6.1 Register model and content

#### T008-SR-001 — Canonical register and matrix model with deterministic serialization (refines T008-STK-006)

**Statement.** The register and the traceability matrix must each exist as a canonical, schema-versioned
model with a fixed top-level field set, a fixed per-entry field set, stable ordering (requirements,
REF-002 dispositions, links, and artifacts each sorted by id; matrix link and artifact ids unique), a
recorded `schema_version`, and a byte-stable JSON serialization plus a deterministic markdown projection.

**Acceptance criteria.** Declared top-level and per-entry schemas are implemented; two serializations are
byte-identical; `schema_version` is present and stable; the markdown projection equals the model; each of the
four declared top-level arrays (`requirements`, `ref002_dispositions`, `artifacts`, `links`) is sorted by id
and no matrix artifact or link id repeats; nested arrays preserve their authored order and carry no sort
requirement.

**Verification intent.** Determinism check CHK-12; structural check CHK-01; negative cases NEG-01
(missing/reordered top-level field), NEG-25 (duplicated link id), NEG-26 (duplicated artifact id), and
NEG-27 (out-of-order requirement array).

#### T008-SR-002 — Requirement identity, level, and vocabulary (refines T008-STK-001)

**Statement.** Every requirement must carry a unique id in a declared level family, a level from the
closed set `{stakeholder, system, software}`, a maturity from the closed vocabulary, and non-empty title,
statement, applicability, verification intent, and acceptance criteria; the register must reject a
duplicate id, an unknown level, or an unknown maturity token.

**Acceptance criteria.** All ids unique; all levels and maturities from their closed sets; all mandatory
fields non-empty; a duplicate id, unknown level, or unknown maturity fails validation.

**Verification intent.** Identity check CHK-02; negative cases NEG-02 (duplicate id) and NEG-03 (unknown
level/vocabulary).

### 6.2 System requirement completeness

#### T008-SR-003 — One-to-one system functional requirement coverage (refines T008-STK-001)

**Statement.** The register must contain exactly one system requirement for each accepted functional
requirement FR-001–FR-035, each anchored to its accepted `FR-###` identity, with no missing, duplicated,
renumbered, or meaning-changed entry; each entry's statement and title must reproduce the accepted FR text
(compared after whitespace normalization) and MUST NOT truncate, drop, or reword it.

**Acceptance criteria.** The set of system FR anchors equals `FR-001..FR-035` exactly; each appears once;
every statement and its `FR-###`-prefixed title equal the accepted spec text after whitespace normalization;
a missing FR, a duplicated/renumbered anchor, or a drifted/truncated statement fails validation.

**Verification intent.** System-coverage and fidelity checks CHK-03; negative cases NEG-04 (missing FR),
NEG-05 (duplicated/renumbered FR anchor), and NEG-24 (truncated/reworded system statement).

#### T008-SR-004 — System success-criterion coverage (refines T008-STK-001)

**Statement.** The register must contain exactly one system requirement for each accepted success
criterion SC-001–SC-011, anchored to its accepted `SC-###` identity and stating the measurable outcome;
each entry's statement and title must reproduce the accepted SC text (compared after whitespace
normalization) and MUST NOT truncate, drop, or reword it.

**Acceptance criteria.** The set of system SC anchors equals `SC-001..SC-011` exactly; each appears once;
every statement and its `SC-###`-prefixed title equal the accepted spec text after whitespace normalization;
a missing SC or a drifted/truncated statement fails validation.

**Verification intent.** System-coverage and fidelity checks CHK-04; negative case NEG-06 (missing SC),
with NEG-24 covering statement drift for the FR/SC family.

### 6.3 Refinement closure

#### T008-SR-005 — Stakeholder→system→software refinement closure (refines T008-STK-003)

**Statement.** Each stakeholder requirement must be refined by ≥1 system requirement, each system
requirement by ≥1 software requirement, and the refinement relation must be acyclic; the register must
reject an orphan parent, an orphan child, a self-refinement, and a refinement cycle.

**Acceptance criteria.** Every STK appears as a `refines` parent of ≥1 SYS; every SYS appears as a
`refines` parent of ≥1 SW; the graph is acyclic; an orphan or cycle fails validation.

**Verification intent.** Refinement check CHK-05/CHK-06; negative cases NEG-07 (orphan stakeholder),
NEG-08 (orphan system), NEG-09 (cycle).

### 6.4 REF-002 dispositions

#### T008-SR-006 — REF-002 disposition register (refines T008-STK-004)

**Statement.** The register must record all twenty direct REF-002 IDs XVE-SYS-0139–0158 exactly once with
the accepted capability-007 disposition, maturity `architectural-target`, the system requirements that
cover each applied ID, and a recorded reason for every deferred ID; the register must reject a missing or
duplicated ID, an unknown disposition, and any promotion of an allocated/deferred target to `implemented`.

**Acceptance criteria.** Exactly the twenty IDs, once each; dispositions equal the accepted table; every
applied ID links to ≥1 system requirement; every deferred ID names its owner/reason; a missing ID or a
promoted target fails validation.

**Verification intent.** REF-002 check CHK-07; negative cases NEG-10 (missing ID) and NEG-11 (promoted
target).

### 6.5 Traceability

#### T008-SR-007 — Traceability link model and artifact resolution (refines T008-STK-003)

**Statement.** The matrix must declare the closed link relations
`{refines, derives_from, allocated_to, implemented_by, verified_by, evidenced_by}` and target kinds
`{requirement, sads, design_unit, source, test, measure, evidence}`, resolve every link source and target
to a requirement in the register, an artifact declared in the matrix, or a REF-002 ID, and reject a
dangling target, an unknown relation, or an unknown target kind.

**Acceptance criteria.** Only declared relations/kinds used; every link source and target resolves; every
declared artifact is referenced by ≥1 link (no orphan artifact); a dangling or unknown link fails
validation.

**Verification intent.** Traceability check CHK-08; negative cases NEG-12 (dangling target), NEG-13
(unknown relation), NEG-14 (forward-only link).

#### T008-SR-008 — Bidirectional closure and non-orphan artifacts (refines T008-STK-003)

**Statement.** The matrix must prove bidirectional closure: every requirement reaches its children
(refinement) and its downstream artifacts, every artifact reaches back to ≥1 requirement, and no design
unit, test, or measure is orphan; the validator must compute closure independently of stored summary
fields.

**Acceptance criteria.** Downward closure holds for every requirement with a non-deferred disposition;
upward closure holds for every declared artifact; an internally inconsistent or forward-only graph fails
validation.

**Verification intent.** Traceability check CHK-09; negative case NEG-14.

### 6.6 Maturity, binding, and safety

#### T008-SR-009 — Maturity and evidence binding honesty (refines T008-STK-005)

**Statement.** Every requirement and artifact must use the closed maturity vocabulary; `implemented` must
require an exact revision binding plus source, test, and measure links; T012–T016 and T021–T024 coverage
must be `partial` with an `unreconciled` reason; a `deferred` requirement must record a reason and no
implementation link; the validator must reject an unproven `implemented`, a missing reason, and an
inconsistency with the T007 reconciliation state; and it must fail closed when the T007 ownership
dependency is missing, unreadable, or malformed rather than silently skipping reconciliation.

**Acceptance criteria.** Closed vocabulary only; `implemented` fully evidenced and revision-bound;
unreconciled coverage labelled `partial` with reason; a violation fails validation; an unavailable
`docs/engineering/xcom/task-ownership.json` yields a distinct nonzero failure and never a passing result.

**Verification intent.** Maturity check CHK-10 and reconciliation-dependency check CHK-10; negative cases
NEG-15 (no code/test/measure), NEG-16 (no revision), NEG-17 (unreconciled source treated as implemented or
without reason), and NEG-28 (ownership register unavailable).

#### T008-SR-010 — Exact baseline and authorization binding (refines T008-STK-002)

**Statement.** The register and matrix must record the exact 40-hex baseline, a candidate-revision rule,
and the accepted authorization set; every claimed relationship must be exact-revision-bound or labelled
`planned`; the validator must reject a non-40-hex baseline and an unknown authorization reference.

**Acceptance criteria.** Both artifacts bind the run baseline; planned versus established links are
distinguished; a malformed baseline or unknown authorization fails validation.

**Verification intent.** Binding check CHK-11; negative case NEG-18 (malformed baseline).

#### T008-SR-011 — Docs-only boundary for the T008 candidate (refines T008-STK-007)

**Statement.** The T008 candidate must change only work-product/governance documentation and add one
validator script under `scripts/`; it must not change, create, or delete any path under `src/`, `tests/`,
or `xdl/`, and must not modify an accepted ADR or weaken an existing requirement or test.

**Acceptance criteria.** `git diff --name-only <baseline>` contains no `src/`, `tests/`, or `xdl/` path;
no accepted ADR text is edited; `git diff --check` is clean; the T007 ownership validator still passes.

**Verification intent.** Boundary check CHK-14; deterministic gate in `verification-plan.md` §2.

#### T008-SR-012 — Public-safe register, matrix, and validator output (refines T008-STK-006)

**Statement.** The register, the matrix, their projections, and the validator output and retained evidence
must contain no credentials, secrets, private addresses, proprietary source excerpts, unrestricted
payloads, private-key markers, or absolute host paths. The documented external deterministic-gate
invocation path in `verification-plan.md` §2 is workflow infrastructure, not register content, and is out
of scope of this content rule.

**Acceptance criteria.** A public-safety scan of the register, matrix, projections, and validator output
finds none of the prohibited classes; the scan is reproducible.

**Verification intent.** Public-safety check CHK-13; negative case NEG-20.

#### T008-SR-013 — Deterministic validator with self-test and ownership consistency (refines T008-STK-006, T008-STK-007)

**Statement.** A repository-owned validator must check the register and matrix against T008-SR-002..012,
provide a self-test over controlled positive and negative fixtures, be deterministic, offline, and
bounded, expose a distinct nonzero exit per failure class, and the T008 candidate must record its new
artifacts in the T007 ownership register and re-run that register's validator without weakening it.

**Acceptance criteria.** The validator passes the real register and matrix; its self-test exercises every
negative case; it performs no network access; file and runtime bounds hold; `--check-human` confirms the
projections; the T007 ownership validator still exits 0 after the consistency update.

**Verification intent.** Validator/self-test cases in `verification-plan.md` §4–§5; ownership re-check
CHK-15.

## 7. Capability 007 requirement links

| Capability anchor | T008 disposition and link | Remaining work |
| --- | --- | --- |
| FR-030 requirements→design→code→test→measure traceability, unit/contract/integration/performance evidence, separate architecture review | **Implemented for this slice (governance)**: T008-STK-001/T008-STK-003, T008-SR-001–SR-008 and SR-013 establish the register, the traceability matrix, and their validator. | T009/T010 own architecture and unit work products; T035–T041 produce and review the software evidence. |
| FR-035 REF-002 accounting | **Implemented for this slice**: T008-STK-004, T008-SR-006 record all twenty XVE-SYS-0139–0158 dispositions without promotion. | Per-target dispositions remain with their owning capabilities. |
| FR-027 / FR-028 public-safe, no legacy/peer access | **Partial (constraint)**: T008-SR-010, SR-011, SR-012 declare the binding, boundary, and public-safety rules. | Enforced at runtime by the implementation slices and verified by T035/T038. |
| SC-009 every requirement traces to design units and automated evidence; warning-free Doxygen | **Partial (governance)**: the matrix provides the requirement-side closure; Doxygen evidence is T011/T037. | T037/T038 complete the evidence and validate the matrix. |
| SC-010 separate review with no unresolved BLOCKER/MAJOR before human acceptance | **Preserved**: T008-STK-008 keeps review and acceptance separate. | T039/T041 perform the review and acceptance. |
| Constitution art. X reproducibility/traceability | **Implemented for this slice**: T008-SR-001, SR-009, SR-010, SR-012. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T008 is a requirements/traceability task and implements **no** direct REF-002 communication requirement
XVE-SYS-0139–0158. It **records** every disposition exactly as accepted and promotes none. Every
capability-007 disposition in `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` remains exactly as accepted.

| REF-002 group | Disposition in T008 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — the accepted allocation/deferment table is copied into the register with its maturity `architectural-target`; no target is promoted | T008 records and links dispositions only; it implements and demonstrates nothing. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may establish contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open item is the reconciliation of already-present source
(§9 A-1), which the register records rather than resolves.

## 9. Assumptions and open items

1. **A-1 (open reconciliation)** — `src/xverse/xcom/**`, `tests/xcom/**`, and the `scripts/validate_xcom_*.py`
   validators contain SESN-era artifacts for T012–T016 and T021–T024, but those task checkboxes are open
   and no accepted exact-candidate revision is recorded (analysis A12; review-016 XCOM-NOSESN-08). The
   register records them as `partial`/`unreconciled`; it does not relabel, delete, or extend them.
2. **A-2** — The accepted T025 successor is merged at `4b01586b438a8587d231ee8828d896c206c06a96`
   (implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a`); the register records T025 requirements as
   the one accepted stimulation slice and links them to that revision.
3. **A-3** — Requirement, family, and unit identifiers are candidate-chosen names fixed by
   `detailed-design.md`; no accepted text is contradicted and no accepted requirement is renumbered.
4. **A-4** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch, tag,
   or ambient state is a valid binding.
5. **A-5** — The deterministic gate for T008 is a work-product gate that runs no C++/Python test suite; the
   T008 verification is static validation of the register, matrix, and docs-only boundary
   (`verification-plan.md` §2).
6. **A-6** — The register is derived from the accepted specification; where the accepted specification is
   silent, the register records a refinement obligation rather than inventing requirement text.

## 10. Requirement index

| Requirement | Refines | Primary units |
| --- | --- | --- |
| T008-STK-001 | — | U-ID, U-STK, U-SYS |
| T008-STK-002 | — | U-BIND |
| T008-STK-003 | — | U-TRACE, U-SW |
| T008-STK-004 | — | U-REF002 |
| T008-STK-005 | — | U-MAT |
| T008-STK-006 | — | U-REG, U-SAFE, U-VALIDATE |
| T008-STK-007 | — | U-SAFE, U-VALIDATE |
| T008-STK-008 | — | U-SAFE |
| T008-SR-001 | STK-006 | U-REG |
| T008-SR-002 | STK-001 | U-ID |
| T008-SR-003 | STK-001 | U-SYS |
| T008-SR-004 | STK-001 | U-SYS |
| T008-SR-005 | STK-003 | U-STK, U-SW |
| T008-SR-006 | STK-004 | U-REF002 |
| T008-SR-007 | STK-003 | U-TRACE |
| T008-SR-008 | STK-003 | U-TRACE |
| T008-SR-009 | STK-005 | U-MAT |
| T008-SR-010 | STK-002 | U-BIND |
| T008-SR-011 | STK-007 | U-SAFE |
| T008-SR-012 | STK-006 | U-SAFE |
| T008-SR-013 | STK-006, STK-007 | U-VALIDATE |

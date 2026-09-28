# T008 Unit Specifications — Requirement Register and Traceability Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T008 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Implementation artifacts | `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}`, `scripts/validate_xcom_requirements_traceability.py` |

## 2. Scope, language, and conventions

T008 is a documentation/governance task. Its units are the requirement-register model, the traceability
matrix model, their validation logic, and the offline validator. The register and matrix are JSON
documents plus derived Markdown projections; the validator is a Python 3.11-compatible script under
`scripts/` (the only executable artifact, and not under `src/`, `tests/`, or `xdl/`).

Conventions:

- All identifiers are stable ASCII tokens; all ordering is declared and deterministic.
- Units are pure functions over the register/matrix models except `U-VALIDATE` (I/O) and `U-REG`
  (serialization).
- "Lifetime" is the process lifetime of a single validator invocation; the register has no runtime state.
- **Thread-safety**: T008 units are offline and single-threaded. Concurrency is not applicable; the
  validator must not spawn threads or subprocesses. This is an explicit design decision, not a gap.
- **Doxygen**: not applicable to this task; T010 owns the Doxygen plan for production C/C++ interfaces
  (FR-029). T008 adds no public C/C++ interface.

**Resource and concurrency bounds (all units).** Inputs are read-only, repository-relative, each ≤ 1 MiB
and ≤ 4 MiB total. No network, no subprocess, no filesystem writes. Wall-clock bound ≤ 60 s,
single-threaded, deterministic output.

## 3. Unit catalogue

### U-REG — Register/matrix model and canonical serialization

- **Responsibility.** Hold the top-level register and matrix models and produce the byte-stable JSON and
  Markdown projections.
- **Interface.** `load(path) -> Model`; `serialize(Model) -> bytes`; `project_markdown(Model) -> str`.
- **Invariants.** `schema_version == 1`; fixed top-level/per-entry field sets and order; every declared
  array (`requirements`, `ref002_dispositions`, `artifacts`, `links`) is sorted by `id` and the matrix
  `artifacts`/`links` ids are unique; an artifact with status `established` carries an exact 40-hex
  `revision_binding` and a `planned` artifact carries the literal `planned`; two serializations of the same
  model are byte-identical; output ends in a single trailing newline; no timestamp/host/absolute path.
- **Failure semantics.** Malformed JSON, a missing top-level field, an unsorted or duplicate-id array, or a
  malformed artifact `revision_binding` yields `SCHEMA_INVALID` (2), never a partial output. Serialization
  failure yields `DETERMINISM_INVALID` (10).
- **Lifetime/ownership.** Immutable value model; owned by the validator invocation.
- **Requirements.** T008-SR-001, T008-SR-013.
- **Planned evidence.** CHK-01, CHK-12, NEG-01, NEG-21, NEG-22, NEG-23, NEG-25, NEG-26, NEG-27, DET-01, DET-02.

### U-ID — Requirement identity, level, and vocabulary

- **Responsibility.** Validate each requirement's identity, level, maturity token, mandatory fields, and
  uniqueness.
- **Interface.** `expected_levels() -> frozenset`; `validate_identity(register) -> Result`.
- **Invariants.** Ids unique and matched to a declared family pattern; levels equal
  `{stakeholder, system, software}`; maturity in the seven-token vocabulary; title/statement/applicability/
  verification intent non-empty; ≥ 1 acceptance criterion.
- **Failure semantics.** Duplicate id, unknown level, unknown maturity, or bad family pattern →
  `ID_INVALID` (3).
- **Lifetime/ownership.** Pure; no I/O.
- **Requirements.** T008-SR-002.
- **Planned evidence.** CHK-02, NEG-02, NEG-03.

### U-SYS — System requirement coverage

- **Responsibility.** Prove one-to-one coverage of the accepted functional requirements and success
  criteria.
- **Interface.** `validate_system_coverage(register) -> Result`.
- **Invariants.** `XCOM-SYS-FR-###` anchors equal `FR-001..FR-035` exactly once; `XCOM-SYS-SC-###` anchors
  equal `SC-001..SC-011` exactly once; each anchor is present as exactly one `derives_from` entry; the
  declared `counts` match the entries; every system `statement` and anchor-prefixed `title` equals the
  accepted FR/SC text parsed from `specs/007-xcom-core/spec.md` after whitespace normalization.
- **Failure semantics.** Missing, duplicated, or mismatched FR/SC coverage, or system text that truncates,
  drops, or rewords the accepted FR/SC text, → `SYSTEM_COVERAGE_INVALID` (4).
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-003, T008-SR-004.
- **Planned evidence.** CHK-03, CHK-04, NEG-04, NEG-05, NEG-06, NEG-24.

### U-STK — Stakeholder requirement set

- **Responsibility.** Validate the eight stakeholder requirements and their refinement coverage.
- **Interface.** `validate_stakeholders(register) -> Result`.
- **Invariants.** Exactly `XCOM-STK-001..008`; each has an empty `refines`; each is a `refines` parent of
  ≥ 1 system requirement; no duplicate or missing stakeholder requirement.
- **Failure semantics.** Missing/duplicated stakeholder requirement or an orphan stakeholder →
  `REFINEMENT_INVALID` (5).
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-002, T008-SR-005.
- **Planned evidence.** CHK-05, NEG-07.

### U-SW — Software requirement set and refinement

- **Responsibility.** Validate the software requirement families and their refinement into system
  requirements.
- **Interface.** `validate_software(register) -> Result`.
- **Invariants.** Every `XCOM-SW-<FAMILY>-###` id uses a declared family and a capability/`T008` owning
  task; every software requirement refines ≥ 1 system requirement; every system requirement is a parent of
  ≥ 1 software requirement; no orphan child.
- **Failure semantics.** Unknown family, orphan system or software requirement, or self-refinement →
  `REFINEMENT_INVALID` (5).
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-005.
- **Planned evidence.** CHK-06, NEG-08, NEG-09.

### U-REF002 — REF-002 disposition register

- **Responsibility.** Validate the twenty direct REF-002 dispositions and forbid promotion.
- **Interface.** `validate_ref002(register, matrix) -> Result`.
- **Invariants.** Exactly `XVE-SYS-0139..0158` once each; disposition copied from the accepted table;
  maturity `architectural-target`; applied IDs list ≥ 1 covering system requirement; deferred IDs carry an
  owner and a reason; no `allocated`/`deferred` ID carries an established implementation link.
- **Failure semantics.** Missing/duplicated ID, unknown disposition, missing reason, or a promoted target →
  `REF002_INVALID` (6).
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-006.
- **Planned evidence.** CHK-07, NEG-10, NEG-11.

### U-TRACE — Traceability links, resolution, and closure

- **Responsibility.** Build the link graph, resolve every link endpoint, and prove bidirectional closure
  with no orphan artifact.
- **Interface.** `build_graph(register, matrix) -> Graph`; `resolve(link) -> Artifact | Requirement`;
  `validate_traceability(register, matrix) -> Result`; `closure(Graph) -> Result`.
- **Invariants.** Relation/target-kind vocabularies closed; every link `from` is a register requirement;
  every `to` resolves to a requirement, a REF-002 ID, or a declared artifact; every declared artifact is
  referenced by ≥ 1 link; matrix `refines` links agree with register `refines`; no forward-only or dangling
  link.
- **Failure semantics.** Dangling target, unknown relation/kind, orphan artifact, or `refines` mismatch →
  `TRACEABILITY_INVALID` (7).
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-007, T008-SR-008.
- **Planned evidence.** CHK-08, CHK-09, NEG-12, NEG-13, NEG-14.

### U-MAT — Maturity and evidence binding

- **Responsibility.** Enforce maturity honesty and per-maturity link requirements, including consistency
  with the T007 reconciliation state.
- **Interface.** `validate_maturity(register, matrix) -> Result`.
- **Invariants.** `implemented` requires ≥ 1 established source, test, and measure link with exact revision
  bindings; `partial`/`allocated` require an `allocated_to` and a planned `verified_by`; `deferred` carries
  a reason and no implementation link; T012–T016/T021–T024 coverage is `partial` with an `unreconciled`
  reason and does not contradict `docs/engineering/xcom/task-ownership.json`; that dependency must be
  present, readable, and well-formed, and reconciliation fails closed when it is unavailable.
- **Failure semantics.** Unproven `implemented`, missing reason, or T007 contradiction →
  `MATURITY_INVALID` (8); an unavailable T007 ownership dependency → `BINDING_INVALID` (9), never a pass.
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-009.
- **Planned evidence.** CHK-10, NEG-15, NEG-16, NEG-17, NEG-28.

### U-BIND — Baseline and authorization binding

- **Responsibility.** Verify the exact baseline and the resolvable authorization set on both models and on
  every claimed relationship.
- **Interface.** `validate_binding(register, matrix) -> Result`.
- **Invariants.** Both `baseline_revision` values are 40 lowercase hex and equal; the candidate-revision
  rule is present; `authorization_records` is a non-empty subset of the accepted set; established links are
  exact-revision-bound and planned links carry `planned`; the reconciliation dependency
  `docs/engineering/xcom/task-ownership.json` is present, readable, and well-formed.
- **Failure semantics.** Malformed baseline, unknown authorization reference, or an unavailable
  reconciliation dependency → `BINDING_INVALID` (9).
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-010.
- **Planned evidence.** CHK-11, NEG-18, NEG-28, BND-02.

### U-SAFE — Safety, boundary, and public-safety rules

- **Responsibility.** Enforce the public-safety content rule and the docs-only/ownership consistency
  boundary.
- **Interface.** `scan_public_safety(text) -> Result`; `validate_boundary(paths) -> Result`.
- **Invariants.** No credential, secret, private address, private-key marker, proprietary excerpt,
  unrestricted payload, or absolute host path in the register, matrix, projections, or validator output;
  the candidate diff contains no `src/`, `tests/`, or `xdl/` path; the T007 ownership register still
  validates after the consistency update. The documented deterministic-gate invocation path is external
  workflow infrastructure and is out of scope of the content scan.
- **Failure semantics.** Prohibited content → `PUBLIC_SAFETY_INVALID` (11); a product-path or ownership
  violation is reported by the deterministic gate and the implementation record.
- **Lifetime/ownership.** Pure.
- **Requirements.** T008-SR-011, T008-SR-012.
- **Planned evidence.** CHK-13, CHK-14, NEG-20, CHK-15.

### U-VALIDATE — Validator driver and self-test

- **Responsibility.** Provide the CLI, run all checks in precedence order, provide the controlled
  self-test, and emit a bounded, deterministic report.
- **Interface.** CLI `--self-test`, `--verify`, `--check-human`; `run_all(register, matrix) -> Result`.
- **Invariants.** Deterministic exit and output for identical input; lowest numeric exit class when several
  apply; no network, subprocess, or write; bounded reads and runtime; self-test covers every NEG case
  (NEG-01..NEG-28) with a passing positive fixture and each of the fourteen check functions is independently
  exercised, including `_check_matrix_schema` via NEG-21..NEG-23, `_check_system_fidelity` via NEG-24,
  `_check_ordering` via NEG-25..NEG-27, and `_check_reconciliation_dependency` via NEG-28.
- **Failure semantics.** Distinct nonzero exit per class (§7.1 of `detailed-design.md`); unreadable or
  over-bound input → `IO_ERROR` (12).
- **Lifetime/ownership.** One invocation; single-threaded; no shared state.
- **Requirements.** T008-SR-013.
- **Planned evidence.** CHK-12, CHK-15, `--self-test` (NEG-01..NEG-28, DET-02).

## 4. Requirement-to-unit trace

| Requirement | Units |
| --- | --- |
| T008-SR-001 | U-REG |
| T008-SR-002 | U-ID, U-STK |
| T008-SR-003 | U-SYS |
| T008-SR-004 | U-SYS |
| T008-SR-005 | U-STK, U-SW |
| T008-SR-006 | U-REF002 |
| T008-SR-007 | U-TRACE |
| T008-SR-008 | U-TRACE |
| T008-SR-009 | U-MAT |
| T008-SR-010 | U-BIND |
| T008-SR-011 | U-SAFE (boundary) |
| T008-SR-012 | U-SAFE |
| T008-SR-013 | U-REG, U-VALIDATE, U-SAFE (ownership consistency) |

## 5. Ownership, lifetime, and thread-safety summary

| Unit | Owner | Lifetime | Thread-safety | Bounds |
| --- | --- | --- | --- | --- |
| U-REG | T008 | invocation | not applicable (single-threaded, offline) | ≤ 4 MiB input |
| U-ID | T008 | invocation | not applicable | fixed level/vocabulary sets |
| U-SYS | T008 | invocation | not applicable | 46 fixed system requirements |
| U-STK | T008 | invocation | not applicable | 8 fixed stakeholder requirements |
| U-SW | T008 | invocation | not applicable | declared family set |
| U-REF002 | T008 | invocation | not applicable | 20 fixed REF-002 IDs |
| U-TRACE | T008 | invocation | not applicable | bounded link/artifact lists |
| U-MAT | T008 | invocation | not applicable | closed maturity vocabulary |
| U-BIND | T008 | invocation | not applicable | closed authorization set |
| U-SAFE | T008 | invocation | not applicable | bounded scan |
| U-VALIDATE | T008 | one process | not applicable | ≤ 60 s, no network |

No unit publishes a C/C++ interface, so no Doxygen unit contract is owed by T008; Doxygen obligations for
production interfaces remain with the slices per FR-029 and T010/T037.

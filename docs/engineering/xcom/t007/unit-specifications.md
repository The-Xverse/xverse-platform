# T007 Unit Specifications — Ownership Register Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T007 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Implementation artifacts | `docs/engineering/xcom/task-ownership.{md,json}`, `scripts/validate_xcom_task_ownership.py` |

## 2. Scope, language, and conventions

T007 is a documentation/governance task. Its units are the register model, its binding and validation
logic, and the offline validator. The register is a JSON document plus a derived Markdown projection;
the validator is a Python 3.11 script under `scripts/` (the only executable artifact, and not under
`src/`, `tests/`, or `xdl/`).

Conventions:

- All identifiers are stable ASCII tokens; all ordering is declared and deterministic.
- Units are pure functions over the register model except `U-VALIDATE` (I/O) and `U-REGISTER`
  (serialization).
- "Lifetime" is the process lifetime of a single validator invocation; the register has no runtime
  state.
- **Thread-safety**: T007 units are offline and single-threaded. Concurrency is not applicable; the
  validator must not spawn threads or subprocesses. This is an explicit design decision, not a gap.
- **Doxygen**: not applicable to this task; T010 owns the Doxygen plan for production C/C++ interfaces
  (FR-029). T007 adds no public C/C++ interface.

**Resource and concurrency bounds (all units).** Inputs are read-only, repository-relative, each
≤ 1 MiB and ≤ 4 MiB total. No network, no subprocess, no filesystem writes. Wall-clock bound ≤ 60 s,
single-threaded, deterministic output.

## 3. Unit catalogue

### U-REGISTER — Register model and canonical serialization

- **Responsibility.** Hold the top-level register model and produce the byte-stable JSON and Markdown
  projections.
- **Interface.** `load(path) -> Register`; `serialize(Register) -> bytes`; `project_markdown(Register)
  -> str`.
- **Invariants.** `schema_version == 1`; fixed top-level field set/order; two serializations of the same
  model are byte-identical; output ends in a single trailing newline; no timestamp/host/absolute path.
- **Failure semantics.** Malformed JSON or a missing top-level field yields `SCHEMA_INVALID` (2), never a
  partial output. Serialization failure yields `DETERMINISM_INVALID` (9).
- **Lifetime/ownership.** Immutable value model; owned by the validator invocation.
- **Requirements.** T007-SR-001, T007-SR-003.
- **Planned evidence.** CHK-01, CHK-09.

### U-SLICE — Slice set and assignment

- **Responsibility.** Define exactly the six named slices plus the `T-ENABLER` group, and assign every
  task T007–T041 to exactly one slice.
- **Interface.** `expected_slices() -> frozenset`; `validate_slices(Register) -> Result`;
  `validate_assignment(Register) -> Result`.
- **Invariants.** Slice id set equals `{T-CORE, T-XDL, T-OBS, T-STIM, T-INTG, T-REVIEW, T-ENABLER}`;
  assignment union covers T008–T041 exactly once; T007 is the producing task and is not double-owned.
- **Failure semantics.** Missing/extra/renamed slice → `SLICE_SET_INVALID` (3); unassigned, unknown, or
  double-assigned task → `ASSIGNMENT_INVALID` (4).
- **Lifetime/ownership.** Pure; no I/O.
- **Requirements.** T007-SR-002, T007-SR-003.
- **Planned evidence.** CHK-02, CHK-03, NEG-01..NEG-04.

### U-BIND — Baseline and authorization binding

- **Responsibility.** Verify each slice's exact baseline and its resolvable authorization references.
- **Interface.** `validate_binding(Register) -> Result`.
- **Invariants.** Every `authorized_baseline` is 40 lowercase hex and equals the top-level baseline;
  `authorization_refs` is non-empty and a subset of the closed `authorization_records` set; the
  candidate-revision rule is present.
- **Failure semantics.** Malformed baseline or empty/unknown authorization reference → `BINDING_INVALID`
  (5); no acceptance is inferred from a missing reference.
- **Lifetime/ownership.** Pure.
- **Requirements.** T007-SR-004, T007-SR-005.
- **Planned evidence.** CHK-04, NEG-05, NEG-06.

### U-PATHS — Path ownership classification and disjointness

- **Responsibility.** Verify the exclusive/shared path classification, pairwise disjointness of
  exclusive patterns under directory-prefix semantics, non-empty exclusive ownership, per-task artifact
  reservation, and the serialized shared-path rule.
- **Interface.** `validate_paths(Register) -> Result`; `check_per_task_ownership(Register) -> Result`;
  `patterns_overlap(pattern, pattern) -> bool`.
- **Invariants.** No pattern appears in two `paths_exclusive`; two exclusive patterns owned by different
  slices never overlap (equal, directory prefix, or `/`-boundary continuation); every slice's
  `paths_exclusive` is non-empty; every task's `docs/engineering/xcom/<task>/` and
  `reports/xcom-queue/<task>-package.json` is reserved to exactly one slice (the producing task's to
  `T-ENABLER`); every multi-slice pattern appears in `shared_paths`; `paths_shared ⊆ shared_paths`;
  `shared_paths` names the root and X-COM build files and the capability specifications; the
  single-writer/dependency-order rule is stated.
- **Failure semantics.** Overlapping exclusive patterns, an empty exclusive set, or an unreserved
  per-task artifact → `PATH_OWNERSHIP_INVALID` (6).
- **Lifetime/ownership.** Pure.
- **Requirements.** T007-SR-006, T007-SR-007.
- **Planned evidence.** CHK-05, CHK-08, CHK-15, NEG-07, NEG-08, NEG-18, NEG-19, NEG-20.

### U-DEPS — Dependency graph and ordering

- **Responsibility.** Build the dependency graph and prove acyclicity, resolvability, and the declared
  ordering constraints.
- **Interface.** `build_graph(Register) -> Graph`; `topological_order(Graph) -> [node]`;
  `validate_order(Register) -> Result`.
- **Invariants.** Every edge endpoint resolves to a slice/task; the graph is acyclic; each required
  precedence pair in `REQUIRED_ORDER_PAIRS` (enablers → core → {xdl, obs, stim} → intg → review, plus
  T025 → T026) is reachable along the edges; each slice's declared `dependencies` equals its direct
  incoming edges.
- **Failure semantics.** Unknown node, cycle, or ordering violation → `DEPENDENCY_INVALID` (7).
- **Lifetime/ownership.** Pure.
- **Requirements.** T007-SR-008.
- **Planned evidence.** CHK-06, NEG-09, NEG-10, NEG-14, NEG-15, NEG-16.

### U-EVID — Evidence and acceptance gate mapping

- **Responsibility.** Verify every slice maps to ≥ 1 evidence item and a named acceptance gate, and that
  `T-REVIEW` owns the separate review and user-acceptance gates.
- **Interface.** `validate_evidence(Register) -> Result`.
- **Invariants.** Non-empty `required_evidence` and `acceptance_gate` per slice; `T-REVIEW` names the
  read-only review and explicit user-acceptance gates; no gate is removed or weakened.
- **Failure semantics.** Missing evidence/gate or a `T-REVIEW` slice without the review gate →
  `GATE_INVALID` (8).
- **Lifetime/ownership.** Pure.
- **Requirements.** T007-SR-009.
- **Planned evidence.** CHK-07, NEG-11.

### U-RECON — Reconciliation state

- **Responsibility.** Validate the reconciliation vocabulary and the honesty of acceptance labels.
- **Interface.** `validate_reconciliation(Register) -> Result`.
- **Invariants.** Status ∈ `{accepted, unreconciled, allocated, deferred}`; T012–T016 and T021–T024 are
  `unreconciled`; T025 is `accepted` with a recorded revision; any `accepted` entry carries an exact
  revision; source presence alone is never `accepted`.
- **Failure semantics.** Unknown status or `accepted` without a recorded revision → `GATE_INVALID` (8).
- **Lifetime/ownership.** Pure.
- **Requirements.** T007-SR-011.
- **Planned evidence.** CHK-11, NEG-13.

### U-SAFE — Safety and public-safety rules

- **Responsibility.** Enforce the global prohibitions and the public-safety content rule.
- **Interface.** `validate_prohibitions(Register) -> Result`; `scan_public_safety(text) -> Result`.
- **Invariants.** The top-level `global_prohibitions` is a superset of the four minimum global
  prohibitions (no legacy modification, no legacy execution, no external peer, no TCP listener) and every
  slice's `prohibitions` is a superset of that same set; no credential, secret, private address,
  proprietary excerpt, unrestricted payload, or absolute host path in the register, projection, or
  validator output. The documented deterministic-gate invocation path is external workflow
  infrastructure and is out of scope of the content scan.
- **Failure semantics.** Missing prohibition at either level → `GATE_INVALID` (8); prohibited content →
  `PUBLIC_SAFETY_INVALID` (10).
- **Lifetime/ownership.** Pure.
- **Requirements.** T007-SR-010, T007-SR-014.
- **Planned evidence.** CHK-10, CHK-13, NEG-12, NEG-17.

### U-VALIDATE — Validator driver and self-test

- **Responsibility.** Provide the CLI, run all checks in precedence order, provide the controlled
  self-test, and emit a bounded, deterministic report.
- **Interface.** CLI `--self-test`, `--verify`, `--check-human`; `run_all(Register) -> Result`.
- **Invariants.** Deterministic exit and output for identical input; lowest numeric exit class when
  several apply; no network, subprocess, or write; bounded reads and runtime; self-test covers every NEG
  case (NEG-01..NEG-20) with a passing positive fixture and each check is independently exercised.
- **Failure semantics.** Distinct nonzero exit per class (§7.1 of `detailed-design.md`); unreadable or
  over-bound input → `IO_ERROR` (11).
- **Lifetime/ownership.** One invocation; single-threaded; no shared state.
- **Requirements.** T007-SR-012, T007-SR-013.
- **Planned evidence.** CHK-09, CHK-12, CHK-14, `--self-test` (NEG-01..NEG-20, DET-02).

## 4. Requirement-to-unit trace

| Requirement | Units |
| --- | --- |
| T007-SR-001 | U-REGISTER |
| T007-SR-002 | U-SLICE |
| T007-SR-003 | U-SLICE, U-REGISTER |
| T007-SR-004 | U-BIND |
| T007-SR-005 | U-BIND |
| T007-SR-006 | U-PATHS |
| T007-SR-007 | U-PATHS |
| T007-SR-008 | U-DEPS |
| T007-SR-009 | U-EVID |
| T007-SR-010 | U-SAFE |
| T007-SR-011 | U-RECON |
| T007-SR-012 | U-VALIDATE |
| T007-SR-013 | validation boundary (gate + U-VALIDATE) |
| T007-SR-014 | U-SAFE |

## 5. Ownership, lifetime, and thread-safety summary

| Unit | Owner | Lifetime | Thread-safety | Bounds |
| --- | --- | --- | --- | --- |
| U-REGISTER | T007 | invocation | not applicable (single-threaded, offline) | ≤ 4 MiB input |
| U-SLICE | T007 | invocation | not applicable | fixed task set |
| U-BIND | T007 | invocation | not applicable | closed reference set |
| U-PATHS | T007 | invocation | not applicable | bounded pattern lists |
| U-DEPS | T007 | invocation | not applicable | acyclic, ≤ 35 nodes |
| U-EVID | T007 | invocation | not applicable | fixed slice set |
| U-RECON | T007 | invocation | not applicable | closed vocabulary |
| U-SAFE | T007 | invocation | not applicable | bounded scan |
| U-VALIDATE | T007 | one process | not applicable | ≤ 60 s, no network |

No unit publishes a C/C++ interface, so no Doxygen unit contract is owed by T007; Doxygen obligations
for production interfaces remain with the slices per FR-029 and T010/T037.

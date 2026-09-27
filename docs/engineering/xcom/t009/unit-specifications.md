# T009 Unit Specifications — Architecture Model and Validator Units

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T009 |
| Stage / role | plan → unit specifications |
| Revision | 1 |
| Baseline revision | `209084b11a211273f815980f753ba728e1251a09` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Implementation artifacts | `docs/engineering/xcom/t009/architecture-model.{json,md}`, `scripts/validate_xcom_architecture_contracts.py` |

## 2. Scope, language, and conventions

T009 is a documentation/governance task. Its units are the architecture-model structure, the component,
boundary, contract, diagram, and invariant projections of it, and the offline validator. The model is a
JSON document plus a derived Markdown projection; the validator is a Python 3.11-compatible script under
`scripts/` (the only executable artifact, and not under `src/`, `tests/`, `xdl/`, or `proto/`).

Conventions:

- All identifiers are stable ASCII tokens; all ordering is declared and deterministic.
- Units are pure functions over the architecture model except `U-VALIDATE` (I/O), `U-MODEL`
  (serialization/projection), and `U-BIND`/`U-COMP` (bounded dependency reads).
- "Lifetime" is the process lifetime of a single validator invocation; the model has no runtime state.
- **Thread-safety**: T009 units are offline and single-threaded. Concurrency is not applicable; the
  validator must not spawn threads or subprocesses. This is an explicit design decision, not a gap.
- **Doxygen**: not applicable to this task; T010 owns the Doxygen plan for production C/C++ interfaces
  (FR-029). T009 adds no public C/C++ interface.

**Resource and concurrency bounds (all units).** Inputs are read-only, repository-relative, each ≤ 1 MiB
and ≤ 4 MiB total, including the `docs/engineering/xcom/task-ownership.json` and
`docs/engineering/xcom/t008/requirements-register.json` dependencies. No network, no subprocess, no
filesystem writes. Wall-clock bound ≤ 60 s, single-threaded, deterministic output.

## 3. Unit catalogue

### U-MODEL — Architecture model, canonical serialization, and projection

- **Responsibility.** Hold the top-level model, validate its fixed field set and vocabularies, and produce
  the byte-stable JSON and Markdown projections (including the deterministic Mermaid diagrams).
- **Interface.** `load(path) -> Model`; `serialize(Model) -> bytes`; `project_markdown(Model) -> str`.
- **Invariants.** `schema_version == 1`; fixed top-level/per-record field sets and key order; every family
  entry `id` is a non-empty string; the `components`, `boundaries`, `contracts`, `diagrams`, and
  `invariants` arrays are sorted by `id` with unique ids; the fixed vocabularies equal their declared sets;
  `counts` matches the entries; two serializations of the same model are byte-identical; output ends in a
  single trailing newline; no timestamp/host/absolute path.
- **Failure semantics.** Malformed JSON, a missing top-level field, a non-string `id`, an unsorted or
  duplicate-id array, a vocabulary mismatch, or a count mismatch yields `SCHEMA_INVALID` (2), never a
  partial output or an uncaught type error. Serialization failure yields `DETERMINISM_INVALID` (10).
- **Lifetime/ownership.** Immutable value model; owned by the validator invocation.
- **Requirements.** T009-SR-001, T009-SR-013.
- **Planned evidence.** CHK-01, CHK-12, ORD-01, NEG-01, NEG-27, NEG-28, NEG-29, NEG-32, NEG-35..NEG-39, DET-01, DET-02.

### U-COMP — Component identity, vocabulary, and product-path anchoring

- **Responsibility.** Validate each component's identity, layer/language/scope/maturity, ownership,
  artifact paths, requirement links, and governing ADRs, and verify path status against the tree.
- **Interface.** `validate_components(model, tree, requirement_register) -> Result`.
- **Invariants.** Ids unique and patterned `XCOM-CMP-###`; layer/language/maturity in the closed
  vocabularies; `owning_slice`/`owning_tasks` consistent (external/downstream layers own no tasks); every
  component has ≥ 1 artifact path tagged `established`/`planned`; an `established` path exists and a
  `planned` path is absent; every `requirement_links` id resolves in the T008 register or the accepted
  `FR-001`–`FR-035`/`SC-001`–`SC-011`/`US1`–`US4` anchor set;
  `governing_adrs` ⊆ `adr_vocabulary`.
- **Failure semantics.** Duplicate id, unknown token, missing mandatory field, or no artifact path →
  `IDENTITY_INVALID` (3); a path-status inconsistency → `PATH_INVALID` (12); a dangling requirement link or
  an unaccepted `FR-###`/`SC-###`/`US#` anchor → `BINDING_INVALID` (9).
- **Lifetime/ownership.** Pure except bounded tree/path checks and the requirement-register read.
- **Requirements.** T009-SR-002, T009-SR-010.
- **Planned evidence.** CHK-02, CHK-06, NEG-02, NEG-03, NEG-04, NEG-24, NEG-25, NEG-26, NEG-31, NEG-34.

### U-BOUND — Boundary model completeness and resolution

- **Responsibility.** Validate each boundary's kind, endpoints, language pair, direction, authorization,
  contract reference, safety constraints, failure semantics, and required-set membership.
- **Interface.** `validate_boundaries(model) -> Result`.
- **Invariants.** `XCOM-XB-001`–`011` present exactly once; each endpoint resolves to a declared
  component; `kind`/`direction`/`authorization` in the closed vocabularies; `from_language`/`to_language`
  are a subset of the resolved contract's `endpoint_languages` and differ for `kind == language`;
  `safety` and `failure_semantics` non-empty.
- **Failure semantics.** Unresolved endpoint, unknown kind, missing required boundary, or duplicated
  boundary id → `BOUNDARY_INVALID` (4); a dangling contract reference → `CONTRACT_INVALID` (5).
- **Lifetime/ownership.** Pure.
- **Requirements.** T009-SR-003.
- **Planned evidence.** CHK-03, NEG-05, NEG-06, NEG-07, NEG-27.

### U-XLANG — Cross-language and external contract catalogue

- **Responsibility.** Validate the contract catalogue and resolve every boundary to a contract whose kind
  and endpoint languages fit.
- **Interface.** `validate_contracts(model) -> Result`.
- **Invariants.** `XCOM-XLC-001`–`006` present exactly once; producer/consumer components resolve;
  `endpoint_languages` a sorted non-empty subset of the language vocabulary; `version`, `encoding`, and
  `evolution_rule` non-empty; `unknown_field_policy` legal for the contract kind; boundary-kind/
  contract-kind consistency holds; the Python→C++, gateway, observation, and provider boundaries each
  resolve.
- **Failure semantics.** Dangling boundary→contract reference, language mismatch, missing version/
  evolution rule, or duplicated contract id → `CONTRACT_INVALID` (5).
- **Lifetime/ownership.** Pure.
- **Requirements.** T009-SR-004.
- **Planned evidence.** CHK-04, NEG-08, NEG-09, NEG-10, NEG-28.

### U-DIAG — Component and sequence diagrams and coverage

- **Responsibility.** Validate diagram structure, participant/step resolution, and bidirectional coverage.
- **Interface.** `validate_diagrams(model) -> Result`.
- **Invariants.** `XCOM-DGM-001`–`005` present; exactly one `component` diagram and one `sequence` diagram
  for each of US1–US4; every participant resolves to a declared component; every step's `from`/`to` are
  participants and its `boundary` resolves; every component appears in ≥ 1 `participants`; every boundary
  appears in ≥ 1 step; every contract is referenced by ≥ 1 boundary that appears in a step.
- **Failure semantics.** Unresolved participant/step, an orphan step, or missing
  component/boundary/contract/user-story coverage → `DIAGRAM_INVALID` (6).
- **Lifetime/ownership.** Pure.
- **Requirements.** T009-SR-005.
- **Planned evidence.** CHK-05, NEG-11, NEG-12, NEG-13.

### U-ADR — Governing ADR and REF-002 non-promotion

- **Responsibility.** Validate governing-ADR references and enforce REF-002 non-promotion.
- **Interface.** `validate_governance(model) -> Result`.
- **Invariants.** Every component/contract/boundary governing ADR is in `adr_vocabulary`;
  `ref002.disposition == "unchanged"`; `ref002.promoted` is empty; no `implemented` record is asserted for
  a deferred/allocated SADS target; the T008 register's REF-002 dispositions are not contradicted.
- **Failure semantics.** Unknown governing ADR or a promoted/REF-002-contradicting record →
  `GOVERNANCE_INVALID` (7).
- **Lifetime/ownership.** Pure except the bounded requirement-register read.
- **Requirements.** T009-SR-006.
- **Planned evidence.** CHK-07, NEG-14, NEG-15.

### U-NEUTRAL — Domain neutrality and dependency direction

- **Responsibility.** Enforce the one-way dependency-direction rule and core domain neutrality.
- **Interface.** `validate_neutrality(model) -> Result`.
- **Invariants.** The dependency-direction and core-neutrality invariants are present; Python is confined
  to `xdl-input`/`build-time` and the data plane to C++; no core-layer component names a domain-specific
  primitive (ECU, CAN, SOME/IP, Zenoh, or a product name as a core primitive); no reverse dependency
  exists between layers.
- **Failure semantics.** A reverse dependency, a core-layer domain primitive, or a
  language/layer-placement violation → `GOVERNANCE_INVALID` (7).
- **Lifetime/ownership.** Pure.
- **Requirements.** T009-SR-007.
- **Planned evidence.** CHK-08, NEG-16, NEG-17.

### U-SAFE — Safety invariants, public safety, and boundary rule

- **Responsibility.** Enforce the declared safety invariants, the public-safety content rule, and the
  docs-only/ownership consistency boundary.
- **Interface.** `validate_safety(model) -> Result`; `scan_public_safety(text) -> Result`;
  `validate_boundary(paths) -> Result`.
- **Invariants.** The safety/neutrality/dependency invariants plus `XCOM-INV-03`/`06` are present with
  stable ids and non-empty statements, each enforced by a named check, and each required safety-boundary
  invariant carries its pinned accepted `(kind, statement)` text; a removed/weakened invariant
  (permitted TCP listener, optional permit, payload-default observation) is rejected; no credential,
  secret, private address, private-key marker, proprietary excerpt, unrestricted payload, or absolute host
  path in the model, projection, or output; the candidate diff contains no `src/`, `tests/`, `xdl/`, or
  `proto/` path; the T007 ownership register still validates after the consistency update. The documented
  deterministic-gate invocation path is external workflow infrastructure and is out of scope of the
  content scan.
- **Failure semantics.** A missing/weakened safety invariant → `SAFETY_INVALID` (8); prohibited content →
  `PUBLIC_SAFETY_INVALID` (11); a product-path or ownership violation is reported by the deterministic
  gate and the implementation record.
- **Lifetime/ownership.** Pure.
- **Requirements.** T009-SR-008, T009-SR-011, T009-SR-012.
- **Planned evidence.** CHK-09, CHK-13, CHK-14, NEG-18, NEG-33, NEG-23, CHK-15.

### U-BIND — Baseline, authorization, and fail-closed dependencies

- **Responsibility.** Verify the exact baseline, the resolvable authorization/ADR sets, and the presence,
  readability, and well-formedness of the reconciliation dependencies.
- **Interface.** `validate_binding(model, task_ownership, requirement_register) -> Result`.
- **Invariants.** `baseline_revision` is 40 lowercase hex; the candidate-revision rule is present;
  `authorization_records` equals the T007 closed set; `adr_vocabulary` is the closed accepted set;
  `accepted_revision` is 40-hex iff `maturity == implemented` and null otherwise; `partial` components
  whose baseline source is unreconciled carry a `reconciliation` reason; the reconciliation state is
  consistent with `docs/engineering/xcom/task-ownership.json`; both dependency files are present,
  readable, and well-formed.
- **Failure semantics.** Malformed baseline, unknown authorization reference, unproven `implemented`, a
  contradiction with the T007 register, or an unavailable/malformed dependency → `BINDING_INVALID` (9),
  never a pass; an unproven `implemented` asserted as governance also reports `GOVERNANCE_INVALID` (7).
- **Lifetime/ownership.** Bounded reads of two dependency files; otherwise pure.
- **Requirements.** T009-SR-009, T009-SR-010, T009-SR-013.
- **Planned evidence.** CHK-10, CHK-11, NEG-19, NEG-20, NEG-21, NEG-30, BND-02.

### U-VALIDATE — Validator driver and self-test

- **Responsibility.** Provide the CLI, run all checks in precedence order, provide the controlled
  self-test, and emit a bounded, deterministic report.
- **Interface.** CLI `--self-test`, `--verify`, `--check-human`; `run_all(model) -> Result`.
- **Invariants.** Deterministic exit and output for identical input; lowest numeric exit class when several
  apply; no network, subprocess, or write; bounded reads and runtime; self-test covers every NEG case
  (NEG-01..NEG-39) with a passing positive fixture and each of the fifteen check functions is independently
  exercised, including `_check_model_schema` (NEG-01/32/35..39), `_check_ordering` (NEG-29), `_check_paths`
  (NEG-25/26), `_check_boundaries` (NEG-05), `_check_contracts` (NEG-08/38), `_check_diagrams` (NEG-13/37),
  `_check_governance` (NEG-14), `_check_neutrality` (NEG-16/35/36/39), `_check_safety` (NEG-18/33/39),
  `_check_binding` (NEG-19/34), `_check_maturity` (NEG-30), `_check_dependencies` (NEG-21),
  `_check_determinism` (NEG-22), and `_scan_public_safety` (NEG-23).
- **Failure semantics.** Distinct nonzero exit per class (§10.1 of `detailed-design.md`); unreadable or
  over-bound input → `IO_ERROR` (13).
- **Lifetime/ownership.** One invocation; single-threaded; no shared state.
- **Requirements.** T009-SR-013.
- **Planned evidence.** CHK-12, CHK-15, CHK-16, `--self-test` (NEG-01..NEG-39, DET-02).

## 4. Requirement-to-unit trace

| Requirement | Units |
| --- | --- |
| T009-SR-001 | U-MODEL |
| T009-SR-002 | U-COMP |
| T009-SR-003 | U-BOUND |
| T009-SR-004 | U-XLANG |
| T009-SR-005 | U-DIAG |
| T009-SR-006 | U-ADR |
| T009-SR-007 | U-NEUTRAL |
| T009-SR-008 | U-SAFE |
| T009-SR-009 | U-BIND |
| T009-SR-010 | U-COMP, U-BIND |
| T009-SR-011 | U-SAFE (boundary) |
| T009-SR-012 | U-SAFE |
| T009-SR-013 | U-MODEL, U-BIND, U-VALIDATE |

## 5. Ownership, lifetime, and thread-safety summary

| Unit | Owner | Lifetime | Thread-safety | Bounds |
| --- | --- | --- | --- | --- |
| U-MODEL | T009 | invocation | not applicable (single-threaded, offline) | ≤ 4 MiB input |
| U-COMP | T009 | invocation | not applicable | fixed component set (13) |
| U-BOUND | T009 | invocation | not applicable | fixed boundary set (11) |
| U-XLANG | T009 | invocation | not applicable | fixed contract set (6) |
| U-DIAG | T009 | invocation | not applicable | fixed diagram set (5) |
| U-ADR | T009 | invocation | not applicable | closed ADR/REF-002 sets |
| U-NEUTRAL | T009 | invocation | not applicable | fixed layer/language sets |
| U-SAFE | T009 | invocation | not applicable | bounded scan |
| U-BIND | T009 | invocation | not applicable | 2 bounded dependency files |
| U-VALIDATE | T009 | one process | not applicable | ≤ 60 s, no network |

No unit publishes a C/C++ interface, so no Doxygen unit contract is owed by T009; Doxygen obligations for
production interfaces remain with the slices per FR-029 and T010/T037.

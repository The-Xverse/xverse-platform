# T007 Detailed Design — Ownership Register, Binding, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T007 |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Maturity | Governance/planning target; documentation-only candidate |

## 2. Implementation artifacts (what the T007 candidate adds)

T007 is a work-product task, so its "implementation" is the ownership register and its validator, all
outside `src/`, `tests/`, and `xdl/`:

| Artifact | Path | Owner | Purpose |
| --- | --- | --- | --- |
| Human-readable register | `docs/engineering/xcom/task-ownership.md` | T007 | Canonical ownership view for reviewers and later tasks |
| Machine-readable register | `docs/engineering/xcom/task-ownership.json` | T007 | Canonical, schema-versioned, deterministic input to the validator |
| Register validator | `scripts/validate_xcom_task_ownership.py` | T007 | Offline, deterministic, bounded checks with a self-test |
| Implementation record | `docs/engineering/xcom/t007/implementation.md` | T007 | Candidate revision, commands, outcomes, limitations (implementation stage) |
| Capability task state | `specs/007-xcom-core/tasks.md` | T007 | Mark T007 complete only in the implementation stage |

The five plan-stage work products (`requirements.md`, `architecture.md`, `detailed-design.md`,
`unit-specifications.md`, `verification-plan.md`) are documentation; they are produced before this
implementation. No `src/`, `tests/`, or `xdl/` path is created or changed.

## 3. Register schema (version 1)

Top-level object (`schema_version = 1`):

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | `= 1` |
| `task_id` | string | `= "T007"` |
| `baseline_revision` | string | 40-hex; must equal the run baseline |
| `candidate_revision_rule` | string | States successor candidates bind their own and predecessor revisions |
| `authorization_records` | array of string | Closed resolvable set: ACC001–ACC015, ADR-0018, ADR-0019, ADR-0020 |
| `global_prohibitions` | array of string | Minimum four: no legacy modification, no legacy execution, no external peer, no TCP listener |
| `shared_paths` | array of string | Declared shared (serialized) path patterns |
| `slices` | array of object | Six slices + enabler group, in fixed order (§5) |
| `task_assignment` | object | Map task-id → slice-id for T007–T041 |
| `dependency_edges` | array of `[from, to]` | Slice/task edges |

Per-slice object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | One of `T-CORE`, `T-XDL`, `T-OBS`, `T-STIM`, `T-INTG`, `T-REVIEW`, `T-ENABLER` |
| `title` | string | Non-empty |
| `owning_tasks` | array of string | Sorted task ids assigned to this slice |
| `purpose` | string | One bounded sentence |
| `authorized_baseline` | string | 40-hex; equals top-level baseline |
| `authorization_refs` | array of string | Subset of `authorization_records`, non-empty |
| `paths_exclusive` | array of string | Sorted; non-empty; pairwise disjoint across slices under directory-prefix semantics (trailing `/` is a directory); reserves the owner's per-task `docs/engineering/xcom/<task>/` and `reports/xcom-queue/<task>-package.json` |
| `paths_shared` | array of string | Subset of top-level `shared_paths`; may be empty |
| `dependencies` | array of string | Slice ids/task ids, acyclic |
| `required_evidence` | array of string | Non-empty |
| `acceptance_gate` | string | Non-empty, named |
| `prohibitions` | array of string | Superset of `global_prohibitions` |
| `reconciliation` | object | Task-id → `accepted`/`unreconciled`/`allocated`/`deferred`; `accepted` requires a recorded revision |
| `ref002_disposition` | string | `unchanged` (as in §7.3) |

**Serialization.** JSON with keys in the fixed order above; slices in the fixed order `T-CORE`,
`T-XDL`, `T-OBS`, `T-STIM`, `T-INTG`, `T-ENABLER`, `T-REVIEW`; every array sorted lexicographically
except `slices` and `dependency_edges`, which keep declared order; two spaces of indentation; trailing
newline. The human-readable `task-ownership.md` is a deterministic projection of the same model.

## 4. Determinism, bounds, and safety rules

- **Determinism (T007-SR-001, T007-SR-012).** Stable key/element ordering; no timestamps, hostnames,
  absolute paths, or unordered iteration in the register or validator output.
- **Bounds (T007-STK-006).** The validator reads only repository-relative files, each ≤ 1 MiB; total
  input ≤ 4 MiB; no recursion outside the repository; wall-clock timeout ≤ 60 s; single-threaded.
- **Offline (T007-SR-012).** No network client, resolver, package manager, or subprocess shell; only
  file reads and pure computation.
- **Public safety (T007-SR-014).** No credential, secret, private address, proprietary source excerpt,
  unrestricted payload, or absolute host path in the register or its log.
- **Docs-only boundary (T007-SR-013).** The candidate diff contains no `src/`, `tests/`, or `xdl/` path
  and no accepted-ADR rewrite.

## 5. Slice records

Identifiers fix the candidate-chosen names; the baseline is
`923a6db65aafbcdbf33a1461e93622777e902deb` for every slice.

### 5.1 `T-CORE` — C++ core

- Owning tasks: T012, T013, T014, T015, T016, T030, T031, T032, T033, T034.
- Purpose: contract/item/diagnostic/policy value types, bounded endpoint/route lifecycle with exact
  generation-bound handles, explicit provider composition and the owned loopback provider, the
  versioned local tool gateway, and reusable provider/observer/stimulation/gateway contract suites.
- Dependencies: `T-ENABLER` (T007–T011).
- Authorization refs: ACC002, ACC004, ACC005, ACC006, ACC007, ACC010, ACC011, ACC014, ACC015, ADR-0018, ADR-0019, ADR-0020.
- Required evidence: unit; negative; deterministic diagnostics; queue-bound; recovery; contract;
  second-provider replaceability/version-rejection; no-TCP-listener proof; later integration run.
- Acceptance gate: per-task exact-candidate verification + review, then T035/T039/T041.
- Reconciliation: T012–T016 `unreconciled` (source present; checkboxes open); T030–T034 `allocated`.

### 5.2 `T-XDL` — XDL compiler

- Owning tasks: T017, T018, T019, T020.
- Purpose: validate the `io.xverse.xcom` Profile v0.1 and canonical activation-plan v1 schema and
  digest/provenance contract; deterministic Profile-aware plan compilation in
  `src/xverse_xdl/xcom_plan.py`; bounded C++ plan decoding with independent version/digest/capability
  checks; ordering-equivalence, malformed-plan, drift, bound, and regression tests.
- Dependencies: `T-CORE`.
- Authorization refs: ACC002, ACC003, ACC013, ACC014, ACC015, ADR-0018, ADR-0020.
- Required evidence: Profile/schema validation, ordering-equivalence, malformed-plan, drift, bound,
  regression tests; Python suite; C++ decoder tests.
- Acceptance gate: per-task verification + review, then T035/T039/T041.
- Reconciliation: all `allocated`.

### 5.3 `T-OBS` — Observation boundary

- Owning tasks: T021, T022, T023, T024.
- Purpose: immutable observation records/filters/payload policy/tap handles, bounded best-effort
  drop/coalesce and explicit lossless-validation modes, synthetic sink with failure/disconnect
  isolation and visible counters, and their tests.
- Dependencies: `T-CORE`.
- Authorization refs: ACC005, ACC010, ACC011, ACC014, ACC015, ADR-0019, ADR-0020.
- Required evidence: metadata-only zero-payload; controlled payload view with redaction/truncation
  state; ordering; saturation; degraded validity; safe detach; disabled-tap performance.
- Acceptance gate: per-task verification + review, then T035/T036/T039/T041.
- Reconciliation: T021–T024 `unreconciled` (source present; checkboxes open).

### 5.4 `T-STIM` — Validation stimulation boundary

- Owning tasks: T025 (accepted), T026, T027, T028, T029.
- Purpose: explicit time-authority interface, local permit/session lifecycle, bounded durable
  intent/outcome journal, fail-closed pre-emission guard, guarded injection/invocation/exclusive
  service emulation, and the full mismatch/lifecycle/concurrency tests.
- Dependencies: `T-CORE`, `T-OBS` (synthetic sink/loopback fixtures).
- Authorization refs: ACC006, ACC010, ACC011, ACC014, ACC015, ADR-0019, ADR-0020.
- Required evidence: permit/action mismatch matrix; journal-before-emission, journal failure/recovery;
  zero emission after rejection; synthetic provenance; unmapped clocks; quotas; loop bounds; lease
  conflicts; drain/terminal behavior; deterministic concurrency.
- Acceptance gate: per-task verification + review, then T035/T039/T041.
- Reconciliation: T025 `accepted` at merge `4b01586b438a8587d231ee8828d896c206c06a96`
  (implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a`); T026–T029 `allocated`.

### 5.5 `T-INTG` — Integration, evidence, and documentation

- Owning tasks: T035, T036, T037, T038, T040.
- Purpose: run the full unit/contract/integration/negative/concurrency/sanitizer/static/Python checks
  and controlled benchmarks; produce warning-free Doxygen; validate Spec Kit plus REF-002
  requirements/design/code/test traceability and public-safe logs; assemble the exact-candidate
  evidence bundle. Also owns the dependency-admission environment (T011) and build documentation.
- Dependencies: `T-CORE`, `T-XDL`, `T-OBS`, `T-STIM`, and `T-ENABLER` (T011).
- Authorization refs: ACC012, ACC014, ACC015, ADR-0020.
- Required evidence: `index.json` evidence records with bounded logs, raw manifests, command argv,
  exit codes, outcomes, and hashes bound to the exact candidate revision; benchmark environment and
  uncertainty; Doxygen warning-free; traceability matrix; package manifest.
- Acceptance gate: T040 inspection, then T039 review and T041 user acceptance.
- Reconciliation: T035–T038, T040 `allocated`.

### 5.6 `T-REVIEW` — Independent review and user acceptance

- Owning tasks: T039, T041.
- Purpose: the separate read-only review that records every finding before any repair, and the explicit
  user acceptance that closes the capability. Owns capability-level review records under `docs/reviews/`
  and its own task artifacts; a per-task `internal-review.json`/`acceptance-decision.md` is owned by the
  slice that owns that task, not by this slice.
- Dependencies: `T-INTG`.
- Authorization refs: ACC012, ACC015, ADR-0020.
- Required evidence: review report with no unresolved BLOCKER/MAJOR finding for the reviewed candidate;
  per-task `internal-review.json` verdicts; acceptance decision record.
- Acceptance gate: user acceptance recorded; a repair creates a successor candidate and repeats
  affected verification and review.
- Reconciliation: T005 review complete (review 012/013/015/016 historical); T039/T041 `allocated`.

### 5.7 `T-ENABLER` — Engineering-baseline enabler group

- Owning tasks: T008, T009, T010, T011 (T007 is the producing task itself).
- Purpose: requirements/traceability (T008), architecture/boundaries/cross-language contracts (T009),
  unit design/ownership/lifetime/thread-safety/failure semantics/bounds/Doxygen plan (T010), and
  compiler/build/dependency admission with hashes, licenses, and generated-code provenance (T011).
- Dependencies: T007.
- Per-task artifacts: reserves `docs/engineering/xcom/t007/` (the producing task's work products,
  including `internal-review.json` and `acceptance-decision.md`) and
  `reports/xcom-queue/t007-package.json`; the only dependency T007 precedes this group, so the
  reservation is satisfied when T007's run writes them.
- Authorization refs: ACC012, ACC014, ACC015, ADR-0020.
- Required evidence: reviewed work products and a passing dependency-admission preflight.
- Reconciliation: T008–T011 `allocated`.

## 6. Task-to-slice assignment (T007–T041)

| Slice | Tasks |
| --- | --- |
| `T-ENABLER` | T008, T009, T010, T011 |
| `T-CORE` | T012, T013, T014, T015, T016, T030, T031, T032, T033, T034 |
| `T-XDL` | T017, T018, T019, T020 |
| `T-OBS` | T021, T022, T023, T024 |
| `T-STIM` | T025, T026, T027, T028, T029 |
| `T-INTG` | T035, T036, T037, T038, T040 |
| `T-REVIEW` | T039, T041 |

T007 itself is the producing task; it is not assigned to a consuming slice. The union covers T008–T041
exactly once; T001–T006 are completed governance tasks and are recorded as prerequisites.

## 7. Validator design

### 7.1 Interface

`scripts/validate_xcom_task_ownership.py` supports:

| Mode | Behaviour |
| --- | --- |
| `--self-test` | Runs controlled positive and negative fixtures for every NEG case. |
| `--verify` (default) | Validates `docs/engineering/xcom/task-ownership.json` against §3–§6 and §8. |
| `--check-human` | Confirms `task-ownership.md` is the deterministic projection of the JSON. |

Exit classes (distinct nonzero per class, lowest numeric when several apply):

| Exit | Class | Covers |
| ---: | --- | --- |
| 0 | `OK` | Valid register |
| 2 | `SCHEMA_INVALID` | Top-level/per-slice field, ordering, or schema version differs |
| 3 | `SLICE_SET_INVALID` | Missing/extra/renamed slice or enabler group |
| 4 | `ASSIGNMENT_INVALID` | Unassigned, double-assigned, or unknown task |
| 5 | `BINDING_INVALID` | Malformed baseline or empty/unresolvable authorization reference |
| 6 | `PATH_OWNERSHIP_INVALID` | Duplicate exclusive path or undeclared shared path |
| 7 | `DEPENDENCY_INVALID` | Cycle, missing node, or ordering violation |
| 8 | `GATE_INVALID` | Missing evidence/acceptance gate, missing prohibition, or unproven `accepted` |
| 9 | `DETERMINISM_INVALID` | Two serializations or the markdown projection differ |
| 10 | `PUBLIC_SAFETY_INVALID` | Prohibited content class found |
| 11 | `IO_ERROR` | Input unreadable or over bound |

### 7.2 Algorithm

```text
validate(json):
  check schema_version, task_id, baseline_revision, candidate_revision_rule
  check authorization_records set; shared_paths non-empty
  check top-level global_prohibitions superset of the four minimum prohibitions
  check slice id set == expected set (T-CORE, T-XDL, T-OBS, T-STIM, T-INTG, T-ENABLER, T-REVIEW)
  for each slice:
    check required fields present with correct types and sorted arrays
    check authorized_baseline == baseline_revision
    check authorization_refs non-empty and subset of authorization_records
    check paths_shared subset of shared_paths
    check required_evidence and acceptance_gate non-empty
    check prohibitions superset of global_prohibitions
    check reconciliation vocabulary and 'accepted' entries carry a revision
  check every slice declares a non-empty paths_exclusive set
  check exclusive patterns are pairwise disjoint across slices under directory-prefix semantics
  check each task's docs/engineering/xcom/<task>/ and reports/xcom-queue/<task>-package.json stays
    reserved to its owning slice (the producing task's dir to T-ENABLER)
  check task_assignment covers T007..T041 exactly once (T007 may be the producing task)
  build graph from dependency_edges; require acyclic; require every REQUIRED_ORDER_PAIRS pair to be
    reachable (enabler -> core -> {xdl, obs, stim} -> intg -> review; T025 -> T026)
  check declared slice dependencies equal the direct incoming edges
  check determinism: re-serialize; require byte-identical
  check public-safety: scan for absolute paths, credentials, private addresses
  report highest-precedence failure or OK
```

### 7.3 REF-002 handling

The register records `ref002_disposition = "unchanged"` for every slice: T007 implements no direct
REF-002 communication requirement and promotes no allocated target. The authoritative disposition table
remains `specs/007-xcom-core/reference-traceability.md`.

## 8. Ordering constraints (validator-enforced)

Each constraint below is enforced by reachability over the declared `dependency_edges`: the validator
checks every pair in its `REQUIRED_ORDER_PAIRS` constant, so a register that reorders the graph while
keeping each slice's declared `dependencies` consistent with the edges is still rejected with
`DEPENDENCY_INVALID` (7). The self-test exercises each family (NEG-10, NEG-14, NEG-15, NEG-16), and
removing the reachability check makes those fixtures pass, so the check is load-bearing.

1. `T-ENABLER` (T008–T011) precedes `T-CORE` and every later slice.
2. `T-CORE` precedes `T-XDL`, `T-OBS`, `T-STIM`.
3. `T-XDL`, `T-OBS`, `T-STIM` precede `T-INTG`.
4. `T-INTG` precedes `T-REVIEW`.
5. T039 (in `T-REVIEW`) follows the implementation slices it reviews.
6. T025 precedes T026 (journal depends on the accepted permit/session/time-authority primitives).

## 9. Alternatives considered

| Alternative | Rejected because |
| --- | --- |
| Rely on the prose `tasks.md` dependency section without a register | Not machine checkable; overlapping C++/build ownership is not provably disjoint; baseline/authorization binding would remain implicit. |
| One monolithic "X-COM implementation" slice | Contradicts the explicit T007 requirement for separate bounded slices and prevents disjoint path ownership. |
| Fold the gateway into integration/evidence | The gateway is X-COM C++ production source and the external contract boundary, not evidence assembly. |
| Treat existing T012–T024 source as accepted | Source presence is not acceptance evidence (Constitution art. IX; analysis A12); the register records `unreconciled`. |
| Place the register inside `src/` or `tests/` | The deterministic gate forbids T007 changes under `src/`, `tests/`, and `xdl/`; the register is a documentation artifact. |

## 10. Requirement-to-design trace

| Requirement | Design section |
| --- | --- |
| T007-SR-001 | §3 |
| T007-SR-002 | §5, §6 |
| T007-SR-003 | §6 |
| T007-SR-004 | §3, §5 |
| T007-SR-005 | §3, §5 |
| T007-SR-006 | §3, architecture §5 |
| T007-SR-007 | §3, architecture §5 |
| T007-SR-008 | §8 |
| T007-SR-009 | §5, §8 |
| T007-SR-010 | §4, §5 |
| T007-SR-011 | §5, §7.2 |
| T007-SR-012 | §7 |
| T007-SR-013 | §2, §4 |
| T007-SR-014 | §4 |

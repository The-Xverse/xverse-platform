# T008 Detailed Design — Requirement Register, Traceability Matrix, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T008 |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Maturity | Governance/planning target; documentation-and-script candidate |

## 2. Implementation artifacts (what the T008 candidate adds)

T008 is a work-product task, so its "implementation" is the requirement register, the traceability matrix,
and their validator, all outside `src/`, `tests/`, and `xdl/`:

| Artifact | Path | Owner | Purpose |
| --- | --- | --- | --- |
| Requirements register (machine) | `docs/engineering/xcom/t008/requirements-register.json` | T008 | Canonical STK/SYS/SW requirement model and REF-002 dispositions |
| Requirements register (human) | `docs/engineering/xcom/t008/requirements-register.md` | T008 | Deterministic projection for reviewers and later tasks |
| Traceability matrix (machine) | `docs/engineering/xcom/t008/traceability-matrix.json` | T008 | Canonical link and artifact model |
| Traceability matrix (human) | `docs/engineering/xcom/t008/traceability-matrix.md` | T008 | Deterministic projection of the link model |
| Register/matrix validator | `scripts/validate_xcom_requirements_traceability.py` | T008 | Offline, deterministic, bounded checks with a self-test |
| Implementation record | `docs/engineering/xcom/t008/implementation.md` | T008 | Candidate revision, commands, outcomes, limitations |
| Capability task state | `specs/007-xcom-core/tasks.md` | shared | Mark T008 complete only in the implementation stage |
| Ownership consistency | `docs/engineering/xcom/task-ownership.{json,md}` | shared | Record the new validator path in `T-ENABLER`, then re-run `scripts/validate_xcom_task_ownership.py` |

The five plan-stage work products (`requirements.md`, `architecture.md`, `detailed-design.md`,
`unit-specifications.md`, `verification-plan.md`) are documentation; they are produced before this
implementation. No `src/`, `tests/`, or `xdl/` path is created or changed.

## 3. Requirements register schema (version 1)

Top-level object (`schema_version = 1`):

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | `= 1` |
| `task_id` | string | `= "T008"` |
| `capability` | string | `= "007-xcom-core"` |
| `baseline_revision` | string | 40-hex; must equal the run baseline |
| `candidate_revision_rule` | string | States successor candidates bind their own and predecessor revisions |
| `levels` | array of string | Exactly `["stakeholder", "system", "software"]` |
| `maturity_vocabulary` | array of string | Exactly the seven accepted maturity tokens |
| `id_scheme` | object | Declared family prefixes and their level |
| `authorization_records` | array of string | Closed set: ACC001–ACC015, ADR-0018, ADR-0019, ADR-0020 |
| `counts` | object | Declared expected counts per level and family, validated against the entries |
| `requirements` | array of object | Sorted by `id` (validator-enforced); unique across the register |
| `ref002_dispositions` | array of object | Exactly XVE-SYS-0139–0158, sorted by `id` (validator-enforced) |

Requirement object:

| Field | Type | Rule |
| --- | --- | --- |
| `id` | string | Matches the declared family pattern; unique |
| `level` | string | `stakeholder` \| `system` \| `software` |
| `title` | string | Non-empty |
| `statement` | string | Non-empty; for system requirements, whitespace-normalized equal to the accepted FR/SC text in `specs/007-xcom-core/spec.md` |
| `source_anchors` | array of string | Non-empty; for system FR/SC includes the accepted `FR-###`/`SC-###` identity; SADS/user-story/ADR anchors allowed; authored (primary-first) order, not lexicographically sorted |
| `refines` | array of string | Resolvable requirement ids in authored (primary-first) order; empty only for stakeholder requirements |
| `family` | string | Software family (`CORE`, `GW`, `XDL`, `OBS`, `STIM`, `INTG`, `ENB`) or `-` |
| `owning_task` | string | `T0xx`; a capability task, or `T008` for `XCOM-SW-ENB` enabler requirements |
| `applicability` | string | Non-empty bounded scope note |
| `maturity` | string | One of the seven tokens |
| `reconciliation` | string or null | Required `unreconciled` reason for source-present-but-unaccepted coverage; else null |
| `verification_intent` | string | Non-empty; names the planned check/measure family |
| `acceptance_criteria` | array of string | ≥ 1 entry; authored order, not lexicographically sorted |

**Array ordering (normative).** The validator enforces ascending `id` order for exactly the four top-level
arrays `requirements`, `ref002_dispositions`, `artifacts`, and `links` (and matrix `artifacts`/`links` id
uniqueness). No other array carries an ordering guarantee: `source_anchors`, `refines`, and
`acceptance_criteria` (and the REF-002 `covers` list) preserve their authored, semantically significant
order. In particular `source_anchors` and `refines` list the primary anchor/refinement first, so
`XCOM-SW-XDL-001.refines = ["XCOM-SYS-FR-031", "XCOM-SYS-FR-002"]` and
`XCOM-STK-001.source_anchors = ["US1", "SC-001", "SC-002"]` are valid and deliberately not sorted.

`ref002_dispositions` object: `{id, disposition, maturity, owner, covers, reason}` where `id` is one of
XVE-SYS-0139–0158, `disposition` is copied from `reference-traceability.md`
(`allocated` \| `deferred`), `maturity` is always `architectural-target`, `owner` names the deferred
owning capability (empty for applied IDs), `covers` lists the system requirement ids that cover an applied
ID (empty for deferred), and `reason` is non-empty for every entry.

**Derivation rule.** `XCOM-SYS-FR-###` and `XCOM-SYS-SC-###` carry a one-to-one `derives_from` anchor to
the accepted `FR-###`/`SC-###`; the register never adds or removes a functional requirement or success
criterion. Stakeholder and software requirements are candidate-authored elaborations; their identifiers are
fixed by this document and do not renumber any accepted requirement.

### 3.1 Expected counts

| Family | Level | Count | Notes |
| --- | ---: | ---: | --- |
| `XCOM-STK-###` | stakeholder | 8 | T008-STK-001..008 elaborated as capability stakeholders |
| `XCOM-SYS-FR-###` | system | 35 | one-to-one with accepted FR-001..FR-035 |
| `XCOM-SYS-SC-###` | system | 11 | one-to-one with accepted SC-001..SC-011 |
| `XCOM-SW-CORE-###` | software | ≥ 6 | contracts, items, diagnostics, endpoint/route lifecycle, provider/loopback |
| `XCOM-SW-GW-###` | software | ≥ 3 | versioned local tool API, no-TCP gateway, separate-process client |
| `XCOM-SW-XDL-###` | software | ≥ 3 | Profile v0.1, activation-plan v1, bounded C++ decode |
| `XCOM-SW-OBS-###` | software | ≥ 4 | records/filters/policy, bounded taps, synthetic sink |
| `XCOM-SW-STIM-###` | software | ≥ 6 | time authority, permit/session, journal, guard, actions, lifecycle |
| `XCOM-SW-INTG-###` | software | ≥ 3 | dependency admission, evidence bundle, benchmarks, Doxygen, traceability |
| `XCOM-SW-ENB-###` | software | ≥ 4 | T008–T011 enabler requirements |

The implementation records the realized count per family in `counts` and the validator checks that each
declared count equals the number of entries in that family and that every family is non-empty. Exact
wording of individual software requirements is authored in the implementation stage from the accepted
spec, plan, contracts, data model, and the accepted T025 record; the register never invents an accepted
requirement.

## 4. Traceability matrix schema (version 1)

Top-level object (`schema_version = 1`):

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | `= 1` |
| `task_id` | string | `= "T008"` |
| `baseline_revision` | string | 40-hex; equals the register baseline |
| `candidate_revision_rule` | string | Same rule as the register |
| `relation_vocabulary` | array of string | Exactly `["refines","derives_from","allocated_to","implemented_by","verified_by","evidenced_by"]` (sorted) |
| `target_kind_vocabulary` | array of string | Exactly `["requirement","sads","design_unit","source","test","measure","evidence"]` (sorted) |
| `artifacts` | array of object | Sorted by `id`, ids unique (validator-enforced); declare every non-requirement link target |
| `links` | array of object | Sorted by `id`; ids unique (validator-enforced) |

Artifact object: `{id, kind, locator, status, revision_binding}` where `kind` ∈
`{design_unit, source, test, measure, evidence}`, `locator` is a repository-relative path or a stable
symbol/measure id, `status` ∈ `{established, planned}`, and `revision_binding` is an exact 40-hex revision
for `established` artifacts and the literal `planned` otherwise.

Link object: `{id, from, from_kind, relation, to, to_kind, status, revision_binding}` where `id` matches
`XCOM-L-####`, `from_kind ∈ {requirement}`, `relation` and `to_kind` are from the declared vocabularies,
`status ∈ {established, planned}`, and `revision_binding` follows the artifact rule. Every `from`
requirement is in the register; every `to` resolves as follows:

| `to_kind` | Resolution |
| --- | --- |
| `requirement` | an id in the register `requirements[]` |
| `sads` | an id in the register `ref002_dispositions[]` |
| `design_unit` \| `source` \| `test` \| `measure` \| `evidence` | an id in the matrix `artifacts[]` |

**Refinement storage.** Refinement edges are stored once in the register (`refines`) and are *also*
materialized as `refines` links in the matrix so a single traversal graph exists. The validator checks the
two representations agree; a mismatch fails validation (T008-SR-008).

**Serialization.** JSON with keys in the fixed order above, two spaces of indentation, and a trailing
newline. The ordering guarantee is exactly the four top-level arrays the validator enforces: `requirements`,
`ref002_dispositions`, `artifacts`, and `links` are stored in ascending `id` order, and matrix
`artifacts`/`links` ids are unique. No other array is required to be sorted: `levels`,
`maturity_vocabulary`, `relation_vocabulary`, and `target_kind_vocabulary` are fixed-vocabulary arrays
compared by exact equality (so their authored order is significant); `authorization_records` is stored
sorted and duplicate-free; and every nested array (`source_anchors`, `refines`, `acceptance_criteria`,
`covers`) preserves its authored order as declared in §3. The human-readable `.md` files are deterministic
projections of the same models.

## 5. Determinism, bounds, and safety rules

- **Determinism (T008-SR-001, T008-SR-013).** Stable key/element ordering; no timestamps, hostnames,
  absolute paths, or unordered iteration in the register, matrix, or validator output.
- **Bounds (T008-STK-006).** The validator reads only repository-relative files, each ≤ 1 MiB; total input
  ≤ 4 MiB; no recursion outside the repository; wall-clock timeout ≤ 60 s; single-threaded.
- **Offline (T008-SR-013).** No network client, resolver, package manager, or subprocess shell; only file
  reads and pure computation. `git`-based path checks are performed by the deterministic gate and the
  implementation record, not inside the validator.
- **Public safety (T008-SR-012).** No credential, secret, private address, private-key marker, proprietary
  source excerpt, unrestricted payload, or absolute host path in the register, matrix, projections, or
  validator output.
- **Docs-only boundary (T008-SR-011).** The candidate diff contains no `src/`, `tests/`, or `xdl/` path,
  no accepted-ADR rewrite, and no weakened requirement or test. The single added script lives under
  `scripts/`.
- **Ownership consistency (T008-SR-013).** The new script path is recorded under `T-ENABLER`
  `paths_exclusive` in `docs/engineering/xcom/task-ownership.json` and its projection; the change is
  regenerated deterministically and `scripts/validate_xcom_task_ownership.py --verify` and `--check-human`
  must both exit 0 afterwards. No other slice's ownership is changed.

## 6. Register content — level elaboration rules

### 6.1 Stakeholder requirements

Eight stakeholder requirements are fixed by this design:
`XCOM-STK-001` stable logical-interface communication (US1, SC-001/SC-002); `XCOM-STK-002` non-perturbing
observation (US2, SC-003/SC-004/SC-005); `XCOM-STK-003` safe bounded stimulation (US3, SC-006/SC-007);
`XCOM-STK-004` replaceable provider/tool boundary (US4); `XCOM-STK-005` deterministic bounded failure
behaviour (FR-007/FR-010/FR-013/FR-025 and the edge cases); `XCOM-STK-006` XDL-derived configuration and
identity separation (FR-001/FR-002/FR-003/FR-031); `XCOM-STK-007` public-safe reproducible traced delivery
(FR-027/FR-028/FR-029/FR-030/FR-035, SC-009/SC-010); `XCOM-STK-008` local-only external tool access
(FR-032, SC-011).

### 6.2 System requirements

`XCOM-SYS-FR-###` mirrors accepted `FR-###` and `XCOM-SYS-SC-###` mirrors accepted `SC-###`. Each entry
names the accepted anchor in `source_anchors`, refines the applicable stakeholder requirement(s), and
reproduces the accepted normative text: its `statement` and its anchor-prefixed `title` must equal the
accepted FR/SC text after whitespace normalization. No accepted functional requirement or success criterion
is dropped, added, renumbered, truncated, or reworded; a violation fails validation (NEG-04..NEG-06,
NEG-24).

### 6.3 Software requirements

Software requirements are authored per family from the accepted spec, plan, contracts, and data model,
each refining ≥ 1 system requirement and naming its `owning_task`. The implementation stage links each to
planned design units, source paths, tests, and measures. For coverage that already exists in the baseline
(`T-CORE`, `T-OBS`, and the accepted `T-STIM`/T025 slice) the links are `established` and revision-bound
only where an exact accepted revision is recorded; the unreconciled `T012`–`T016`/`T021`–`T024` coverage is
labelled `partial` with an `unreconciled` reason and `planned` links (T008-SR-009).

## 7. Validator design

### 7.1 Interface

`scripts/validate_xcom_requirements_traceability.py` supports:

| Mode | Behaviour |
| --- | --- |
| `--self-test` | Runs controlled positive and negative fixtures for every NEG case. |
| `--verify` (default) | Validates `requirements-register.json` and `traceability-matrix.json` against §3–§6 and §7.2. |
| `--check-human` | Confirms both `.md` files are the deterministic projections of the JSON models. |

Exit classes (distinct nonzero per class, lowest numeric when several apply):

| Exit | Class | Covers |
| ---: | --- | --- |
| 0 | `OK` | Valid register and matrix |
| 2 | `SCHEMA_INVALID` | Top-level/per-entry field, array ordering/uniqueness, or schema version differs |
| 3 | `ID_INVALID` | Duplicate id, unknown level, unknown maturity token, or bad family pattern |
| 4 | `SYSTEM_COVERAGE_INVALID` | Missing/duplicated/mismatched FR or SC coverage, or system text drifting from the accepted FR/SC |
| 5 | `REFINEMENT_INVALID` | Orphan stakeholder/system requirement, self-refinement, or refinement cycle |
| 6 | `REF002_INVALID` | Missing/duplicated REF-002 ID, unknown disposition, or promoted target |
| 7 | `TRACEABILITY_INVALID` | Dangling target, unknown relation/kind, forward-only link, orphan artifact, or `refines` mismatch |
| 8 | `MATURITY_INVALID` | Unproven `implemented`, missing reason, or T007-reconciliation contradiction |
| 9 | `BINDING_INVALID` | Malformed baseline, unknown authorization reference, or an unavailable reconciliation dependency |
| 10 | `DETERMINISM_INVALID` | Two serializations or a markdown projection differ |
| 11 | `PUBLIC_SAFETY_INVALID` | Prohibited content class found |
| 12 | `IO_ERROR` | Input unreadable or over bound |

### 7.2 Algorithm

```text
validate(register, matrix):
  require specs/007-xcom-core/spec.md present and readable; else fail (IO_ERROR)
  check schema_version, task_id, capability, baseline_revision, candidate_revision_rule
  check levels == ["stakeholder","system","software"]; maturity vocabulary closed
  check authorization_records set; counts consistent with entries and non-empty families
  for each requirement:
    check id pattern/level/family consistency and uniqueness
    check mandatory non-empty fields and >= 1 acceptance criterion
    check refines ids resolve; stakeholders have empty refines; others non-empty
    check system FR/SC have exactly one accepted FR-###/SC-### anchor
    check each system statement/title equals the accepted FR/SC text (whitespace-normalized)
    check maturity in vocabulary and reconciliation reason present iff required
  check FR anchors == FR-001..FR-035 exactly once; SC anchors == SC-001..SC-011 exactly once
  check requirements/ref002_dispositions/artifacts/links are sorted by id; artifact/link ids unique
  build refinement graph; require acyclic; require every STK has a child SYS and every
    SYS has a child SW (no orphan parent; no orphan child)
  check ref002_dispositions == XVE-SYS-0139..0158 exactly once
    check disposition == accepted table; maturity == architectural-target
    check applied IDs have non-empty covers of system ids; deferred IDs have owner+reason
    check no allocated/deferred ID is referenced by any established implemented_by link
  check matrix vocabularies; every artifact revision_binding is a 40-hex revision when the
    artifact is established and the literal planned otherwise; every link from/to resolves;
    no unknown relation/kind
  check matrix refines links agree with register refines
  require every declared artifact to be referenced by >= 1 link (no orphan artifact)
  for each requirement by maturity:
    implemented -> >= 1 established source + >= 1 established test + >= 1 established measure,
                   each link and its artifact carrying an exact 40-hex revision binding
    partial/allocated -> >= 1 allocated_to and >= 1 verified_by (planned allowed)
    deferred -> no implemented_by link; a recorded reason
    superseded/conflicting/needs_clarification -> a recorded disposition note
  require docs/engineering/xcom/task-ownership.json present, readable, and well-formed;
    if unavailable -> fail closed (no reconciliation skip); else check reconciliation consistency
  check determinism: re-serialize both models; require byte-identical
  check public-safety: scan for absolute paths, credentials, private addresses, key markers
  report highest-precedence failure or OK
```

### 7.3 REF-002 handling

The register's `ref002_dispositions` is a faithful copy of the accepted capability-007 table. T008 promotes
no `architectural-target` to `implemented`; the validator rejects any promoted target (exit 6) and any
`established` implementation link into a deferred ID (exit 6). The authoritative disposition table remains
`specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/sads-requirements-traceability.json`.

## 8. Ordering and closure constraints (validator-enforced)

1. `FR-001..FR-035` and `SC-001..SC-011` coverage is exact and one-to-one.
2. Every stakeholder requirement is refined by ≥ 1 system requirement.
3. Every system requirement is refined by ≥ 1 software requirement.
4. The refinement graph is acyclic; no self-refinement.
5. Every declared artifact is referenced by ≥ 1 requirement; every non-deferred requirement reaches
   ≥ 1 downstream artifact.
6. `implemented` requires established source, test, and measure links with exact revision bindings.
7. Every deferred REF-002 ID carries a reason and no implementation link.

Each constraint is enforced by a distinct check; the self-test includes a register-schema fixture
(NEG-01) and a matrix-schema fixture (NEG-21), a malformed established-artifact binding (NEG-22), a
planned artifact carrying a SHA (NEG-23), a truncated system statement (NEG-24), declared ordering and
uniqueness fixtures (NEG-25 duplicated link id, NEG-26 duplicated artifact id, NEG-27 out-of-order
requirement array), and an unavailable ownership dependency (NEG-28). It neutralises one check at a time
and confirms the corresponding NEG fixture fails, so all fourteen check functions
(`_check_register_schema`, `_check_matrix_schema`, `_check_ordering`, `_check_identity`,
`_check_system_coverage`, `_check_system_fidelity`, `_check_refinement`, `_check_ref002`,
`_check_traceability`, `_check_maturity`, `_check_reconciliation_dependency`, `_check_binding`,
`_check_determinism`, `_scan_public_safety`) are load-bearing (`verification-plan.md` DET-04).

## 9. Alternatives considered

| Alternative | Rejected because |
| --- | --- |
| Copy the accepted FR/SC into a new register without a separate software level | Provides no traceability to design/code/test/measure and leaves no implementable refinement layer (FR-030). |
| Keep the SESN requirement/link JSON shapes as the forward format | ADR-0020 retires SESN for forward work; historical SESN records stay revision-bound evidence only. |
| Store only prose tables in `requirements.md` | Not machine checkable; orphan requirements/units/tests cannot be proven absent; determinism and public safety cannot be validated. |
| Place the register under `specs/007-xcom-core/` | That path is shared with the accepted specification; a T008-only generated artifact would create conflicting writers. The per-task `docs/engineering/xcom/t008/` directory is already exclusively owned by `T-ENABLER`. |
| Treat existing T012–T024 source as `implemented` | Source presence is not acceptance evidence (Constitution art. IX; analysis A12); those requirements are `partial`/`unreconciled`. |
| Fold the matrix into the register | Requirement content and link evidence have different revision lifecycles; separating them keeps determinism and refresh independent. |

## 10. Requirement-to-design trace

| Requirement | Design section |
| --- | --- |
| T008-SR-001 | §3, §4, §5 |
| T008-SR-002 | §3 |
| T008-SR-003 | §3, §6.2 |
| T008-SR-004 | §3, §6.2 |
| T008-SR-005 | §6.1, §6.3, §8 |
| T008-SR-006 | §3, §7.3 |
| T008-SR-007 | §4, §7.2 |
| T008-SR-008 | §4, §7.2, §8 |
| T008-SR-009 | §3, §6.3, §7.2, §8 |
| T008-SR-010 | §3, §4, §5 |
| T008-SR-011 | §2, §5 |
| T008-SR-012 | §5, §7.2 |
| T008-SR-013 | §5, §7 |

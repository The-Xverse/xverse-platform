# T008 Implementation Record — Requirement Register, Traceability Matrix, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T008 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | implement → implementation record (revision 4 repair of internal-review finding T008-IR-007) |
| Revision | 4 |
| Authorized baseline | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| Candidate state | working tree over the authorized baseline (candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), [`requirements-register.json`](requirements-register.json), [`requirements-register.md`](requirements-register.md), [`traceability-matrix.json`](traceability-matrix.json), [`traceability-matrix.md`](traceability-matrix.md), this record |
| Authorization | ACC001–ACC015, ADR-0018, ADR-0019, ADR-0020; `specs/007-xcom-core/tasks.md` T008 |
| Maturity | Governance work product implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T008 implements the bounded work-product slice required by the T008 task entry: the canonical
capability-007 requirement register, the bidirectional traceability matrix, their deterministic
Markdown projections, and an offline validator with a controlled self-test. It is a
**documentation-and-governance** change plus one offline script. The candidate changes **no** path
under `src/`, `tests/`, or `xdl/`, adds no CMake target or runtime artifact, and does not accept,
complete, or integrate any other task or software candidate.

The register preserves the accepted specification one-to-one: 8 stakeholder requirements, 35 system
functional requirements reproducing `FR-001`–`FR-035` in full, 11 system success criteria reproducing
`SC-001`–`SC-011` in full, and 37 software requirements across the seven declared families. The matrix
declares 21 artifacts and 327 links and materialises the register `refines` relation. All twenty
REF-002 IDs `XVE-SYS-0139`–`0158` are recorded once with their accepted disposition and no promotion.

Each `XCOM-SYS-FR-###`/`XCOM-SYS-SC-###` entry carries the complete accepted normative text (not only its
first physical line): the `statement` and the anchor-prefixed `title` are whitespace-normalized-equal to
the corresponding accepted FR/SC bullet in `specs/007-xcom-core/spec.md`, enforced by
`_check_system_fidelity` (T008-IR-003/004 closure).

## 3. Changed artifacts and symbols

| Artifact | Change | Symbols / structure |
| --- | --- | --- |
| `docs/engineering/xcom/t008/requirements-register.json` | new | Canonical register model, `schema_version = 1`: `levels`, `maturity_vocabulary`, `id_scheme`, `authorization_records`, `counts`, `requirements` (91), `ref002_dispositions` (20). |
| `docs/engineering/xcom/t008/requirements-register.md` | new | Deterministic projection of the register model. |
| `docs/engineering/xcom/t008/traceability-matrix.json` | new | Canonical matrix model, `schema_version = 1`: `relation_vocabulary`, `target_kind_vocabulary`, `artifacts` (21), `links` (327). |
| `docs/engineering/xcom/t008/traceability-matrix.md` | new | Deterministic projection of the matrix model. |
| `scripts/validate_xcom_requirements_traceability.py` | new | `Findings`, `serialize`, `project_register_markdown`, `project_matrix_markdown`, `_parse_accepted_anchors`, `_is_sorted_ids`, `_ids_unique`, `_check_register_schema`, `_check_matrix_schema`, `_check_ordering`, `_check_identity`, `_check_system_coverage`, `_check_system_fidelity`, `_check_refinement`, `_check_ref002`, `_check_traceability`, `_check_maturity`, `_check_reconciliation_dependency`, `_check_binding`, `_check_determinism`, `_scan_public_safety`, `run_checks`, `_self_test` (NEG-01..NEG-28, NEG-19 projection), CLI `--verify`, `--check-human`, `--self-test`. |
| `docs/engineering/xcom/task-ownership.json` | modified | Added `scripts/validate_xcom_requirements_traceability.py` to `T-ENABLER` `paths_exclusive`; no other slice or field changed. |
| `docs/engineering/xcom/task-ownership.md` | modified | Deterministic projection regenerated from the updated model. |
| `specs/007-xcom-core/tasks.md` | modified | T008 checkbox marked complete; no other task line changed. |
| `docs/engineering/xcom/t008/implementation.md` | new | This record. |

No production source, test, XDL asset, accepted ADR, or accepted requirement was changed. The T008
candidate's affected product source paths are none; the product paths it links to are declared as
`planned` artifacts in the matrix (and as `established` only for the accepted T025 revision).

### 3.1 Register content summary

- Requirements: 8 `XCOM-STK-###`, 35 `XCOM-SYS-FR-###`, 11 `XCOM-SYS-SC-###`, 10 `XCOM-SW-CORE-###`,
  3 `XCOM-SW-GW-###`, 3 `XCOM-SW-XDL-###`, 5 `XCOM-SW-OBS-###`, 9 `XCOM-SW-STIM-###`,
  3 `XCOM-SW-INTG-###`, and 4 `XCOM-SW-ENB-###` = 91 entries.
- Refinement closure: every stakeholder requirement is refined by ≥1 system requirement, every
  system requirement by ≥1 software requirement, and the graph is acyclic. Software refines only
  system requirements; system refines only stakeholders.
- Maturity: `XCOM-SW-CORE-###` and `XCOM-SW-OBS-###` are `partial` with the recorded `unreconciled`
  reason (analysis A12; review-016 XCOM-NOSESN-08); `XCOM-SW-STIM-001`/`-002` (T025) are
  `implemented` and revision-bound to the accepted T025 merge
  `4b01586b438a8587d231ee8828d896c206c06a96`; `XCOM-SW-ENB-001`/`-002` are `partial`; all remaining
  software requirements are `allocated`.
- REF-002: 10 IDs allocated to the first prototype and 10 deferred, each with its accepted owner and
  reason; maturity stays `architectural-target`; no allocated or deferred ID carries an
  implementation link.

## 3.2 Repair revision 2 — internal-review finding closure

Revision 1 of this candidate was inspected by the separate read-only internal review recorded in
[`internal-review.json`](internal-review.json) (revision 1, verdict `fail`). Two findings were raised
against the delivered validator; revision 2 repairs them without weakening any accepted requirement,
check, or test: no register or matrix data changed, and no requirement, acceptance criterion, or exit
class was removed.

| Finding | Severity | Repair |
| --- | --- | --- |
| T008-IR-001 | major | `_check_matrix_schema` now enforces the `detailed-design.md` §4 artifact rule: an `established` artifact must carry an exact 40-hex `revision_binding` and a `planned` artifact must carry the literal `planned`, reported as `SCHEMA_INVALID` (2). `_check_maturity` additionally requires the artifact of an implemented requirement's established source/test/measure link to carry an exact 40-hex binding. |
| T008-IR-002 | minor | The self-test gains matrix-schema fixtures NEG-21 (removed matrix top-level field), NEG-22 (established artifact with a non-SHA binding), and NEG-23 (planned artifact with a SHA binding), so `_check_matrix_schema` is now independently exercised. The DET-04 load-bearing claim in `verification-plan.md`, `detailed-design.md` §8, `unit-specifications.md` (U-REG, U-VALIDATE), and this record now matches the fixtures actually present. |

Closure evidence for revision 2 is recorded in commands 13–17 below (self-test, `--verify`,
`--check-human`, the eleven-check neutralisation probe as it stood at revision 2, and the ownership
checks).

## 3.3 Repair revision 3 — internal-review finding closure

Revision 2 was re-inspected by the separate read-only internal review recorded in
[`internal-review.json`](internal-review.json) (revision 3, verdict `fail`). Four findings remained;
revision 3 repairs them without weakening any accepted requirement, check, or test.

| Finding | Severity | Repair |
| --- | --- | --- |
| T008-IR-003 | major | Every `XCOM-SYS-FR-###`/`XCOM-SYS-SC-###` `statement` and anchor-prefixed `title` was restored to the complete accepted FR-001–FR-035/SC-001–SC-011 text (45 of 46 statements and all 46 titles had stopped at the first physical spec line). The register was regenerated byte-stably; `requirements-register.md` is unchanged because the projection does not render title/statement. The §2 "mirror" claim is replaced by the explicit full-text statement above. |
| T008-IR-004 | minor | `_check_system_fidelity` parses the accepted FR/SC text from `specs/007-xcom-core/spec.md` and rejects a system `statement`/`title` that drifts after whitespace normalization; NEG-24 injects a truncated `XCOM-SYS-FR-001` statement and the fresh DET-04 probe confirms the check is load-bearing, so the defect can no longer pass every declared check. |
| T008-IR-005 | minor | `run_checks` now calls `_check_reconciliation_dependency`, which fails closed with `BINDING_INVALID` (9) when `docs/engineering/xcom/task-ownership.json` is missing, unreadable, or has no `slices` array, instead of silently skipping the T012–T016/T021–T024 reconciliation; NEG-28 proves the failure. |
| T008-IR-006 | minor | `_check_ordering` enforces the declared `detailed-design.md` §3/§4 rules: `requirements`, `ref002_dispositions`, `artifacts`, and `links` must be sorted by `id`, and matrix `artifacts`/`links` ids must be unique. NEG-25 (duplicate link id), NEG-26 (duplicate artifact id), and NEG-27 (out-of-order requirement array) prove the enforcement. |

Closure evidence for revision 3 is recorded in commands 18–24 below (self-test over NEG-01..NEG-28,
`--verify`, `--check-human`, the fourteen-check neutralisation probe, the independent normalized-fidelity
comparison, the ownership checks, and the docs-only/baseline checks).

## 3.4 Repair revision 4 — internal-review finding T008-IR-007 closure

Revision 3 was re-inspected by the separate read-only internal review recorded in
[`internal-review.json`](internal-review.json) (revision 4, verdict `fail`). One minor finding remained:
`detailed-design.md` declared nested-array ordering (`refines` "Sorted requirement ids" and "every array
sorted lexicographically except `requirements`") that the register's authored-order nested arrays
contradict and that `_check_ordering` does not enforce. Revision 4 repairs it **without weakening any
accepted check**: no validator check was removed or relaxed, no requirement was weakened, no exit class
changed, and the register and matrix data are byte-unchanged.

| Aspect | Repair |
| --- | --- |
| Disposition | Option (a) of the finding's `required_correction`: narrow the declared ordering guarantee to exactly the arrays the validator enforces, and state the nested-array order explicitly. |
| `detailed-design.md` §3 | `refines` is no longer declared "Sorted"; `source_anchors`/`acceptance_criteria` state their authored order; a new normative **Array ordering** paragraph names exactly `requirements`, `ref002_dispositions`, `artifacts`, and `links` as `id`-sorted and records that the deliberately-unsorted `XCOM-SW-XDL-001.refines = ["XCOM-SYS-FR-031","XCOM-SYS-FR-002"]` and `XCOM-STK-001.source_anchors = ["US1","SC-001","SC-002"]` are valid (primary-first) authored order. |
| `detailed-design.md` §4 | The Serialization rule replaces "every array sorted lexicographically" with the exact enforced set (the four top-level `id`-sorted arrays) plus the fixed-vocabulary, `authorization_records`, and nested-authored-order rules. |
| `scripts/validate_xcom_requirements_traceability.py` | The `_check_ordering` docstring now states the enforced array set; executable behaviour is unchanged, so `_check_ordering` still enforces exactly `requirements`, `ref002_dispositions`, `artifacts`, `links`. |
| Register and projections | No data change: the authored nested order already conforms to the narrowed rule, and `requirements-register.json` (`bc6cc9fe…`) and `requirements-register.md` (`ca1c4357…`) are byte-identical to revision 3. |
| `requirements.md` T008-SR-001 | The acceptance criterion now names the four `id`-sorted top-level arrays explicitly (the statement already did) and states nested arrays carry no sort requirement; no expected result is weakened. |
| `unit-specifications.md` | No change needed: U-REG already names exactly the four top-level arrays as sorted. |

Closure test (the review's option (a)) is reproduced in command 29: a mechanical extraction of the sorted-id
array set named in `detailed-design.md` §4 equals the set `_check_ordering` enforces (exactly four arrays).
Commands 25–32 record the determinism, self-test, neutralisation, ownership, gate, and docs-only evidence.

## 4. Commands, results, and evidence

Environment: Python 3.13.13; repository checkout at baseline `957a60723f99c3a31efba1cbd137c454c4acb462`.

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `python3 -m py_compile scripts/validate_xcom_requirements_traceability.py` | 0 | Validator compiles. |
| 2 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | 0 | `X-COM requirements/traceability validation passed` (CHK-01..CHK-11, CHK-13). |
| 3 | `python3 scripts/validate_xcom_requirements_traceability.py --check-human` | 0 | Both Markdown projections match the JSON models exactly (CHK-12). |
| 4 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` (twice) | 0 | Byte-identical stdout and exit status (DET-01). |
| 5 | `python3 scripts/validate_xcom_requirements_traceability.py --self-test` | 0 | Positive fixture passes; NEG-01..NEG-23 reject with their declared classes (CHK-15). |
| 6 | `python3 scripts/validate_xcom_task_ownership.py --verify` | 0 | T007 register still valid with the new `T-ENABLER` path (CHK-15). |
| 7 | `python3 scripts/validate_xcom_task_ownership.py --check-human` | 0 | Ownership projection matches the updated JSON model. |
| 8 | `git rev-parse 957a607…` | 0 | Prints `957a60723f99c3a31efba1cbd137c454c4acb462` (BND-02). |
| 9 | `git diff --check 957a607… --` | 0 | Clean (BND-06). |
| 10 | `git diff --name-only 957a607… --` | 0 | Only documentation/governance paths; no `src/`, `tests/`, or `xdl/` path (CHK-14, BND-01). |
| 11 | mutation probes: neutralise one check, run `--self-test` | 8 for each probe | Every check is load-bearing (DET-04). |
| 12 | validator `--verify` wall-clock measurement, taken locally with the shell `time` builtin | 0 | Wall clock ≈ 0.16 s (BND-05, ≤ 60 s). |
| 13 | `python3 scripts/validate_xcom_requirements_traceability.py --self-test` (revision 2) | 0 | Positive fixture passes; NEG-01..NEG-23 reject with their declared classes, including the new NEG-21..NEG-23 `SCHEMA_INVALID` cases (CHK-15; T008-IR-002 closure). |
| 14 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` (revision 2) | 0 | `X-COM requirements/traceability validation passed`; the real register and matrix still satisfy the strengthened artifact-binding rule (T008-IR-001 closure). |
| 15 | `python3 scripts/validate_xcom_requirements_traceability.py --check-human` (revision 2) | 0 | Both Markdown projections still match the JSON models exactly (CHK-12). |
| 16 | mutation probes: neutralise each of the eleven check functions, one at a time, and run `--self-test` | nonzero (exit 8) for every probe | All eleven checks are load-bearing, now including `_check_matrix_schema` (DET-04; T008-IR-002 closure). |
| 17 | `python3 scripts/validate_xcom_task_ownership.py --verify` and `--check-human` (revision 2) | 0 | T007 ownership register still valid and its projection unchanged (CHK-15). |
| 18 | `python3 -m py_compile scripts/validate_xcom_requirements_traceability.py` (revision 3) | 0 | Compiles after the new checks and fixtures. |
| 19 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` (revision 3) | 0 | `X-COM requirements/traceability validation passed`; the real register preserves the full accepted text and both arrays are sorted/unique (T008-IR-003/004/006 closure). |
| 20 | `python3 scripts/validate_xcom_requirements_traceability.py --check-human` (revision 3) | 0 | Both Markdown projections still match the JSON models exactly (CHK-12). |
| 21 | `python3 scripts/validate_xcom_requirements_traceability.py --self-test` (revision 3) | 0 | Positive fixture passes; NEG-01..NEG-28 reject with their declared classes, including NEG-24 `SYSTEM_COVERAGE_INVALID`, NEG-25..NEG-27 `SCHEMA_INVALID`, and NEG-28 `BINDING_INVALID` (CHK-15). |
| 22 | mutation probes: neutralise each of the fourteen check functions, one at a time, and run `--self-test` | nonzero (exit 8) for every probe | All fourteen checks are load-bearing, including `_check_ordering`, `_check_system_fidelity`, and `_check_reconciliation_dependency` (DET-04). |
| 23 | independent normalized comparison of all 46 system `statement`/`title` values against `specs/007-xcom-core/spec.md` FR-001–FR-035 and SC-001–SC-011 | 0 | no truncation or drift remains (T008-IR-003/004 closure). |
| 24 | `python3 scripts/validate_xcom_task_ownership.py --verify` and `--check-human`; `git diff --check 957a607… --`; `git diff --name-only 957a607… --` (revision 3) | 0 | T007 register still valid; diff clean; still only documentation/governance paths, no `src/`, `tests/`, or `xdl/` (CHK-14/15, BND-01/06). |
| 25 | `python3 -m py_compile scripts/validate_xcom_requirements_traceability.py` (revision 4) | 0 | Compiles after the `_check_ordering` docstring correction (T008-IR-007 closure). |
| 26 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` (revision 4) | 0 | `X-COM requirements/traceability validation passed`; the real register and matrix still satisfy the narrowed §3/§4 ordering contract (T008-IR-007 closure). |
| 27 | `python3 scripts/validate_xcom_requirements_traceability.py --check-human` (revision 4) | 0 | Both Markdown projections still match the JSON models exactly (CHK-12); `requirements-register.md` byte-identical to revision 3. |
| 28 | `python3 scripts/validate_xcom_requirements_traceability.py --self-test` (revision 4) | 0 | Positive fixture passes; NEG-01..NEG-28 reject with their declared classes (CHK-15). |
| 29 | closure test (option (a)): extracted the `id`-sorted array set named in `detailed-design.md` §4 and the set `_check_ordering` iterates | match | Both equal `{requirements, ref002_dispositions, artifacts, links}`; the design names only arrays the validator enforces (T008-IR-007 closure). |
| 30 | mutation probes: neutralise each of the fourteen check functions, one at a time, and run `--self-test` | nonzero (exit 8) for every probe | All fourteen checks, including `_check_ordering`, remain load-bearing after the repair (DET-04). |
| 31 | two `--verify` runs (byte-identical stdout `sha256 aff780c7…`, wall clock 0.066 s); `validate_xcom_task_ownership.py --verify`/`--check-human`; `git diff --check`; `git diff --name-only` (revision 4) | 0 | Determinism and runtime bound hold; T007 register still valid; diff clean and still only documentation/governance paths (CHK-12/14/15, DET-01, BND-01/05/06). |
| 32 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T008 957a607…` (revision 4) | 0 | `{"ok": true, "task_id": "T008", "changed_paths": 14, "checks": []}`; the deterministic gate accepts the repaired candidate (T008-SR-011). |

Self-test detail (commands 5, 21):

```
positive fixture: passed
NEG-01: rejected with SCHEMA_INVALID (exit 2)
NEG-02: rejected with ID_INVALID (exit 3)
NEG-03: rejected with ID_INVALID (exit 3)
NEG-04: rejected with SYSTEM_COVERAGE_INVALID (exit 4)
NEG-05: rejected with SYSTEM_COVERAGE_INVALID (exit 4)
NEG-06: rejected with SYSTEM_COVERAGE_INVALID (exit 4)
NEG-07: rejected with REFINEMENT_INVALID (exit 5)
NEG-08: rejected with REFINEMENT_INVALID (exit 5)
NEG-09: rejected with REFINEMENT_INVALID (exit 5)
NEG-10: rejected with REF002_INVALID (exit 6)
NEG-11: rejected with REF002_INVALID (exit 6)
NEG-12: rejected with TRACEABILITY_INVALID (exit 7)
NEG-13: rejected with TRACEABILITY_INVALID (exit 7)
NEG-14: rejected with TRACEABILITY_INVALID (exit 7)
NEG-15: rejected with MATURITY_INVALID (exit 8)
NEG-16: rejected with MATURITY_INVALID (exit 8)
NEG-17: rejected with MATURITY_INVALID (exit 8)
NEG-18: rejected with BINDING_INVALID (exit 9)
NEG-20: rejected with PUBLIC_SAFETY_INVALID (exit 11)
NEG-21: rejected with SCHEMA_INVALID (exit 2)
NEG-22: rejected with SCHEMA_INVALID (exit 2)
NEG-23: rejected with SCHEMA_INVALID (exit 2)
NEG-24: rejected with SYSTEM_COVERAGE_INVALID (exit 4)
NEG-25: rejected with SCHEMA_INVALID (exit 2)
NEG-26: rejected with SCHEMA_INVALID (exit 2)
NEG-27: rejected with SCHEMA_INVALID (exit 2)
NEG-19: tampered projection rejected with DETERMINISM_INVALID (exit 10)
NEG-28: missing ownership register rejected with BINDING_INVALID (exit 9)
X-COM requirements/traceability self-test passed
```

DET-04 mutation probes (commands 11, 16, 22): neutralising `_check_register_schema`,
`_check_matrix_schema`, `_check_ordering`, `_check_reconciliation_dependency`, `_check_identity`,
`_check_system_coverage`, `_check_system_fidelity`, `_check_refinement`, `_check_ref002`,
`_check_traceability`, `_check_maturity`, `_check_binding`, `_check_determinism`, and
`_scan_public_safety` one at a time makes the self-test exit nonzero, so each of the fourteen checks is
load-bearing rather than decorative.

Artifact identity at this candidate state:

| Artifact | sha256 | Bytes |
| --- | --- | ---: |
| `docs/engineering/xcom/t008/requirements-register.json` | `bc6cc9feb315b3b2f88acb1880302b9e0545dfb99baf2a48972c8a3f93d472af` | 97071 |
| `docs/engineering/xcom/t008/requirements-register.md` | `ca1c4357f6fa6014b93483f3fb9e039f4145be00e12d01bb5d5ed81ab23885d3` | 13401 |
| `docs/engineering/xcom/t008/traceability-matrix.json` | `eb3510e3a7c5489e8af0ee0c015098dff7e7661da871b15c4e74efaa8e2fae9f` | 93077 |
| `docs/engineering/xcom/t008/traceability-matrix.md` | `83fe6c8efc5b4e52693c41e1899fd8355ca3ecd1997644b7c9a9346396950139` | 37823 |
| `scripts/validate_xcom_requirements_traceability.py` | `ba82b783c5004d371ef4841e06c0f6aca03ef77079e4473378ef73ee2d3188fd` | 74749 |
| `docs/engineering/xcom/task-ownership.json` | `d3f628550567c5b90b1b5d6071fc2cf6d3980ed2eed96c239097ecfce5de9c70` | 28333 |
| `docs/engineering/xcom/task-ownership.md` | `6cbbc99a58f49c64119040699b117a17a8ea5fc8c4232158b793cf17f37098de` | 21446 |
| `specs/007-xcom-core/tasks.md` | `88243c3c43596327327824b30042d35ad83714540482826b88d2fb6c3b4493af` | 8026 |

Hashes and bounded outputs are bound to this candidate state; the deterministic gate re-runs after
the checkbox update and its output is retained by the workflow. A successor candidate (for example a
repair) must record its own exact revision and repeat the affected checks.

## 5. Requirement-to-evidence trace

| Requirement | Checks / evidence |
| --- | --- |
| T008-SR-001 | CHK-01, CHK-12, DET-01, NEG-01, NEG-19, NEG-21, NEG-22, NEG-23, NEG-25, NEG-26, NEG-27 (commands 2, 3, 4, 5, 13, 19, 20, 21) |
| T008-SR-002 | CHK-02, NEG-02, NEG-03 (commands 2, 5, 19, 21) |
| T008-SR-003 | CHK-03, NEG-04, NEG-05, NEG-24 (commands 2, 5, 19, 21, 23) |
| T008-SR-004 | CHK-04, NEG-06 (commands 2, 5, 19, 21, 23) |
| T008-SR-005 | CHK-05, CHK-06, NEG-07, NEG-08, NEG-09 (commands 2, 5, 19, 21) |
| T008-SR-006 | CHK-07, NEG-10, NEG-11 (commands 2, 5, 19, 21) |
| T008-SR-007 | CHK-08, NEG-12, NEG-13, NEG-14 (commands 2, 5, 19, 21) |
| T008-SR-008 | CHK-09, NEG-14, DET-04 (commands 2, 5, 11, 19, 22) |
| T008-SR-009 | CHK-10, NEG-15, NEG-16, NEG-17, NEG-28 (commands 2, 5, 19, 21) |
| T008-SR-010 | CHK-11, NEG-18, BND-02 (commands 2, 5, 8, 19, 21) |
| T008-SR-011 | CHK-14, BND-01, BND-06, deterministic gate (commands 9, 10, 24) |
| T008-SR-012 | CHK-13, NEG-20 (commands 2, 5, 19, 21; validator content scan) |
| T008-SR-013 | CHK-12, CHK-15, DET-01..DET-04, BND-03..BND-05 (commands 1–7, 11–24) |

REF-002: no direct communication requirement `XVE-SYS-0139–0158` is implemented, promoted, or
unlinked. All twenty dispositions are recorded exactly as accepted; the authoritative table remains
`specs/007-xcom-core/reference-traceability.md`.

## 6. Limitations and honesty notes

1. **No acceptance or integration claim.** T008 implements and locally verifies only its own bounded
   work products. It does not accept or integrate any candidate, including itself, and it claims no
   external review or user acceptance. The internal review is a separate read-only stage; external
   Codex review is deferred until the `xcom-t007-t010-t017-t020` backlog completes.
2. **Reconciliation is recorded, not resolved.** `T012`–`T016` and `T021`–`T024` coverage stays
   `partial`/`unreconciled`; the accepted `T025` slice is the only requirement coverage bound to an
   accepted exact revision. Reconciliation against accepted revisions stays with the owning slices.
3. **Planned product links.** Every product path linked from the matrix other than the accepted T025
   artifacts is declared `planned`; a planned path is a traceability intent, not implementation
   evidence.
4. **Public-safety scan scope.** The validator mechanically detects absolute host paths, private
   IPv4 ranges, credential assignment tokens, private-key markers, and unbounded base64-like tokens.
   The non-mechanical classes (proprietary source excerpts, unrestricted payloads) are assessed by
   the review stage; inspection finds none in the register, matrix, projections, or output.
5. **No runtime evidence.** T008 has no runtime artifact, so no performance, availability, or
   concurrency claim is made; the validator is offline, single-threaded, and bounded (≤ 1 MiB per
   file, ≤ 4 MiB total, no network or subprocess, wall clock well under 60 s).
6. **Environment identity is recorded, not pinned by T008.** Compiler/dependency admission with
   hashes and licenses is T011's deliverable; this record names only the Python interpreter used.
7. **External review deferred.** The separate read-only review is a distinct stage recorded in
   [`internal-review.json`](internal-review.json); the copy present at this candidate state is the
   predecessor (revision 4) review of the revision-3 candidate, and the workflow's internal-review stage
   re-inspects this repaired candidate. It is a DeepSeek internal pass, not the external Codex review, and
   it does not constitute user acceptance.
8. **Reconciliation and fidelity dependencies fail closed (revision 3).** The validator now reads
   `specs/007-xcom-core/spec.md` (accepted FR/SC text) and `docs/engineering/xcom/task-ownership.json`
   (reconciliation state) as bounded inputs. A missing or unreadable ownership register is a hard
   `BINDING_INVALID` failure (NEG-28), not a skip; a system statement/title that drifts from the accepted
   text is a hard `SYSTEM_COVERAGE_INVALID` failure (NEG-24). Fidelity is compared after whitespace
   normalization, so line wrapping in the accepted spec is not significant while normative wording is.

# T008 Verification Plan — Named Checks, Commands, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T008 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `957a60723f99c3a31efba1cbd137c454c4acb462` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | repository-owned Python 3.11-compatible validator plus the deterministic Fabro gate; no C++/GTest case is added by T008 |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
Because T008 is a documentation/governance task, the checks are deterministic static checks over the
requirement register and the traceability matrix; the deterministic gate for T008 runs no C++/Python test
suite.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T008 957a60723f99c3a31efba1cbd137c454c4acb462
```

For T008 this gate requires:

- `docs/engineering/xcom/t008/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` present;
- the T008 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- a changed-path set containing **no** `src/`, `tests/`, or `xdl/` path (T008 is a work-product task; the
  added `scripts/` validator is permitted);
- `git diff --check <baseline> --` clean.

Supporting commands (same tools, no network):

```sh
python3 scripts/validate_xcom_requirements_traceability.py --self-test
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_requirements_traceability.py --check-human
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
git rev-parse 957a60723f99c3a31efba1cbd137c454c4acb462
git diff --name-only 957a60723f99c3a31efba1cbd137c454c4acb462 --
git diff --check 957a60723f99c3a31efba1cbd137c454c4acb462 --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Register and matrix parse and match the schema | `--verify` on both JSON models | exit 0; `schema_version == 1`; fixed fields/order; every declared array sorted by id; matrix link/artifact ids unique |
| CHK-02 | Requirement identity, level, and vocabulary | `--verify` | unique ids; levels/vocabulary closed; all mandatory fields non-empty |
| CHK-03 | System functional coverage and text fidelity | `--verify` | FR anchors equal `FR-001..FR-035` exactly once; counts match; each FR statement/title equals the accepted spec text after whitespace normalization |
| CHK-04 | System success-criterion coverage and text fidelity | `--verify` | SC anchors equal `SC-001..SC-011` exactly once; each SC statement/title equals the accepted spec text after whitespace normalization |
| CHK-05 | Stakeholder→system refinement | `--verify` | exactly `XCOM-STK-001..008`; each refined by ≥ 1 system requirement; no orphan |
| CHK-06 | System→software refinement | `--verify` | every system requirement refined by ≥ 1 software requirement; families declared; acyclic |
| CHK-07 | REF-002 disposition completeness | `--verify` | `XVE-SYS-0139..0158` once each; dispositions equal the accepted table; no promotion |
| CHK-08 | Link resolution and matrix id integrity | `--verify` | every link resolves; only declared relations/kinds; no orphan artifact; artifact/link ids unique and arrays sorted by id |
| CHK-09 | Bidirectional closure | `--verify` | downward closure for non-deferred requirements; upward closure for every artifact; matrix `refines` agrees with the register |
| CHK-10 | Maturity and evidence honesty | `--verify` | `implemented` fully evidenced and revision-bound; T012–T016/T021–T024 `partial`/`unreconciled`; T007 state consistent; a missing/unreadable ownership register fails closed (exit 9) |
| CHK-11 | Baseline and authorization binding | `--verify` + `git rev-parse` | both models bind the run baseline; authorization refs resolvable; planned vs established distinguished |
| CHK-12 | Deterministic serialization | `--verify` twice, `--check-human` | both JSON runs byte-identical; both markdown projections exact |
| CHK-13 | Public-safety scan | `--verify` plus manual inspection | no credential, private address, key marker, unrestricted payload, or absolute host path in models, projections, or output |
| CHK-14 | Docs-only boundary | `git diff --name-only <baseline> --` | no path starts with `src/`, `tests/`, or `xdl/`; the only added executable is `scripts/validate_xcom_requirements_traceability.py` |
| CHK-15 | Ownership consistency and validator self-test | `validate_xcom_task_ownership.py --verify/--check-human`; `--self-test` | T007 register still exits 0 with the new `T-ENABLER` path; positive fixture passes; every NEG case fails with its declared exit class |

## 4. Negative cases (validator self-test fixtures)

Each NEG case injects one controlled defect — into a copy of the register/matrix, or by withholding the
T007 ownership dependency (NEG-28) — and asserts the declared nonzero exit with **no** partial success and
no output claiming a valid model.

| ID | Injected defect | Expected exit / class |
| --- | --- | --- |
| NEG-01 | Remove a required top-level field or reorder keys | 2 `SCHEMA_INVALID` |
| NEG-02 | Duplicate a requirement id | 3 `ID_INVALID` |
| NEG-03 | Set a requirement level/maturity to an unknown token | 3 `ID_INVALID` |
| NEG-04 | Remove one system `XCOM-SYS-FR-###` entry | 4 `SYSTEM_COVERAGE_INVALID` |
| NEG-05 | Duplicate/renumber an FR anchor (two entries share `FR-007`) | 4 `SYSTEM_COVERAGE_INVALID` |
| NEG-06 | Remove one system `XCOM-SYS-SC-###` entry | 4 `SYSTEM_COVERAGE_INVALID` |
| NEG-07 | Remove every `refines` child of one stakeholder requirement | 5 `REFINEMENT_INVALID` |
| NEG-08 | Remove every software requirement refining one system requirement | 5 `REFINEMENT_INVALID` |
| NEG-09 | Introduce a refinement cycle or self-refinement | 5 `REFINEMENT_INVALID` |
| NEG-10 | Remove one REF-002 ID from the disposition set | 6 `REF002_INVALID` |
| NEG-11 | Mark an allocated/deferred REF-002 ID `implemented` | 6 `REF002_INVALID` |
| NEG-12 | Point a link `to` at an undeclared artifact id | 7 `TRACEABILITY_INVALID` |
| NEG-13 | Use an unknown link relation | 7 `TRACEABILITY_INVALID` |
| NEG-14 | Add a forward `implemented_by` link without the reverse requirement reference (orphan artifact) | 7 `TRACEABILITY_INVALID` |
| NEG-15 | Mark a requirement `implemented` without a test/measure link | 8 `MATURITY_INVALID` |
| NEG-16 | Mark a requirement `implemented` without an exact revision binding | 8 `MATURITY_INVALID` |
| NEG-17 | Label unreconciled T012–T016 source `implemented` (or drop the `unreconciled` reason) | 8 `MATURITY_INVALID` |
| NEG-18 | Set a model baseline to a short/empty string | 9 `BINDING_INVALID` |
| NEG-19 | Tamper the markdown projection (reorder a section) and run `--check-human` | 10 `DETERMINISM_INVALID` |
| NEG-20 | Insert an absolute host path or private address token | 11 `PUBLIC_SAFETY_INVALID` |
| NEG-21 | Remove a required matrix top-level field (register-schema counterpart NEG-01) | 2 `SCHEMA_INVALID` |
| NEG-22 | Give an established artifact a non-SHA `revision_binding` | 2 `SCHEMA_INVALID` |
| NEG-23 | Give a planned artifact a 40-hex `revision_binding` | 2 `SCHEMA_INVALID` |
| NEG-24 | Truncate/reword a system requirement `statement` away from the accepted FR text | 4 `SYSTEM_COVERAGE_INVALID` |
| NEG-25 | Duplicate a link id | 2 `SCHEMA_INVALID` |
| NEG-26 | Duplicate an artifact id | 2 `SCHEMA_INVALID` |
| NEG-27 | Store the requirement array out of id order | 2 `SCHEMA_INVALID` |
| NEG-28 | Remove/bypass the T007 ownership register so reconciliation is unavailable | 9 `BINDING_INVALID` |

A mutation probe that neutralises any one check makes the self-test fail, which is the load-bearing
evidence recorded in `implementation.md` (DET-04). The probe covers all fourteen check functions,
including `_check_matrix_schema` (NEG-21..NEG-23), `_check_system_fidelity` (NEG-24), `_check_ordering`
(NEG-25..NEG-27), and `_check_reconciliation_dependency` (NEG-28).

### 4.1 Declared-ordering contract consistency (T008-IR-007 closure)

The declared array-ordering contract is exactly the set the validator enforces: ascending `id` order for the
four top-level arrays `requirements`, `ref002_dispositions`, `artifacts`, and `links`, with unique matrix
`artifacts`/`links` ids (`detailed-design.md` §3/§4, `_check_ordering`). Nested arrays (`source_anchors`,
`refines`, `acceptance_criteria`, `covers`) and the fixed-vocabulary arrays preserve their authored order and
carry no lexical-sort guarantee. Closing check **ORD-01**: the `id`-sorted array set named in
`detailed-design.md` §4 must equal the set `_check_ordering` iterates; they must both be the four arrays.

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| ORD-01 | Declared ordering contract matches enforcement | inspect `detailed-design.md` §3/§4 against `_check_ordering`, or extract both name sets mechanically | identical four-array sets; `--verify`, `--check-human`, and `--self-test` exit 0 on the real data; `requirements-register.md` remains the byte-exact projection |

Reproduced at revision 4: ORD-01 matches (both sets are `{requirements, ref002_dispositions, artifacts,
links}`); NEG-25..NEG-27 still reject with `SCHEMA_INVALID` (2); all three validator modes exit 0; and
`requirements-register.{json,md}` are byte-unchanged from revision 3. The repair narrows the *declared* rule
to the enforced behaviour and weakens no accepted check. Evidence is recorded in `implementation.md`
commands 25–31.

**Precedence closure.** When several defects are present, the validator must return the numerically lowest
applicable exit class and report all diagnostics in deterministic order; a failure must never report `OK`.

## 5. Determinism and boundary cases

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| DET-01 | Byte-identical serialization | serialize each model twice | identical bytes |
| DET-02 | Markdown projection | `--check-human` after a manual key reorder | mismatch detected; exit 10 |
| DET-03 | Stable diagnostics | inject two defects, run twice | identical output and exit |
| DET-04 | New checks are load-bearing | neutralise one check at a time, run `--self-test` | the corresponding NEG case fails, so the self-test exits nonzero |
| BND-01 | Docs-only diff | `git diff --name-only <baseline> --` | no `src/`, `tests/`, or `xdl/` path |
| BND-02 | Baseline resolves | `git rev-parse <baseline>` | prints the baseline SHA |
| BND-03 | Bounded input | each model ≤ 1 MiB, totals ≤ 4 MiB | accepted; over bound → exit 12 |
| BND-04 | Offline | no network/subprocess in the validator | no syscall to any peer; source inspection plus review |
| BND-05 | Runtime bound | wall clock ≤ 60 s | holds on the local checkout |
| BND-06 | Clean diff | `git diff --check <baseline> --` | no whitespace errors |

## 6. Concurrency and resource bounds

T008 has **no runtime concurrency**: the register and matrix are static documents and the validator is
single-threaded and offline. Concurrency is therefore not applicable, and the plan does not invent a
concurrency case. The applicable bounds are BND-03 (input size), BND-04 (no network/subprocess), BND-05
(runtime ≤ 60 s), and determinism DET-01..DET-03. Production concurrency/resource bounds remain owned by
the implementation slices (`T-CORE`, `T-OBS`, `T-STIM`) and their own verification plans.

## 7. Requirement traceability

| Requirement | Checks |
| --- | --- |
| T008-SR-001 | CHK-01, CHK-12, ORD-01, NEG-01, NEG-21, NEG-22, NEG-23, NEG-25, NEG-26, NEG-27, DET-01, DET-02 |
| T008-SR-002 | CHK-02, NEG-02, NEG-03 |
| T008-SR-003 | CHK-03, NEG-04, NEG-05, NEG-24 |
| T008-SR-004 | CHK-04, NEG-06 |
| T008-SR-005 | CHK-05, CHK-06, NEG-07, NEG-08, NEG-09 |
| T008-SR-006 | CHK-07, NEG-10, NEG-11 |
| T008-SR-007 | CHK-08, NEG-12, NEG-13 |
| T008-SR-008 | CHK-09, NEG-14, DET-04 |
| T008-SR-009 | CHK-10, NEG-15, NEG-16, NEG-17, NEG-28 |
| T008-SR-010 | CHK-11, NEG-18, BND-02 |
| T008-SR-011 | CHK-14, BND-01, BND-06, gate step |
| T008-SR-012 | CHK-13, NEG-20 |
| T008-SR-013 | CHK-15, DET-01..DET-04, BND-03..BND-05 |

## 8. Implementation-stage sequence

1. Author `docs/engineering/xcom/t008/requirements-register.json` implementing `detailed-design.md`
   §3/§6, and its deterministic projection `requirements-register.md`.
2. Author `docs/engineering/xcom/t008/traceability-matrix.json` implementing §4, and its projection
   `traceability-matrix.md`.
3. Create `scripts/validate_xcom_requirements_traceability.py` implementing §7 and the self-test.
4. Run `--self-test`, `--verify`, and `--check-human`; run the mutation probes (DET-04).
5. Record the new script path under `T-ENABLER` in `docs/engineering/xcom/task-ownership.{json,md}` and
   re-run `scripts/validate_xcom_task_ownership.py --verify` and `--check-human`.
6. Run `git diff --check` and the docs-only diff.
7. Record the candidate revision, commands, tool versions, exit codes, and bounded outputs in
   `docs/engineering/xcom/t008/implementation.md`.
8. Mark the T008 checkbox complete in `specs/007-xcom-core/tasks.md` (implementation stage only).
9. Run the deterministic gate in §2 and retain its output.

## 9. Evidence to retain with the candidate revision

- The gate command stdout/stderr and exit status.
- `--self-test`, `--verify`, and `--check-human` outputs and exit codes for the T008 validator.
- The T007 ownership validator `--verify`/`--check-human` outputs showing the consistency update holds.
- The mutation-probe (DET-04) output showing each new check is load-bearing.
- The `git diff --name-only` and `git diff --check` outputs proving the docs-only boundary.
- The candidate revision hash and the Python/tool identities used.
- The ORD-01 declared-ordering/enforcement set comparison (T008-IR-007 closure).
- The register and matrix file hashes recorded in the T008 package manifest.

Evidence must be bound to the exact candidate revision; missing, stale, or mismatched evidence cannot
support acceptance. This plan records no external-review or user-acceptance claim; external Codex review
is deferred until the `xcom-t007-t010-t017-t020` backlog completes.

## 10. Review plan (separate pass, not performed here)

The T008 requirements and traceability are reviewed in a separate read-only pass that:
records findings before any repair; verifies the register's one-to-one FR/SC coverage, refinement closure,
REF-002 non-promotion, maturity honesty, and traceability resolution independently of the validator;
confirms the docs-only boundary and public safety; and produces `docs/engineering/xcom/t008/internal-review.json`
with `task_id = "T008"`, the run baseline, a `pass`/`fail` verdict, and an empty `findings` list on pass.
T008 itself performs no acceptance and marks no other task complete.

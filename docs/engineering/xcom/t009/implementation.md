# T009 Implementation Record — Architecture Model, Projection, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T009 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | repair → implementation record (revision 2; successor to the revision-1 implement record) |
| Revision | 2 |
| Authorized baseline | `209084b11a211273f815980f753ba728e1251a09` |
| Candidate state | working tree over the authorized baseline (candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), [`architecture-model.json`](architecture-model.json), [`architecture-model.md`](architecture-model.md), this record |
| Authorization | ACC001–ACC015, ADR-0016, ADR-0018, ADR-0019, ADR-0020; `specs/007-xcom-core/tasks.md` T009 |
| Maturity | Governance/planning work product implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T009 implements the bounded architecture/boundary/diagram/contract work-product slice required by the
T009 task entry: one canonical, schema-versioned architecture model, its deterministic Markdown
projection (including Mermaid diagrams), and an offline validator with a controlled self-test. It is a
**documentation-and-governance** change plus one offline script under `scripts/`. The candidate changes
**no** path under `src/`, `tests/`, `xdl/`, or `proto/`, adds no CMake target or runtime artifact, and
does not accept, complete, or integrate any other task or software candidate.

The model elaborates — it does not replace — the accepted capability-007 architecture in
`specs/007-xcom-core/{plan,data-model}.md` and `specs/007-xcom-core/contracts/*.md`. It declares 13
components, 11 boundaries, 6 contracts, 5 diagrams (one component view + one sequence per US1–US4), and
15 invariants, and it records `ref002.disposition = "unchanged"` with an empty promoted set. Every
component is anchored to real (`established`) or explicitly planned product paths: `established` paths
are verified present and `planned` paths verified absent by `_check_paths`.

### 2.1 Design-detail resolutions

Two accepted-detail decisions were resolved during implementation and are recorded here (they do not
change any accepted requirement, boundary, or contract):

1. **Out-of-process component path marker.** `detailed-design.md` §3 requires every component to carry at
   least one `artifact_paths` entry, while §5 records `XCOM-CMP-012` (external validation tool) as
   owning no repository path (`n/a`). The model therefore stores `XCOM-CMP-012.artifact_paths =
   [{"path": "n/a", "status": "planned"}]`; `_check_identity` permits the literal `n/a` marker only for an
   `external`/`downstream` component, and `_check_paths` skips it. This keeps the non-empty rule uniform
   while honestly recording that the external tool is not owned.
2. **NEG-07 isolation.** The declared NEG-07 fixture removes a required boundary. Removing
   `XCOM-XB-007` would also orphan its sole contract (`XCOM-XLC-006`), which the diagram-coverage check
   independently rejects; the fixture therefore removes `XCOM-XB-002` (whose contract `XCOM-XLC-001` is
   also referenced by `XCOM-XB-003`) together with its diagram step, isolating the defect to the
   required-boundary-set check. The removal-detection behaviour is identical; only the fixture's chosen
   boundary differs from the illustrative name in `verification-plan.md` §4.

### 2.2 Repair pass (revision 2)

The revision-1 internal read-only review recorded verdict `fail` with four findings against the exact
revision-1 candidate. Revision 2 repairs all four without weakening any accepted requirement, check, or
fixture, and re-runs the affected verification. Each correction and its closure evidence:

| Finding | Severity | Correction | Closure evidence |
| --- | --- | --- | --- |
| T009-IR-01 candidate work products untracked | high | Staged the nine candidate work products with `git add` (no commit) so the tracked baseline diff is the full 12-path candidate; `docs/engineering/xcom/t009/internal-review.json` and `reports/xcom-queue/t009-package.json` remain untracked. Command rows 10 and 18 now record the final 12-path inventory. | Command 10 (12 paths), command 18 (`changed_paths: 12`), command 21 (untracked = exactly the review record and the package manifest). |
| T009-IR-02 uncaught `TypeError` on a non-string id | medium | `_check_model_schema` now requires every family entry `id` to be a non-empty string (`SCHEMA_INVALID` 2); `_ids_of` coerces ids to hashable strings so ordering, uniqueness, and set-difference checks stay total. New fixture NEG-32. | Commands 4, 19: NEG-32 rejects with `SCHEMA_INVALID` (2); integer and null ids yield a classified exit with no traceback. The revision-2 sentence below the command table also claimed *list* ids; that case was **not** actually handled and is repaired in §2.3 as T009-IR-05. |
| T009-IR-03 weakened-but-present required invariant not detected | low | `_check_safety` now compares the seven required safety-boundary invariants (`XCOM-INV-03/06/08/11/12/13/15`) against their pinned accepted `(kind, statement)` text (`EXPECTED_REQUIRED_INVARIANTS`). New fixture NEG-33. | Commands 4, 19: NEG-33 rejects with `SAFETY_INVALID` (8); weakened `XCOM-INV-06/08/13/15` statements each reject with exit 8. |
| T009-IR-04 `FR-`/`SC-`/`US` anchors accepted by pattern alone | low | `_check_binding` now resolves anchors against the closed accepted set `FR-001`–`FR-035` / `SC-001`–`SC-011` / `US1`–`US4` (`ACCEPTED_REQUIREMENT_ANCHORS`); a pattern-matching but unaccepted anchor is `BINDING_INVALID` (9). New fixture NEG-34. | Commands 4, 19: NEG-34 (`FR-999`) rejects with `BINDING_INVALID` (9); `SC-099`/`US9` reject, an accepted `FR-032` anchor is accepted. |

Two further review observations were also closed while repairing, because they were inaccurate declared
statements rather than new scope: `architecture.md` §7 now reads `NEG-01..NEG-34` (extended to
`NEG-01..NEG-39` in §2.3), and
`verification-plan.md` §4.1 now restates the stored-sorted nested arrays that `detailed-design.md` §3
declares. `_check_maturity` also enforces the `detailed-design.md` §3 reconciliation rule exactly (present
for `partial`, null otherwise), which command 20 probes; the accepted model already satisfies it, so no
fixture changes.

The model content itself was not changed: the review confirmed it faithful (13 components, 11 boundaries,
6 contracts, 5 diagrams, 15 invariants), and only the validator, the design/governance prose, and the
candidate inventory changed. The accepted baseline, the accepted T025 revision
(`4b01586b438a8587d231ee8828d896c206c06a96`), the requirement register, and the accepted specification are
untouched.

### 2.3 Repair pass (revision 3)

The revision-3 internal read-only review recorded verdict `fail` with one finding (T009-IR-05) against the
exact revision-2 candidate. Revision 3 repairs it without weakening any accepted requirement, check, or
fixture, and re-runs the affected verification. The correction and its closure evidence:

| Finding | Severity | Correction | Closure evidence |
| --- | --- | --- | --- |
| T009-IR-05 uncaught `TypeError` on an unhashable family id | medium | `_check_contracts`, `_check_diagrams`, `_check_neutrality`, and `_check_safety` now coerce every id used as a dict key or set element with `str(...)`, matching `_ids_of`, so a list/dict family id is reported as `SCHEMA_INVALID` (2) instead of aborting with `TypeError: unhashable type`. New fixtures NEG-35..NEG-39. | Commands 4, 19, 21: NEG-35..NEG-39 reject with `SCHEMA_INVALID` (2) and no traceback for list and dict ids on components, boundaries, contracts, and invariants; neutralising any one of the four `str(...)` coercions makes the self-test raise `TypeError` (load-bearing, command 22). |

The revision-2 evidence remains attached to revision 2 and is not extrapolated; revision 3 binds the same
authorized baseline `209084b11a211273f815980f753ba728e1251a09`. The model content, the accepted
specification, and the requirement register are unchanged, so this repair adds no new requirement and
weakens no accepted one.

## 3. Changed artifacts and symbols

| Artifact | Change | Symbols / structure |
| --- | --- | --- |
| `docs/engineering/xcom/t009/architecture-model.json` | new | Canonical model, `schema_version = 1`: closed vocabularies (`layer`, `language`, `boundary_kind`, `contract_kind`, `diagram_kind`, `maturity`, `invariant_kind`, `direction`, `authorization`, `adr`), `ref002`, `counts`, `components` (13), `boundaries` (11), `contracts` (6), `diagrams` (5), `invariants` (15). |
| `docs/engineering/xcom/t009/architecture-model.md` | new | Deterministic projection of the model, including one Mermaid block per diagram. |
| `scripts/validate_xcom_architecture_contracts.py` | new | `Findings`, `serialize`, `project_markdown`, `_check_model_schema` (incl. non-string-id rejection), `_check_ordering`, `_check_identity`, `_check_paths`, `_check_boundaries`, `_check_contracts`, `_check_diagrams`, `_check_governance`, `_check_neutrality`, `_check_safety` (incl. pinned required-invariant content), `_check_binding` (incl. closed accepted-anchor resolution), `_check_maturity`, `_check_dependencies`, `_check_determinism`, `_scan_public_safety`, `run_checks`, `_self_test` (NEG-01..NEG-39, NEG-22 projection), CLI `--verify`, `--check-human`, `--self-test`. |
| `docs/engineering/xcom/task-ownership.json` | modified | Added `scripts/validate_xcom_architecture_contracts.py` to `T-ENABLER` `paths_exclusive`; no other slice or field changed. |
| `docs/engineering/xcom/task-ownership.md` | modified | Deterministic projection regenerated from the updated model. |
| `specs/007-xcom-core/tasks.md` | modified | T009 checkbox marked complete; no other task line changed. |
| `docs/engineering/xcom/t009/implementation.md` | new | This record. |

No production source, test, XDL asset, accepted ADR, or accepted requirement was changed. The T009
candidate's affected product source paths are none; the product paths it anchors are declared
`planned` (and `established` only where baseline source already exists, e.g. the accepted T025
stimulation artifacts).

## 4. Model content summary

- **Components (13).** `XCOM-CMP-001`–`013` across the `xdl-input`, `build-time`, `derived-artifact`,
  `data-plane`, `boundary`, `edge`, `test-fixture`, `external`, and `downstream` layers. `XCOM-CMP-005`
  is the only `intra_layer = true` internal core unit; `XCOM-CMP-012`/`013` are external/downstream and
  own no task. `XCOM-CMP-009` (validation session) and its contract `XCOM-XLC-006` plus boundary
  `XCOM-XB-007` are `implemented`, bound to the accepted T025 merge
  `4b01586b438a8587d231ee8828d896c206c06a96`. The T012–T016/T021–T024 components are `partial` with an
  `unreconciled` reason (analysis A12); T017–T020/T030–T033 components are `allocated`.
- **Boundaries (11).** `XCOM-XB-001`–`011` cover the Python→Python input seam, the artifact seam, the
  Python/JSON→C++ language seam, the in-process core/provider/observation seams, the validation-session
  seam, the local-IPC gateway seams, the provider realization seam, and the downstream/trust seams.
  Boundary-kind/contract-kind consistency and endpoint-language subset checks pass; `ipc` boundaries are
  `local IPC only, no TCP listener`.
- **Contracts (6).** `XCOM-XLC-001` (activation plan, `cross-language-schema`), `002` (local tool
  gateway, `external-rpc`), `003` (observation record), `004` (provider), `005` (XDL resource/Profile
  input, `schema`), `006` (validation stimulation/time). Each declares producer/consumer components,
  endpoint languages, a version, canonical artifact, encoding, unknown-field policy, and an additively
  stated evolution rule.
- **Diagrams (5).** `XCOM-DGM-001` component view plus US1–US4 sequence views; every component appears in
  ≥ 1 `participants` set, every boundary in ≥ 1 step, and every contract is referenced by a covered
  boundary.
- **Invariants (15).** All data-model invariants 1–10 plus the dependency-direction, neutrality, and
  safety invariants; the seven required safety-boundary invariants
  (`XCOM-INV-03/06/08/11/12/13/15`) are present with stable ids, non-empty statements, resolving
  `applies_to`, and a named enforcing check.

## 5. Commands, results, and evidence

Environment: Python 3.13.13; repository checkout at baseline
`209084b11a211273f815980f753ba728e1251a09`.

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `python3 -m py_compile scripts/validate_xcom_architecture_contracts.py` | 0 | Validator compiles. |
| 2 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | 0 | `X-COM architecture/contracts validation passed` (CHK-01..CHK-14). |
| 3 | `python3 scripts/validate_xcom_architecture_contracts.py --check-human` | 0 | `architecture-model.md` is the exact deterministic projection (CHK-12). |
| 4 | `python3 scripts/validate_xcom_architecture_contracts.py --self-test` | 0 | Positive fixture passes; NEG-01..NEG-39 reject with their declared classes (CHK-15). |
| 5 | two `--verify` runs, stdout piped to `sha256sum` | 0 | Byte-identical stdout `864c435a…` (DET-01). |
| 6 | `python3 scripts/validate_xcom_task_ownership.py --verify` | 0 | T007 register valid with the new `T-ENABLER` path (CHK-14). |
| 7 | `python3 scripts/validate_xcom_task_ownership.py --check-human` | 0 | Ownership projection matches the updated JSON model. |
| 8 | `python3 scripts/validate_xcom_task_ownership.py --self-test` | 0 | T007 self-test still passes; no fixture weakened. |
| 9 | `git rev-parse 209084b11a211273f815980f753ba728e1251a09` | 0 | Prints the baseline SHA (BND-02). |
| 10 | `git diff --name-only 209084b11a211273f815980f753ba728e1251a09 --` | 0 | The full 12-path candidate diff (5 plan docs, 3 implementation artifacts, ownership `.{json,md}`, and `specs/007-xcom-core/tasks.md`); no `src/`, `tests/`, `xdl/`, or `proto/` path (CHK-14, BND-01). |
| 11 | `git diff --check 209084b11a211273f815980f753ba728e1251a09 --` | 0 | Clean (BND-06). |
| 12 | validator `--verify` wall clock (shell `time`) | 0 | Wall clock ≈ 0.09 s (BND-05, ≤ 60 s). |
| 13 | DET-04 probe (re-run after repair): neutralise each of the fifteen check functions, run `--self-test` | nonzero (exit 7) for every probe | Every check is load-bearing; no check is decorative. |
| 14 | DET-03 probe: inject two defects (`XCOM-CMP-004` unknown layer + unknown ADR), run twice | 3, 3 | Identical exit and byte-identical diagnostics (DET-03). |
| 15 | BND-03 probe: `_read_bounded` on a >1 MiB file | 13 | `IO_ERROR` over bound (BND-03). |
| 16 | ORD-01 probe: extract the `id`-sorted array names from `detailed-design.md` §3 "Array ordering" and compare with `FAMILIES` | match | Both equal `{components, boundaries, contracts, diagrams, invariants}` (ORD-01). |
| 17 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T009 209084b…` | 0 | `{"ok": true, "task_id": "T009", "changed_paths": 12, "checks": []}` — the deterministic gate accepts the tracked candidate (T009-SR-011). |
| 18 | `git ls-files --others --exclude-standard` | 0 | Untracked set is exactly `docs/engineering/xcom/t009/internal-review.json` and `reports/xcom-queue/t009-package.json`; the nine candidate work products are tracked (T009-IR-01). |
| 19 | adversarial repair probe: non-string ids (integer/null/list/dict across components, boundaries, contracts, invariants), weakened required invariants (`XCOM-INV-06/08/13/15`), and unaccepted anchors (`FR-999`, `SC-099`, `US9`) through `run_checks` | classified exits, no traceback | ids → `SCHEMA_INVALID` (2); weakened invariants → `SAFETY_INVALID` (8); unaccepted anchors → `BINDING_INVALID` (9); accepted `FR-032` → exit 0 (T009-IR-02/03/04/05). |
| 20 | reconciliation-rule probe: give an `allocated` component a reconciliation reason, and remove the reason from a `partial` component | 7 | `GOVERNANCE_INVALID` (7) both ways (`detailed-design.md` §3 "else null" now enforced). |
| 21 | unhashable-id probe: set `components[0].id`, `boundaries[0].id`, `contracts[0].id`, and `invariants[0].id` each to a list (and components to a dict) through `run_checks` | 2 for every case | Each yields `SCHEMA_INVALID` (2) with no traceback; the review's revision-3 reproduction now exits 2 (T009-IR-05, NEG-35..NEG-39). |
| 22 | load-bearing probe: neutralise each of the four `str(...)` id coercions in `_check_contracts`, `_check_diagrams`, `_check_neutrality`, and `_check_safety`, then run `--self-test` in memory | `TypeError: unhashable type: 'list'` for each neutralisation | Every coercion is load-bearing; the uncoerced self-test aborts instead of rejecting (T009-IR-05). |

Self-test detail (command 4):

```
positive fixture: passed
NEG-01: rejected with SCHEMA_INVALID (exit 2)
NEG-02: rejected with IDENTITY_INVALID (exit 3)
NEG-03: rejected with IDENTITY_INVALID (exit 3)
NEG-04: rejected with IDENTITY_INVALID (exit 3)
NEG-05: rejected with BOUNDARY_INVALID (exit 4)
NEG-06: rejected with BOUNDARY_INVALID (exit 4)
NEG-07: rejected with BOUNDARY_INVALID (exit 4)
NEG-08: rejected with CONTRACT_INVALID (exit 5)
NEG-09: rejected with CONTRACT_INVALID (exit 5)
NEG-10: rejected with CONTRACT_INVALID (exit 5)
NEG-11: rejected with DIAGRAM_INVALID (exit 6)
NEG-12: rejected with DIAGRAM_INVALID (exit 6)
NEG-13: rejected with DIAGRAM_INVALID (exit 6)
NEG-14: rejected with GOVERNANCE_INVALID (exit 7)
NEG-15: rejected with GOVERNANCE_INVALID (exit 7)
NEG-16: rejected with GOVERNANCE_INVALID (exit 7)
NEG-17: rejected with GOVERNANCE_INVALID (exit 7)
NEG-18: rejected with SAFETY_INVALID (exit 8)
NEG-19: rejected with BINDING_INVALID (exit 9)
NEG-20: rejected with BINDING_INVALID (exit 9)
NEG-23: rejected with PUBLIC_SAFETY_INVALID (exit 11)
NEG-24: rejected with IDENTITY_INVALID (exit 3)
NEG-25: rejected with PATH_INVALID (exit 12)
NEG-26: rejected with PATH_INVALID (exit 12)
NEG-27: rejected with BOUNDARY_INVALID (exit 4)
NEG-28: rejected with CONTRACT_INVALID (exit 5)
NEG-29: rejected with SCHEMA_INVALID (exit 2)
NEG-30: rejected with GOVERNANCE_INVALID (exit 7)
NEG-31: rejected with BINDING_INVALID (exit 9)
NEG-32: rejected with SCHEMA_INVALID (exit 2)
NEG-33: rejected with SAFETY_INVALID (exit 8)
NEG-34: rejected with BINDING_INVALID (exit 9)
NEG-35: rejected with SCHEMA_INVALID (exit 2)
NEG-36: rejected with SCHEMA_INVALID (exit 2)
NEG-37: rejected with SCHEMA_INVALID (exit 2)
NEG-38: rejected with SCHEMA_INVALID (exit 2)
NEG-39: rejected with SCHEMA_INVALID (exit 2)
NEG-21: missing dependencies rejected with BINDING_INVALID (exit 9)
NEG-22: tampered projection rejected with DETERMINISM_INVALID (exit 10)
X-COM architecture/contracts self-test passed
```

DET-04 mutation probes (command 13): neutralising `_check_model_schema`, `_check_ordering`,
`_check_identity`, `_check_paths`, `_check_boundaries`, `_check_contracts`, `_check_diagrams`,
`_check_governance`, `_check_neutrality`, `_check_safety`, `_check_binding`, `_check_maturity`,
`_check_dependencies`, `_check_determinism`, and `_scan_public_safety` one at a time makes the self-test
exit nonzero (exit 7), so each of the fifteen checks is load-bearing.

Artifact identity at this candidate state:

| Artifact | sha256 | Bytes |
| --- | --- | ---: |
| `docs/engineering/xcom/t009/requirements.md` | `a75776fef3c09c3565df53393863ab3a33418a425f84067b183aed28a4581eb5` | — |
| `docs/engineering/xcom/t009/architecture.md` | `55323a65ca701276788eebf6678924bc74eeac738ad168a450217bfc1c2c96a3` | — |
| `docs/engineering/xcom/t009/detailed-design.md` | `4c87b910436ef51cd5050964aee9b1d98b191791121dbc2c489a0b4634d098d1` | — |
| `docs/engineering/xcom/t009/unit-specifications.md` | `f58a3add222ec5e695f06080cbe12558ecc276de1207ca86eeeb7b122078bffd` | — |
| `docs/engineering/xcom/t009/verification-plan.md` | `3ad7d86e364bcc1c34cea3b60e2b101d5d0f21d7fe1b3c66b1717102b9a1d4e4` | — |
| `docs/engineering/xcom/t009/architecture-model.json` | `ce818ffe2ba17f32d9ba2dcdafa7be98a978d0872002d0b236009d993d86ef18` | — |
| `docs/engineering/xcom/t009/architecture-model.md` | `fac61d8b8560b9250e7d4a382798bae0ef5a3c565ecee3ed217b3402b078b74c` | — |
| `scripts/validate_xcom_architecture_contracts.py` | `1358ecd5c445fca5728cfb7dc4b6eefed80369157451f7ad32f3c27f7f32720c` | — |
| `docs/engineering/xcom/task-ownership.json` | `1c341ddaf7c83b6d58bd120f44cf19336df87220f8538904d6bfb3ec3d6e565a` | — |
| `docs/engineering/xcom/task-ownership.md` | `79b46be1d072fb9a1f6055638606c3182b80560df38f2a0d806e2a26b2bc64d6` | — |
| `specs/007-xcom-core/tasks.md` | `ee827248eed5eb47118e1a68eba60ff93161a9dd1381b9a30b3ba795f2505e2b` | — |

The model and its projection are byte-identical to revision 1 (`ce818ffe…`, `fac61d8b…`), so the
architecture content is unchanged; only the validator and the design/governance prose differ. Hashes and
bounded outputs are bound to this candidate state; the deterministic gate re-runs after the checkbox
update and its output is retained by the workflow. A successor candidate (for example a repair) must
record its own exact revision and repeat the affected checks.

## 6. Requirement-to-evidence trace

| Requirement | Checks / evidence |
| --- | --- |
| T009-SR-001 | CHK-01, CHK-12, ORD-01, NEG-01, NEG-27, NEG-28, NEG-29, NEG-32, NEG-35..NEG-39, DET-01 (commands 2, 3, 4, 5, 16) |
| T009-SR-002 | CHK-02, CHK-06, NEG-02, NEG-03, NEG-04, NEG-24, NEG-31, NEG-34 (commands 2, 4) |
| T009-SR-003 | CHK-03, NEG-05, NEG-06, NEG-07, NEG-27 (commands 2, 4) |
| T009-SR-004 | CHK-04, NEG-08, NEG-09, NEG-10, NEG-28 (commands 2, 4) |
| T009-SR-005 | CHK-05, NEG-11, NEG-12, NEG-13 (commands 2, 4) |
| T009-SR-006 | CHK-07, NEG-14, NEG-15 (commands 2, 4) |
| T009-SR-007 | CHK-08, NEG-16, NEG-17 (commands 2, 4) |
| T009-SR-008 | CHK-09, NEG-18, NEG-33 (commands 2, 4, 19) |
| T009-SR-009 | CHK-11, NEG-21, NEG-30 (commands 2, 4, 20) |
| T009-SR-010 | CHK-06, CHK-10, NEG-19, NEG-20, NEG-25, NEG-26, BND-02 (commands 2, 4, 9) |
| T009-SR-011 | CHK-14, BND-01, BND-06, deterministic gate (commands 10, 11, 17, 18) |
| T009-SR-012 | CHK-13, NEG-23 (commands 2, 4) |
| T009-SR-013 | CHK-12, CHK-15, CHK-16, DET-01..DET-04, BND-03..BND-05 (commands 1, 3, 4, 5, 12, 13, 14, 15, 19) |

REF-002: no direct communication requirement `XVE-SYS-0139`–`0158` is implemented, promoted, or
unlinked. `ref002.disposition = "unchanged"` with an empty promoted set; the authoritative table remains
`specs/007-xcom-core/reference-traceability.md`.

## 7. Limitations and honesty notes

1. **No acceptance or integration claim.** T009 implements and locally verifies only its own bounded
   work products. It does not accept or integrate any candidate, including itself, and it claims no
   external review or user acceptance. The internal review is a separate read-only stage; external
   Codex review is deferred until the `xcom-t007-t010-t017-t020` backlog completes.
2. **Reconciliation is recorded, not resolved.** `T012`–`T016` and `T021`–`T024` coverage stays
   `partial`/`unreconciled`; the accepted `T025` slice is the only coverage bound to an accepted exact
   revision.
3. **Planned anchors.** Every product path the model anchors other than baseline-present
   (`established`) artifacts is declared `planned`; a planned path is a traceability intent, not
   implementation evidence.
4. **Public-safety scan scope.** The validator mechanically detects absolute host paths, private IPv4
   ranges, credential assignment tokens, private-key markers, and unbounded base64-like tokens. The
   non-mechanical classes (proprietary source excerpts, unrestricted payloads) are assessed by the
   review stage; inspection finds none in the model, projection, or output.
5. **No runtime evidence.** T009 has no runtime artifact, so no performance, availability, or
   concurrency claim is made; the validator is offline, single-threaded, and bounded (≤ 1 MiB per file,
   ≤ 4 MiB total, no network or subprocess, wall clock well under 60 s).
6. **Environment identity is recorded, not pinned by T009.** Compiler/dependency admission with hashes
   and licenses is T011's deliverable; this record names only the Python interpreter used.
7. **Revision 2 is a successor candidate.** Revision 2 repairs the revision-1 internal-review findings
   §2.2 and re-runs the affected checks; it binds the same authorized baseline
   `209084b11a211273f815980f753ba728e1251a09`. The revision-1 evidence remains attached to revision 1 and
   is not extrapolated. The model content and the accepted specification are unchanged, so this repair
   adds no new requirement and weakens no accepted one.
8. **Revision 3 is a further successor candidate.** Revision 3 repairs the single revision-3
   internal-review finding (T009-IR-05) in §2.3 and re-runs the affected checks; it binds the same
   authorized baseline `209084b11a211273f815980f753ba728e1251a09`. The revision-2 evidence remains attached
   to revision 2 and is not extrapolated. The model content and the accepted specification are unchanged, so
   this repair adds no new requirement and weakens no accepted one.

# T007 Implementation Record — Ownership Register, Binding, and Validator

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T007 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | implement → implementation record (revision 2, repair successor) |
| Revision | 2 |
| Authorized baseline | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Candidate state | working tree over the authorized baseline (candidate revision assigned when the workflow checkpoints); revision 1 was reviewed read-only and failed, and this successor repairs every finding (see §7) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Authorization | ACC001–ACC015, ADR-0018, ADR-0019, ADR-0020; `specs/007-xcom-core/tasks.md` T007 |
| Maturity | Governance work product implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T007 implements the bounded ownership register required by the T007 task entry. It is a
**documentation-and-governance** change only. The candidate adds the canonical register, its deterministic
human projection, and the offline validator, and records the T007 completion checkbox. It changes **no**
path under `src/`, `tests/`, or `xdl/`, adds no CMake target or runtime artifact, and does not accept,
complete, or integrate any other task or software candidate.

## 3. Changed artifacts and symbols

| Artifact | Change | Symbols / structure |
| --- | --- | --- |
| `docs/engineering/xcom/task-ownership.json` | new | Canonical register model, `schema_version = 1`: `slices` (T-CORE, T-XDL, T-OBS, T-STIM, T-INTG, T-ENABLER, T-REVIEW), `task_assignment` (T007–T041), `dependency_edges`, `authorization_records`, `global_prohibitions`, `shared_paths`. |
| `docs/engineering/xcom/task-ownership.md` | new | Deterministic projection of the JSON model, including the shared-path serialization rule. |
| `scripts/validate_xcom_task_ownership.py` | new | `Findings`, `serialize`, `project_markdown`, `_check_schema`, `_check_slice_set`, `_check_assignment`, `_check_binding`, `_check_paths`, `_check_per_task_ownership`, `_patterns_overlap`, `_check_dependencies`, `_check_gates`, `_check_required_reconciliation`, `_check_determinism`, `_scan_public_safety`, `_sync_declared_dependencies`, `_reshape_dependencies`, `run_checks`, `main`, and the `_self_test` fixtures NEG-01..NEG-20 / DET-02. CLI `--verify`, `--check-human`, `--self-test`. |
| `docs/engineering/xcom/t007/implementation.md` | new | This record. |
| `specs/007-xcom-core/tasks.md` | modified | T007 checkbox marked complete; no other task line changed. |

No production source, test, XDL asset, accepted ADR, or accepted requirement was changed. The T007
candidate's affected product source paths are none.

### 3.1 Register content summary

- Six bounded work slices plus the `T-ENABLER` engineering-baseline group; every task T008–T041 is
  assigned to exactly one slice, and T007 is the producing task (`T-PRODUCING`).
- Every slice binds `authorized_baseline = 923a6db…` and at least one resolvable authorization record.
- Exclusive path patterns are non-empty and pairwise disjoint across slices under directory-prefix
  semantics; every task's `docs/engineering/xcom/<task>/` directory and
  `reports/xcom-queue/<task>-package.json` is reserved to its owning slice (T007's to `T-ENABLER`), so
  each per-task review, acceptance, and queue artifact has exactly one owner; the shared
  build/specification paths (`CMakeLists.txt`, `src/xverse/xcom/CMakeLists.txt`, `cmake/*`,
  `specs/007-xcom-core/tasks.md`, the register artifacts) are declared and serialized.
- The dependency graph is acyclic and every `REQUIRED_ORDER_PAIRS` precedence pair is reachable
  (enabler → core → {xdl, obs, stim} → integration → review, with T025 before T026); each slice's
  declared `dependencies` equals its direct incoming edges.
- The top-level `global_prohibitions` contains the four minimum prohibitions, and every slice repeats
  them.
- Every slice declares required evidence, an acceptance gate, and the global prohibitions.
- Reconciliation is honest: T012–T016 and T021–T024 are `unreconciled` (source present, checkbox open, no
  accepted exact-candidate revision); T025 is `accepted` at merge `4b01586b438a8587d231ee8828d896c206c06a96`
  (implementation `cc9044ab28d0ae9b4df8447072f68b73b3db184a`); all remaining tasks are `allocated`.

## 4. Commands, results, and evidence

Environment: Python 3.13.13; repository checkout at baseline `923a6db65aafbcdbf33a1461e93622777e902deb`.

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `python3 -m py_compile scripts/validate_xcom_task_ownership.py` | 0 | Validator compiles. |
| 2 | `python3 scripts/validate_xcom_task_ownership.py --verify` | 0 | `X-COM task-ownership validation passed` (CHK-01..CHK-08, CHK-10, CHK-11, CHK-13, CHK-15). |
| 3 | `python3 scripts/validate_xcom_task_ownership.py --check-human` | 0 | Markdown projection matches the JSON model exactly (CHK-09). |
| 4 | `python3 scripts/validate_xcom_task_ownership.py --self-test` | 0 | Positive fixture passes; NEG-01..NEG-20 reject with their declared exit classes; DET-02 rejects a tampered projection (exit 9). |
| 5 | `python3 scripts/validate_xcom_task_ownership.py --verify` (twice) | 0 | Byte-identical stdout and exit status (DET-01). |
| 6 | `git rev-parse 923a6db…` | 0 | Prints `923a6db65aafbcdbf33a1461e93622777e902deb` (BND-02). |
| 7 | `git diff --name-only 923a6db… --` | 0 | Only documentation/governance paths; no `src/`, `tests/`, or `xdl/` path (CHK-12, BND-01). |
| 8 | `git diff --check 923a6db… --` | 0 | Clean (BND-06). |
| 9 | mutation probes: neutralise one new check, run `--self-test` | nonzero for each | Ordering (exit 8), top-level prohibitions (8), prefix overlap (8), and per-task reservation (8) are all load-bearing (DET-04). |

Self-test detail (command 4):

```
positive fixture: passed
NEG-01: rejected with SLICE_SET_INVALID (exit 3)
NEG-02: rejected with SLICE_SET_INVALID (exit 3)
NEG-03: rejected with ASSIGNMENT_INVALID (exit 4)
NEG-04: rejected with ASSIGNMENT_INVALID (exit 4)
NEG-05: rejected with BINDING_INVALID (exit 5)
NEG-06: rejected with BINDING_INVALID (exit 5)
NEG-07: rejected with PATH_OWNERSHIP_INVALID (exit 6)
NEG-08: rejected with PATH_OWNERSHIP_INVALID (exit 6)
NEG-09: rejected with DEPENDENCY_INVALID (exit 7)
NEG-10: rejected with DEPENDENCY_INVALID (exit 7)
NEG-11: rejected with GATE_INVALID (exit 8)
NEG-12: rejected with GATE_INVALID (exit 8)
NEG-13: rejected with GATE_INVALID (exit 8)
NEG-14: rejected with DEPENDENCY_INVALID (exit 7)
NEG-15: rejected with DEPENDENCY_INVALID (exit 7)
NEG-16: rejected with DEPENDENCY_INVALID (exit 7)
NEG-17: rejected with GATE_INVALID (exit 8)
NEG-18: rejected with PATH_OWNERSHIP_INVALID (exit 6)
NEG-19: rejected with PATH_OWNERSHIP_INVALID (exit 6)
NEG-20: rejected with PATH_OWNERSHIP_INVALID (exit 6)
DET-02: tampered projection rejected with DETERMINISM_INVALID (exit 9)
X-COM task-ownership self-test passed
```

Artifact identity at this candidate state (revision 2):

| Artifact | sha256 | Bytes |
| --- | --- | ---: |
| `docs/engineering/xcom/task-ownership.json` | `977595a5c77e1625b1fb905b2d1bd937c77f803a5b6c81065bd6dd007ba2be81` | 28271 |
| `docs/engineering/xcom/task-ownership.md` | `7e83642e8cf21c1c2be176c09faf3f289e7c56fffa7bc0ccd9140e8e30201464` | 21391 |
| `scripts/validate_xcom_task_ownership.py` | `181747c9d118b12f10aec058d6e800505f3bebabf5597e0d4d128112b7c43250` | 47254 |

Hashes and bounded outputs are bound to this candidate state; the deterministic gate re-runs after the
checkbox update and its output is retained by the workflow. A successor candidate (for example a repair)
must record its own exact revision and repeat the affected checks.

## 5. Requirement-to-evidence trace

| Requirement | Checks / evidence |
| --- | --- |
| T007-SR-001 | CHK-01, DET-01 (commands 2, 5; `serialize`) |
| T007-SR-002 | CHK-02, NEG-01, NEG-02 (commands 2, 4) |
| T007-SR-003 | CHK-03, NEG-03, NEG-04 (commands 2, 4) |
| T007-SR-004 | CHK-04, NEG-05, BND-02 (commands 2, 4, 6) |
| T007-SR-005 | CHK-04, NEG-06 (commands 2, 4) |
| T007-SR-006 | CHK-05, CHK-15, NEG-07, NEG-08, NEG-18, NEG-19, NEG-20 (commands 2, 4) |
| T007-SR-007 | CHK-08, markdown shared-path rule (commands 2, 3) |
| T007-SR-008 | CHK-06, NEG-09, NEG-10, NEG-14, NEG-15, NEG-16; DET-04 (commands 2, 4, 9) |
| T007-SR-009 | CHK-07, NEG-11 (commands 2, 4) |
| T007-SR-010 | CHK-10, NEG-12, NEG-17 (commands 2, 4) |
| T007-SR-011 | CHK-11, NEG-13 (commands 2, 4) |
| T007-SR-012 | CHK-14, DET-01..DET-04, BND-03..BND-05 (commands 1, 2, 4, 5, 9) |
| T007-SR-013 | CHK-12, BND-01, BND-06, deterministic gate (commands 7, 8) |
| T007-SR-014 | CHK-13 (command 2 public-safety scan; manual `grep` over the register and projection) |

REF-002: `ref002_disposition = "unchanged"` for every slice; T007 implements no direct communication
requirement and promotes no allocated SADS target. The authoritative disposition table remains
`specs/007-xcom-core/reference-traceability.md`.

## 6. Limitations and honesty notes

1. **No acceptance or integration claim.** T007 implements and locally verifies only its own bounded
   work products. It does not accept or integrate any candidate, including itself, and it does not claim
   external review or user acceptance. The internal review is a separate read-only stage; external Codex
   review is deferred until the `xcom-t007-t010-t017-t020` backlog completes.
2. **Reconciliation is not resolution.** T012–T016 and T021–T024 remain `unreconciled`; their presence in
   the baseline is recorded, not accepted. Reconciliation against exact accepted revisions stays with the
   owning slices.
3. **Public-safety scan scope.** The validator mechanically detects absolute host paths, private IPv4
   ranges, credential assignment tokens, private-key markers, and unbounded base64-like tokens. The
   non-mechanical classes (proprietary source excerpts, unrestricted payloads) are assessed by the review
   stage; no such content is present in the register or projection by inspection.
4. **Ownership is over files, not over the act of running checks.** Integration may run tests owned by
   other slices but may not change those files without the owning slice's candidate and evidence.
5. **No runtime evidence.** T007 has no runtime artifact, so no performance, availability, or concurrency
   claim is made; the validator is offline, single-threaded, and bounded (≤ 1 MiB per file, ≤ 4 MiB total,
   no network or subprocess, wall clock well under 60 s).
6. **Environment identity is recorded, not pinned by T007.** Compiler/dependency admission with hashes and
   licenses is T011's deliverable; this record names only the Python interpreter used locally.

## 7. Repair closure (revision 2 successor candidate)

The revision-1 candidate was inspected read-only and failed with four findings
(`internal-review.json` F-01..F-04). The successor candidate fixes each finding at the root cause,
without weakening any accepted requirement, check, or test, and records the closure evidence below.
The finder is a separate pass; this repair is recorded before the successor review.

| Finding | Root cause in revision 1 | Repair | Closure evidence |
| --- | --- | --- | --- |
| F-01 (major) | `REQUIRED_ORDER_PAIRS` was dead code; `_check_dependencies` proved only T-ENABLER reachability and declared-vs-direct consistency, so a reordered graph validated | `_check_dependencies` now emits `DEPENDENCY_INVALID` (7) for every unreachable `(source, target)` pair; `VM_ORDER` was removed. Fixtures NEG-14/NEG-15/NEG-16 reshape T-XDL/T-INTG/T-REVIEW onto `T-ENABLER` alone with consistent declared dependencies; NEG-09/NEG-10 also keep the edges and declared deps consistent | NEG-10/14/15/16 → exit 7; probe A (neutralise the reachability loop) makes `--self-test` fail with exit 8 |
| F-02 (minor) | only per-slice prohibitions were compared, so weakening the top-level `global_prohibitions` validated | `_check_gates` now requires the top-level set to be a superset of `MINIMUM_PROHIBITIONS` and emits `GATE_INVALID` (8) otherwise | NEG-17 (remove `no TCP listener` from the top-level list only) → exit 8; probe B makes `--self-test` fail |
| F-03 (minor) | exclusivity compared exact strings only and empty exclusive lists were accepted | `_patterns_overlap` compares directory prefixes (`/`-bounded); cross-slice overlaps and empty exclusive sets are rejected as `PATH_OWNERSHIP_INVALID` (6) | NEG-18 (parent `tests/xcom/`) → exit 6; NEG-19 (empty set) → exit 6; probe C (exact-only overlap) makes `--self-test` fail |
| F-04 (minor) | per-task `internal-review.json`/`acceptance-decision.md` were owned by T-REVIEW (after T-INTG) and `reports/xcom-queue/` by T-INTG, so their owners' dependencies were not satisfied when the artifacts are produced; the t007 paths were double-assigned | `_check_per_task_ownership` requires every task's `docs/engineering/xcom/<task>/` directory and `reports/xcom-queue/<task>-package.json` to be reserved to exactly one slice; the register now assigns per-task artifacts to the owning task's slice and T007's to `T-ENABLER` (whose only dependency, T007, precedes it); `architecture.md` §5 and `detailed-design.md` §5.6/§5.7 document the rule | `docs/engineering/xcom/t007/internal-review.json`, `docs/engineering/xcom/t007/acceptance-decision.md`, and `reports/xcom-queue/t007-package.json` each resolve to exactly T-ENABLER; NEG-20 → exit 6; probe E makes `--self-test` fail |

Probe D (neutralising the explicit empty-exclusive guard) still leaves the self-test passing because the
per-task reservation check independently rejects an empty `paths_exclusive` set; the empty-ownership
guarantee is therefore enforced by two independent mechanisms rather than one, and no fixture passes for
the wrong reason.

Revision-2 verification is command set 1..9 above, all exit 0 except the intended nonzero mutation probes.
The deterministic gate is re-run after this repair by the workflow; this record claims only local,
candidate-bound evidence and no acceptance.

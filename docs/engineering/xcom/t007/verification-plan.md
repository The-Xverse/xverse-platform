# T007 Verification Plan — Named Checks, Commands, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T007 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `923a6db65aafbcdbf33a1461e93622777e902deb` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | repository-owned Python 3.11 validator plus the deterministic Fabro gate; no C++/GTest case is added by T007 |

This plan is written **before** implementation. The implementation must realise every named check with
the stated expected result. Weakening an expected result is a verification-contract change requiring
review. Because T007 is a documentation/governance task, the checks are deterministic static checks over
the ownership register; the deterministic gate for T007 runs no C++/Python test suite.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T007 923a6db65aafbcdbf33a1461e93622777e902deb
```

For T007 this gate requires:

- `docs/engineering/xcom/t007/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` present;
- the T007 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- a changed-path set containing **no** `src/`, `tests/`, or `xdl/` path (T007 is a work-product task);
- `git diff --check <baseline> --` clean.

Supporting commands (same tools, no network):

```sh
python3 scripts/validate_xcom_task_ownership.py --self-test
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
git rev-parse 923a6db65aafbcdbf33a1461e93622777e902deb
git diff --name-only 923a6db65aafbcdbf33a1461e93622777e902deb --
git diff --check 923a6db65aafbcdbf33a1461e93622777e902deb --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Register parses and matches the schema | `--verify` on `task-ownership.json` | exit 0; `schema_version == 1`; fixed fields/order |
| CHK-02 | Exactly the six named slices plus the enabler group | `--verify` | slice set equals `{T-CORE,T-XDL,T-OBS,T-STIM,T-INTG,T-REVIEW,T-ENABLER}` |
| CHK-03 | Complete single-owner assignment | `--verify` | T008–T041 each assigned once; T007 producing task; no gap/duplicate |
| CHK-04 | Baseline and authorization binding | `--verify` + `git rev-parse` | every slice baseline = run baseline; every slice ≥ 1 resolvable authorization ref |
| CHK-05 | Exclusive path disjointness | `--verify` | no pattern in two `paths_exclusive` sets; no cross-slice directory-prefix overlap; no empty exclusive set |
| CHK-06 | Acyclic graph and ordering | `--verify` | no cycle; every `REQUIRED_ORDER_PAIRS` pair is reachable (enablers → core → {xdl,obs,stim} → intg → review); T025 before T026; declared dependencies equal direct edges |
| CHK-07 | Evidence/acceptance gate mapping | `--verify` | every slice has ≥ 1 evidence item and a named gate; `T-REVIEW` names review + user acceptance |
| CHK-08 | Shared-path declaration | `--verify` | `shared_paths` non-empty and names root/X-COM build files and capability specs; `paths_shared ⊆ shared_paths` |
| CHK-09 | Deterministic serialization | `--verify` twice, `--check-human` | both JSON runs byte-identical; markdown is the exact projection |
| CHK-10 | Global prohibitions | `--verify` | top-level `global_prohibitions` is a superset of the four minimum prohibitions; every slice's prohibitions are too |
| CHK-11 | Reconciliation honesty | `--verify` | T012–T016/T021–T024 `unreconciled`; T025 `accepted` with revision; no unproven `accepted` |
| CHK-12 | Docs-only boundary | `git diff --name-only <baseline> --` | no path starts with `src/`, `tests/`, or `xdl/` |
| CHK-13 | Public-safety scan | `--verify` plus manual inspection | no credential, private address, proprietary excerpt, unrestricted payload, or absolute host path in the register, projection, or validator output |
| CHK-14 | Validator self-test | `--self-test` | positive fixture passes; every NEG case fails with its declared exit class |
| CHK-15 | Per-task artifact ownership | `--verify` | each task's `docs/engineering/xcom/<task>/` and `reports/xcom-queue/<task>-package.json` is reserved to exactly one slice (T007's to `T-ENABLER`); no double owner |

## 4. Negative cases (validator self-test fixtures)

Each NEG case injects one controlled defect into a copy of the register and asserts the declared
nonzero exit with **no** partial success and no output claiming a valid register.

| ID | Injected defect | Expected exit / class |
| --- | --- | --- |
| NEG-01 | Remove one named slice | 3 `SLICE_SET_INVALID` |
| NEG-02 | Add an unnamed extra slice | 3 `SLICE_SET_INVALID` |
| NEG-03 | Remove a task from every assignment | 4 `ASSIGNMENT_INVALID` |
| NEG-04 | Assign one task to two slices | 4 `ASSIGNMENT_INVALID` |
| NEG-05 | Set a slice baseline to a short/empty string | 5 `BINDING_INVALID` |
| NEG-06 | Set an authorization ref to an unknown token | 5 `BINDING_INVALID` |
| NEG-07 | Put one path pattern in two exclusive sets | 6 `PATH_OWNERSHIP_INVALID` |
| NEG-08 | Move a shared file into an exclusive set only | 6 `PATH_OWNERSHIP_INVALID` |
| NEG-09 | Introduce a dependency cycle (edges and declared deps consistent) | 7 `DEPENDENCY_INVALID` |
| NEG-10 | Reverse enabler→core ordering, keeping declared dependencies consistent | 7 `DEPENDENCY_INVALID` |
| NEG-11 | Remove a slice's acceptance gate or evidence list | 8 `GATE_INVALID` |
| NEG-12 | Remove one minimum global prohibition from a slice | 8 `GATE_INVALID` |
| NEG-13 | Label a task `accepted` without a recorded revision | 8 `GATE_INVALID` |
| NEG-14 | Make T-XDL depend only on T-ENABLER (edges and declared deps consistent) | 7 `DEPENDENCY_INVALID` |
| NEG-15 | Make T-INTG depend only on T-ENABLER | 7 `DEPENDENCY_INVALID` |
| NEG-16 | Make T-REVIEW depend only on T-ENABLER | 7 `DEPENDENCY_INVALID` |
| NEG-17 | Remove a minimum prohibition from the top-level `global_prohibitions` only | 8 `GATE_INVALID` |
| NEG-18 | Add parent pattern `tests/xcom/` to T-OBS exclusive paths (overlaps T-CORE) | 6 `PATH_OWNERSHIP_INVALID` |
| NEG-19 | Empty a slice's `paths_exclusive` list entirely | 6 `PATH_OWNERSHIP_INVALID` |
| NEG-20 | Remove a task's reserved queue package from its owning slice | 6 `PATH_OWNERSHIP_INVALID` |

NEG-10 and NEG-14..NEG-16 update each slice's declared `dependencies` to match the mutated edge list, so
they exercise the ordering (reachability) check rather than the declared-vs-direct consistency check
alone. NEG-18 and NEG-19 exercise directory-prefix disjointness and non-empty ownership; NEG-20
exercises the per-task reservation. A mutation probe that neutralises any one new check makes the
self-test fail, which is the load-bearing evidence recorded in `implementation.md` (DET-04).

**Precedence closure.** When several defects are present, the validator must return the numerically
lowest applicable exit class and report all diagnostics in deterministic order; a failure must never
report `OK`.

## 5. Determinism and boundary cases

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| DET-01 | Byte-identical serialization | serialize the same model twice | identical bytes |
| DET-02 | Markdown projection | `--check-human` after a manual key reorder | mismatch detected; exit 9 |
| DET-03 | Stable diagnostics | inject two defects, run twice | identical output and exit |
| DET-04 | New checks are load-bearing | neutralise one new check at a time, run `--self-test` | the corresponding NEG case fails, so the self-test exits nonzero |
| BND-01 | Docs-only diff | `git diff --name-only <baseline> --` | no `src/`, `tests/`, `xdl/` path |
| BND-02 | Baseline resolves | `git rev-parse <baseline>` | prints the baseline SHA |
| BND-03 | Bounded input | register ≤ 1 MiB, totals ≤ 4 MiB | accepted; over bound → exit 11 |
| BND-04 | Offline | no network/subprocess in the validator | no syscall to any peer; source inspection plus review |
| BND-05 | Runtime bound | wall clock ≤ 60 s | holds on the local checkout |
| BND-06 | Clean diff | `git diff --check <baseline> --` | no whitespace errors |

## 6. Concurrency and resource bounds

T007 has **no runtime concurrency**: the register is a static document and the validator is
single-threaded and offline. Concurrency is therefore not applicable, and the plan does not invent a
concurrency case. The applicable bounds are BND-03 (input size), BND-04 (no network/subprocess), BND-05
(runtime ≤ 60 s), and determinism DET-01..DET-03. Production concurrency/resource bounds remain owned by
the implementation slices (`T-CORE`, `T-OBS`, `T-STIM`) and their own verification plans.

## 7. Requirement traceability

| Requirement | Checks |
| --- | --- |
| T007-SR-001 | CHK-01, DET-01 |
| T007-SR-002 | CHK-02, NEG-01, NEG-02 |
| T007-SR-003 | CHK-03, NEG-03, NEG-04 |
| T007-SR-004 | CHK-04, NEG-05, BND-02 |
| T007-SR-005 | CHK-04, NEG-06 |
| T007-SR-006 | CHK-05, CHK-15, NEG-07, NEG-08, NEG-18, NEG-19, NEG-20 |
| T007-SR-007 | CHK-08 |
| T007-SR-008 | CHK-06, NEG-09, NEG-10, NEG-14, NEG-15, NEG-16, DET-04 |
| T007-SR-009 | CHK-07, NEG-11 |
| T007-SR-010 | CHK-10, NEG-12, NEG-17 |
| T007-SR-011 | CHK-11, NEG-13 |
| T007-SR-012 | CHK-14, DET-01..DET-04, BND-03..BND-05 |
| T007-SR-013 | CHK-12, BND-01, BND-06, gate step |
| T007-SR-014 | CHK-13 |

## 8. Implementation-stage sequence

1. Create `docs/engineering/xcom/task-ownership.json` and `task-ownership.md` implementing
   `detailed-design.md` §3–§6.
2. Create `scripts/validate_xcom_task_ownership.py` implementing §7 and the self-test.
3. Run `--self-test`, `--verify`, and `--check-human`; run `git diff --check` and the docs-only diff.
4. Record the candidate revision, commands, tool versions, exit codes, and bounded outputs in
   `docs/engineering/xcom/t007/implementation.md`.
5. Mark the T007 checkbox complete in `specs/007-xcom-core/tasks.md` (implementation stage only).
6. Run the deterministic gate in §2 and retain its output.

## 9. Evidence to retain with the candidate revision

- The gate command stdout/stderr and exit status.
- `--self-test`, `--verify`, and `--check-human` outputs and exit codes.
- The mutation-probe (DET-04) output showing each new check is load-bearing.
- The `git diff --name-only` and `git diff --check` outputs proving the docs-only boundary.
- The candidate revision hash and the Python/tool identities used.
- The register file hashes recorded in the T007 package manifest.

Evidence must be bound to the exact candidate revision; missing, stale, or mismatched evidence cannot
support acceptance. This plan records no external-review or user-acceptance claim; external Codex review
is deferred until the `xcom-t007-t010-t017-t020` backlog completes.

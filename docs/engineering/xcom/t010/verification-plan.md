# T010 Verification Plan — Named Checks, Commands, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T010 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `abb81681e0d844edaecbaf2843f1c2a7deb1e40f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | repository-owned Python 3.11-compatible validator plus the deterministic Fabro gate; no C++/GTest case is added by T010 |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
Because T010 is a documentation/governance task, the checks are deterministic static checks over the
unit-design model; the deterministic gate for T010 runs no C++/Python test suite.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T010 abb81681e0d844edaecbaf2843f1c2a7deb1e40f
```

For T010 this gate requires:

- `docs/engineering/xcom/t010/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present;
- the T010 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan
  stage leaves it unchecked, per the stage instruction);
- a changed-path set containing **no** `src/`, `tests/`, or `xdl/` path (T010 is a work-product task; the
  added `scripts/` validator is permitted);
- `git diff --check <baseline> --` clean.

Supporting commands (same tools, no network):

```sh
python3 scripts/validate_xcom_unit_design.py --self-test
python3 scripts/validate_xcom_unit_design.py --verify
python3 scripts/validate_xcom_unit_design.py --check-human
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
git rev-parse abb81681e0d844edaecbaf2843f1c2a7deb1e40f
git diff --name-only abb81681e0d844edaecbaf2843f1c2a7deb1e40f --
git diff --check abb81681e0d844edaecbaf2843f1c2a7deb1e40f --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves. The
`--self-test` fixtures are the exact negative cases in §4; the `--check-human` comparison is the
`design-units.md` projection.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Model parses and matches the schema | `--verify` | exit 0; `schema_version == 1`; fixed top-level fields in order; each fixed vocabulary equals its declared set |
| CHK-02 | Ordering, uniqueness, and id types | `--verify` | `units` and `invariants` sorted by `id` with unique, non-empty-string ids; `counts` matches the entries; a non-string or unhashable id is a classified schema failure |
| CHK-03 | Unit identity, vocabulary, ownership slice/tasks, artifact paths | `--verify` + filesystem | required id set exactly `XCOM-DU-001`–`030`; family/kind/language/scope/maturity present and closed (an absent or null scalar is `IDENTITY_INVALID`); owning slice/tasks consistent with the T007 register; every unit has ≥ 1 path tagged `established`/`planned`, every entry carries a non-empty string `path`, and `planned_evidence` is a non-empty string array |
| CHK-04 | Ownership and lifetime contract | `--verify` | ownership/lifetime models closed with non-empty rationales; `view_lifetime` present and non-`n/a` iff the unit exposes a view; mutating units declare an issued-handle rule |
| CHK-05 | Thread-safety and concurrency contract | `--verify` | thread-safety model closed with a rationale; non-empty `shared_state` implies `internally-synchronized`/`externally-synchronized`/`message-passing`; `synchronization` is non-null for those three models and null for `immutable-value`/`read-only-static`/`single-thread-owner`/`offline-single-threaded`/`process-isolated`; `internally-synchronized` names a mechanism; `message-passing` declares a capacity bound and policy |
| CHK-06 | Bounds and overflow policy | `--verify` | ≥ 1 finite bound per unit; kinds closed; values null or non-negative integers; `retry` is 0; `overflow_policies` non-empty and exactly `["n/a"]` iff no capacity/quota/depth/rate bound exists |
| CHK-07 | Failure semantics and outcome honesty | `--verify` | non-empty condition → outcome mapping; outcomes closed; `unknown` never maps to `accepted`/`delivered`; journal/write units declare `evidence-incomplete` |
| CHK-08 | Doxygen plan and per-unit obligation | `--verify` | plan declares configuration, `WARN_AS_ERROR`, file block, mandatory tags, per-family groups, coverage rule, gaps with owning tasks; every `cpp` unit carries the mandatory tags/group and equal element counts; non-`cpp` units declare `required = false` with a reason |
| CHK-09 | Unit↔component/contract cross-resolution | `--verify` + T009 model | every `component_refs`/`contract_refs` resolves; families `CORE`/`XDL`/`OBS`/`STIM`/`GW` have non-empty component refs |
| CHK-10 | Coverage and exemptions | `--verify` + T008/T009 | every non-exempt T009 component and every non-exempt `XCOM-SW-*` requirement is covered; every exemption is real, reasoned, and task-owned |
| CHK-11 | Governance, maturity, and REF-002 non-promotion | `--verify` | ADR references resolve; `ref002.disposition == "unchanged"` with empty `promoted`; `implemented` requires an accepted revision; `partial`-unreconciled carries a reason; direction/neutrality/safety invariants enforced |
| CHK-12 | Baseline and authorization binding | `--verify` + `git rev-parse` | model binds the run baseline; `authorization_records` equals the T007 closed set; `adr_vocabulary` closed |
| CHK-13 | Fail-closed dependency integrity | `--verify` with a withheld dependency | the three dependencies present, readable, ≤ bound, well-formed; an unavailable/malformed dependency is a distinct nonzero failure and never a pass |
| CHK-14 | Public-safety scan | `--verify` plus manual inspection | no credential, private address, key marker, unrestricted payload, or absolute host path in the model, projection, or output |
| CHK-15 | Path status consistency | `--verify` + filesystem | `established` paths exist; `planned` paths are absent |
| CHK-16 | Deterministic serialization, stored-model canonicality, and projection | `--verify` twice, `--check-human`, one run against a whitespace-altered copy | both runs byte-identical; the stored `unit-design.json` bytes equal the canonical serialization (a non-canonical stored model → `DETERMINISM_INVALID` 11); `design-units.md` is the exact deterministic projection |
| CHK-17 | Validator self-test | `--self-test` | positive fixture passes; every NEG case rejects with its declared exit class; a one-check neutralisation makes the self-test fail (DET-04) |
| CHK-18 | Offline, bounded, no-subprocess, and work-product boundary | source inspection + over-bound probe + `git diff` | imports limited to stdlib file/json/re/pathlib and pure computation; no network/subprocess/write; over-bound input → `IO_ERROR` (14); the candidate diff contains no `src/`, `tests/`, `xdl/`, or `proto/` path and no `Doxyfile`/CMake change |

## 4. Negative cases (validator self-test fixtures)

Each NEG case injects one controlled defect — into a copy of the model, or by withholding a dependency
(NEG-38) — and asserts the declared nonzero exit with **no** partial success and no output claiming a valid
model.

| ID | Injected defect | Expected exit / class |
| --- | --- | --- |
| NEG-01 | Remove a required top-level field or reorder keys | 2 `SCHEMA_INVALID` |
| NEG-02 | Make `counts` disagree with the entries | 2 `SCHEMA_INVALID` |
| NEG-03 | Store the `units` array out of id order | 2 `SCHEMA_INVALID` |
| NEG-04 | Give a unit a non-string `id` (integer or null) | 2 `SCHEMA_INVALID` |
| NEG-05 | Give `units[0]` an unhashable container `id` (a list, then a dict) | 2 `SCHEMA_INVALID` |
| NEG-06 | Duplicate a unit id | 3 `IDENTITY_INVALID` |
| NEG-07 | Set a unit family/kind/language/maturity to an unknown token | 3 `IDENTITY_INVALID` |
| NEG-08 | Remove a mandatory unit field (empty `name`/`responsibility`) | 3 `IDENTITY_INVALID` |
| NEG-08b..NEG-08f | Delete one mandatory per-unit scalar (`family`, `kind`, `language`, `scope`, `maturity`) from a non-`cpp` unit (`XCOM-DU-026`) | 3 `IDENTITY_INVALID` |
| NEG-08g..NEG-08k | Delete the same five mandatory scalars from a `cpp` unit (`XCOM-DU-006`) | 3 `IDENTITY_INVALID` |
| NEG-08l | Set `planned_evidence = []` on a unit | 3 `IDENTITY_INVALID` |
| NEG-08m | Delete `planned_evidence` from a unit | 3 `IDENTITY_INVALID` |
| NEG-09 | Remove every `artifact_path` from a unit | 3 `IDENTITY_INVALID` |
| NEG-09b | Leave an `artifact_paths` entry with no `path` (status only) | 3 `IDENTITY_INVALID` |
| NEG-10 | Set `thread_safety.model` to an unknown token | 3 `IDENTITY_INVALID` |
| NEG-11 | Map a failure condition to an unknown outcome token | 3 `IDENTITY_INVALID` |
| NEG-12 | Remove a unit's ownership model | 4 `OWNERSHIP_INVALID` |
| NEG-13 | Remove a unit's lifetime model | 4 `OWNERSHIP_INVALID` |
| NEG-14 | Remove a unit's owning slice or owning task set | 4 `OWNERSHIP_INVALID` |
| NEG-15 | Declare a mutating unit with caller-owns-value and no issued-handle rule | 4 `OWNERSHIP_INVALID` |
| NEG-16 | Declare an owning slice that disagrees with the T007 register | 4 `OWNERSHIP_INVALID` |
| NEG-17 | Remove a unit's thread-safety model | 5 `THREAD_INVALID` |
| NEG-18 | Declare non-empty `shared_state` with an `immutable-value` model | 5 `THREAD_INVALID` |
| NEG-18b | Declare non-empty `shared_state` with a `single-thread-owner` model | 5 `THREAD_INVALID` |
| NEG-19 | Declare `internally-synchronized` without a synchronization mechanism | 5 `THREAD_INVALID` |
| NEG-19b | Declare a non-null `synchronization` on an `immutable-value` model | 5 `THREAD_INVALID` |
| NEG-20 | Mark a unit `exposes_view = true` but leave `view_lifetime` null | 4 `OWNERSHIP_INVALID` |
| NEG-21 | Remove every bound from a unit | 6 `BOUNDS_INVALID` |
| NEG-22 | Give a bound a negative or non-integer `value` | 6 `BOUNDS_INVALID` |
| NEG-23 | Declare a capacity/quota/depth/rate bound with an empty `overflow_policies` | 6 `BOUNDS_INVALID` |
| NEG-24 | Declare `overflow_policies = ["n/a"]` alongside a capacity bound, or permit a non-zero `retry` | 6 `BOUNDS_INVALID` |
| NEG-25 | Remove a unit's `failure_semantics` | 7 `FAILURE_INVALID` |
| NEG-26 | Map `unknown` to `accepted` (or `delivered`) | 7 `FAILURE_INVALID` |
| NEG-27 | Remove `evidence-incomplete` from a journal/write unit | 7 `FAILURE_INVALID` |
| NEG-28 | Remove a mandatory Doxygen tag from a `cpp` unit | 8 `DOXYGEN_INVALID` |
| NEG-29 | Remove the warning-as-error rule from the Doxygen plan | 8 `DOXYGEN_INVALID` |
| NEG-30 | Make `documented_elements` disagree with `public_elements` | 8 `DOXYGEN_INVALID` |
| NEG-31 | Cite an unknown governing ADR | 9 `GOVERNANCE_INVALID` |
| NEG-32 | Add a promoted REF-002 id | 9 `GOVERNANCE_INVALID` |
| NEG-33 | Mark a unit `implemented` without an accepted revision, or give an unreconciled `partial` unit no reason | 9 `GOVERNANCE_INVALID` |
| NEG-34 | Introduce a reverse dependency or a domain primitive (CAN/ECU/SOME/IP) in a core unit | 9 `GOVERNANCE_INVALID` |
| NEG-35 | Set the model baseline to a short/empty string | 10 `BINDING_INVALID` |
| NEG-36 | Cite an authorization record outside the accepted set | 10 `BINDING_INVALID` |
| NEG-37 | Point a `requirement_links` id at an id absent from the T008 register | 10 `BINDING_INVALID` |
| NEG-38 | Withhold or corrupt a dependency (T007 register, T008 register, or T009 model) | 10 `BINDING_INVALID` |
| NEG-39 | Use an `FR-###`/`SC-###`/`US#` anchor instead of a T008 software requirement id | 10 `BINDING_INVALID` |
| NEG-40 | Tamper the Markdown projection and run `--check-human` | 11 `DETERMINISM_INVALID` |
| NEG-41 | Insert an absolute host path or private address token | 12 `PUBLIC_SAFETY_INVALID` |
| NEG-42 | Mark a path `established` that does not exist in the tree | 13 `PATH_INVALID` |
| NEG-43 | Mark an existing path `planned` | 13 `PATH_INVALID` |
| NEG-44 | Remove the units covering a non-exempt T009 component | 10 `BINDING_INVALID` |
| NEG-45 | Remove the unit(s) covering one `XCOM-SW-*` register requirement | 10 `BINDING_INVALID` |
| NEG-46 | Declare an exemption for a component/requirement that is in fact covered, or declare an exemption without a reason/owning task | 10 `BINDING_INVALID` |

NEG-04 and NEG-05 also prove the id-keyed dict/set lookups coerce each raw entry id, so a container id is
reported as `SCHEMA_INVALID` (2) rather than raising an uncaught `TypeError`. The isolating fixtures
NEG-08b..NEG-08m and NEG-09b exist alongside the declared NEG-01..NEG-46 set without renumbering it: each
exercises one distinct mandatory-field or artifact-anchor path already implied by NEG-08/NEG-09, so a
regression in `_check_identity` is caught rather than skipped. A mutation probe that neutralises
any one check function makes the self-test fail, which is the load-bearing evidence recorded in
`implementation.md` (DET-04).

**Precedence closure.** When several defects are present, the validator must return the numerically lowest
applicable exit class and report all diagnostics in deterministic order; a failure must never report `OK`.

### 4.1 Declared-ordering contract consistency (ORD-01)

The declared array-ordering contract is exactly the set the validator enforces: ascending `id` order with
unique ids for the two top-level arrays `units` and `invariants`, and every family entry id is a non-empty
string (`detailed-design.md` §3.5). The stored-sorted nested arrays (`authorization_records`, `owning_tasks`,
`shared_state`, `artifact_paths`, `bounds`, `failure_semantics`, `component_refs`, `contract_refs`,
`governing_adrs`) are stored sorted and duplicate-free; the remaining nested arrays (`requirement_links`,
`file_block`, `public_tags`, `overflow_policies`, `planned_evidence`) preserve their authored order and carry
no lexical-sort guarantee.

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| ORD-01 | Declared ordering contract matches enforcement | inspect `detailed-design.md` §3.5 against the ordering check, or extract both name sets mechanically | identical two-array set; `--verify`, `--check-human`, and `--self-test` exit 0 on the real data |

## 5. Determinism and boundary cases

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| DET-01 | Byte-identical serialization and stored-model canonicality | serialize the model twice; compare the stored `unit-design.json` bytes with the canonical serialization | identical bytes; a whitespace-altered stored model → exit 11 |
| DET-02 | Markdown projection | `--check-human` after a manual key reorder | mismatch detected; exit 11 |
| DET-03 | Stable diagnostics | inject two defects, run twice | identical output and exit |
| DET-04 | New checks are load-bearing | neutralise one check function at a time and run `--self-test` | the corresponding NEG case fails, so the self-test exits nonzero |
| BND-01 | Work-product diff | `git diff --name-only <baseline> --` | no `src/`, `tests/`, `xdl/`, or `proto/` path; no `Doxyfile`/CMake change |
| BND-02 | Baseline resolves | `git rev-parse <baseline>` | prints the baseline SHA |
| BND-03 | Bounded input | each model/dependency ≤ 1 MiB, totals ≤ 4 MiB | accepted; over bound → exit 14 |
| BND-04 | Offline | no network/subprocess in the validator | no syscall to any peer; source inspection plus review |
| BND-05 | Runtime bound | wall clock ≤ 60 s | holds on the local checkout |
| BND-06 | Clean diff | `git diff --check <baseline> --` | no whitespace errors |
| BND-07 | Doxygen artifacts untouched | `git diff --name-only <baseline> -- Doxyfile scripts/check_doxygen.py` | empty; T010 plans, it does not execute |

## 6. Concurrency and resource bounds

T010 has **no runtime concurrency**: the unit-design model is a static document and the validator is
single-threaded and offline. Concurrency is therefore not applicable to the T010 candidate, and this plan does
not invent a concurrency case. The applicable candidate bounds are BND-03 (input size), BND-04 (no
network/subprocess), BND-05 (runtime ≤ 60 s), and determinism DET-01..DET-03.

The **designed** units' concurrency and resource bounds are first-class content and are verified structurally
by CHK-05 and CHK-06: every designed unit declares a thread-safety model, its shared mutable state, the
protecting mechanism or message-passing/process boundary, at least one finite resource bound, and the
overflow/backpressure policy set required by its bound kinds (`unit-specifications.md` §4,
`detailed-design.md` §7–§8). The production bounded-behaviour measurements under saturation (SC-004/SC-005)
remain owned by the implementation slices (T014, T021–T024, T029) and by T036's controlled benchmark; T010
asserts no measured concurrency result.

## 7. Requirement traceability

| Requirement | Checks |
| --- | --- |
| T010-SR-001 | CHK-01, CHK-02, CHK-16, ORD-01, DET-01, DET-02, NEG-01..NEG-05, NEG-40 |
| T010-SR-002 | CHK-03, CHK-11, CHK-15, NEG-06..NEG-09 (incl. NEG-08b..NEG-08m, NEG-09b), NEG-42, NEG-43 |
| T010-SR-003 | CHK-04, NEG-12..NEG-16, NEG-20 |
| T010-SR-004 | CHK-05, NEG-10, NEG-17..NEG-19, NEG-18b, NEG-19b |
| T010-SR-005 | CHK-06, NEG-21..NEG-24 |
| T010-SR-006 | CHK-07, NEG-11, NEG-25..NEG-27 |
| T010-SR-007 | CHK-08, NEG-28..NEG-30 |
| T010-SR-008 | CHK-09, CHK-10, NEG-44, NEG-46 |
| T010-SR-009 | CHK-10, NEG-37, NEG-39, NEG-45, NEG-46 |
| T010-SR-010 | CHK-11, NEG-31..NEG-34 |
| T010-SR-011 | CHK-12, CHK-13, CHK-15, NEG-35, NEG-36, NEG-38, NEG-42, NEG-43 |
| T010-SR-012 | CHK-18, BND-01, BND-06, BND-07, deterministic gate |
| T010-SR-013 | CHK-14, NEG-41 |
| T010-SR-014 | CHK-02, CHK-16, CHK-17, DET-01..DET-04, BND-03..BND-05, `--self-test` |

The T008 matrix declares `XCOM-DU-INTG-BASELINE` (locator `docs/engineering/xcom/t010/design-units.md`) and
allocates `XCOM-SW-INTG-001/002/003` to it; the T010 projection realises that locator and covers those
requirements through `XCOM-DU-022`–`025`. T010 does not edit the T008 matrix.

## 8. Implementation-stage sequence

1. Author `docs/engineering/xcom/t010/unit-design.json` implementing `detailed-design.md` §3–§11, and its
   deterministic projection `docs/engineering/xcom/t010/design-units.md`.
2. Create `scripts/validate_xcom_unit_design.py` implementing §12 and the self-test for NEG-01..NEG-46.
3. Run `--self-test`, `--verify`, and `--check-human`; run the mutation probes (DET-04) and ORD-01.
4. Record the new script path under `T-ENABLER` in `docs/engineering/xcom/task-ownership.{json,md}` and re-run
   `scripts/validate_xcom_task_ownership.py --verify` and `--check-human`.
5. Run `git diff --check`, the work-product diff, and the Doxygen-untouched check (BND-07).
6. Record the candidate revision, commands, tool versions, exit codes, and bounded outputs in
   `docs/engineering/xcom/t010/implementation.md`.
7. Mark the T010 checkbox complete in `specs/007-xcom-core/tasks.md` (implementation stage only).
8. Run the deterministic gate in §2 and retain its output.
9. Conduct the separate read-only review and record `docs/engineering/xcom/t010/internal-review.json`.

## 9. Evidence to retain with the candidate revision

- The gate command stdout/stderr and exit status.
- `--self-test`, `--verify`, and `--check-human` outputs and exit codes for the T010 validator.
- The T007 ownership validator `--verify`/`--check-human` outputs showing the consistency update holds.
- The mutation-probe (DET-04) output showing each check function is load-bearing, and the ORD-01 set
  comparison.
- The `git diff --name-only` and `git diff --check` outputs proving the work-product boundary, plus the
  BND-07 output proving `Doxyfile`/`check_doxygen.py` are untouched.
- The candidate revision hash and the Python/tool identities used.
- The model and projection file hashes recorded in the T010 package manifest.

Evidence must be bound to the exact candidate revision; missing, stale, or mismatched evidence cannot support
acceptance. This plan records no external-review or user-acceptance claim; external Codex review is deferred
until the `xcom-t007-t010-t017-t020` backlog completes.

## 10. Review plan (separate pass, not performed here)

The T010 unit design is reviewed in a separate read-only pass that: records findings before any repair;
verifies independently of the validator that every unit's ownership, lifetime, thread-safety, failure, bounds,
and Doxygen contract is complete and internally consistent, that requirement/component/contract coverage holds
against the T008 register and the T009 model, that the ADR/REF-002 dispositions and dependency-direction/
neutrality/safety invariants are preserved, that the work-product boundary holds and `Doxyfile` is untouched,
and that the model is public-safe; and produces `docs/engineering/xcom/t010/internal-review.json` with
`task_id = "T010"`, the run baseline, a `pass`/`fail` verdict, and an empty `findings` list on pass. T010
itself performs no acceptance and marks no other task complete.

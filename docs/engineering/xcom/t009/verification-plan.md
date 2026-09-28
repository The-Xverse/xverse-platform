# T009 Verification Plan — Named Checks, Commands, and Expected Results (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T009 |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `209084b11a211273f815980f753ba728e1251a09` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | repository-owned Python 3.11-compatible validator plus the deterministic Fabro gate; no C++/GTest case is added by T009 |

This plan is written **before** implementation. The implementation must realise every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
Because T009 is a documentation/governance task, the checks are deterministic static checks over the
architecture model; the deterministic gate for T009 runs no C++/Python test suite.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T009 209084b11a211273f815980f753ba728e1251a09
```

For T009 this gate requires:

- `docs/engineering/xcom/t009/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md` present;
- the T009 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- a changed-path set containing **no** `src/`, `tests/`, or `xdl/` path (T009 is a work-product task; the
  added `scripts/` validator is permitted);
- `git diff --check <baseline> --` clean.

Supporting commands (same tools, no network):

```sh
python3 scripts/validate_xcom_architecture_contracts.py --self-test
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --check-human
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
git rev-parse 209084b11a211273f815980f753ba728e1251a09
git diff --name-only 209084b11a211273f815980f753ba728e1251a09 --
git diff --check 209084b11a211273f815980f753ba728e1251a09 --
```

`git rev-parse` for the baseline must print the baseline SHA, proving the binding resolves.

## 3. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Model parses and matches the schema | `--verify` | exit 0; `schema_version == 1`; fixed fields/order; five top-level arrays sorted by id with unique non-empty-string ids; each fixed vocabulary equals its declared set; `counts` matches the entries |
| CHK-02 | Component identity, vocabulary, ownership | `--verify` | unique `XCOM-CMP-###` ids; layer/language/scope/maturity closed; owning slice/tasks consistent; mandatory fields non-empty |
| CHK-03 | Boundary completeness and resolution | `--verify` | exactly `XCOM-XB-001..011`; endpoints resolve; kind/direction/authorization closed; language pair ⊆ contract languages; safety/failure semantics non-empty |
| CHK-04 | Cross-language and external contracts | `--verify` | exactly `XCOM-XLC-001..006`; producer/consumer resolve; version/encoding/evolution rule present; boundary-kind/contract-kind consistency; Python→C++, gateway, observation, provider boundaries all resolve |
| CHK-05 | Diagram resolution and coverage | `--verify` | exactly `XCOM-DGM-001..005`; one component + one US1–US4 sequence each; participants/steps resolve; every component/boundary/contract covered |
| CHK-06 | Product-path anchoring and status | `--verify` + filesystem | every component has ≥ 1 path; `established` paths exist; `planned` paths are absent |
| CHK-07 | Governing ADR and REF-002 non-promotion | `--verify` | every ADR reference ∈ `adr_vocabulary`; `ref002.disposition == "unchanged"`; `promoted` empty; no promoted target |
| CHK-08 | Domain neutrality and dependency direction | `--verify` | direction/neutrality invariants present and enforced; Python build-time only; core free of domain primitives; no reverse dependency |
| CHK-09 | Safety invariant completeness | `--verify` | all declared safety/neutrality/dependency invariants plus `XCOM-INV-03`/`06` present, each required safety-boundary invariant carrying its accepted `kind` and statement text, non-empty enforcement; each `applies_to` resolves |
| CHK-10 | Baseline and authorization binding | `--verify` + `git rev-parse` | model binds the run baseline; `authorization_records` equals the T007 closed set; `adr_vocabulary` closed |
| CHK-11 | Maturity and reconciliation honesty | `--verify` | `implemented` requires an exact accepted revision; unreconciled coverage `partial` with reason; consistent with the T007 register; a missing/unreadable dependency fails closed (exit 9) |
| CHK-12 | Deterministic serialization and projection | `--verify` twice, `--check-human` | both JSON runs byte-identical; the Markdown projection (including Mermaid blocks) is exact |
| CHK-13 | Public-safety scan | `--verify` plus manual inspection | no credential, private address, key marker, unrestricted payload, or absolute host path in the model, projection, or output |
| CHK-14 | Docs-only boundary and ownership consistency | `git diff --name-only <baseline> --`; `validate_xcom_task_ownership.py` | no path starts with `src/`, `tests/`, `xdl/`, or `proto/`; the only added executable is `scripts/validate_xcom_architecture_contracts.py`; the T007 register still exits 0 |
| CHK-15 | Validator self-test | `--self-test` | positive fixture passes; every NEG case rejects with its declared exit class; a one-check neutralisation makes the self-test fail (DET-04) |
| CHK-16 | Offline, bounded, no-subprocess | source inspection + over-bound probe | imports limited to stdlib file/json/re/pathlib/pure computation; no network/subprocess/write; over-bound input → `IO_ERROR` (13) |

## 4. Negative cases (validator self-test fixtures)

Each NEG case injects one controlled defect — into a copy of the model, or by withholding a dependency
(NEG-21) — and asserts the declared nonzero exit with **no** partial success and no output claiming a valid
model.

| ID | Injected defect | Expected exit / class |
| --- | --- | --- |
| NEG-01 | Remove a required top-level field or reorder keys | 2 `SCHEMA_INVALID` |
| NEG-02 | Duplicate a component id | 3 `IDENTITY_INVALID` |
| NEG-03 | Set a component layer/language/scope/maturity to an unknown token | 3 `IDENTITY_INVALID` |
| NEG-04 | Remove a mandatory component field (empty responsibility) | 3 `IDENTITY_INVALID` |
| NEG-05 | Point a boundary endpoint at an undeclared component | 4 `BOUNDARY_INVALID` |
| NEG-06 | Use an unknown boundary kind | 4 `BOUNDARY_INVALID` |
| NEG-07 | Remove a required boundary (`XCOM-XB-007`) | 4 `BOUNDARY_INVALID` |
| NEG-08 | Point a boundary `contract` at an undeclared contract | 5 `CONTRACT_INVALID` |
| NEG-09 | Give a `language` boundary a language pair not in the contract `endpoint_languages` | 5 `CONTRACT_INVALID` |
| NEG-10 | Remove a contract `version` or `evolution_rule` | 5 `CONTRACT_INVALID` |
| NEG-11 | Reference an undeclared component as a diagram participant | 6 `DIAGRAM_INVALID` |
| NEG-12 | Reference an undeclared boundary in a sequence step | 6 `DIAGRAM_INVALID` |
| NEG-13 | Remove the US2 sequence diagram (user-story coverage loss) | 6 `DIAGRAM_INVALID` |
| NEG-14 | Cite an unknown governing ADR | 7 `GOVERNANCE_INVALID` |
| NEG-15 | Add a promoted REF-002 id (or mark a deferred target `implemented`) | 7 `GOVERNANCE_INVALID` |
| NEG-16 | Introduce a reverse dependency (runtime component consumed by an XDL-layer component) | 7 `GOVERNANCE_INVALID` |
| NEG-17 | Add a domain primitive (CAN/ECU/SOME/IP) to a core-layer component | 7 `GOVERNANCE_INVALID` |
| NEG-18 | Remove the no-TCP-listener invariant or make the permit optional | 8 `SAFETY_INVALID` |
| NEG-19 | Set the model baseline to a short/empty string | 9 `BINDING_INVALID` |
| NEG-20 | Cite an authorization record outside the accepted set | 9 `BINDING_INVALID` |
| NEG-21 | Withhold/bypass the T007 ownership register or the T008 requirement register | 9 `BINDING_INVALID` |
| NEG-22 | Tamper the Markdown projection and run `--check-human` | 10 `DETERMINISM_INVALID` |
| NEG-23 | Insert an absolute host path or private address token | 11 `PUBLIC_SAFETY_INVALID` |
| NEG-24 | Remove every `artifact_path` from a component | 3 `IDENTITY_INVALID` |
| NEG-25 | Mark a path `established` that does not exist in the tree | 12 `PATH_INVALID` |
| NEG-26 | Mark an existing path `planned` | 12 `PATH_INVALID` |
| NEG-27 | Duplicate a boundary id | 4 `BOUNDARY_INVALID` |
| NEG-28 | Duplicate a contract id | 5 `CONTRACT_INVALID` |
| NEG-29 | Store the component array out of id order | 2 `SCHEMA_INVALID` |
| NEG-30 | Mark an unreconciled component `implemented` without an accepted revision | 7 `GOVERNANCE_INVALID` |
| NEG-31 | Point a `requirement_links` id at an id absent from the T008 register | 9 `BINDING_INVALID` |
| NEG-32 | Give a family entry a non-string `id` (integer or null) | 2 `SCHEMA_INVALID` |
| NEG-33 | Keep a required safety invariant but weaken its statement (permitted TCP listener) | 8 `SAFETY_INVALID` |
| NEG-34 | Cite an `FR-###` anchor outside the accepted spec anchor set (`FR-999`) | 9 `BINDING_INVALID` |
| NEG-35 | Give `components[0]` an unhashable container `id` (a list) | 2 `SCHEMA_INVALID` |
| NEG-36 | Give `components[0]` an unhashable container `id` (a dict) | 2 `SCHEMA_INVALID` |
| NEG-37 | Give `boundaries[0]` an unhashable container `id` (a list) | 2 `SCHEMA_INVALID` |
| NEG-38 | Give `contracts[0]` an unhashable container `id` (a list) | 2 `SCHEMA_INVALID` |
| NEG-39 | Give `invariants[0]` an unhashable container `id` (a list) | 2 `SCHEMA_INVALID` |

NEG-35..NEG-39 exercise the id-keyed dict/set lookups in `_check_contracts`, `_check_diagrams`,
`_check_neutrality`, and `_check_safety`, which coerce each raw entry id with `str(...)` exactly as
`_ids_of` does; without that coercion an unhashable container id raises an uncaught `TypeError` instead of
the declared `SCHEMA_INVALID` (T009-IR-05).

A mutation probe that neutralises any one check function makes the self-test fail, which is the
load-bearing evidence recorded in `implementation.md` (DET-04). The probe covers all fifteen check
functions, including `_check_model_schema` (NEG-01/32/35..39), `_check_ordering` (NEG-29), `_check_paths`
(NEG-25/26), `_check_boundaries` (NEG-05/06/07/27), `_check_contracts` (NEG-08/09/10/28/35..39),
`_check_diagrams` (NEG-11/12/13/37), `_check_governance` (NEG-14/15), `_check_neutrality`
(NEG-16/17/35/36/39), `_check_safety` (NEG-18/33/39), `_check_binding` (NEG-19/20/21/31/34),
`_check_maturity` (NEG-30), `_check_dependencies` (NEG-21), `_check_determinism` (NEG-22), and
`_scan_public_safety` (NEG-23).

### 4.1 Declared-ordering contract consistency (ORD-01)

The declared array-ordering contract is exactly the set the validator enforces: ascending `id` order with
unique ids for the five top-level arrays `components`, `boundaries`, `contracts`, `diagrams`, and
`invariants`, and every family entry id is a non-empty string (`detailed-design.md` §3, `_check_ordering`
and `_check_model_schema`). The stored-sorted nested arrays (`authorization_records`, `adr_vocabulary`,
`owning_tasks`, `participants`, `endpoint_languages`, and each `artifact_paths` list) are stored sorted and
duplicate-free; the remaining nested arrays (`requirement_links`, `governing_adrs`, `safety`, `constraints`,
`applies_to`, and diagram `steps`) preserve their authored order and carry no lexical-sort guarantee.

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| ORD-01 | Declared ordering contract matches enforcement | inspect `detailed-design.md` §3 against `_check_ordering`, or extract both name sets mechanically | identical five-array sets; `--verify`, `--check-human`, and `--self-test` exit 0 on the real data; `architecture-model.md` remains the byte-exact projection |

**Precedence closure.** When several defects are present, the validator must return the numerically lowest
applicable exit class and report all diagnostics in deterministic order; a failure must never report `OK`.

## 5. Determinism and boundary cases

| ID | Name | Stimulus | Expected |
| --- | --- | --- | --- |
| DET-01 | Byte-identical serialization | serialize the model twice | identical bytes |
| DET-02 | Markdown projection | `--check-human` after a manual key reorder | mismatch detected; exit 10 |
| DET-03 | Stable diagnostics | inject two defects, run twice | identical output and exit |
| DET-04 | New checks are load-bearing | neutralise one check at a time, run `--self-test` | the corresponding NEG case fails, so the self-test exits nonzero |
| BND-01 | Docs-only diff | `git diff --name-only <baseline> --` | no `src/`, `tests/`, `xdl/`, or `proto/` path |
| BND-02 | Baseline resolves | `git rev-parse <baseline>` | prints the baseline SHA |
| BND-03 | Bounded input | each model/dependency ≤ 1 MiB, totals ≤ 4 MiB | accepted; over bound → exit 13 |
| BND-04 | Offline | no network/subprocess in the validator | no syscall to any peer; source inspection plus review |
| BND-05 | Runtime bound | wall clock ≤ 60 s | holds on the local checkout |
| BND-06 | Clean diff | `git diff --check <baseline> --` | no whitespace errors |

## 6. Concurrency and resource bounds

T009 has **no runtime concurrency**: the architecture model is a static document and the validator is
single-threaded and offline. Concurrency is therefore not applicable, and the plan does not invent a
concurrency case. The applicable bounds are BND-03 (input size), BND-04 (no network/subprocess), BND-05
(runtime ≤ 60 s), and determinism DET-01..DET-03. Production concurrency/resource bounds remain owned by
the implementation slices (`T-CORE`, `T-OBS`, `T-STIM`) and their own verification plans, and by T010's
unit-design deliverable.

## 7. Requirement traceability

| Requirement | Checks |
| --- | --- |
| T009-SR-001 | CHK-01, CHK-12, ORD-01, NEG-01, NEG-27, NEG-28, NEG-29, NEG-32, NEG-35..NEG-39, DET-01, DET-02 |
| T009-SR-002 | CHK-02, CHK-06, NEG-02, NEG-03, NEG-04, NEG-24, NEG-31, NEG-34 |
| T009-SR-003 | CHK-03, NEG-05, NEG-06, NEG-07, NEG-27 |
| T009-SR-004 | CHK-04, NEG-08, NEG-09, NEG-10, NEG-28 |
| T009-SR-005 | CHK-05, NEG-11, NEG-12, NEG-13 |
| T009-SR-006 | CHK-07, NEG-14, NEG-15 |
| T009-SR-007 | CHK-08, NEG-16, NEG-17 |
| T009-SR-008 | CHK-09, NEG-18, NEG-33 |
| T009-SR-009 | CHK-11, NEG-21, NEG-30 |
| T009-SR-010 | CHK-06, CHK-10, NEG-19, NEG-20, NEG-25, NEG-26, BND-02 |
| T009-SR-011 | CHK-14, BND-01, BND-06, gate step |
| T009-SR-012 | CHK-13, NEG-23 |
| T009-SR-013 | CHK-12, CHK-15, CHK-16, DET-01..DET-04, BND-03..BND-05 |

## 8. Implementation-stage sequence

1. Author `docs/engineering/xcom/t009/architecture-model.json` implementing `detailed-design.md`
   §3–§9, and its deterministic projection `architecture-model.md` (including Mermaid diagrams).
2. Create `scripts/validate_xcom_architecture_contracts.py` implementing §10 and the self-test.
3. Run `--self-test`, `--verify`, and `--check-human`; run the mutation probes (DET-04) and ORD-01.
4. Record the new script path under `T-ENABLER` in `docs/engineering/xcom/task-ownership.{json,md}` and
   re-run `scripts/validate_xcom_task_ownership.py --verify` and `--check-human`.
5. Run `git diff --check` and the docs-only diff.
6. Record the candidate revision, commands, tool versions, exit codes, and bounded outputs in
   `docs/engineering/xcom/t009/implementation.md`.
7. Mark the T009 checkbox complete in `specs/007-xcom-core/tasks.md` (implementation stage only).
8. Run the deterministic gate in §2 and retain its output.

## 9. Evidence to retain with the candidate revision

- The gate command stdout/stderr and exit status.
- `--self-test`, `--verify`, and `--check-human` outputs and exit codes for the T009 validator.
- The T007 ownership validator `--verify`/`--check-human` outputs showing the consistency update holds.
- The mutation-probe (DET-04) output showing each of the fifteen check functions is load-bearing.
- The ORD-01 declared-ordering/enforcement set comparison.
- The `git diff --name-only` and `git diff --check` outputs proving the docs-only boundary.
- The candidate revision hash and the Python/tool identities used.
- The model and projection file hashes recorded in the T009 package manifest.

Evidence must be bound to the exact candidate revision; missing, stale, or mismatched evidence cannot
support acceptance. This plan records no external-review or user-acceptance claim; external Codex review is
deferred until the `xcom-t007-t010-t017-t020` backlog completes.

## 10. Review plan (separate pass, not performed here)

The T009 architecture model is reviewed in a separate read-only pass that: records findings before any
repair; verifies independently of the validator that every boundary and cross-language contract resolves,
that the required component/boundary/contract/diagram/invariant sets are complete, that the ADR/REF-002
dispositions and dependency-direction/neutrality/safety invariants are preserved, that the docs-only
boundary holds, and that the model is public-safe; and produces
`docs/engineering/xcom/t009/internal-review.json` with `task_id = "T009"`, the run baseline, a
`pass`/`fail` verdict, and an empty `findings` list on pass. T009 itself performs no acceptance and marks
no other task complete.

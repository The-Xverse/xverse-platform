# T013 Implementation Record — Immutable Core Value, Contract, Policy, and Diagnostic Types

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T013 (capability 007, slice `T-CORE`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` |
| Predecessor | T012 reviewed terminal package (`docs/engineering/xcom/t012/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t013/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t013-package.json` (produced by the deterministic package action) |
| Authorization | ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0020; `specs/007-xcom-core/tasks.md` T013 |
| Maturity | Prototype-only immutable value library implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T013 implements the bounded slice required by the T013 task entry: *"Implement immutable contract, item,
origin, time, correlation, diagnostic, and policy types."*

The baseline already provides the immutable value, result, contract, item, origin, time, correlation, and
diagnostic types. The accepted `XCOM-CMP-004` responsibility additionally requires **policy** value types,
and none existed. The candidate therefore:

1. adds the immutable, bounded `FlowPolicy` declaration value with the `OrderingPolicy`,
   `ReliabilityPolicy`, and `OverflowPolicy` enumerations whose external text and numeric ranges are taken
   verbatim from the accepted `io.xverse.xcom` Profile `flow-policy` form
   (`xdl/profiles/xcom-v0.1.schema.json`);
2. adds the stable policy diagnostic code `DiagnosticCode::invalid_policy` (`XCOM-TYPE-E006`) and the
   `ValidationPhase::policy` phase so a rejected declaration produces the same deterministic, sorted
   diagnostics as every other core value;
3. adds the focused T013 policy unit and negative cases to the existing `tests/xcom/core_types/`
   executables;
4. re-verifies every T013-owned existing core type unchanged: the value, result, contract, item, and
   diagnostic sources are compiled and tested at the candidate revision with no behavioural change and no
   test weakening.

It changes **no** build file (the core-types target already compiles `contract.cpp` and
`diagnostic.cpp`, so no `.cmake`/`CMakeLists.txt` change and no inherited T020 trace-link hash refresh is
required), XDL schema, Profile, plan, provider, lifecycle, observation, stimulation, gateway, Meson/Python,
or any later task's path; it adds no dependency, opens no endpoint, and accesses no ambient, network,
filesystem, process, or legacy resource. It implements T013 only and accepts nothing.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/contract.hpp` | edit | adds `OrderingPolicy`, `ReliabilityPolicy`, `OverflowPolicy`, their `to_string` overloads, `FlowPolicyInput`, and the immutable `FlowPolicy` declaration; no existing declaration changed or removed |
| `src/xverse/xcom/src/contract.cpp` | edit | adds the three policy `to_string` mappings, the policy vocabulary/range validators, and `FlowPolicy::create`; the contract accumulator gained a phase parameter defaulted to `contract`, so every existing contract diagnostic is byte-identical |
| `src/xverse/xcom/include/xverse/xcom/diagnostic.hpp` | edit | adds `DiagnosticCode::invalid_policy` and `ValidationPhase::policy` as declared enumerators; no existing code, phase, value, or bound changed |
| `src/xverse/xcom/src/diagnostic.cpp` | edit | extends `known_code`, `known_phase`, and the two `to_string` switches for the new policy code and phase |
| `tests/xcom/core_types/unit_tests.cpp` | edit | adds `test_flow_policy_table`, `test_flow_policy_boundaries`, `test_flow_policy_immutability_and_determinism` |
| `tests/xcom/core_types/negative_tests.cpp` | edit | adds `test_flow_policy_rejections`, `test_flow_policy_exact_diagnostics` |
| `docs/engineering/xcom/t013/requirements.md` | add (plan stage, frozen) | T013-STK/T013-SR requirements, scope, authorities, affected paths, REF-002 disposition, gaps, requirement-to-check index |
| `docs/engineering/xcom/t013/architecture.md` | add (plan stage, frozen) | boundary, trust boundaries, components, ordered data flow, interfaces, quality attributes, traceability |
| `docs/engineering/xcom/t013/detailed-design.md` | add (plan stage, frozen) | policy vocabulary/range tables, rules, failure semantics, bounds, Doxygen/public-safety design |
| `docs/engineering/xcom/t013/unit-specifications.md` | add (plan stage, frozen) | unit inventory, ownership/lifetime/thread-safety/bounds, planned tests, traceability |
| `docs/engineering/xcom/t013/verification-plan.md` | add (plan stage, frozen) | deterministic gate, CHK-01–CHK-18, NEG-01–NEG-25, candidate-bound evidence, exit criteria |
| `docs/engineering/xcom/t013/implementation.md` | add (this record) | realized change, symbols, commands and results, limitations, traceability |
| `specs/007-xcom-core/tasks.md` | edit (T013 checkbox `[ ]` → `[X]`) | capability task ledger; marked complete only after the authorized work and every required local check passed |

### 3.1 Realized policy vocabulary, ranges, and external text

| Field | C++ enumerator / type | Accepted set | External `to_string` text |
| --- | --- | --- | --- |
| `ordering` | `OrderingPolicy` | `fifo`, `priority`, `unordered` | `"fifo"`, `"priority"`, `"unordered"` |
| `reliability` | `ReliabilityPolicy` | `at_most_once`, `at_least_once`, `exactly_once`, `best_effort` | `"at-most-once"`, `"at-least-once"`, `"exactly-once"`, `"best-effort"` |
| `overflow` | `OverflowPolicy` | `drop_oldest`, `drop_newest`, `coalesce`, `lossless_backpressure`, `reject`, `fail_closed` | `"drop-oldest"`, `"drop-newest"`, `"coalesce"`, `"lossless-backpressure"`, `"reject"`, `"fail-closed"` |
| `deadline_ms` | `std::int64_t` | 0 ≤ value ≤ 600000 (`kMaximumDeadlineMs`) | decimal |
| `retry` | `std::int64_t` | 0 ≤ value ≤ 64 (`kMaximumRetry`) | decimal |
| `queue_depth` | `std::int64_t` | 1 ≤ value ≤ 65536 (`kMaximumQueueDepth`) | decimal |

The set and every numeric bound equal the accepted Profile `flow-policy` form exactly (command 12).
Unknown enumerations and out-of-range numbers are rejected by `FlowPolicy::create` with
`invalid_policy` (`XCOM-TYPE-E006`) in the `policy` phase, at most one diagnostic per violated field, in
the fixed validation order `ordering`, `reliability`, `overflow`, `deadline_ms`, `retry`, `queue_depth`,
and the returned `DiagnosticSet` is deterministically sorted by the canonical ordering key.

### 3.2 Realized symbols and locations

| Symbol / construct | Location | Realized behaviour |
| --- | --- | --- |
| `OrderingPolicy`, `ReliabilityPolicy`, `OverflowPolicy` | `contract.hpp` (§3.1) | declared immutable value enumerations; static-lifetime vocabulary |
| `to_string(OrderingPolicy/ReliabilityPolicy/OverflowPolicy)` | `contract.hpp` declaration, `contract.cpp` definition | static-lifetime external text matching the Profile exactly; `"unknown"` for out-of-vocabulary values |
| `FlowPolicyInput` | `contract.hpp` | call-scoped declaration aggregate; owns nothing |
| `FlowPolicy` | `contract.hpp` | immutable value-owned policy: const accessors only, copy constructor `noexcept` defaulted, copy assignment deleted, `operator==` compares every declared field |
| `FlowPolicy::create` | `contract.cpp` | `noexcept`, allocation-free; validates three enumerations and three ranges; returns `Result<FlowPolicy>` |
| `known_ordering` / `known_reliability` / `known_overflow` | `contract.cpp` (anonymous namespace) | exhaustive, fail-closed vocabulary checks |
| `validate_policy_range` | `contract.cpp` (anonymous namespace) | one inclusive-range check appending one `invalid_policy` diagnostic in the `policy` phase |
| `DiagnosticAccumulator::add` phase parameter | `contract.cpp` | additive default `ValidationPhase::contract`; the six existing contract call sites are unchanged |
| `DiagnosticCode::invalid_policy` | `diagnostic.hpp` | appended enumerator; external text `XCOM-TYPE-E006` |
| `ValidationPhase::policy` | `diagnostic.hpp` | appended enumerator; external text `"policy"` |
| `known_code` / `known_phase` / `to_string` switches | `diagnostic.cpp` | extended with the new policy code and phase; every existing value unchanged |

### 3.3 Additivity and baseline preservation

- Both new enumerators are **appended** after the existing enumerators, so no existing enumerator value,
  diagnostic code text, phase text, ordering key, or capacity changes. `"policy"` (6 bytes) and
  `XCOM-TYPE-E006` (14 bytes) fit the unchanged `kMaximumPhaseBytes = 23` and `kMaximumCodeBytes = 14`.
- `FlowPolicy` is a standalone declaration value; it is **not** composed into `CommunicationContract`
  (`D-01`, `T013-OPEN-01`). Every existing contract/item consumer and test is therefore untouched.
- The change lives in the already-compiled `contract.cpp`/`diagnostic.cpp` translation units, so no build
  file changes and no inherited T020 provenance refresh (`D-04`, `T013-OPEN-02`).
- No existing test case is removed, renamed, or weakened; the new cases are added inside the existing
  executables, so the discovered CTest count is unchanged at 248 (command 4).

## 4. Verification method and evidence

Environment: CMake 3.22.1, Ninja 1.10.1, CTest 3.22.1, GNU C++ 11.4.0 (C++20, `-Wall -Wextra
-Wpedantic -Werror`), Python 3.13; repository checkout at the authorized baseline
`863f11ac990c1ce178a0f9d8eb2489e4a5243fe7`. The three T011 admitted offline inputs are required as the
named variables `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN`; their private-store **values** are not restated here
(`T013-SR-014`). As recorded for T012/T019/T020, the deterministic gate's plain configure fails closed
at the T025 test-toolchain admission check because the run process environment carries none of them; the
only permitted resolution is the narrow A-1 cache seeding, used for the candidate build and for the
gate.

### 4.1 Commands and observed results

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `git rev-parse 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` | 0 | Prints the baseline SHA; the binding resolves (CHK-01). |
| 2 | `cmake -S . -B build/t013-cand -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON` with the three admitted inputs seeded as explicit cache values (A-1) | 0 | Configure succeeds; `-- Configuring done` / `-- Generating done` (CHK-03). |
| 3 | `cmake --build build/t013-cand --parallel 4` | 0 | 61/61 targets build with no warning promoted to an error (CHK-03, CHK-10). |
| 4 | `ctest --test-dir build/t013-cand -N` | 0 | `Total Tests: 248` — identical to the baseline count; no test added, removed, or renamed (CHK-13, NEG-22). |
| 5 | `ctest --test-dir build/t013-cand -R xcom_core_types --output-on-failure` | 0 | `100% tests passed, 0 tests failed out of 3` — `xcom_core_types_unit`, `xcom_core_types_negative`, `xcom_core_types_external_consumer` (CHK-05, CHK-06, CHK-07, CHK-08). |
| 6 | `ctest --test-dir build/t013-cand --output-on-failure --parallel 4` | 0 | `100% tests passed, 0 tests failed out of 248` in ~3.1 s (CHK-13). |
| 7 | `python3 scripts/validate_xcom_task_ownership.py --verify` and `--check-human` | 0 / 0 | `X-COM task-ownership validation passed` (CHK-14). |
| 8 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | 0 | `X-COM requirements/traceability validation passed` (CHK-14). |
| 9 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | 0 | `X-COM architecture/contracts validation passed` (CHK-14). |
| 10 | `python3 scripts/validate_xcom_unit_design.py --verify` | 0 | `X-COM unit-design validation passed` (CHK-14). |
| 11 | `git diff --name-only 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7 --` + `git ls-files --others --exclude-standard` | 0 | exactly the four T013 production files, the two T013 test files, the five frozen T013 plan work products, and the one-line `tasks.md` checkbox; no `xdl/`, `proto/`, `src/xverse_xdl/`, `.cmake`, root/`CMakeLists.txt`, or other task's path (CHK-02, CHK-15, CHK-17). |
| 12 | Profile cross-read of `xdl/profiles/xcom-v0.1.schema.json` `$defs/flowPolicy` | 0 | `ordering [fifo, priority, unordered]`; `reliability [at-most-once, at-least-once, exactly-once, best-effort]`; `overflow [drop-oldest, drop-newest, coalesce, lossless-backpressure, reject, fail-closed]`; ranges 0–600000 / 0–64 / 1–65536 — equal to §3.1 (CHK-06, T013-SR-007). |
| 13 | `git diff --check 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7 --` | 0 | empty output; the candidate diff is whitespace-clean (CHK-16). |
| 14 | forbidden-API source scan of the six changed core/test files | 0 | no socket/network/resolver, ambient/secret lookup, filesystem, process/subprocess, dynamic-load, or legacy include or call; standard library only; no added thread or dependency (CHK-10, NEG-20, NEG-25). |
| 15 | public-safety scan of the six changed core/test files | 0 | no credential, private address, unrestricted payload, proprietary excerpt, environment-specific absolute host path, or sensitive deployment value (CHK-11, NEG-23). |
| 16 | `python3 scripts/check_doxygen.py --coverage-only` | 1 | pre-existing Python-docstring findings only; its input set is `**/*.py`, disjoint from every T013 changed path, and it reports **zero** `src/xverse/xcom` findings. Strict declaration-level C++ Doxygen remains `DOX-GAP-01`/`T011-GAP-01`, owned by T011/T037 (`T013-LIM-02`); every new/changed declaration carries a `@brief` and the new API its ownership/lifetime/thread-safety/failure clauses (CHK-12). |
| 17 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T013 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` | 0 | `{"ok": true, "task_id": "T013", "changed_paths": 7, "checks": ["ctest:248"]}` (CHK-16). |

Command 17 is run **after** the T013 checkbox is marked and this record is written. The seven counted
changed paths are the four T013 production files, the two T013 test files, and the one-line `tasks.md`
checkbox (the five frozen plan work products are still untracked at this point and are captured by the
package action once the workflow checkpoints them). The A-1 seeding configure supplies the three
admitted input values as explicit cache values into the gate's own git-ignored `build/fabro-t013` cache;
the gate's unmodified configure/build/`ctest` sequence then reuses it. The hash-verified offline
preflight is unchanged, no ambient path or network resolution is added, and no admission check is
weakened.

### 4.2 Exact policy diagnostic sequence (NEG-17, CHK-07)

For `{ordering = fifo, reliability = at_least_once, overflow = reject, deadline_ms = -5, retry = 65,
queue_depth = 4}` (two violations), `FlowPolicy::create` returns the byte-stable sequence:

```text
policy|error|XCOM-TYPE-E006|deadline_ms|deadline is outside the declared range|use a deadline between 0 and 600000 milliseconds
policy|error|XCOM-TYPE-E006|retry|retry is outside the declared range|use a retry count between 0 and 64
```

For `{ordering = unordered, reliability = best_effort, overflow = <unknown>, deadline_ms = -5, retry =
65, queue_depth = 4}` (three violations), the sorted sequence is exactly:

```text
policy|error|XCOM-TYPE-E006|deadline_ms|deadline is outside the declared range|use a deadline between 0 and 600000 milliseconds
policy|error|XCOM-TYPE-E006|overflow|overflow policy is outside the declared vocabulary|use one declared overflow policy
policy|error|XCOM-TYPE-E006|retry|retry is outside the declared range|use a retry count between 0 and 64
```

`test_flow_policy_immutability_and_determinism` additionally feeds the same five `invalid_policy`
diagnostic inputs in forward and reverse order through `DiagnosticSet::create_from_inputs` and asserts
byte-identical serialization, so the new code/phase participates in the same deterministic ordering key
as every existing diagnostic.

### 4.3 Artifact identity at this candidate state

| Artifact | SHA-256 | Bytes |
| --- | --- | ---: |
| `src/xverse/xcom/include/xverse/xcom/contract.hpp` | `4a1ed3c817322deafbb0a7e29b61a88439b9aad302d0c57bac17eaedc15a75db` | 14537 |
| `src/xverse/xcom/src/contract.cpp` | `27174faaa462f067805eaac703c083aa4436e34b76d00b23a811baf1283c72dc` | 12332 |
| `src/xverse/xcom/include/xverse/xcom/diagnostic.hpp` | `c0df81c7868453e8509deedfd02e6d08f800a477c70cbdf3e7e83f411967bdc5` | 10922 |
| `src/xverse/xcom/src/diagnostic.cpp` | `4aaa25338266a898cec7c6ecbe913f33a4de3c52e0716ecc72bfb2b34cef48f1` | 10838 |
| `tests/xcom/core_types/unit_tests.cpp` | `07a537adc0e1c83672ab7a36539259e6329f8de99b435791d6d09176305c51c1` | 21164 |
| `tests/xcom/core_types/negative_tests.cpp` | `fb8830b77b4f1c44b324d8f6dfac7a109de975122451221a7e348b617701edee` | 21814 |
| `docs/engineering/xcom/t013/requirements.md` | `12ae81611a10e6d9635e8580b67d4e4fd4470bbc609d812f367782a368910886` | 29105 |
| `docs/engineering/xcom/t013/architecture.md` | `2244c8f43eb2c8fdae7dcd14233f9f71f2f247af8498e629b0b3581a62948908` | 13790 |
| `docs/engineering/xcom/t013/detailed-design.md` | `c23d4eed9648f593e97146286f0c41e9db528c778a73778b39bbaffd4e4285fa` | 13959 |
| `docs/engineering/xcom/t013/unit-specifications.md` | `cf2fd6b4efe2fb2bb006ca7bb031c45d6892d2770b36506a5815669801cabc62` | 13489 |
| `docs/engineering/xcom/t013/verification-plan.md` | `55ee45c279d5882fd36ad1ec0ba9b6df7b70fd5dc8b7cf88e38805d0706a081a` | 15060 |

`docs/engineering/xcom/t013/implementation.md`, `docs/engineering/xcom/t013/internal-review.json`,
`reports/xcom-queue/t013-package.json`, and the one-line `specs/007-xcom-core/tasks.md` checkbox are bound
by the package record's per-file SHA-256. The package action recomputes every changed tracked path's
SHA-256; a successor candidate must record its own exact revision and repeat every affected check.

## 5. Requirement-to-evidence traceability

| Requirement | Primary check(s) | Evidence |
| --- | --- | --- |
| T013-STK-001 | CHK-02, CHK-03, CHK-13 | cmd 2, 3, 4, 11 |
| T013-STK-002 | CHK-05, CHK-09, NEG-01..NEG-18 | cmd 3, 5, 6; §3.1, §4.2 |
| T013-STK-003 | CHK-08, CHK-12 | cmd 5; §3.2; `test_flow_policy_immutability_and_determinism` |
| T013-STK-004 | CHK-04, CHK-10 | cmd 14; §3.3 |
| T013-STK-005 | CHK-02, CHK-14, CHK-15, CHK-18 | cmd 7–11 |
| T013-SR-001 | CHK-03, CHK-05, CHK-09 | cmd 3, 5, 6 (existing value cases unchanged) |
| T013-SR-002 | CHK-03, CHK-04, CHK-08 | cmd 5; contract sources re-verified unchanged |
| T013-SR-003 | CHK-03, CHK-04, CHK-09 | cmd 5 (existing item cases unchanged) |
| T013-SR-004 | CHK-06, CHK-09 | cmd 5, 12; §3.1; `test_flow_policy_table`, `test_flow_policy_boundaries` |
| T013-SR-005 | CHK-05, CHK-06, NEG-13..NEG-17 | cmd 5; §4.2; `test_flow_policy_rejections` |
| T013-SR-006 | CHK-06, CHK-08 | `test_flow_policy_immutability_and_determinism` (copy and no-upgrade cases) |
| T013-SR-007 | CHK-06 | cmd 12; §3.1 |
| T013-SR-008 | CHK-07, NEG-11, NEG-17 | cmd 5; §4.2; `test_flow_policy_exact_diagnostics` |
| T013-SR-009 | CHK-06, CHK-07, CHK-12 | cmd 5, 12, 16; §3.2; `test_flow_policy_rejections` (`E006`/`policy` text) |
| T013-SR-010 | CHK-03, CHK-08, NEG-18 | cmd 5; `test_rvalue_source_invariants` (existing, unchanged) |
| T013-SR-011 | CHK-09 | cmd 5; §3.1; boundary cases |
| T013-SR-012 | CHK-04, NEG-19 | cmd 5; item/value sources re-verified unchanged |
| T013-SR-013 | CHK-10, NEG-20, NEG-25 | cmd 14; cmd 3 offline build |
| T013-SR-014 | CHK-11, NEG-23 | cmd 15 |
| T013-SR-015 | CHK-12 | cmd 16; §3.2 (documented declarations) |
| T013-SR-016 | CHK-02, CHK-14, CHK-15, CHK-18 | cmd 7–11 |
| T013-SR-017 | CHK-16, NEG-24 | cmd 13, 17 |

## 6. Public safety

The T013 work products and the committed source, tests, and CMake contract contain repository-relative
paths, type and field names, stable code text, bounded fixed diagnostic text, and pass/fail outcomes only.
They contain no credential, private address, unrestricted payload, proprietary source excerpt, or
sensitive deployment value. The T011 admitted input **values** (host prefix, package manifest, and
test-toolchain locations) are referenced by variable **name** only and are not committed; generated build
evidence exists only beneath the git-ignored build directory. The single non-repository absolute path is
the workflow's own deterministic-gate invocation in command 17
(`/home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py`), retained exactly as in the accepted
T009–T012 records; it is the workflow tool path, not a sensitive deployment value (`T013-SR-014`,
CHK-11, NEG-23).

## 7. Limitations, gaps, and maturity

Recorded from the requirements package and **not** resolved by T013:

- `T013-LIM-01` — the core model is a prototype value library: it makes no runtime, transport, timing,
  compatibility, or production-readiness claim, and it is not yet user-accepted (T041).
- `T013-LIM-02` — strict declaration-level Doxygen (`WARN_IF_UNDOCUMENTED`/`WARN_NO_PARAMDOC`) remains
  open (`DOX-GAP-01`, `T011-GAP-01`), owned by T011/T037; T013 documents every new/changed declaration
  but does not enable the strict configuration. `scripts/check_doxygen.py` is a Python-only docstring
  gate (command 16) whose pre-existing findings are disjoint from the T013 changed paths.
- `T013-LIM-03` — the policy value is a declaration/validation type; queueing, backpressure, deadline,
  and retry are neither enforced nor measured here, and no timing fidelity is claimed.
- `T013-LIM-04` — the large fixed payload capacity keeps item and successful-result objects
  correspondingly large; this bounded-storage tradeoff is inherited unchanged from the baseline.
- `T013-LIM-05` — `scripts/validate_xcom_core_types.py` is legacy SESN-era tooling in the T013-owned path
  set; the repository-owned workflow neither depends on nor executes it, and T013 neither runs nor edits
  it.
- `T013-GAP-01` — the T008 register attributes `XCOM-SW-CORE-001`/`-010` to T012 and `XCOM-SW-CORE-006`
  to T015, and the T010 unit design attributes `XCOM-DU-002` to T012, while `tasks.md`/`XCOM-CMP-004`
  assign the core contract and diagnostic value types to T013. T013 records the anomaly (this record and
  `requirements.md` §7.3/§8.2) and rewrites nothing; both registers remain unchanged.
- `T013-GAP-02` — composing and enforcing the declared policy on endpoints, routes, and provider
  capability matching is `XCOM-SW-CORE-004`'s runtime half, owned by T014/T015.
- `T013-GAP-03` — the consolidated cross-cutting core unit/negative matrix remains T016.
- `T013-GAP-04` — candidate acceptance under capability 007 remains with T039/T041.

Maturity: prototype-only, Linux x86-64, standard-library-only immutable value library, locally verified,
making **no** X-COM runtime, transport, compatibility, or production-readiness claim. Not user-accepted
(T041) and not externally reviewed (Codex review deferred until this ordered backlog completes). No
REF-002 target requirement is promoted; the capability disposition stays `unchanged` with an empty
`promoted` set (`T013-SR-016`).

## 8. Definition-of-done status (requirements view)

- (a) The six named work products exist under `docs/engineering/xcom/t013/` and are mutually
  consistent. ✔
- (b) Every requirement in `requirements.md` §3–§4 maps to ≥ 1 named check in `verification-plan.md`. ✔
- (c) The implementation stage delivered the policy value types, the new policy diagnostic code/phase,
  and the focused policy cases, marked the T013 checkbox, and recorded this note. ✔
- (d) The deterministic gate and the named checks pass at the candidate revision (commands 2–17). ✔
- (e) The package record is written by the package action after the review pass. ◐
- (f) A separate DeepSeek internal review records a passing verdict with no findings
  (`docs/engineering/xcom/t013/internal-review.json`). ◐ — produced by the review stage, not self-declared
  here.

This does **not** constitute external review or user acceptance, which remain deferred to the backlog and
to T041 respectively.

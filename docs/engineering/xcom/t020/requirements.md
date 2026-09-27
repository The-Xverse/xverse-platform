# T020 Requirements — Ordering-Equivalence, Malformed-Plan, Drift, Bound, and Regression Tests

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T020 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `1e289bfe6234553df94eb25065371f7d423fad88` |
| Predecessor tasks | T007–T010 (engineering-baseline enablers), T017 (Profile v0.1 / activation-plan v1 schema and digest contract), T018 (Python plan compiler), T019 (bounded C++ decoder; reviewed terminal package `1e289bf`) |
| Successor tasks | T035–T041 (integration, evidence, independent review, acceptance) |
| Requirement ID families | `T020-STK-###` (stakeholder), `T020-SR-###` (software) |
| Authority | the T020 entry in `specs/007-xcom-core/tasks.md` ("Add ordering-equivalence, malformed-plan, drift, bound, and regression tests"); `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4, "Complexity Tracking"; `specs/007-xcom-core/spec.md` FR-002, FR-006, FR-007, FR-025/FR-027, FR-030, FR-031, SC-001, SC-002, failure semantics; `specs/007-xcom-core/contracts/{xdl-profile,communication-plan}.md`; `specs/007-xcom-core/data-model.md` invariants 1, 2, 7; `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-010`, `XCOM-DU-011`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-003`, `XCOM-CMP-004`, `XCOM-XLC-001`, `XCOM-XB-003`); `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` (`XCOM-SW-XDL-001`, `XCOM-SW-XDL-002`, `XCOM-SW-XDL-003`, `XCOM-SW-CORE-003`, `XCOM-DU-XDL-BASELINE`, `XCOM-T-XDL`); `docs/engineering/xcom/task-ownership.{md,json}` (`T-XDL` slice); `docs/engineering/xcom/t017/{detailed-design,verification-plan}.md`; `docs/engineering/xcom/t018/{detailed-design,verification-plan}.md`; `docs/engineering/xcom/t019/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`; Constitution 2.1.0 articles II, III, VII, VIII, IX, X and the capability acceptance gates; ADR-0016, ADR-0018, ADR-0020; ACC002, ACC003, ACC013, ACC014, ACC015 |
| Classification | Public-safe engineering work product |
| Maturity | Plan/design target. `XCOM-DU-010`/`XCOM-DU-011` verification coverage remains `allocated`; no T020 test source is accepted, reviewed, or integrated by this document. |

### 1.1 Authority statement

This document specifies only the bounded T020 slice: the independent **test** package that proves the accepted
XDL-derived activation-plan chain end to end. It exercises the accepted T017 Profile/digest contract, the
accepted T018 Python compiler, and the accepted T019 bounded C++ decoder with five named suites —
ordering-equivalence, malformed-plan, drift, bound, and regression — under the `T-XDL` shared test path
`tests/xcom/activation_plan/`.

It elaborates the accepted software requirements `XCOM-SW-XDL-001`, `XCOM-SW-XDL-002`, `XCOM-SW-XDL-003`, and
`XCOM-SW-CORE-003`, and the accepted design units `XCOM-DU-010` (canonical schema and digest contract) and
`XCOM-DU-011` (bounded activation-plan decode with independent version/digest checks).

It does **not** author or change production code: no `src/xverse_xcom/**` decoder, compiler, schema, or
runtime source is created or edited, and no test authored by T017, T018, or T019 is edited or weakened. It does
not activate, bind, or run any endpoint, route, provider, observation, stimulation, permit/session, journal, or
gateway; does not redesign the accepted architecture; does not change a functional requirement, success
criterion, ADR, schema, or contract statement; does not fix a production numeric bound value; does not create a
competing configuration language; does not add an admitted dependency; does not accept or integrate any
candidate; and does not approve any other task.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the accepted plan and
contracts, the T017 schemas and digest/provenance contract, the constitution, an accepted ADR, the T007
ownership register, the T008 register/matrix, the T009 architecture model, or the T010 unit design is resolved
in favour of the accepted source. A material gap is reported rather than guessed. Unresolved gaps are recorded
in §9.

## 2. Scope

### 2.1 In scope (bounded T020)

Keep T020 strictly inside the T020 task entry: *"Add ordering-equivalence, malformed-plan, drift, bound, and
regression tests."*

1. **Add an owned test package under the `T-XDL` shared test path `tests/xcom/activation_plan/`** consisting of
   one header-only support artifact and five C++ GoogleTest suites (ordering-equivalence, malformed-plan,
   drift, bound-matrix, regression) plus one Python `pytest` module for the cross-language ordering/regression
   checks. No T017/T018/T019 test source or fixture is edited.
2. **Ordering-equivalence suite.** Prove that equivalent normalized inputs and equivalent plan
   representations produce byte-identical canonical plan bodies and equal domain-separated digests, that the
   declared per-collection ordering and the duplicate-free `activationOrder` rule are enforced, that diagnostics
   are ordered deterministically, and that the accepted T018 compiler and the accepted T019 C++ decoder agree
   on one canonical body and digest (`SC-002`, `XCOM-SW-XDL-003`).
3. **Malformed-plan suite.** Systematically inject structural defects (truncation, unbalanced delimiters,
   duplicate members at every object level, non-object roots, trailing content, wrong JSON types, `null` where
   an object/array is required, missing required members, unknown nested members, invalid UTF-8, and
   over-nesting) and assert the declared fail-closed outcome, stable code, and the **absence** of a decoded
   plan.
4. **Drift suite.** Guard the decoder's declared member, vocabulary, pattern, ordering-key, and numeric-range
   tables against the committed `activation-plan.schema.json`; guard the plan-version constant, the closed
   digest sub-schema, and the canonical-body/digest rule against silent drift; and guard the anchored T017
   fixtures and the accepted Profile form vocabulary against change.
5. **Bound-matrix suite.** Exercise every declared `DecodeLimits` bound (byte, depth, node, string, and each of
   the nine decoded-entity caps) at, below, and above its declared value, prove the `below/over` behaviour is
   `failed`/`rejected` exactly as declared, prove a limit `< 1` fails closed with `XCOM-DECODE-UNKNOWN`, and
   prove no value is returned on any breach.
6. **Regression suite.** Pin the accepted behaviour: the committed T017 plan fixtures still decode; their
   recorded and recomputed digests still equal the T017 golden values; the canonical digested bytes, the 16
   required members, the `DecodeLimits` defaults, the closed decode-code vocabulary, and the SHA-256 known
   answers are unchanged; and no accepted artifact is mutated by the T020 candidate.
7. **Register the C++ suites as CMake/CTest targets** under the shared `src/xverse/xcom/CMakeLists.txt` with
   T020-specific labels, so the deterministic gate discovers them via `ctest -N` and runs them via `ctest`
   together with the existing suites.
8. **Integrate the Python module into the existing `pytest` discovery** (no `pyproject.toml`/config change) so
   the T020 cross-language checks run under the gate's `python3 -m pytest -q`.
9. **Preserve the accepted architecture, ADRs, dependency direction, domain neutrality, safety boundaries,
   REF-002 dispositions, ownership, and dependency order**, and record the T020 candidate's changed paths,
   baseline, and evidence in its work products.

### 2.2 Explicit exclusions (must remain absent from the T020 candidate)

No production code under `src/xverse/xcom/include/**` or `src/xverse/xcom/src/**` is created or changed (T019);
no Python compiler or validator source under `src/xverse_xdl/**` or `scripts/**` is created or changed
(T017/T018); no `xdl/**` schema or Profile artifact is changed (T017); no `proto/**` file, `Doxyfile`, CMake
library definition, or dependency-admission input is changed (T030/T011); no T017/T018/T019 test source or
fixture is edited or weakened; no schema or digest/provenance contract statement is rewritten; no accepted
requirement or success criterion is weakened; no endpoint/route/provider is activated or bound; no observation,
stimulation, permit/session, journal, or gateway unit is implemented; no second configuration language or
competing topology is invented; no XDL normalization or reference-resolution logic is duplicated into a test;
no new admitted dependency is introduced (the C++ tests use only the standard library, the already-admitted
`nlohmann/json` header, and the already-required GTest/gmock prefix; the Python module uses only the
already-admitted interpreter and standard library plus the repository's own modules); no legacy repository is
read or written; no external network peer, TCP listener, package manager, or production workload is used; no
production numeric bound value is fixed; no other task is marked complete; no software candidate is accepted
or integrated; no REF-002 target is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T020 |
| --- | --- | --- |
| The bounded C++ decoder and its own unit/negative tests | T019 | complete; T020 consumes the decoder API read-only and edits no T019 source |
| The Python compiler, its own tests, and the T017 validator | T017/T018 | complete; T020 imports them read-only for cross-language checks and edits no source |
| Endpoint/route/provider activation and binding from a decoded plan | T-CORE | allocated; T020 decodes and asserts values, binds nothing |
| Observation, stimulation, permit/session, journal, gateway | T-OBS / T-STIM / T-CORE | allocated; outside the T020 boundary |
| Compiler/build/dependency admission with hashes, licenses, and generated-code provenance | T011 | allocated; T020 adds no dependency and runs in the admitted offline build environment |
| Warning-free Doxygen generation and full traceability/public-safety validation | T037, T038 | allocated; T020 supplies the test evidence those tasks consolidate |
| Full evidence bundle, independent review, explicit user acceptance | T035–T041 | allocated; T020 does not accept, complete, or integrate any candidate |
| Configured production bound values | implementation slices | allocated; T020 asserts finite declared bounds and fixes no production numeric value |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths (T020-owned, from the `T-XDL` slice exclusive list).** The plan stage adds exactly
`docs/engineering/xcom/t020/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`.
The implementation stage adds `tests/xcom/activation_plan/t020_support.hpp`
(`T020-TEST-SUPPORT`), `tests/xcom/activation_plan/t020_ordering_equivalence_tests.cpp`,
`tests/xcom/activation_plan/t020_malformed_plan_tests.cpp`,
`tests/xcom/activation_plan/t020_drift_tests.cpp`,
`tests/xcom/activation_plan/t020_bound_matrix_tests.cpp`,
`tests/xcom/activation_plan/t020_regression_tests.cpp`,
`tests/xcom/activation_plan/test_xcom_plan_ordering_equivalence.py`, and
`docs/engineering/xcom/t020/implementation.md`; it edits the **shared** build path
`src/xverse/xcom/CMakeLists.txt` (new CTest targets and labels only; the pre-existing
`xcom_observation_disabled_benchmark` registration is unchanged) and the **shared** capability path
`specs/007-xcom-core/tasks.md` (T020 checkbox line only). The review and package stages add
`docs/engineering/xcom/t020/internal-review.json` and `reports/xcom-queue/t020-package.json`.

No file under `src/xverse/xcom/include/`, `src/xverse/xcom/src/`, `src/xverse_xdl/`, `scripts/`, `proto/`, or
`xdl/` is changed. No T017 artifact (`xdl/profiles/xcom-v0.1.schema.json`,
`src/xverse/xcom/contracts/v1/activation-plan.schema.json`, `scripts/validate_xcom_plan.py`,
`specs/007-xcom-core/contracts/xdl-profile.md`, `docs/engineering/xcom/t017/**`), no T018 artifact
(`src/xverse_xdl/xcom_plan.py`, `tests/test_xcom_plan.py`, `docs/engineering/xcom/t018/**`), and no T019
artifact (`src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`,
`src/xverse/xcom/src/activation_plan.cpp`, `tests/xcom/activation_plan/decoder_unit_tests.cpp`,
`tests/xcom/activation_plan/decoder_negative_tests.cpp`, `docs/engineering/xcom/t019/**`) is changed. The
committed T017 plan fixtures under `tests/xcom/activation_plan/fixtures/plan/valid/` are read **read-only**,
and T020 adds no fixture under the T017 `fixtures/` tree.

**Negative cases.** The declared T020 negative set is the ordering-equivalence cases `T20-ORD-01`..`T20-ORD-08`,
the malformed-plan cases `T20-MAL-01`..`T20-MAL-14`, the drift cases `T20-DRF-01`..`T20-DRF-09`, the bound cases
`T20-BND-01`..`T20-BND-11`, the regression cases `T20-REG-01`..`T20-REG-10`, the determinism cases
`T20-DET-01`..`T20-DET-04`, and the boundary/governance cases `T20-G01`..`T20-G05` in `verification-plan.md`
§4–§7. Each case injects one controlled defect into a bounded, repository-owned, public-safe synthetic plan or
a mutation of a committed fixture and asserts the declared outcome (`accepted`/`rejected`/`failed`), code,
affected identifier, and the presence/absence of a decoded plan. These identifiers are T020-scoped and are
distinct from any same-named identifier in the T017, T018, or T019 work products.

**Public safety.** The T020 test source, Python module, and retained evidence must contain no credentials,
secrets, private addresses, proprietary excerpts, unrestricted payloads, or absolute host paths. Every plan
input is repository-owned, public-safe, and synthetic, or a read-only committed fixture. The Python module
absolute paths are derived from `__file__` at run time and never embedded in an authored artifact. The
deterministic gate is operationally invoked by the Workflow harness; the retained work products reference it by
the repository-relative locator `automation/xcom_feature_gate.py` and never embed a host-specific absolute
path, so the public-safe artifact set satisfies this rule without an exemption.

**Concurrency and resource bounds.** T020 has no mutable shared state and spawns no thread: the C++ suites are
`offline-single-threaded` GoogleTest executables that call the pure decoder API and compare immutable values;
the Python module is a pure `pytest` module. Consequently **no concurrency bound applies and none is asserted**;
the suites are deterministic and repeatable. Applicable resource bounds are inherited from `DecodeLimits`:
plan bytes ≤ 5 MiB, nesting depth ≤ 100, node count ≤ 100 000, bounded string length, and the finite decoded-
entity caps for contracts, endpoints, routes, providers, observation points, clock domains, diagnostics,
activation order, and provenance resources; the bound-matrix suite asserts them explicitly. The suites perform
no network, subprocess, or filesystem **write** access; the only filesystem reads are the read-only committed
fixtures and schemas. T020 fixes **no** production numeric bound value; runtime bounds come from the activation
plan or unit configuration (FR-007).

## 3. Terminology and measurement

| Term | Meaning in T020 |
| --- | --- |
| Ordering equivalence | Two representations of one normalized plan derive the same canonical bytes, digest, outcome, and decoded value (`SC-002`). |
| Malformed plan | Plan bytes that violate JSON syntax or the closed plan shape; rejected fail-closed with no value. |
| Drift | Any divergence between the decoder's declared tables/constants and the committed normative schema, contract, fixture, or golden value. |
| Bound | A finite declared `DecodeLimits` member; a limit `< 1` is invalid and an input over a limit fails closed. |
| Regression | A pinned accepted behaviour (fixture decode, golden digest, canonical bytes, member set, defaults, code vocabulary) that must not change silently. |
| Cross-language anchor | A committed artifact (T017 plan fixture) whose canonical body and digest are independently reproduced by the Python compiler/validator and the C++ decoder. |
| Outcome | Closed vocabulary `accepted`, `rejected`, `failed`. |
| Maturity | Closed vocabulary `implemented`/`partial`/`allocated`/`deferred`/`superseded`/`conflicting`/`needs_clarification`. |
| First proof | The bounded capability-007 prototype scope: owned synthetic fixtures, no legacy asset, no external peer, no TCP listener. |

Measurements are discrete and observable: the test outcome and stable code; the recomputed versus recorded
digest; byte-level canonical output equality; whether a decoded value is returned; per-family and per-bound
results; and the `ctest`/`pytest` exit status and discovered-test count. No availability, throughput, timing, or
probability figure is asserted.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-002, FR-006, FR-007, FR-025/FR-027, FR-030, FR-031, SC-001, SC-002, failure semantics, key entities | the ordering-equivalence, fail-closed, bounds, and evidence obligations |
| Task entry | `specs/007-xcom-core/tasks.md` T020 and the dependency-order section | authorized bounded scope and successor ordering |
| Accepted plan | `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4 | test placement and the bounded-decode boundary |
| Profile contract | `specs/007-xcom-core/contracts/xdl-profile.md` "Profile v0.1 payload grammar", "Activation-plan v1 digest and provenance" | the canonical serialization, domain separator, digested region, digest form, and fail-closed rules |
| Plan contract | `specs/007-xcom-core/contracts/communication-plan.md` | required plan content, unknown-fields-fail-closed, inspectable-vs-activatable, and independent decode/verify before activation |
| Data model | `specs/007-xcom-core/data-model.md` invariants 1, 2, 7 | logical/physical separation, exact-handle ownership, plan-digest binding |
| Plan schema | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` | the closed member set, vocabularies, patterns, conditional status rule, and collection keys |
| Decoder API | `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`, `src/xverse/xcom/src/activation_plan.cpp` (T019; anchored, unchanged) | the bounded decode entry points and immutable value the tests consume |
| T019 tests | `tests/xcom/activation_plan/decoder_{unit,negative}_tests.cpp` (T019; anchored, unchanged) | the existing decoder test style and the `NEG-D*` set T020 must not duplicate or weaken |
| T017/T018 references | `scripts/validate_xcom_plan.py` (`canonical_bytes`, `compute_digest`, `check_digest`, `validate_plan_structure`), `src/xverse_xdl/xcom_plan.py` (`compile_plan_text`, `compile_plan`, `canonical_plan_bytes`, `compute_digest`) | the independent Python reference the T020 Python module cross-checks read-only |
| T017 fixtures | `tests/xcom/activation_plan/fixtures/plan/valid/plan-activatable.json`, `plan-inspectable.json` | bounded positive inputs read read-only by both the C++ and Python suites |
| Unit design | `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-010`, `XCOM-DU-011`) | ownership, lifetime, thread-safety, bounds, failure semantics, and planned-evidence tokens |
| Architecture model | `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-003`, `XCOM-CMP-004`, `XCOM-XLC-001`, `XCOM-XB-003`) | component/boundary identities and the one-way dependency rule |
| Requirement register/matrix | `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` | `XCOM-SW-XDL-001/002/003`, `XCOM-SW-CORE-003`, and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators |
| Ownership register | `docs/engineering/xcom/task-ownership.{md,json}`, `scripts/validate_xcom_task_ownership.py` | slice/path ownership, baseline/authorization binding |
| Build environment | `docs/engineering/xcom/{build-environment,dependency-lock}.md`, `docs/engineering/xcom/t025/test-dependency-admission.md`, `cmake/XComOfflineDependencies.cmake` | the admitted offline inputs and GTest test prefix the C++ suites require |
| REF-002 traceability | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/sads-requirements-traceability.json` | the accepted dispositions T020 records without promotion |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles II, III, VII, VIII, IX, X and the capability acceptance gates | domain neutrality, XDL centrality, platform-first, direction, maturity, traceability |
| ADRs | ADR-0016, ADR-0018, ADR-0020 | governing decisions the design cites |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC002/ACC003/ACC013/ACC014/ACC015 | exact authorization references |
| Baseline provenance | `git rev-parse 1e289bfe6234553df94eb25065371f7d423fad88`, `git log` for `src/xverse/xcom/**`, `tests/xcom/**`, `src/xverse_xdl/**`, `xdl/**` | existing-artifact anchoring only; never acceptance proof |

## 5. Stakeholder requirements

### T020-STK-001 — Ordering-equivalence is proven across the derived plan chain

**Statement.** Capability 007 must prove that equivalent normalized inputs and equivalent representations of one
plan produce byte-identical canonical plan bodies, equal domain-separated digests, and identical decode
outcomes and diagnostic ordering regardless of source document order, and that the accepted Python compiler and
the accepted C++ decoder agree on that one canonical body and digest.

**Acceptance criteria (observable).**

- AC-1: Member-reordered, whitespace-varied, and integral-number-variant representations of one plan yield one
  canonical byte string and one digest from both the Python reference and the C++ decoder.
- AC-2: Per-collection ordering by the declared key, unique keys, and the duplicate-free `activationOrder` rule
  are asserted; an out-of-order or duplicate-keyed collection is rejected.
- AC-3: Diagnostics are ordered deterministically, and a reordered-but-equivalent input yields the same decoded
  diagnostics and outcome as the original.

**Source anchors.** `XCOM-SW-XDL-003`; spec SC-002, FR-002; `contracts/communication-plan.md`; T017
`detailed-design.md` §5; T018 `verification-plan.md`; T019 `verification-plan.md` §5.

### T020-STK-002 — Malformed plans are rejected fail-closed and systematically

**Statement.** The derived-plan chain must reject malformed plan bytes and closed-shape violations
fail-closed — with a stable code and no decoded value — across a systematic matrix of structural defects, and
T020 must exercise that matrix without duplicating or weakening the T019 `NEG-D*` set.

**Acceptance criteria (observable).**

- AC-1: Truncation, unbalanced delimiters, trailing content, duplicate members, non-object roots, wrong JSON
  types, `null` where an object/array is required, missing required members, unknown nested members, invalid
  UTF-8, and over-nesting are each classified with the declared outcome and code.
- AC-2: Every malformed-plan case returns no decoded plan; no case reports `accepted`.
- AC-3: The T020 matrix is a distinct superset family from the T019 `NEG-D*` set and neither edits nor weakens
  any T019 case.

**Source anchors.** spec FR-006, failure semantics; `contracts/communication-plan.md`; T019
`requirements.md` §2.2/§2.4; T010 `XCOM-DU-011` failure semantics; `XCOM-SW-CORE-003`.

### T020-STK-003 — Silent drift is detected and prevented

**Statement.** T020 must guard the decoder's declared member, vocabulary, pattern, ordering-key, and
numeric-range tables against the committed normative plan schema; guard the plan-version constant, the closed
`digest` sub-schema, the canonical-body/digest rule, and the anchored T017 fixtures against silent change; and
detect any drift fail-closed.

**Acceptance criteria (observable).**

- AC-1: The decoder's declared tables are asserted equal to the committed `activation-plan.schema.json` for the
  16 required members, every closed enum, the identifier/version/digest/generator/diagnostic patterns, the
  collection keys, the `minItems` minimums, and the numeric ranges.
- AC-2: The closed `$defs/digest` sub-schema (`algorithm ∈ {sha256}`, value `^[0-9a-f]{64}$`) is asserted equal
  to the decoder's embedded-digest rule, and a violated embedded digest is rejected.
- AC-3: The plan-version const, the domain separator, and each committed fixture's canonical body/digest are
  pinned against golden values so a silent change fails the suite.

**Source anchors.** `XCOM-SW-XDL-001`, `XCOM-SW-XDL-003`; spec FR-031, SC-002; `contracts/xdl-profile.md`;
T017 `detailed-design.md` §5; T019 `verification-plan.md` §3 CHK-06.

### T020-STK-004 — Every declared bound is exercised and fails closed

**Statement.** T020 must exercise every declared `DecodeLimits` bound — byte, depth, node, string, and each
decoded-entity cap — at, below, and above its declared value; a limit `< 1` must fail closed with
`XCOM-DECODE-UNKNOWN`; and no bound breach may return a decoded value.

**Acceptance criteria (observable).**

- AC-1: For each bound, an input within the bound is `accepted` and an input over the bound is `failed`
  (`XCOM-DECODE-BOUND`) or, for an over-length string, `rejected` (`XCOM-DECODE-SHAPE`) exactly as the T019 unit
  contract declares — with no decoded value in either breach case.
- AC-2: Every `DecodeLimits` member is exercised with the value `0` and is `failed` (`XCOM-DECODE-UNKNOWN`).
- AC-3: The bound-matrix cases are finite, bounded, and deterministic, and fix no production numeric value.

**Source anchors.** spec FR-007 (partial); T010 `XCOM-DU-011` bounds/failure semantics; T019
`unit-specifications.md` §3.4; `XCOM-SW-XDL-003`.

### T020-STK-005 — Accepted behaviour is pinned, and governance is preserved

**Statement.** T020 must pin the accepted behaviour of the derived-plan chain, must preserve the accepted
architecture, accepted ADRs, REF-002 dispositions, safety boundaries, failure semantics, one-way dependency
direction, domain neutrality, ownership, and dependency order, must not implement or change another task, must
not weaken an existing requirement, schema, contract, or test, and must not mark the task complete in the plan
stage or claim acceptance/review.

**Acceptance criteria (observable).**

- AC-1: The T020 regression suite pins the committed fixtures' decode, recorded and recomputed digests, the
  canonical digested bytes, the 16 required members, the `DecodeLimits` defaults, the closed decode-code
  vocabulary, and the SHA-256 known answers.
- AC-2: The candidate changes only the T020-owned and declared shared paths of §2.4; no production source under
  `src/xverse/xcom/include/**`, `src/xverse/xcom/src/**`, `src/xverse_xdl/**`, `scripts/**`, `xdl/**`,
  `proto/**`, or `Doxyfile` is changed, and no existing test is edited or weakened.
- AC-3: The C++ suites and Python module are offline and pure, add no admitted dependency, and import no legacy
  artifact.
- AC-4: `ref002.disposition = "unchanged"` with an empty promoted set; no deferred/allocated target is
  reported as implemented.
- AC-5: The T020 checkbox is left unchecked in the plan stage and marked only in the implementation stage; no
  acceptance, review, or integration claim is recorded; the T007 ownership validator still passes.

**Source anchors.** ADR-0018/ADR-0020; ACC014/ACC015; Constitution arts. II, III, VII, VIII, IX, X; T007
register; `tasks.md` T039/T041.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names of the test artifacts
and units are fixed by `detailed-design.md` and `unit-specifications.md`.

### 6.1 The five suites

#### T020-SR-001 — Ordering-equivalence suite (refines T020-STK-001)

**Statement.** The T020 candidate must add an ordering-equivalence suite that proves, in both the C++ decoder
and the Python reference, that equivalent plan representations produce one canonical body and digest; that the
declared per-collection ordering, unique-key, and duplicate-free `activationOrder` rules hold; and that
diagnostics are ordered deterministically across equivalent inputs.

**Acceptance criteria.** Canonical bytes and digests are equal across member-order, whitespace, and
integral-number variants in both languages; each identity-bearing collection is asserted in declared key order
and a reordered collection is rejected (`XCOM-DECODE-SHAPE`); the decoded diagnostics and outcome are identical
across equivalent inputs.

**Verification intent.** CHK-20-01, CHK-20-02; `T20-ORD-01`..`T20-ORD-08`; `T20-DET-01`..`T20-DET-04`.

#### T020-SR-002 — Malformed-plan suite (refines T020-STK-002)

**Statement.** The T020 candidate must add a malformed-plan suite that systematically injects structural and
closed-shape defects and asserts the declared fail-closed outcome, stable code, affected identifier, and the
absence of a decoded plan, as a distinct family from the T019 `NEG-D*` set.

**Acceptance criteria.** Every `T20-MAL-*` case asserts `rejected` or `failed` with its declared code and no
plan; no malformed case reports `accepted`; no T019 test is edited.

**Verification intent.** CHK-20-03; `T20-MAL-01`..`T20-MAL-14`.

#### T020-SR-003 — Drift suite (refines T020-STK-003)

**Statement.** The T020 candidate must add a drift suite that asserts the decoder's declared member, enum,
pattern, ordering-key, and numeric-range tables equal the committed plan schema; that the closed `$defs/digest`
sub-schema equals the decoder's embedded-digest rule; and that the plan-version const, the domain separator, and
the committed fixtures' canonical body/digest are pinned against golden values.

**Acceptance criteria.** Every declared table is asserted equal to the schema; a violated embedded digest is
rejected (`XCOM-DECODE-SHAPE`); a pinned golden value mismatch fails the suite; the Profile form vocabulary
remains the accepted five-form set.

**Verification intent.** CHK-20-04; `T20-DRF-01`..`T20-DRF-09`.

#### T020-SR-004 — Bound-matrix suite (refines T020-STK-004)

**Statement.** The T020 candidate must add a bound-matrix suite that exercises each declared `DecodeLimits`
member at, below, and above its value; asserts the declared `failed`/`rejected` classification with no decoded
value on a breach; and asserts a limit `< 1` is `failed` (`XCOM-DECODE-UNKNOWN`).

**Acceptance criteria.** For each of the 13 `DecodeLimits` members an accepting and a failing case exists; an
over-length string is `rejected` (`XCOM-DECODE-SHAPE`); every zero limit is `failed` (`XCOM-DECODE-UNKNOWN`);
no breach returns a plan.

**Verification intent.** CHK-20-05; `T20-BND-01`..`T20-BND-11`.

#### T020-SR-005 — Cross-language regression suite (refines T020-STK-001, T020-STK-005)

**Statement.** The T020 candidate must add a regression suite, in C++ and Python, that pins the committed T017
fixtures' decode, recorded and recomputed digests, canonical digested bytes, the 16 required members, the
`DecodeLimits` defaults, the closed decode-code vocabulary, and the SHA-256 known answers; and that proves the
Python compiler/validator and the C++ decoder agree on the committed fixtures' canonical body and digest.

**Acceptance criteria.** Both fixtures decode to `accepted` with the pinned field values; the recorded and
recomputed digests equal the pinned golden values in both languages; the canonical body hash and digest match
across languages; the defaults, member set, and code vocabulary equal their pinned values.

**Verification intent.** CHK-20-06, CHK-20-07; `T20-REG-01`..`T20-REG-10`.

### 6.2 Tests, governance, and binding

#### T020-SR-006 — Test registration and no-existing-test weakening (refines T020-STK-005)

**Statement.** The five C++ suites must be registered as CMake/CTest targets under the shared
`src/xverse/xcom/CMakeLists.txt` with T020-specific labels and discovered/executed by the deterministic gate;
the Python module must be discovered by `python3 -m pytest -q`; and neither the T017/T018 Python suites nor the
T019 decoder suites may be edited or weakened.

**Acceptance criteria.** `ctest -N` discovers the T020 suites and `ctest` passes them together with the
existing suites; `pytest -q` passes and collects the T020 module; `git diff` shows no edit to an existing test.

**Verification intent.** CHK-20-08, CHK-20-10; `ctest` and `pytest` gates.

#### T020-SR-007 — Boundary, dependency, and REF-002 non-promotion (refines T020-STK-005)

**Statement.** The T020 candidate must change only the T020-owned and declared shared paths of §2.4, must bind
to baseline `1e289bfe6234553df94eb25065371f7d423fad88`, must cite only accepted authorizations, must link
`XCOM-SW-XDL-001/002/003`/`XCOM-SW-CORE-003` and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators, must add no
admitted dependency and no Python/legacy coupling beyond the read-only repository modules the tests exercise,
must leave the T020 checkbox unchecked in the plan stage, and must record `ref002.disposition = "unchanged"`
with an empty promoted set; a change outside the authorized paths, an unknown authorization, a dangling link, a
new dependency, a REF-002 promotion, or a public-safety leak fails validation.

**Acceptance criteria.** `git diff --name-only` ⊆ the declared path set; baseline binds by `git rev-parse`;
links resolve in the T008 matrix; the C++ suites include only admitted headers; the Python module imports only
the repository's own modules and the standard library; REF-002 promoted set empty; public-safety scan clean.

**Verification intent.** CHK-20-09; `T20-G01`..`T20-G05`.

## 7. Capability 007 requirement links

| Capability anchor | T020 disposition and link | Remaining work |
| --- | --- | --- |
| FR-002 derive from the exact normalized XDL graph; no competing configuration language | **Implemented for this slice (test)**: the suites exercise only the derived, digest-bound plan chain and invent no configuration; `XCOM-SW-XDL-002`, `XCOM-SW-XDL-003`. | T038 validates traceability. |
| FR-006 fail before traffic flows on an incompatible identity/direction/schema/interaction/capability/policy | **Partial for this slice (test)**: the malformed-plan and regression suites prove that an inconsistent or malformed plan is rejected before any activation; `XCOM-SW-CORE-003`. | Binding/activation enforcement stays with the end/route lifecycle units. |
| FR-031 versioned `io.xverse.xcom` Profile compiled into the digest-bound activation plan | **Implemented for this slice (test)**: the drift and regression suites pin the plan version and the digest/provenance contract; the Profile form vocabulary is asserted unchanged. | T035/T038 verify; T011 admits the environment. |
| SC-001 supported XDL inputs derive without manual rework | **Partial for this slice (test)**: the ordering-equivalence suite proves equivalent normalized inputs derive one canonical plan. | T036 benchmarks. |
| SC-002 equivalent normalized inputs produce byte-identical plans and diagnostic ordering | **Implemented for this slice (test)**: `XCOM-SW-XDL-003`; `T20-ORD-*` and the Python cross-language checks prove byte-identity and diagnostic ordering, and the regression suite pins it. | T036 benchmarks; T038 validates. |
| FR-007 explicit bounded queue/ordering/reliability/deadline/retry/overflow/backpressure | **Partial (test)**: the bound-matrix suite proves the declared decode bounds and policy-set bounds fail closed; runtime enforcement is T-CORE. | Runtime enforcement by the core units. |
| FR-025/FR-027 safe, deterministic diagnostics and public-safe evidence | **Partial (constraint, test)**: the suites assert stable codes and identifiers only, with no payload content or sensitive value. | T035/T038 verify. |
| FR-030 traceability, evidence, separate review | **Partial (governance)**: T020 binds `XCOM-SW-XDL-001/002/003`/`XCOM-SW-CORE-003` and the T008/T010 locators; review/acceptance remain separate. | T038 validates; T039/T041 review and accept. |
| Constitution arts. II, III, VII, VIII, IX, X | **Implemented for this slice (design)**: T020-SR-001..007 preserve neutrality, XDL centrality, platform-first, direction, maturity, and traceability. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T020 adds tests only and implements **no** direct REF-002 communication requirement `XVE-SYS-0139`–`0158` and
no shared requirement. It **records** `ref002_disposition = "unchanged"` and promotes none. Every capability-007
disposition in `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` remains exactly as accepted.

| REF-002 group | Disposition in T020 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — no target is promoted; the disposition set is empty | T020 adds tests over a build-time derived artifact and demonstrates no runtime communication or interoperability. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may validate contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open items are the build-environment prerequisite (§9 A-1) and the
fact that T020 is a test-only slice (§9 A-2), which T020 records rather than resolves.

## 9. Assumptions and open items

1. **A-1 (build-environment prerequisite)** — the deterministic T020 gate runs `pytest`, `cmake`, and `ctest`,
   which requires the already-admitted offline inputs `XVERSE_XCOM_TOOLCHAIN`,
   `XVERSE_XCOM_PACKAGE_MANIFEST` (the twelve-entry lock), and the GTest test prefix
   `XVERSE_XCOM_T025_TEST_TOOLCHAIN` documented in `docs/engineering/xcom/build-environment.md` and
   `docs/engineering/xcom/t025/test-dependency-admission.md`. These are provisioned outside the repository and
   are not part of any Git artifact. The implementation stage must run the gate's exact command first and, if
   it fails solely because these inputs are not in the process environment, resolve it only as permitted by
   `verification-plan.md` §2.4 (the same narrow, already-authorised A-1 fallback T019 recorded, reaching the
   shared `cmake/XComOfflineDependencies.cmake` only if still required) without weakening hash-verified
   admission; if it cannot be resolved that way, the implementation stage records a blocker rather than
   weakening the gate.
2. **A-2 (test-only slice)** — T020 adds tests only. It changes no production source path under
   `src/xverse/xcom/include/**`, `src/xverse/xcom/src/**`, `src/xverse_xdl/**`, `scripts/**`, `xdl/**`, or
   `proto/**`. The only non-test, non-doc change is the shared `src/xverse/xcom/CMakeLists.txt` CTest wiring and
   the shared `specs/007-xcom-core/tasks.md` checkbox line.
3. **A-3 (no new fixture tree)** — T020 reads the two committed T017 plan fixtures read-only and uses inline,
   bounded, repository-owned synthetic vectors. It adds no fixture under `tests/xcom/activation_plan/fixtures/`
   and changes no `expected-summary.txt`.
4. **A-4 (cross-language anchor without a subprocess)** — the C++ suites are pure and cannot invoke Python, and
   the Python module cannot load the C++ library. Cross-language equivalence is proven by both languages
   independently reproducing the canonical body and digest of the same committed fixture and agreeing on the
   pinned golden values, and by the Python module compiling synthetic normalized graphs and comparing the
   result to the T017 validator reference. This is the bounded capability-007 prototype scope; it fixes no
   production value and adds no dependency.
5. **A-5 (no concurrency surface)** — T020 introduces no thread and no mutable shared state; the C++ suites are
   single-threaded GoogleTest executables and the Python module is a pure `pytest` module. No concurrency bound
   is applicable or asserted; determinism is asserted by repetition within one process.
6. **A-6** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch, tag, or
   ambient state is a valid binding.
7. **A-7** — T020 fixes **no** production numeric bound value. Every bound the suites exercise is the finite
   declared `DecodeLimits` cap; runtime bounds come from the activation plan or unit configuration (FR-007).
8. **A-8** — Requirement identifiers `T020-STK-###`/`T020-SR-###`, test-unit identifiers `T020-U-###`, and case
   identifiers `T20-ORD-*`/`T20-MAL-*`/`T20-DRF-*`/`T20-BND-*`/`T20-REG-*`/`T20-DET-*`/`T20-G*` are
   candidate-chosen names fixed by `detailed-design.md`; no accepted component, contract, requirement, schema,
   design unit, or T019 case identifier is renumbered. `T020-U-01`..`T020-U-05` extend the verification coverage
   of `XCOM-DU-010`/`XCOM-DU-011`; T020 does not renumber `XCOM-DU-009`/`010`/`011` or `T019-U-*`.
9. **A-9** — The T020 Python module is a new test module under `tests/xcom/activation_plan/`; it does not edit
   `tests/test_xcom_plan.py` or the T017 Python test modules, and it does not change `pyproject.toml` or pytest
   configuration. The existing T018 traceability test that reconciles `tests/test_xcom_plan.py` with the T018
   verification plan is unaffected because T020 authors no test in that module.

## 10. Requirement index

| Requirement | Refines | Primary test units |
| --- | --- | --- |
| T020-STK-001 | — | T020-U-01, T020-U-05 |
| T020-STK-002 | — | T020-U-02 |
| T020-STK-003 | — | T020-U-03 |
| T020-STK-004 | — | T020-U-04 |
| T020-STK-005 | — | T020-U-05, T020-U-07, T020-U-08 |
| T020-SR-001 | STK-001 | T020-U-01, T020-U-05 |
| T020-SR-002 | STK-002 | T020-U-02 |
| T020-SR-003 | STK-003 | T020-U-03 |
| T020-SR-004 | STK-004 | T020-U-04 |
| T020-SR-005 | STK-001, STK-005 | T020-U-05 |
| T020-SR-006 | STK-005 | T020-U-06, T020-U-07 |
| T020-SR-007 | STK-005 | T020-U-08 |

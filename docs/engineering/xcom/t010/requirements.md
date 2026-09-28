# T010 Requirements — Unit Design, Ownership, Lifetime, Thread-Safety, Failure Semantics, Bounds, and Doxygen Plan

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T010 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `abb81681e0d844edaecbaf2843f1c2a7deb1e40f` |
| Predecessor task | T009 (architecture model, boundaries, diagrams, cross-language contracts; reviewed terminal package `abb8168`) |
| Successor tasks | T011 (dependency admission), then implementation slices T012–T034, integration/evidence T035–T040, and review/acceptance T039/T041 |
| Requirement ID families | `T010-STK-###` (stakeholder), `T010-SR-###` (software) |
| Authority | the T010 entry in `specs/007-xcom-core/tasks.md`; `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 1, "Complexity Tracking"; `specs/007-xcom-core/spec.md` FR-005, FR-007–FR-010, FR-012–FR-014, FR-017, FR-021, FR-025–FR-030, FR-032–FR-034 and SC-004/SC-005/SC-006/SC-009; `specs/007-xcom-core/data-model.md` state models and invariants 1–10; `specs/007-xcom-core/contracts/*.md`; Constitution 2.1.0 articles II, III, V, VI, VII, VIII, IX, X and the capability acceptance gates; ADR-0016, ADR-0018, ADR-0019, ADR-0020; ACC001–ACC015; `docs/engineering/xcom/task-ownership.{md,json}` (T007); `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` (T008); `docs/engineering/xcom/t009/{architecture,architecture-model}.{md,json}` (T009) |
| Classification | Public-safe engineering work product |

### 1.1 Authority statement

This document specifies only the bounded T010 slice. T010 **maintains the unit design of capability 007**:
one authoritative, machine-checkable record per design unit that declares ownership, lifetime,
thread-safety and concurrency behaviour, failure semantics, finite resource bounds, planned evidence, and
the public-interface Doxygen obligation. It elaborates the accepted architecture that T009 modelled
(`XCOM-CMP-*`, `XCOM-XB-*`, `XCOM-XLC-*`) and the accepted software requirements that T008 registered
(`XCOM-SW-*`). It does **not** redesign the accepted architecture, change an accepted functional requirement,
success criterion, ADR, contract, or ownership boundary, weaken an existing requirement or test, fix
production numeric bound values, author production or test source, or approve any other task.

T010 is a repository-owned work-product task. Its candidate may change documentation/governance artifacts and
add one offline validator script under `scripts/`, but the deterministic gate rejects any T010 change under
`src/`, `tests/`, or `xdl/` (T010-SR-012). The unit design T010 produces is the design authority the
implementation slices (T012–T034), T035–T038 (integration/evidence and Doxygen), and T039/T041
(review/acceptance) consume.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the accepted plan and
contracts, the constitution, an accepted ADR, the T007 ownership register, the T008 register/matrix, or the
T009 architecture model is resolved in favour of the accepted source. A material gap is reported rather than
guessed. Unresolved gaps are recorded in §9.

## 2. Scope

### 2.1 In scope (bounded T010)

Keep T010 strictly inside the T010 task entry: *"Maintain and review unit design, ownership, lifetime,
thread-safety, failure semantics, bounds, and Doxygen plan."*

1. **Maintain one authoritative unit design** as a canonical, schema-versioned model with an explicit closed
   vocabulary set and one uniquely identified, uniquely owned record per design unit, anchored to the
   accepted T009 component/contract catalogue and to real or explicitly planned product paths.
2. **Maintain the ownership and lifetime contract** of every unit: which component/slice/task owns it, which
   resource-ownership model applies, what its valid lifetime is, which exact issued handle may mutate or close
   it, and whether it exposes a borrowed view whose lifetime is bounded.
3. **Maintain the thread-safety and concurrency contract** of every unit: an explicit model from a closed
   vocabulary, the shared mutable state it owns or exposes, the synchronization mechanism that protects it,
   and the cross-thread/-process hand-off rule.
4. **Maintain finite resource bounds** for every unit: the bound kinds it declares (capacity, depth, quota,
   rate, bytes, deadline, timeout, retry, thread count), the exact numeric value where one is fixed by
   T010 (none), the source that configures the value, and the declared overflow/backpressure policy.
5. **Maintain explicit failure semantics** for every unit: classified outcome vocabulary, condition → outcome
   mapping, the rule that an unknown outcome is never reported as success, and the evidence-incomplete outcome
   for journaled or partially-written state.
6. **Maintain the Doxygen plan** for every public C/C++ interface: the admitted configuration, mandatory file
   block, mandatory public tags (ownership, lifetime, thread-safety, failure), group structure, coverage rule,
   warning-as-error gate, and the explicit known gaps with their owning task. T010 owns the plan; it does not
   claim the generated documentation exists.
7. **Preserve the accepted architecture, ADRs, dependency direction, domain neutrality, safety boundaries,
   REF-002 dispositions, ownership, and dependency order.**
8. **Provide a deterministic, public-safe, offline validator** with a controlled self-test over the declared
   negative cases, and re-run it plus the T007 ownership validator before the candidate is presented.
9. **Maintain consistency with the T007 ownership register** by declaring T010's new artifacts to the owning
   `T-ENABLER` slice and re-validating, without weakening the accepted register.

### 2.2 Explicit exclusions (must remain absent from the T010 candidate)

No production or test source is created or modified; no `src/`, `tests/`, or `xdl/` path is changed; no
`proto/` definition is authored (T030 owns the gateway `.proto`); no `Doxyfile`, CMake, or build file is
changed (T011/T037 own the strict configuration); no compilation, linking, runtime execution, benchmark, or
dependency retrieval occurs; no legacy repository is read or written; no external network peer, package
manager, or TCP listener is used; no accepted ADR, accepted requirement, accepted contract, other task's work
product, or existing test is rewritten or weakened; no production numeric bound value is fixed; no unit or
capability that the accepted plan does not sanction is invented; no other task is marked complete; no
software candidate is accepted or integrated; no SESN artifact is created, rewritten, or extended; no target
REF-002 SADS requirement is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T010 |
| --- | --- | --- |
| Compiler/build/`nlohmann/json`/gRPC/Protocol Buffers/static-analysis/sanitizer/Doxygen admission with versions, hashes, licenses, generated-code provenance | T011 | allocated; T010 declares the unit contracts and the Doxygen plan, not the admitted toolchain |
| `io.xverse.xcom` Profile, activation-plan v1 schema, Python plan compiler | T017–T018 | allocated; T010 designs the units and their failure/bounds contracts, and does not author the profile or schema |
| C++ activation-plan decoding | T019–T020 | allocated; T010 specifies the decode unit and its bounds/failure contract |
| Core, observation, stimulation, and gateway implementation and their tests | T012–T016, T021–T034 | allocated; T010 specifies units, ownership, lifetime, thread-safety, failure semantics, and bounds |
| Configured production bound values | implementation slices | allocated; T010 requires every bound to be finite and declared in the activation plan or unit configuration, and fixes no numeric value |
| Strict Doxygen C++ configuration and warning-free generation | T011 (admission), T037 (execution) | allocated; T010 declares the plan, the mandatory tags, and the current gap |
| Full verification, benchmarks, traceability validation, evidence bundle | T035–T038, T040 | allocated; T010 supplies the unit design they verify and extend |
| Independent read-only review and explicit user acceptance | T039, T041 | allocated; T010 does not accept, complete, or integrate any candidate |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths.** T010 changes documentation/governance and adds one offline validator. The plan
stage adds exactly the five work products
`docs/engineering/xcom/t010/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`.
The implementation stage adds `docs/engineering/xcom/t010/unit-design.json` (canonical model),
`docs/engineering/xcom/t010/design-units.md` (its deterministic projection; the `design_unit` locator that the
T008 matrix already declares as `XCOM-DU-INTG-BASELINE`), `scripts/validate_xcom_unit_design.py`, and
`docs/engineering/xcom/t010/implementation.md`, and updates the T010 checkbox in
`specs/007-xcom-core/tasks.md` and T010's new script path in `docs/engineering/xcom/task-ownership.{json,md}`.
The review and package stages add `docs/engineering/xcom/t010/internal-review.json` and
`reports/xcom-queue/t010-package.json`. The **affected product source paths are none**: no `src/`, `tests/`,
`xdl/`, or `proto/` path is created or changed (T010-SR-012). The product paths T010 *designs* are the
`artifact_paths` of the design units in `unit-specifications.md` §4–§10 and `detailed-design.md` §5.

**Negative cases.** T010-SR-001..014 each name the negative case(s) that must fail. The declared set is
`NEG-01`..`NEG-46` in `verification-plan.md` §4: schema/top-level defects (NEG-01, NEG-02), ordering and id
type defects (NEG-03, NEG-04, NEG-05), duplicate id (NEG-06), unknown vocabulary token (NEG-07, NEG-10,
NEG-11), missing mandatory field (NEG-08), no artifact path (NEG-09), ownership and lifetime defects
(NEG-12..NEG-16, NEG-20), thread-safety defects (NEG-17..NEG-19, plus the isolating NEG-18b/NEG-19b), bounds defects (NEG-21..NEG-24), failure-semantics
defects (NEG-25..NEG-27), Doxygen defects (NEG-28..NEG-30), governance defects (NEG-31..NEG-34), binding
defects (NEG-35..NEG-39), determinism (NEG-40), public safety (NEG-41), path status (NEG-42, NEG-43),
architecture/requirement coverage (NEG-44, NEG-45), and an invalid coverage exemption (NEG-46). Each fixture
isolates one check or one declared ordering/uniqueness/coverage rule.

**Concurrency and resource bounds.** T010 has no runtime concurrency of its own: the unit-design model is a
static document and the validator is offline and single-threaded. No concurrency case is defined for the T010
candidate. Applicable candidate bounds are input ≤ 1 MiB per file and ≤ 4 MiB total, no
network/subprocess/filesystem write, wall clock ≤ 60 s, and byte-stable deterministic output. The
**designed** units' concurrency and resource bounds are first-class T010 content: every unit declares a
thread-safety model, its shared state and synchronization, at least one finite resource bound, and a declared
overflow/backpressure policy (`unit-specifications.md` §4–§10, `verification-plan.md` §6).

## 3. Terminology and measurement

| Term | Meaning in T010 |
| --- | --- |
| Design unit | One owned implementation unit of capability 007 (C++ class/header unit, Python compiler unit, schema/derived artifact, boundary unit, fixture, documentation/evidence unit, or enabler work-product unit) with an explicit ownership, lifetime, thread-safety, failure, bounds, and Doxygen contract. |
| Family | Closed unit family: `CORE`, `XDL`, `OBS`, `STIM`, `GW`, `INTG`, `ENB`. |
| Unit kind | Closed kind: `data-plane`, `boundary`, `edge`, `build-time`, `derived-artifact`, `test-fixture`, `documentation`, `evidence`. |
| Ownership model | Closed rule describing which principal owns a unit's mutable resources: `caller-owns-value`, `platform-owns-shared`, `provider-issued-handle`, `session-issued-handle`, `gateway-issued-handle`, `task-owns-artifact`. |
| Lifetime model | Closed rule for the interval over which a unit's state or handle is valid: `static-immutable`, `process-scoped`, `plan-scoped`, `route-scoped`, `endpoint-generation`, `session-scoped`, `invocation-scoped`, `document-scoped`. |
| Thread-safety model | Closed rule for concurrent use: `immutable-value`, `read-only-static`, `single-thread-owner`, `externally-synchronized`, `internally-synchronized`, `message-passing`, `process-isolated`, `offline-single-threaded`. |
| Bound | A finite declared limit on one resource (capacity, depth, quota, rate, bytes, deadline, timeout, retry, thread count) with its configuring source and its overflow behaviour. |
| Overflow policy set | Declared behaviour when a bound is reached: `drop-oldest`, `drop-newest`, `coalesce`, `lossless-backpressure`, `reject`, `fail-closed`, or exactly `["n/a"]` for a unit with no capacity/quota/depth/rate bound. |
| Outcome | Classified result of an operation: `accepted`, `delivered`, `rejected`, `expired`, `cancelled`, `failed`, `unknown`, `evidence-incomplete`. |
| Doxygen obligation | The documented public-interface contract of a unit: file block plus mandatory `@brief` and the `@ownership`/`@lifetime`/`@thread_safety`/`@failure` aliases for every public declaration. |
| Maturity | Closed vocabulary `implemented`/`partial`/`allocated`/`deferred`/`superseded`/`conflicting`/`needs_clarification`. |
| First proof | The bounded capability-007 prototype scope: owned loopback providers, synthetic sink/tools, no legacy asset, no external peer, no TCP listener beyond the local-only tool gateway. |
| Deterministic serialization | A byte-stable canonical ordering that yields identical output across runs and hosts. |

Measurements are discrete and observable: unit counts per family and kind, ownership/lifetime/thread-safety
model counts, bound-kind coverage, declared-bounds-per-unit counts, Doxygen element-coverage and
tag-coverage counts, requirement/component coverage results, vocabulary-consistency results, validator exit
status, and byte-level model/projection contents. No availability, throughput, timing, or probability figure
is asserted; no production numeric bound is fixed; none is derivable from the accepted capability and none is
invented.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-001–FR-035, SC-001–SC-011, edge cases, key entities | the interaction, observation, stimulation, external-tool, failure, and documentation obligations per unit |
| Task entry | `specs/007-xcom-core/tasks.md` T010 and the dependency-order section | authorized bounded scope and successor ordering |
| Accepted plan | `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases", "Complexity Tracking" | the accepted unit decomposition, mixed-language boundary, dependency order, and the C++20/Python 3.11 language allocation |
| Data model | `specs/007-xcom-core/data-model.md` entities, state models, invariants 1–10 | per-unit ownership, lifetime, and failure semantics |
| Contracts | `specs/007-xcom-core/contracts/{communication-plan,xdl-profile,provider,observation,tool-gateway,validation-tool}.md` | per-unit contract obligations |
| Analysis | `specs/007-xcom-core/analysis.md` A09/A12 and the consistency checks | unreconciled-coverage and traceability state the design records without resolving |
| REF-002 traceability | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/sads-requirements-traceability.json` | the accepted dispositions T010 records without promotion |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles II, III, V, VI, VII, VIII, IX, X and the capability acceptance gates | domain neutrality, XDL centrality, dependency direction, hardware/lifetime, maturity, traceability, public safety |
| ADRs | ADR-0016, ADR-0018, ADR-0019, ADR-0020 | governing decisions the design cites |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC001–ACC015 | exact authorization references |
| Ownership register | `docs/engineering/xcom/task-ownership.{md,json}`, `scripts/validate_xcom_task_ownership.py` | slice/path ownership, baseline/authorization binding, reconciliation vocabulary |
| Requirement register/matrix | `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` | stable `XCOM-SW-*` requirement links and the `XCOM-DU-INTG-BASELINE` design-unit locator the T010 projection satisfies |
| Architecture model | `docs/engineering/xcom/t009/architecture-model.{json,md}` | the `XCOM-CMP-*`/`XCOM-XLC-*` component and contract identities every unit resolves to |
| Doxygen baseline | `Doxyfile`, `scripts/check_doxygen.py`, `docs/xcom/*.md` | the admitted documentation configuration, aliases (`ownership`, `lifetime`, `thread_safety`, `failure`, `unitspec`), and the current strictness gap |
| Baseline provenance | `git log`/`git rev-parse` for `src/xverse/xcom/**`, `tests/xcom/**`, `src/xverse_xdl/**`, `scripts/*.py`, `proto/**` | existing-artifact anchoring only; never acceptance proof |

## 5. Stakeholder requirements

### T010-STK-001 — One authoritative unit design with ownership and lifetime contracts

**Statement.** Capability 007 must have a single authoritative unit design in which every design unit is
uniquely identified, uniquely owned by an accepted slice/task, anchored to real or explicitly planned product
paths, and carries an explicit ownership model, a valid-lifetime model, and the rule that only the exact issued
handle may mutate or close the unit's resources.

**Acceptance criteria (observable).**

- AC-1: Exactly one record exists per design unit, with a unique id in the declared family and a non-empty
  mandatory field set.
- AC-2: Every unit names exactly one owning slice and a task set consistent with the T007 register, and at
  least one artifact path tagged `established` or `planned`.
- AC-3: Every unit declares an ownership model, a lifetime model, and — where it exposes a borrowed view —
  a bounded view lifetime.
- AC-4: No accepted T009 component or contract is left without a designing unit, and no unit is invented that
  the accepted plan does not sanction.

**Source anchors.** `tasks.md` T010; `plan.md` "Project Structure"; `data-model.md` entities and invariants
1/2; spec FR-005/FR-009/FR-010; Constitution art. V/VI; T009 architecture model; ACC012/ACC014.

### T010-STK-002 — Accepted architecture, ADR, and dependency governance preserved

**Statement.** T010 must preserve the accepted architecture, accepted ADRs, the one-way dependency direction
blueprints → domain profiles → XDL/platform APIs → runtime abstractions, and domain neutrality of the core,
changing no accepted decision and introducing no reverse dependency, domain primitive, or promoted REF-002
target.

**Acceptance criteria (observable).**

- AC-1: Every unit cites a governing ADR from the accepted set, and every unit's family/slice placement is
  consistent with the T009 model and the T007 register.
- AC-2: The model asserts the dependency-direction and core-neutrality rules; a reverse dependency or a
  domain-specific core primitive is rejected.
- AC-3: `ref002.disposition = "unchanged"` with an empty promoted set; no deferred/allocated target is
  reported as implemented.
- AC-4: No accepted ADR, requirement, contract, or existing test is rewritten or weakened.

**Source anchors.** ADR-0016/ADR-0018/ADR-0019/ADR-0020; Constitution arts. II, III, VII, VIII; spec
FR-001/FR-035; T009 `XCOM-INV-11`/`XCOM-INV-12`.

### T010-STK-003 — Exact baseline, authorization, and traceability binding

**Statement.** The unit design and every unit record must be bound to the exact baseline revision and to the
exact accepted authorizations that permit the work, and must resolve bidirectionally to the accepted
requirement register, the accepted architecture model, and the accepted contracts.

**Acceptance criteria (observable).**

- AC-1: The model records `baseline_revision = abb81681e0d844edaecbaf2843f1c2a7deb1e40f` and a
  candidate-revision rule.
- AC-2: Every `requirement_links` entry resolves in the T008 register; every `component_refs`/`contract_refs`
  entry resolves in the T009 model.
- AC-3: Only accepted authorization records (ACC001–ACC015, ADR-0016/0018/0019/0020) are cited.
- AC-4: A malformed baseline, an unknown authorization reference, a dangling requirement link, an unaccepted
  `FR-###`/`SC-###`/`US#` anchor, or an unavailable dependency fails closed.

**Source anchors.** ADR-0020 §Decision; ACC012/ACC014/ACC015; Constitution art. X; T008 register/matrix;
T009 model; `requirements.md` §9 A-4.

### T010-STK-004 — Explicit per-unit concurrency and finite resource bounds

**Statement.** Every design unit must declare an explicit thread-safety model, its shared mutable state and
the mechanism that protects it, and at least one finite resource bound with a declared overflow/backpressure
policy, so no unit is silently unbounded, unsynchronized, or dependent on hidden retry.

**Acceptance criteria (observable).**

- AC-1: Every unit declares a thread-safety model from the closed vocabulary with a rationale; a unit with
  non-empty shared mutable state uses an `internally-synchronized`/`externally-synchronized`/`message-passing`
  model, and a unit that owns no shared mutable state declares `synchronization = null`.
- AC-2: Every queue, quota, depth, rate, byte, and retry bound is finite and names its configuring source.
- AC-3: A queue/quota bound declares its overflow policy; a unit with no such bound declares `n/a`.
- AC-4: No unit silently retries, silently upgrades delivery, or declares an unbounded resource.

**Source anchors.** spec FR-007/FR-008/FR-013/FR-026; `plan.md` "Performance Goals"/"Constraints";
`data-model.md` invariant 5; `contracts/observation.md`; T009 `XCOM-INV-05`.

### T010-STK-005 — Explicit, observable, fail-closed failure semantics

**Statement.** Every design unit must declare its failure conditions and their classified outcomes, keep an
incomplete or unknown outcome explicit, and never report an unknown outcome as success, so activation,
delivery, observation, and stimulation failures remain bounded and observable.

**Acceptance criteria (observable).**

- AC-1: Every unit has a non-empty condition → outcome mapping using the closed outcome vocabulary.
- AC-2: Every unit with an asynchronous, journaled, or externally observable path maps `unknown` to a
  non-success outcome and declares `evidence-incomplete` where an outcome can be lost.
- AC-3: Configuration, authorization, and validation errors fail before emission or activation.
- AC-4: A unit that infers success for an unknown outcome fails validation.

**Source anchors.** spec "Failure semantics"; FR-006/FR-021/FR-025/FR-027; `contracts/validation-tool.md`;
T009 `XCOM-INV-07`/`XCOM-INV-08`; ACC011/ACC014.

### T010-STK-006 — Doxygen plan for every public C/C++ interface

**Statement.** Capability 007 must have a maintained Doxygen plan under which every public C/C++ interface of
every designed unit carries useful documentation of its ownership, lifetime, thread-safety, and failure
contract, the generated reference documentation is warning-free, and every known gap is explicit with an
owning task.

**Acceptance criteria (observable).**

- AC-1: The plan declares the admitted configuration, the mandatory file block, the mandatory public tags
  (including ownership/lifetime/thread-safety/failure), the group structure, the coverage rule, and the
  warning-as-error gate.
- AC-2: Every unit whose language is C++ declares a Doxygen obligation with a group, a file block, the
  mandatory public tags, and a declared public/documented element count.
- AC-3: Every non-C++ or documentation/evidence unit declares `doxygen.required = false` with a reason.
- AC-4: Every known gap (for example the current `WARN_IF_UNDOCUMENTED = NO` configuration and generated
  protobuf code) is recorded with its owning task, and no gap is reported as closed.

**Source anchors.** spec FR-029; SC-009; `plan.md` "Primary Dependencies"/"Testing"; `Doxyfile` aliases;
T009 requirement-link row FR-029; `docs/xcom/*.md`.

### T010-STK-007 — Public-safe, deterministic, reproducible, bounded work product

**Statement.** The unit-design model, its projection, and their validation must be deterministic and
public-safe: byte-stable across runs, free of credentials, private addresses, proprietary source excerpts,
sensitive deployment values, and absolute host paths, and reproducible offline with no network or subprocess.

**Acceptance criteria (observable).**

- AC-1: Serializing the same model twice yields byte-identical output; the stored `unit-design.json` bytes equal the canonical serialization (a non-canonical stored model is `DETERMINISM_INVALID`, 11); the Markdown projection matches.
- AC-2: The validator performs no network access and reads only repository-relative files.
- AC-3: A public-safety scan finds no credential, secret, private address, private-key marker, or absolute
  host path in the model, projection, or validator output.
- AC-4: Verification is bounded in file size and runtime.

**Source anchors.** spec FR-027; Constitution art. X; ADR-0020 §Decision; T009 `XCOM-INV-15` and T009-SR-012.

### T010-STK-008 — Review and acceptance remain separate; no other task completed

**Statement.** T010 must preserve the separate read-only review and explicit user acceptance gates and must
not accept, complete, or integrate any candidate, including its own or any other task's.

**Acceptance criteria (observable).**

- AC-1: T010 leaves the T010 and all other task checkboxes unchanged in the plan stage and marks only its own
  checkbox in the implementation stage.
- AC-2: T010 records no acceptance or integration claim for any candidate.
- AC-3: The review of T010's unit design is a separate read-only pass recorded in `internal-review.json`;
  external Codex review remains deferred until the `xcom-t007-t010-t017-t020` backlog completes.

**Source anchors.** ADR-0020 §Decision; ACC012/ACC015; `tasks.md` T039/T041; T008 `XCOM-SW-ENB-003`.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names below are fixed by
`detailed-design.md`; the requirements state their observable contract.

### 6.1 Unit-design model and structure

#### T010-SR-001 — Canonical unit-design model with deterministic serialization (refines T010-STK-007)

**Statement.** The unit design must exist as one canonical, schema-versioned JSON model with a fixed
top-level and per-record field set, stable ordering (`units` and `invariants` sorted by `id`, ids unique), a
recorded `schema_version`, a byte-stable serialization, and a deterministic Markdown projection.

**Acceptance criteria.** Declared top-level/per-record schemas implemented; every family entry `id` a
non-empty string; two serializations byte-identical; `counts` matches the entries; the projection equals the
model; both top-level arrays sorted by `id` with unique ids; nested arrays follow their declared ordering rule.

**Verification intent.** CHK-01, CHK-02, CHK-16, ORD-01; negative cases NEG-01..NEG-05 and NEG-40.

#### T010-SR-002 — Unit identity, family/task ownership, and artifact-path anchoring (refines T010-STK-001, T010-STK-003)

**Statement.** Every unit must carry a unique `XCOM-DU-###` id, a `family` and `kind` from the closed
vocabularies, a covering language, a `first-proof`/`later` scope, a T007 owning slice and task set, a maturity
from the closed vocabulary, and at least one repository-relative `artifact_path` tagged `established` or
`planned`; the model must reject a duplicate id, an unknown token, a missing mandatory field, the wrong id
pattern, or a unit with no artifact path.

**Acceptance criteria.** All unit ids unique and patterned; all family/kind/language/maturity tokens closed;
owning slice/task consistent with the T007 register; every unit has ≥ 1 artifact path; a duplicate id, unknown
token, missing field, or empty path set fails validation.

**Verification intent.** CHK-03, CHK-11, CHK-15; negative cases NEG-06..NEG-09.

#### T010-SR-003 — Ownership and lifetime contract per unit (refines T010-STK-001)

**Statement.** Every unit must declare an ownership model and rationale, a lifetime model and rationale, and,
when it exposes a borrowed view or payload view, a bounded `view_lifetime`; the model must reject a missing
ownership or lifetime model, a unit with no owning task/slice, a mutable unit with no exact-handle ownership
rule, and a declared owning slice that disagrees with the T007 register.

**Acceptance criteria.** Ownership/lifetime tokens closed and rationales non-empty; view lifetime declared
whenever a view is exposed; mutating units declare an issued-handle or platform-owned rule; ownership
disagreement with the T007 register fails validation.

**Verification intent.** CHK-04; negative cases NEG-12..NEG-16 and NEG-20.

#### T010-SR-004 — Thread-safety and concurrency contract per unit (refines T010-STK-004)

**Statement.** Every unit must declare a thread-safety model from the closed vocabulary with a rationale, the
shared mutable state it holds or exposes, and—where required—the synchronization mechanism or message-passing
boundary that protects it; the model must reject a missing model, an unknown model token, non-empty shared
mutable state declared with a non-synchronizing model (`immutable-value`, `read-only-static`,
`single-thread-owner`, `offline-single-threaded`, or `process-isolated`), a non-null `synchronization` on such a
model, an `internally-synchronized` model without a named synchronization
mechanism, and a `message-passing`/`process-isolated` claim inconsistent with the declared shared state or
capacity bound.

**Acceptance criteria.** Thread-safety model present and closed; rationale non-empty; shared-state and model
are mutually consistent; synchronization declared iff required; a contradictory or missing declaration fails
validation.

**Verification intent.** CHK-05; negative cases NEG-10, NEG-17..NEG-19, NEG-18b, NEG-19b.

#### T010-SR-005 — Finite resource bounds and overflow policy per unit (refines T010-STK-004)

**Statement.** Every unit must declare at least one finite resource bound with a bound kind from the closed
vocabulary, a configuring source, and—for capacity/quota/depth/rate bounds—a declared non-empty overflow policy
set from the closed vocabulary (and `["n/a"]` otherwise); a numeric value, when present, must be a
non-negative integer and any numeric value fixed by T010 must be absent; the model must reject a unit with no
bound, a `unbounded` kind, a negative or non-integer value, a capacity/quota/depth/rate bound without an
overflow policy set, and a bound whose configuring source is empty.

**Acceptance criteria.** Bound kinds closed and finite; at least one bound per unit; numeric values
non-negative and integral when present; overflow policy set declared exactly when a capacity/quota/depth/rate
bound exists and `["n/a"]` otherwise; a missing, unbounded, or negative bound fails validation.

**Verification intent.** CHK-06; negative cases NEG-21..NEG-24.

#### T010-SR-006 — Failure semantics and outcome honesty per unit (refines T010-STK-005)

**Statement.** Every unit must declare a non-empty condition → outcome mapping using the closed outcome
vocabulary, must map any unknown/indeterminate outcome to a non-success outcome, and must declare an
`evidence-incomplete` outcome for any unit that journals, writes durably, or reports an outcome asynchronously;
the model must reject missing failure semantics, an unknown outcome token, a unit that maps unknown to
success, and a journaled unit without an evidence-incomplete outcome.

**Acceptance criteria.** Outcome vocabulary closed; every unit maps at least one failure condition; `unknown`
never maps to `accepted`/`delivered`; journaled/write units declare `evidence-incomplete`; a violation fails
validation.

**Verification intent.** CHK-07; negative cases NEG-11, NEG-25..NEG-27.

### 6.2 Doxygen plan

#### T010-SR-007 — Doxygen plan and per-unit documentation obligation (refines T010-STK-006)

**Statement.** The model must declare the Doxygen plan (admitted configuration, warning-as-error gate,
mandatory file block, mandatory public tags including `@ownership`/`@lifetime`/`@thread_safety`/`@failure`,
group per family, coverage rule, and known gaps with owning tasks), and every C++ unit must declare a Doxygen
obligation whose group is one of the plan groups, whose file block and public tags include the mandatory sets,
and whose declared documented-element count equals its declared public-element count; the model must reject a
C++ unit missing a mandatory tag, a plan without the warning-as-error rule, an element-coverage mismatch, a
C++ unit with `doxygen.required = false`, and a non-C++ unit that claims a documentation obligation.

**Acceptance criteria.** Plan fields present and consistent; every C++ unit carries the mandatory tags and a
group from the plan; element counts consistent; non-C++ units declare `required = false` with a reason;
generated-code gaps declared with an owning task; a violation fails validation.

**Verification intent.** CHK-08; negative cases NEG-28..NEG-30.

### 6.3 Cross-resolution, coverage, and governance

#### T010-SR-008 — Unit↔architecture/contract cross-resolution and completeness (refines T010-STK-001, T010-STK-003)

**Statement.** Every unit's `component_refs` must resolve to declared T009 components and every
`contract_refs` to declared T009 contracts; every T009 component in the first-proof scope must be covered by
≥ 1 unit except for explicitly declared, reasoned exemptions; the required unit-id set must be exactly present;
and the model must reject an undeclared component/contract reference, an uncovered non-exempt component, and
an exemption for a component that is in fact covered.

**Acceptance criteria.** All refs resolve; the required unit set is exactly present; component coverage holds
with only declared exemptions; a dangling reference, uncovered component, or invalid exemption fails
validation.

**Verification intent.** CHK-09, CHK-10; negative cases NEG-44, NEG-46.

#### T010-SR-009 — Requirement-coverage completeness against the T008 register (refines T010-STK-003)

**Statement.** Every `requirement_links` entry must resolve to a T008 register requirement id, and every
`XCOM-SW-*` software requirement in the T008 register must be referenced by ≥ 1 unit except for explicitly
declared, reasoned exemptions; the model must reject a dangling link, an uncovered non-exempt software
requirement, and an exemption for a requirement that is in fact covered.

**Acceptance criteria.** All links resolve; software-requirement coverage is total modulo declared
exemptions; a dangling link or uncovered requirement fails validation with a distinct class.

**Verification intent.** CHK-10; negative cases NEG-37, NEG-39, NEG-45, NEG-46.

### 6.4 Governance, binding, boundary, and public safety

#### T010-SR-010 — Governance: ADR, REF-002 non-promotion, neutrality, and maturity honesty (refines T010-STK-002)

**Statement.** Every unit must cite a governing ADR from the accepted set; the model must record
`ref002.disposition = "unchanged"` with an empty promoted set; no deferred/allocated target may be reported as
implemented; `implemented` must require an exact accepted revision and unreconciled baseline coverage must be
`partial` with a reason; the dependency-direction and core-neutrality invariants must be present and enforced;
and the model must reject an unknown ADR, a promoted REF-002 target, an unproven `implemented`, a reverse
dependency, and a domain-specific primitive in a core unit.

**Acceptance criteria.** ADR references resolve; REF-002 promoted set empty; maturity/reconciliation honest
and consistent with the T007 register; neutrality/direction invariants enforced; a violation fails validation
with a distinct class.

**Verification intent.** CHK-11; negative cases NEG-31..NEG-34.

#### T010-SR-011 — Baseline, authorization, and fail-closed dependency checks (refines T010-STK-003, T010-STK-007)

**Statement.** The model must record the exact 40-hex baseline and a candidate-revision rule, cite only
accepted authorization records, tag every artifact path `established` or `planned`, and read the T007
ownership register, the T008 requirement register, and the T009 architecture model as required dependencies;
the validator must reject a non-40-hex baseline, an unknown authorization reference, an `established` path
absent from the tree, a `planned` path already present, and an unavailable or malformed dependency as a hard
failure rather than a skipped check.

**Acceptance criteria.** Baseline binds the run baseline; authorization records are a non-empty subset of the
accepted set; path status is consistent with the tree; an unavailable dependency yields a distinct nonzero
failure and never a passing result.

**Verification intent.** CHK-12, CHK-13, CHK-15; negative cases NEG-35, NEG-36, NEG-38, NEG-42, NEG-43.

#### T010-SR-012 — Work-product boundary for the T010 candidate (refines T010-STK-002)

**Statement.** The T010 candidate must change only work-product/governance documentation and add one
validator script under `scripts/`; it must not change, create, or delete any path under `src/`, `tests/`, or
`xdl/`, must not author a `proto/` definition, must not change `Doxyfile`/CMake/build files, and must not
modify an accepted ADR, accepted contract, or other task's work product, or weaken an existing requirement or
test.

**Acceptance criteria.** `git diff --name-only <baseline>` contains no `src/`, `tests/`, or `xdl/` path; no
accepted ADR or contract text is edited; `git diff --check` is clean; the T007 ownership validator still
passes.

**Verification intent.** CHK-18 and the deterministic gate in `verification-plan.md` §2.

#### T010-SR-013 — Public-safe unit-design model, projection, and validator output (refines T010-STK-007)

**Statement.** The unit-design model, its projection, and the validator output and retained evidence must
contain no credentials, secrets, private addresses, proprietary source excerpts, unrestricted payloads,
private-key markers, or absolute host paths. The documented deterministic-gate invocation path in
`verification-plan.md` §2 is workflow infrastructure, not model content, and is out of scope of this content
rule.

**Acceptance criteria.** A public-safety scan of the model, projection, and validator output finds none of the
prohibited classes; the scan is reproducible.

**Verification intent.** CHK-14; negative case NEG-41.

#### T010-SR-014 — Deterministic offline validator with self-test and ownership consistency (refines T010-STK-007, T010-STK-003)

**Statement.** A repository-owned validator must check the unit-design model against T010-SR-001..013,
provide a self-test over controlled positive and negative fixtures, be deterministic, offline, bounded, and
single-threaded, expose a distinct nonzero exit per failure class, and the T010 candidate must record its new
artifacts in the T007 ownership register and re-run that register's validator without weakening it.

**Acceptance criteria.** The validator passes the real model; its self-test exercises every declared negative
case; it performs no network access or subprocess; file/runtime bounds hold; `--check-human` confirms the
projection; the T007 ownership validator still exits 0 after the consistency update.

**Verification intent.** CHK-16, CHK-17, CHK-18, DET-01..DET-04, BND-01..BND-07 in `verification-plan.md`.

## 7. Capability 007 requirement links

| Capability anchor | T010 disposition and link | Remaining work |
| --- | --- | --- |
| FR-005 item identity, FR-007 bounded delivery, FR-008 no silent upgrade | **Implemented for this slice (design)**: units `XCOM-DU-001`–`008` declare item identity, bounded delivery, no hidden retry, and no delivery upgrade (T010-SR-003/004/005/006, `UDI-05`/`UDI-06`). | T013–T016 implement; T016/T035 verify. |
| FR-009/FR-010 explicit ownership, exact handles, idempotent lifecycle | **Implemented for this slice (design)**: `XCOM-DU-006`–`008` and `XCOM-DU-015`/`020` declare issued-handle ownership and generation-bound lifetimes (`UDI-02`). | T014/T015 implement; T033/T034 prove replaceability. |
| FR-011–FR-014 observation boundary, metadata-only, bounded queues, isolation | **Implemented for this slice (design)**: `XCOM-DU-012`/`013` declare metadata-only default, bounded observer queues, overflow policy, counters, and view lifetime (`UDI-09`). | T021–T024 implement; T032/T036 verify. |
| FR-015–FR-021 stimulation boundary, permit, provenance, guard, journal | **Implemented for this slice (design)**: `XCOM-DU-014`–`018` declare permit-bound session, journal-before-emission, fail-closed guard, synthetic provenance, and evidence-incomplete outcomes (`UDI-07`, `UDI-10`). | T025 (accepted) plus T026–T029 implement; T029 verifies. |
| FR-022/FR-023 provider-neutral tool contracts and normalized records | **Implemented for this slice (design)**: `XCOM-DU-012`/`019`–`021` declare the versioned tool API and normalized observation records. | T030–T034 implement; Argus consumption is a later capability. |
| FR-025/FR-026/FR-027/FR-028 stable diagnostics, no ambient dependency, public-safe, loopback-only | **Partial (constraint)**: `XCOM-DU-004` declares deterministic diagnostics; T010-SR-011/013 declare binding and public-safety rules. | Enforced at runtime by the slices and verified by T035/T038. |
| FR-029 Doxygen for every public C/C++ interface and changed unit | **Implemented for this slice (plan)**: the Doxygen plan `DOX-01` and per-unit obligations (T010-SR-007, `UDI-08`) cover every C++ unit; the plan declares the strictness gap and its owning task. | T011 admits the strict toolchain; T037 executes warning-free generation. |
| FR-030 traceability, evidence, separate review | **Partial (governance)**: T010-SR-008/009/014 bind units to requirements, components, contracts, and evidence; T010-STK-008 keeps review/acceptance separate. | T038 validates traceability; T039/T041 review and accept. |
| FR-032/FR-033/FR-034 local IPC gateway, time authority, service lease | **Implemented for this slice (design)**: `XCOM-DU-014`/`018`/`019`–`021` declare the time authority, exclusive lease, and local-IPC-only gateway units with no TCP listener (`UDI-13`). | T025 (accepted) plus T026–T034 implement and verify. |
| SC-004/SC-005/SC-006 bounded queues, observer isolation, synthetic provenance | **Partial (design)**: the bounds, thread-safety, and failure contracts assert these outcomes; no runtime claim is made. | Implementation and verification slices produce the measurements. |
| SC-009 traceability and warning-free Doxygen | **Partial (design/plan)**: every unit links requirements and declares its Doxygen obligation; the model/projection are machine-checked. | T037/T038 produce the documentation and traceability evidence. |
| Constitution arts. II, III, V, VI, VII, VIII, IX, X | **Implemented for this slice (design)**: T010-SR-010/011/012 and `UDI-11`/`UDI-12`/`UDI-13` declare neutrality, direction, maturity, and public-safety rules. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T010 is a unit-design/engineering-baseline task and implements **no** direct REF-002 communication
requirement XVE-SYS-0139–0158 and no shared requirement. It **records** `ref002_disposition = "unchanged"`
and promotes none. Every capability-007 disposition in `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` remains exactly as accepted.

| REF-002 group | Disposition in T010 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — no target is promoted; the model's promoted set is empty | T010 records unit-design structure only; it implements and demonstrates nothing. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may establish unit contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open items are the reconciliation of already-present source (§9 A-1)
and the strictness gap in the admitted Doxygen configuration (§9 A-3), both of which the model records rather
than resolves.

## 9. Assumptions and open items

1. **A-1 (open reconciliation)** — `src/xverse/xcom/**`, `tests/xcom/**`, `src/xverse_xdl/**`, and the
   `scripts/validate_xcom_*.py` validators contain SESN-era artifacts for T012–T016 and T021–T024, but those
   task checkboxes are open and no accepted exact-candidate revision is recorded (analysis A12). The units
   covering that source are recorded `partial` with an `unreconciled` reason; they are not relabelled, deleted,
   or extended.
2. **A-2** — The accepted T025 successor is merged at
   `4b01586b438a8587d231ee8828d896c206c06a96` (implementation
   `cc9044ab28d0ae9b4df8447072f68b73b3db184a`); the time-authority, permit/session, and lease units are bound
   to that accepted revision where their artifacts are the accepted ones.
3. **A-3 (Doxygen strictness gap)** — The admitted `Doxyfile` sets `WARN_AS_ERROR = YES` but
   `WARN_IF_UNDOCUMENTED = NO` and `WARN_NO_PARAMDOC = NO`, and `scripts/check_doxygen.py` currently covers
   Python docstrings plus generated output. The plan therefore records the strict C++ configuration
   (`WARN_IF_UNDOCUMENTED = YES`, `WARN_NO_PARAMDOC = YES`, C++-scoped inputs) as an **allocated** gap owned by
   T011 (admission) and T037 (execution); T010 claims no warning-free generation.
4. **A-4** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch, tag, or
   ambient state is a valid binding.
5. **A-5** — The deterministic gate for T010 is a work-product gate that runs no C++/Python test suite; the
   T010 verification is static validation of the unit-design model, its projection, and the work-product
   boundary (`verification-plan.md` §2).
6. **A-6** — Unit identifiers `XCOM-DU-001`–`030` and requirement identifiers are candidate-chosen names fixed
   by `detailed-design.md`; no accepted text is contradicted and no accepted component or contract is
   renumbered.
7. **A-7** — T010 fixes **no** production numeric bound value. Bound *kinds* and the finite-bound rule are
   design; the values come from the activation plan or unit configuration at runtime (FR-007).
8. **A-8** — The `docs/engineering/xcom/t010/design-units.md` projection satisfies the `design_unit` locator
   `XCOM-DU-INTG-BASELINE` that the T008 traceability matrix already declares; T010 realises that locator and
   does not edit any T008 artifact.
9. **A-9** — A unit whose only paths are `planned` is `allocated`; a unit whose baseline source exists but is
   unreconciled is `partial`; a unit bound to the accepted T025 revision is `implemented`. No unit is
   `implemented` on the basis of source presence alone.

## 10. Requirement index

| Requirement | Refines | Primary validator units |
| --- | --- | --- |
| T010-STK-001 | — | U-UNIT, U-COVER |
| T010-STK-002 | — | U-GOV, U-SAFE |
| T010-STK-003 | — | U-BIND, U-COVER |
| T010-STK-004 | — | U-THREAD, U-BOUND |
| T010-STK-005 | — | U-FAIL |
| T010-STK-006 | — | U-DOXY |
| T010-STK-007 | — | U-MODEL, U-SAFE, U-VALIDATE |
| T010-STK-008 | — | U-SAFE |
| T010-SR-001 | STK-007 | U-MODEL |
| T010-SR-002 | STK-001, STK-003 | U-UNIT |
| T010-SR-003 | STK-001 | U-UNIT |
| T010-SR-004 | STK-004 | U-THREAD |
| T010-SR-005 | STK-004 | U-BOUND |
| T010-SR-006 | STK-005 | U-FAIL |
| T010-SR-007 | STK-006 | U-DOXY |
| T010-SR-008 | STK-001, STK-003 | U-COVER |
| T010-SR-009 | STK-003 | U-COVER |
| T010-SR-010 | STK-002 | U-GOV |
| T010-SR-011 | STK-003, STK-007 | U-BIND |
| T010-SR-012 | STK-002 | U-SAFE |
| T010-SR-013 | STK-007 | U-SAFE |
| T010-SR-014 | STK-007, STK-003 | U-MODEL, U-VALIDATE |

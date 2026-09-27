# T019 Requirements — Bounded C++ Activation-Plan Decode with Independent Version/Digest/Capability Checks

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T019 (capability 007, phase 4 XDL-derived activation plan) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `199de0baa1f50e1d429527b6d6525a6e5d8cf7cf` |
| Predecessor tasks | T007–T010 (engineering-baseline enablers), T017 (Profile v0.1 / activation-plan v1 schema and digest contract), T018 (Python plan compiler; reviewed terminal package `199de0b`) |
| Successor tasks | T020 (ordering-equivalence, malformed-plan, drift, bound, and regression suites), then T035–T041 |
| Requirement ID families | `T019-STK-###` (stakeholder), `T019-SR-###` (software) |
| Authority | the T019 entry in `specs/007-xcom-core/tasks.md` ("Implement bounded C++ plan decoding and independent version/digest/capability checks"); `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4, "Complexity Tracking"; `specs/007-xcom-core/spec.md` FR-002, FR-006, FR-031, SC-002, failure semantics; `specs/007-xcom-core/contracts/{xdl-profile,communication-plan}.md`; `specs/007-xcom-core/data-model.md` invariants 1, 2, 7; `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-011`); `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-003`, `XCOM-CMP-004`, `XCOM-XLC-001`, `XCOM-XB-003`); `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` (`XCOM-SW-XDL-003`, `XCOM-SW-CORE-003`, `XCOM-DU-XDL-BASELINE`, `XCOM-T-XDL`); `docs/engineering/xcom/task-ownership.{md,json}` (`T-XDL` slice); `docs/engineering/xcom/t017/{detailed-design,unit-specifications,verification-plan}.md`; Constitution 2.1.0 articles II, III, VII, VIII, IX, X and the capability acceptance gates; ADR-0016, ADR-0018, ADR-0020; ACC002, ACC003, ACC013, ACC014, ACC015 |
| Classification | Public-safe engineering work product |
| Maturity | Plan/design target. `XCOM-DU-011` remains `allocated`; no T019 source is accepted, reviewed, or integrated by this document. |

### 1.1 Authority statement

This document specifies only the bounded T019 slice: a C++20, bounded, domain-neutral decoder for the
canonical activation-plan v1 artifact defined by T017 and produced by T018, with independent version, digest,
and capability/cross-reference checks that fail closed. It elaborates the accepted architecture
(`XCOM-CMP-003`, `XCOM-CMP-004`, `XCOM-XLC-001`, `XCOM-XB-003`) and the accepted software requirements
`XCOM-SW-XDL-003` and `XCOM-SW-CORE-003`.

It does **not** author the Python compiler (T018), author the ordering-equivalence, malformed-plan, drift,
bound, or regression suites (T020), activate or bind any endpoint/route/provider, implement observation,
stimulation, or a gateway, redesign the accepted architecture, change a functional requirement, success
criterion, ADR, schema, or contract statement, fix a production numeric bound value, create a competing
configuration language, add a new admitted dependency, accept or integrate any candidate, or approve any
other task.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the accepted plan and
contracts, the T017 schemas and digest/provenance contract, the constitution, an accepted ADR, the T007
ownership register, the T008 register/matrix, the T009 architecture model, or the T010 unit design is
resolved in favour of the accepted source. A material gap is reported rather than guessed. Unresolved gaps
are recorded in §9.

## 2. Scope

### 2.1 In scope (bounded T019)

Keep T019 strictly inside the T019 task entry: *"Implement bounded C++ plan decoding and independent
version/digest/capability checks."*

1. **Implement the bounded decoder unit** `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` and
   `src/xverse/xcom/src/activation_plan.cpp` in namespace `xverse::xcom::plan`, realising `XCOM-DU-011`
   (bounded activation-plan decode with independent version and digest checks that fails closed on malformed
   or drifted input).
2. **Ingest plan bytes under explicit bounds.** Parse the canonical activation-plan v1 JSON under finite
   byte, nesting-depth, and node bounds, and reject a repeated object member, malformed JSON, a non-object
   root, and any structural defect fail-closed. Parsing performs no filesystem, network, or subprocess
   access.
3. **Reproduce the T017 canonical serialization rule independently in C++**: object members ordered
   lexicographically by member name, no insignificant whitespace, every mathematically integral number in
   its single integer form, no non-finite numbers, arrays in their validated order, and no duplicate object
   members.
4. **Recompute the domain-separated SHA-256 digest independently.** The digested region is the plan value
   with the top-level `digest` member removed; the domain separator is the ASCII prefix
   `xverse.xcom.activation-plan.v1` followed by one `0x00` byte; the recorded digest is
   `{algorithm:"sha256", value:"<64 lowercase hex>"}`. The decoder recomputes the digest over the received
   body and rejects a mismatch. SHA-256 is implemented in-tree so the admitted dependency set is unchanged.
5. **Run independent version and capability/cross-reference checks** that fail closed: `planVersion` is
   exactly `"1"`; every provider's `requiredCapabilities` is a subset of its declared `capabilities`; every
   `routes[].contractId`, `routes[].from`, and `routes[].to` references a declared contract/endpoint; every
   `observationPoints[].routeId` references a declared route; `activationOrder` is a non-empty duplicate-free
   sequence of declared endpoint or route identifiers; and a plan that declares `status = "activatable"`
   carries six `"resolved"` input-resolution states.
6. **Validate the closed shape and vocabularies** of the plan: exactly the sixteen required top-level
   members, no unknown member at any object, the closed `status`/`role`/`ordering`/`reliability`/`overflow`/
   `backpressure`/`payloadAccess`/`validityEffect`/`clockDomain.source`/`severity`/input-state enums, the
   declared identifier/version/digest patterns, and the declared collection ordering and uniqueness rules.
7. **Produce a bounded, immutable decoded model** (`caller-owns-value`, `plan-scoped`, `immutable-value`)
   with an explicit outcome classification (`accepted`/`rejected`/`failed`), a stable diagnostic code, and an
   affected identifier or the fixed `xcom-plan` target; a rejected or failed decode returns **no** decoded
   plan.
8. **Add decoder unit and negative tests** under the `T-XDL` shared test path `tests/xcom/activation_plan/`,
   registered as CTest targets, that prove the positive decode of the committed T017 plan fixtures, the
   independent digest agreement, the version/capability/cross-reference checks, the canonicalization rule,
   the bound behaviour, the immutable value contract, and the declared negative set, without weakening or
   editing any existing test.
9. **Preserve the accepted architecture, ADRs, dependency direction, domain neutrality, safety boundaries,
   REF-002 dispositions, ownership, and dependency order**, and record the T019 candidate's changed paths,
   baseline, and evidence in its work products.

### 2.2 Explicit exclusions (must remain absent from the T019 candidate)

No Python module is authored or changed (`src/xverse_xdl/**` is T018); no ordering-equivalence,
malformed-plan, drift, bound-matrix, or regression suite file or target is authored (T020); no activation,
endpoint/route/provider binding, observation, stimulation, permit/session, journal, or gateway unit is
implemented; no `proto/` file, `Doxyfile`, T017 artifact, T018 artifact, or other task's work product is
rewritten or weakened; no schema or digest/provenance contract is changed; no authored YAML/JSON is
re-parsed and no second configuration language or competing topology is invented; no XDL normalization or
reference-resolution logic is duplicated; no new admitted dependency is introduced (the decoder uses only
the C++20 standard library and the already-admitted `nlohmann/json` 3.10.5 header); no legacy repository is
read or written; no external network peer, TCP listener, package manager, or production workload is used;
no accepted requirement, schema, contract, or existing test is weakened; no production numeric bound value
is fixed; no other task is marked complete; no software candidate is accepted or integrated; no REF-002
target is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T019 |
| --- | --- | --- |
| Ordering-equivalence, malformed-plan, drift, bound, and regression suites | T020 | allocated; T019 supplies decoder unit/negative tests only |
| Endpoint/route/provider activation and binding from a decoded plan | T-CORE (`XCOM-CMP-004` consumers) | allocated; T019 returns an immutable value and binds nothing |
| Observation, stimulation, permit/session, journal, gateway | T-OBS / T-STIM / T-CORE | allocated; outside the T019 boundary |
| Compiler/build/dependency admission with hashes, licenses, and generated-code provenance | T011 | allocated; T019 adds no dependency and runs in the admitted offline build environment |
| Warning-free Doxygen generation and full traceability/public-safety validation | T037, T038 | allocated; T019 supplies header Doxygen blocks and its unit evidence |
| Full evidence bundle, independent review, explicit user acceptance | T035–T041 | allocated; T019 does not accept, complete, or integrate any candidate |
| Configured production bound values | implementation slices | allocated; T019 enforces finite declared decode bounds and fixes no production numeric value |

### 2.4 Affected paths, negative cases, and bounds

**Affected source paths (T019-owned, from the `T-XDL` slice exclusive list).** The plan stage adds exactly
`docs/engineering/xcom/t019/{requirements,architecture,detailed-design,unit-specifications,verification-plan}.md`.
The implementation stage adds `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp`,
`src/xverse/xcom/src/activation_plan.cpp`, the decoder test sources under `tests/xcom/activation_plan/`, and
`docs/engineering/xcom/t019/implementation.md`; it edits the **shared** build path
`src/xverse/xcom/CMakeLists.txt` (new static library and CTest targets) and the **shared** capability path
`specs/007-xcom-core/tasks.md` (T019 checkbox line only). The review and package stages add
`docs/engineering/xcom/t019/internal-review.json` and `reports/xcom-queue/t019-package.json`.

The implementation stage may additionally edit the **shared** dependency-admission path
`cmake/XComOfflineDependencies.cmake` only if the deterministic gate's `cmake` configure cannot otherwise
read the already-admitted offline inputs, and only to (a) accept an explicit, previously admitted CMake
cache value for `XVERSE_XCOM_TOOLCHAIN`/`XVERSE_XCOM_PACKAGE_MANIFEST` without changing the hash-verified
preflight, and (b) when the environment does not already provide it, prepend the **named admitted prefix's**
own library directory (`<XVERSE_XCOM_TOOLCHAIN>/usr/lib/x86_64-linux-gnu`) to `LD_LIBRARY_PATH` so the
preflight's locked-version executable probe can load the prefix's shared objects. Allowance (b) derives
only from the explicit admitted prefix, adds no ambient path, is applied only when the directory is absent,
and does not change the hash-verified preflight (see `verification-plan.md` §2.4 A-1). Any such change is
recorded in `implementation.md` and weakens no admission check.

No file under `src/xverse_xdl/`, `proto/`, or `xdl/` is changed. No T017 artifact
(`xdl/profiles/xcom-v0.1.schema.json`, `src/xverse/xcom/contracts/v1/activation-plan.schema.json`,
`scripts/validate_xcom_plan.py`, `specs/007-xcom-core/contracts/xdl-profile.md`,
`docs/engineering/xcom/t017/**`) and no T018 artifact (`src/xverse_xdl/xcom_plan.py`,
`tests/test_xcom_plan.py`, `docs/engineering/xcom/t018/**`) is changed. The committed T017 plan fixtures
under `tests/xcom/activation_plan/fixtures/plan/valid/` are read read-only by the decoder tests and are not
modified.

**Negative cases.** The declared negative set is `NEG-D01`..`NEG-D22` (input, shape, version, digest,
capability, cross-reference, status, and bound defects) plus `NEG-G01`..`NEG-G05` (boundary/governance
defects) in `verification-plan.md` §4. Each case injects one controlled defect into a bounded,
repository-owned, public-safe synthetic plan or a mutation of a committed fixture and asserts the declared
outcome (`rejected`/`failed` code) with no partial decoded plan and no success claim. These identifiers are
T019-scoped and are distinct from any same-named identifier in the T017 or T018 work products.

**Public safety.** The decoder source, tests, and retained evidence must contain no credentials, secrets,
private addresses, proprietary excerpts, unrestricted payloads, or absolute host paths. Any plan input and
fixture is repository-owned, public-safe, and synthetic. The deterministic gate is operationally invoked by
the Workflow harness; the retained work products reference it by the repository-relative locator
`automation/xcom_feature_gate.py` and never embed a host-specific absolute path, so the public-safe artifact
set satisfies this rule without an exemption.

**Concurrency and resource bounds.** T019 has no mutable shared state: the decoder is a pure
`offline-single-threaded`/pure-function unit, the decoded plan is an immutable value after decode
(`immutable-value`, no synchronization), and a decoded plan may be shared read-only without a lock. Applicable
bounds are plan bytes ≤ 5 MiB (aligned with the T017 `MAX_DOCUMENT_BYTES` and the T018 `max_bytes`), nesting
depth ≤ 100, node count ≤ 100 000, bounded string lengths, and finite decoded-entity caps for contracts,
endpoints, routes, providers, observation points, clock domains, diagnostics, activation order, and
provenance resources; overflow policy `fail-closed`. The decoder performs no network, subprocess, or
filesystem access. T019 fixes **no** production numeric bound value; runtime bounds come from the activation
plan or unit configuration (FR-007).

## 3. Terminology and measurement

| Term | Meaning in T019 |
| --- | --- |
| Canonical activation plan | The T017 activation-plan v1 JSON value; the only interface between the Python compiler (T018) and this C++ decoder. |
| Decoder | The pure `xverse::xcom::plan` function set that ingests bounded plan bytes and returns a decoded immutable value or a classified outcome. |
| Bounded decode | Parse and validate within finite byte, depth, node, string, and entity bounds; a breach is `failed` (fail closed), never a partial result. |
| Independent check | A verification the decoder recomputes itself from the received bytes rather than trusting a recorded value: the canonical digest, the plan version, and the capability/cross-reference closure. |
| Canonical bytes | The UTF-8 encoding with member-name order, no insignificant whitespace, single integral-number form, and no duplicate members (T017 rule reproduced in C++). |
| Digested region | The plan value with the top-level `digest` member removed; the digest is never computed over itself. |
| Duplicate member | A repeated object member name in the received JSON; rejected fail-closed rather than collapsed last-wins. |
| Outcome | Closed vocabulary `accepted`, `rejected`, `failed`. |
| Status | The plan's own closed vocabulary `inspectable`, `activatable`; not the decoder outcome. |
| Maturity | Closed vocabulary `implemented`/`partial`/`allocated`/`deferred`/`superseded`/`conflicting`/`needs_clarification`. |
| First proof | The bounded capability-007 prototype scope: owned synthetic fixtures, no legacy asset, no external peer, no TCP listener. |

Measurements are discrete and observable: the decode outcome and stable code; the recomputed versus recorded
digest; byte-level canonical output; whether a decoded value or no value is returned; per-family and
per-collection validity results; and bound-rejection results. No availability, throughput, timing, or
probability figure is asserted.

## 4. Admitted inputs

| Input | Reference | Use |
| --- | --- | --- |
| Capability specification | `specs/007-xcom-core/spec.md` FR-002, FR-006, FR-031, SC-002, failure semantics, key entities | the digest-bound, fail-before-activation obligation and the no-competing-language rule |
| Task entry | `specs/007-xcom-core/tasks.md` T019 and the dependency-order section | authorized bounded scope and successor ordering |
| Accepted plan | `specs/007-xcom-core/plan.md` "Technical Context", "Project Structure", "Delivery phases" 4 | the decoder placement and bounded-decode boundary |
| Profile contract | `specs/007-xcom-core/contracts/xdl-profile.md` "Profile v0.1 payload grammar", "Activation-plan v1 digest and provenance" | the canonical serialization, domain separator, digested region, digest form, and fail-closed rules the decoder reproduces |
| Plan contract | `specs/007-xcom-core/contracts/communication-plan.md` | required plan content, unknown-fields-fail-closed, inspectable-vs-activatable, and independent decode/verify before activation |
| Data model | `specs/007-xcom-core/data-model.md` invariants 1, 2, 7 | logical/physical separation, exact-handle ownership, plan-digest binding |
| Plan schema | `src/xverse/xcom/contracts/v1/activation-plan.schema.json` | the closed member set, vocabularies, patterns, conditional status rule, and collection keys |
| T017 design/evidence | `docs/engineering/xcom/t017/{detailed-design,verification-plan}.md` §5/§9; `scripts/validate_xcom_plan.py` (`canonical_bytes`, `compute_digest`, `check_digest`) | the fixed canonicalization/digest rules and the reference recomputation the C++ decoder must agree with |
| T017 fixtures | `tests/xcom/activation_plan/fixtures/plan/valid/plan-activatable.json`, `plan-inspectable.json` | bounded positive inputs read read-only by the decoder tests |
| Unit design | `docs/engineering/xcom/t010/design-units.md` (`XCOM-DU-011`) | ownership, lifetime, thread-safety, bounds, and failure semantics |
| Architecture model | `docs/engineering/xcom/t009/architecture-model.{json,md}` (`XCOM-CMP-003`, `XCOM-CMP-004`, `XCOM-XLC-001`, `XCOM-XB-003`) | component/boundary identities and the one-way dependency rule |
| Requirement register/matrix | `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` | `XCOM-SW-XDL-003`, `XCOM-SW-CORE-003`, and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators |
| Ownership register | `docs/engineering/xcom/task-ownership.{md,json}`, `scripts/validate_xcom_task_ownership.py` | slice/path ownership, baseline/authorization binding |
| Build environment | `docs/engineering/xcom/{build-environment,dependency-lock}.md`, `docs/engineering/xcom/t025/test-dependency-admission.md`, `cmake/XComOfflineDependencies.cmake` | the admitted offline inputs and GTest test prefix the decoder build and tests require |
| REF-002 traceability | `specs/007-xcom-core/reference-traceability.md`, `docs/architecture/sads-requirements-traceability.json` | the accepted dispositions T019 records without promotion |
| Constitution | `.specify/memory/constitution.md` 2.1.0, articles II, III, VII, VIII, IX, X and the capability acceptance gates | domain neutrality, XDL centrality, platform-first, direction, maturity, traceability |
| ADRs | ADR-0016, ADR-0018, ADR-0020 | governing decisions the design cites |
| Acceptance records | `specs/007-xcom-core/checklists/acceptance.md` ACC002/ACC003/ACC013/ACC014/ACC015 | exact authorization references |
| Baseline provenance | `git rev-parse 199de0baa1f50e1d429527b6d6525a6e5d8cf7cf`, `git log` for `src/xverse/xcom/**`, `tests/xcom/**`, `src/xverse_xdl/**`, `xdl/**` | existing-artifact anchoring only; never acceptance proof |

## 5. Stakeholder requirements

### T019-STK-001 — Bounded, fail-closed C++ decode of the canonical plan

**Statement.** Capability 007 must decode the canonical activation-plan v1 artifact produced by the accepted
compiler into an immutable C++ value under finite byte, nesting, node, string, and entity bounds, using only
declared plan data and introducing no competing configuration language, and must fail closed with a
classified outcome and no partial value on malformed, out-of-shape, or over-bound input.

**Acceptance criteria (observable).**

- AC-1: `src/xverse/xcom/include/xverse/xcom/activation_plan.hpp` exposes a bounded decode entry point; a
  committed positive plan fixture decodes to `accepted` with an immutable value.
- AC-2: Every decoded member is read from a declared plan member; no identity, version, capability, address,
  permit, handle, or session is synthesized or defaulted.
- AC-3: Malformed JSON, a duplicate member, a non-object root, an unknown member, a missing required member,
  a vocabulary/pattern violation, or an out-of-order/duplicate collection is `rejected`; a byte, depth, node,
  string, or entity bound breach is `failed`; neither returns a decoded value.

**Source anchors.** `contracts/communication-plan.md`; spec FR-002; `data-model.md` invariants 1, 7; T010
`XCOM-DU-011`; `XCOM-XLC-001`, `XCOM-XB-003`.

### T019-STK-002 — Independent version and digest verification

**Statement.** The decoder must verify the plan independently of the recorded values: `planVersion` is
exactly `"1"`; the digest algorithm is `sha256` with a 64-lowercase-hex value; and the decoder must reproduce
the T017 canonical serialization rule and recompute the domain-separated SHA-256 over the digested region,
rejecting a mismatch rather than trusting the recorded digest.

**Acceptance criteria (observable).**

- AC-1: The decoder's canonicalization and recomputed digest agree with the T017 reference
  (`scripts/validate_xcom_plan.py` `canonical_bytes`/`compute_digest`) for every committed positive fixture.
- AC-2: A tampered body, a digest computed over a non-canonical serialization, a non-`sha256` algorithm, or a
  malformed digest value is `rejected` with a stable code.
- AC-3: Canonical bytes are member-name-ordered, whitespace-free, integral-number-normalized, and
  duplicate-member-free, so a reordered, respaced, or integral-number-variant representation of one body
  yields one digest.

**Source anchors.** `contracts/communication-plan.md`; `contracts/xdl-profile.md` "Activation-plan v1 digest
and provenance"; spec SC-002; `data-model.md` invariant 7; T017 `detailed-design.md` §5; T010 `XCOM-DU-011`.

### T019-STK-003 — Independent capability and cross-reference verification

**Statement.** The decoder must independently verify the plan's declared capability and reference closure
before the plan may be treated as activatable: every provider's required capabilities must be a subset of its
declared capabilities, every route/observation/activation-order reference must resolve to a declared
identity, and a plan that claims `status = "activatable"` must carry six resolved input-resolution states.
Closure is enforced against the plan's declared resolution states: a plan that records the governing
capability/schema/identity state `unresolved` declares an incomplete closure and is accepted as inspectable
but non-activatable, so the accepted T018 producer's route-with-no-provider artifact remains decodable.

**Acceptance criteria (observable).**

- AC-1: A plan declaring `capability: resolved` whose provider requires an undeclared capability, or which
  declares routes but selects no provider, is `rejected` with a capability code and the affected `providerId`
  or `xcom-plan` target.
- AC-2: A plan declaring its `schema`/`identity` state `resolved` but containing an unresolved
  route/contract/endpoint/observation/activation-order reference is `rejected` with a reference code and the
  affected identifier.
- AC-3: A plan that declares `activatable` while any input-resolution member is `unresolved` is `rejected`; a
  well-formed `inspectable` plan with an explicit unresolved member — including the accepted T018 producer's
  route-with-no-provider shape and an unresolved schema/identity reference — is `accepted` and remains
  non-activatable.

**Source anchors.** spec FR-006, failure semantics; `contracts/communication-plan.md`; plan schema
conditional rule; T010 `XCOM-DU-011` failure semantics; `XCOM-SW-XDL-003`, `XCOM-SW-CORE-003`.

### T019-STK-004 — Deterministic outcome, bounded resources, and immutable decoded value

**Statement.** The decoder must classify every input into the closed outcome set with a stable diagnostic
code and deterministic ordering, must bound every resource it allocates, and must return an immutable decoded
value that the caller owns and may share read-only without synchronization.

**Acceptance criteria (observable).**

- AC-1: Decoding the same input twice, or two representations of one canonical body, yields the same outcome,
  code, and (when accepted) equal decoded values.
- AC-2: Every declared bound is finite and positive; a value below the minimum is rejected at construction;
  an over-bound input is `failed` before any value is returned.
- AC-3: The decoded value exposes no mutation surface; it is copyable/movable and readable concurrently
  without a lock; no global mutable state is retained between calls.

**Source anchors.** T010 `XCOM-DU-011` ownership/lifetime/thread-safety/bounds; spec FR-007 (partial);
`data-model.md` invariant 7.

### T019-STK-005 — Accepted intent, governance, and dependency order preserved

**Statement.** T019 must preserve the accepted architecture, accepted ADRs, REF-002 dispositions, safety
boundaries, failure semantics, one-way dependency direction, domain neutrality, ownership, and dependency
order; must not implement T018/T020 or any later task; must not weaken an existing requirement, schema,
contract, or test; and must not mark the task complete in the plan stage or claim acceptance/review.

**Acceptance criteria (observable).**

- AC-1: The candidate changes only the T019-owned and declared shared paths of §2.4; no `src/xverse_xdl/**`,
  `proto/**`, `xdl/**`, `Doxyfile`, T017 artifact, or T018 artifact is changed.
- AC-2: The decoder depends only on the C++20 standard library and the already-admitted `nlohmann/json`
  header; it imports no Python module, no legacy artifact, and adds no admitted dependency.
- AC-3: `ref002.disposition = "unchanged"` with an empty promoted set; no deferred/allocated target is
  reported as implemented.
- AC-4: The T019 checkbox is left unchecked in the plan stage and marked only in the implementation stage; no
  acceptance, review, or integration claim is recorded; the T007 ownership validator still passes.

**Source anchors.** ADR-0018/ADR-0020; ACC014/ACC015; Constitution arts. II, III, VII, VIII, IX, X; T007
register; `tasks.md` T039/T041.

## 6. Software requirements

Each software requirement refines one or more stakeholder requirements. Identifier names of the design
artifacts and units are fixed by `detailed-design.md` and `unit-specifications.md`.

### 6.1 Ingestion, shape, and version

#### T019-SR-001 — Bounded strict JSON ingestion (refines T019-STK-001, T019-STK-004)

**Statement.** The decoder must parse plan bytes under finite byte, nesting-depth, and node bounds; reject a
repeated object member, malformed JSON, a non-object root, a non-finite or out-of-range number, and an
over-bound input; and return no partial document on error, without any filesystem, network, or subprocess
access.

**Acceptance criteria.** A valid plan parses; an over-byte/over-depth/over-node document is `failed`
(`XCOM-DECODE-BOUND`); a repeated member or malformed/non-object document is `rejected`
(`XCOM-DECODE-INPUT`); no partial document is returned on error.

**Verification intent.** CHK-07; NEG-D01..NEG-D03, NEG-D19, NEG-D21, BND-01, BND-02, BND-04.

#### T019-SR-002 — Closed shape, required members, vocabularies, identifiers, order (refines T019-STK-001)

**Statement.** The decoder must require exactly the sixteen declared top-level members, reject any unknown
member at any object, enforce the closed vocabularies (`status`, endpoint `role`, `ordering`, `reliability`,
`overflow`, `backpressure`, `payloadAccess`, `validityEffect`, `clockDomain.source`, `severity`, and the six
input-resolution states), enforce the declared identifier/version/digest patterns (the closed `digest`
sub-schema applies to every embedded digest — the top-level `digest`, `provenance.graphDigest`, and each
`provenance.resources[].sourceDigest`) and integer ranges, and enforce per-collection ordering by the declared
key with unique keys and a duplicate-free `activationOrder`.

**Acceptance criteria.** A schema-conformant plan is accepted; a missing/unknown member, a vocabulary or
pattern violation (including an embedded `graphDigest`/`sourceDigest` algorithm or value-pattern violation), a
non-integer integer field, an out-of-order or duplicate-keyed collection, or an empty `activationOrder` is
`rejected` (`XCOM-DECODE-SHAPE`); the decoder's declared member/enum tables agree with the committed plan
schema (drift guard).

**Verification intent.** CHK-06; NEG-D04..NEG-D08, NEG-D17, NEG-D18, CHK-10.

#### T019-SR-003 — Independent canonicalization, SHA-256, and digest verification (refines T019-STK-002)

**Statement.** The decoder must reproduce the T017 canonical serialization rule (member-name order, no
insignificant whitespace, single integral-number form, no non-finite numbers, no duplicate members, arrays
in validated order), remove the top-level `digest` member to form the digested region, and recompute the
SHA-256 over `xverse.xcom.activation-plan.v1` + `0x00` + canonical body bytes; it must verify `planVersion`
is `"1"`, the recorded algorithm is `sha256`, the recorded value is 64 lowercase hex, and the recorded value
equals the recomputed value.

**Acceptance criteria.** The recomputed digest equals the T017 reference digest for both committed fixtures;
a version, algorithm, hex, or recomputed-value mismatch is `rejected` (`XCOM-DECODE-VERSION`/
`XCOM-DECODE-DIGEST`); the canonical bytes are stable under member reordering, whitespace variation, and
integral-number representation; the digest is never computed over itself.

**Verification intent.** CHK-02, CHK-04, CHK-08; NEG-D09..NEG-D12, NEG-D22, DET-01..DET-04.

#### T019-SR-004 — Independent capability and cross-reference verification (refines T019-STK-003)

**Statement.** The decoder must independently verify the plan's declared capability and reference closure,
treating the plan's own `inputResolution` states as the authority: it must reject a plan that declares
`capability: resolved` while a route is declared but no provider is selected or a provider's
`requiredCapabilities` is not a subset of its declared `capabilities`; reject a plan that declares its
`schema`/`identity` state `resolved` while any `routes[]` `from`/`to`/`contractId`, `observationPoints[].routeId`,
or `activationOrder` identifier does not resolve to a declared identity/contract/route; and reject
`status = "activatable"` while any input-resolution state is `unresolved`. A plan that honestly records a
state `unresolved` (the accepted T018 producer's inspectable shape) is accepted as non-activatable.

**Acceptance criteria.** Each defect is `rejected` with `XCOM-DECODE-CAPABILITY`/`XCOM-DECODE-REFERENCE`/
`XCOM-DECODE-UNRESOLVED` and the affected identifier; a schema-valid `inspectable` plan is `accepted`,
including one that records an unresolved capability or schema/identity reference; an `activatable` plan with
all six states `resolved` is `accepted`.

**Verification intent.** CHK-05; NEG-D13..NEG-D16.

#### T019-SR-005 — Bounded immutable decoded model (refines T019-STK-001, T019-STK-004)

**Statement.** The decoder must produce a bounded, immutable C++ value in namespace `xverse::xcom::plan`
carrying the decoded plan members (version, generator, provenance, contracts, endpoints, routes, providers,
policies, observation points, stimulation, clock domains, activation order, diagnostics, status, and input
resolution) with every string bounded and every collection capped, owned by the caller and shareable
read-only without synchronization, and it must apply the finite entity caps after decode and fail closed
before returning a value.

**Acceptance criteria.** A positive plan decodes to a value whose members equal the fixture; an entity-cap
breach is `failed` (`XCOM-DECODE-BOUND`) with no value; the value is copyable/movable, exposes no mutation
surface, and has no internal synchronization or global state.

**Verification intent.** CHK-03, CHK-07, CHK-10; NEG-D20, BND-03.

#### T019-SR-006 — Deterministic outcome classification and diagnostics (refines T019-STK-004)

**Statement.** The decoder must classify every input into `accepted`/`rejected`/`failed`, return for a
non-accepted input a stable code from the closed decode-code vocabulary plus an affected identifier or the
fixed `xcom-plan` target, with no partial value, and produce byte-identical results for the same input across
repeated and reordered-but-equivalent decodes.

**Acceptance criteria.** Each defect family maps deterministically to its declared code and outcome; a
`rejected`/`failed` result carries no decoded value; repeated and reordered-but-equivalent decodes yield
identical results.

**Verification intent.** CHK-04, CHK-06, CHK-08; DET-01, DET-02; every `NEG-D*` case.

### 6.2 Tests, governance, and binding

#### T019-SR-007 — Decoder unit/negative tests and CMake/CTest integration (refines T019-STK-001..T019-STK-004)

**Statement.** The decoder test sources under `tests/xcom/activation_plan/` must exercise the positive decode
of the committed T017 fixtures, the independent digest agreement and SHA-256 known answers, the
canonicalization invariance, the version/capability/cross-reference checks, the bound behaviour, the
immutable value contract, and every declared `NEG-D*` case; the decoder library and its tests must be
registered as CMake/CTest targets under `src/xverse/xcom/CMakeLists.txt` and discovered and executed by the
deterministic gate, without editing or weakening the existing T017 Python tests or any existing test.

**Acceptance criteria.** Tests exist for each family; every `NEG-D*` case is asserted with its declared code
and no partial value; `ctest -N` discovers the decoder tests and `ctest` passes them together with the
existing suites; the T017 Python suite is unchanged.

**Verification intent.** CHK-01..CHK-11; `ctest` gate.

#### T019-SR-008 — Boundary, dependency, and REF-002 non-promotion (refines T019-STK-005)

**Statement.** The T019 candidate must change only the T019-owned and declared shared paths of §2.4, must bind
to baseline `199de0baa1f50e1d429527b6d6525a6e5d8cf7cf`, must cite only accepted authorizations, must link
`XCOM-SW-XDL-003`/`XCOM-SW-CORE-003` and the `XCOM-DU-XDL-BASELINE`/`XCOM-T-XDL` locators, must add no admitted
dependency and no Python/legacy coupling, must leave the T019 checkbox unchecked in the plan stage, and must
record `ref002.disposition = "unchanged"` with an empty promoted set; a change outside the authorized paths,
an unknown authorization, a dangling link, a new dependency, a REF-002 promotion, or a public-safety leak
fails validation.

**Acceptance criteria.** `git diff --name-only` ⊆ the declared path set; baseline binds by `git rev-parse`;
links resolve in the T008 matrix; the decoder includes only admitted headers; REF-002 promoted set empty;
public-safety scan clean.

**Verification intent.** CHK-09; NEG-G01..NEG-G05.

## 7. Capability 007 requirement links

| Capability anchor | T019 disposition and link | Remaining work |
| --- | --- | --- |
| FR-002 derive from the exact normalized XDL graph; no competing configuration language | **Partial for this slice (decode)**: the decoder consumes only the derived, digest-bound plan bytes and invents no configuration; `XCOM-SW-XDL-003`. | T020 proves equivalence end to end; T038 validates traceability. |
| FR-006 fail before traffic flows on an incompatible identity/direction/schema/interaction/capability/policy | **Partial for this slice (decode-time closure)**: independent capability and cross-reference checks reject an inconsistent plan before any activation; `XCOM-SW-CORE-003`. | Binding/activation enforcement is owned by the end/route lifecycle units. |
| FR-031 versioned `io.xverse.xcom` Profile compiled into the digest-bound activation plan | **Partial for this slice (decode)**: the decoder independently verifies the plan version and recomputes the T017 digest. | T020 regresses; T035/T038 verify. |
| SC-002 equivalent normalized inputs produce byte-identical plans and diagnostic ordering | **Partial for this slice (decode)**: the C++ canonicalization/digest reproduces the T017 rule, so equivalent plan bodies share one digest and decode result. | T020 extends ordering-equivalence coverage; T036 benchmarks. |
| FR-007 explicit bounded queue/ordering/reliability/deadline/retry/overflow/backpressure | **Partial (decode)**: the decoder validates and records the declared policy set within bounds; runtime enforcement is T-CORE. | T019/T020 prove decode bounds. |
| FR-025/FR-027 safe, deterministic diagnostics and public-safe evidence | **Partial (constraint)**: the decoder emits stable codes and identifiers only, with no payload content or sensitive value. | T035/T038 verify. |
| FR-030 traceability, evidence, separate review | **Partial (governance)**: T019 binds `XCOM-SW-XDL-003`/`XCOM-SW-CORE-003` and the T008/T010 locators; review/acceptance remain separate. | T038 validates; T039/T041 review and accept. |
| Constitution arts. II, III, VII, VIII, IX, X | **Implemented for this slice (design)**: T019-SR-001/002/008 preserve neutrality, XDL centrality, platform-first, direction, maturity, and traceability. | Bound to exact candidates by later tasks. |

## 8. REF-002 dispositions

T019 decodes plans and implements **no** direct REF-002 communication requirement XVE-SYS-0139–0158 and no
shared requirement. It **records** `ref002_disposition = "unchanged"` and promotes none. Every capability-007
disposition in `specs/007-xcom-core/reference-traceability.md` and
`docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` remains exactly as accepted.

| REF-002 group | Disposition in T019 | Basis |
| --- | --- | --- |
| `XVE-SYS-0139`–`0158` (communication/interoperability) | **unchanged** — no target is promoted; the disposition set is empty | T019 decodes a build-time derived artifact and demonstrates no runtime communication or interoperability. |
| Shared extensibility (`XVE-SYS-0237`–`0250`), time (`XVE-SYS-0251`–`0264`), failure recovery (`XVE-SYS-0265`–`0279`) | **allocated to their owning capabilities; unchanged** | `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md` §X-COM allocation; capability 007 may validate contracts but claims no full system requirement. |

**Conflicting:** none identified within the admitted inputs.
**Needing clarification:** none; the only open items are the build-environment prerequisite (§9 A-1) and the
T020 suite artifacts (§9 A-2), which T019 records rather than resolves.

## 9. Assumptions and open items

1. **A-1 (build-environment prerequisite)** — the deterministic T019 gate runs `cmake`/`ctest`, which
   requires the already-admitted offline inputs `XVERSE_XCOM_TOOLCHAIN`,
   `XVERSE_XCOM_PACKAGE_MANIFEST` (the twelve-entry lock), and the GTest test prefix
   `XVERSE_XCOM_T025_TEST_TOOLCHAIN` documented in `docs/engineering/xcom/build-environment.md` and
   `docs/engineering/xcom/t025/test-dependency-admission.md`. These are provisioned outside the repository and
   are not part of any Git artifact. The implementation stage must run the gate's exact command first and, if
   it fails solely because these inputs are not in the process environment, resolve it only as permitted by
   `verification-plan.md` §2.4 A-1 (the explicit-cache fallback and the conditional prefix-derived
   `LD_LIBRARY_PATH` described in §2.4) without weakening hash-verified admission; if it cannot be resolved
   that way, the implementation stage records a blocker rather than weakening the gate.
2. **A-2 (owned successor artifacts pending)** — the ordering-equivalence, malformed-plan, drift, bound, and
   regression suites (T020) are not present in the baseline. T019 implements the decoder and its unit/negative
   tests; it does not create, read, or reconcile T020's suites.
3. **A-3 (unreconciled SESN-era `src/xverse/xcom/**`)** — the baseline contains SESN-era C++ artifacts whose
   capability task checkboxes are open (T012–T016). T019 neither reads, extends, nor reconciles them: the
   decoder is self-contained on the C++20 standard library plus the admitted `nlohmann/json` header and links
   no other X-COM target. Its `XCOM-DU-011` component reference `XCOM-CMP-003` is the accepted derived-artifact
   component, not an unreconciled runtime unit.
4. **A-4 (SHA-256 implemented in-tree)** — the decoder implements SHA-256 directly so that the admitted
   dependency set (nlohmann/json, Protocol Buffers, gRPC, clang-tidy) is unchanged and no cryptographic
   library is added. This is a design decision owned by `docs/engineering/xcom/t019/`; it introduces no new
   cross-language contract and changes no accepted sentence. Repository-owned known-answer and fixture-vector
   tests bind the implementation.
5. **A-5** — "Baseline" means the exact Git commit identified by `git rev-parse`; no floating branch, tag, or
   ambient state is a valid binding.
6. **A-6** — T019 fixes **no** production numeric bound value. Every bound in §2.4 is an offline-input,
   decode-structure, or decoded-entity cap; runtime bounds come from the activation plan or unit
   configuration (FR-007).
7. **A-7** — Requirement identifiers `T019-STK-###`/`T019-SR-###` and design-unit identifiers `T019-U-###`
   are candidate-chosen names fixed by `detailed-design.md`; no accepted component, contract, requirement,
   schema, or design unit is renumbered. `T019-U-01`..`T019-U-08` realise the accepted `XCOM-DU-011`;
   T019 does not renumber `XCOM-DU-009`/`010`/`011`.
8. **A-8** — The plan-input derivation mapping and the decode checks are implementation design owned by
   `docs/engineering/xcom/t019/`; the T017 `xdl-profile.md` contract is not changed and no accepted sentence
   is rewritten.
9. **A-9** — The committed T017 plan fixtures under `tests/xcom/activation_plan/fixtures/plan/valid/` are
   read-only decoder test inputs. T019 adds no fixture under the T017 `--check-human`/`run_checks` directories
   and does not change the T017 `expected-summary.txt`; any T019-owned synthetic vector is inline in the
   decoder test sources.

## 10. Requirement index

| Requirement | Refines | Primary design units |
| --- | --- | --- |
| T019-STK-001 | — | T019-U-01, T019-U-02, T019-U-05 |
| T019-STK-002 | — | T019-U-03 |
| T019-STK-003 | — | T019-U-04 |
| T019-STK-004 | — | T019-U-05, T019-U-06 |
| T019-STK-005 | — | T019-U-07 |
| T019-SR-001 | STK-001, STK-004 | T019-U-01 |
| T019-SR-002 | STK-001 | T019-U-02 |
| T019-SR-003 | STK-002 | T019-U-03 |
| T019-SR-004 | STK-003 | T019-U-04 |
| T019-SR-005 | STK-001, STK-004 | T019-U-05 |
| T019-SR-006 | STK-004 | T019-U-06 |
| T019-SR-007 | STK-001..004 | T019-U-08 |
| T019-SR-008 | STK-005 | T019-U-07 |

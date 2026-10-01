# XDL Lite Phase 1 — software requirements (successor)

**Feature:** XDL1 (XDL Lite Phase 1 — offline declared experiment intent compilation)
**Stage:** requirements (repository-owned Spec Kit work-product workflow, ADR-0020)
**Attempt:** XDL1 attempt 1 successor; supersedes the rejected predecessor XDL1 draft, which is retained
only as external failing review evidence.
**Date:** 2026-10-01
**Status:** engineering requirements baseline for the Phase 1 XDL Lite successor candidate. `accepted`
records mean *internal engineering intent* only. Nothing in this document is implementation satisfaction,
runtime evidence, compatibility/parity, live readiness, or external delivery acceptance.

## 1. Scope and authority

This document records the bounded software allocation derived from the admitted thesis planning inputs
for **Phase 1 only**: compile offline *declared experiment intent* into one versioned, canonical,
side-effect-free resolved experiment plan.

Authoritative planning stays external to this repository. The inputs below were admitted read-only and
are referenced by identity/hash, not reproduced or duplicated:

| Admitted input identity | SHA-256 |
| --- | --- |
| `specs/021-thesis-lite-program/fabro/phase1-brief.md` | `1a74abbda2e63892d1678233f3c3160b72dd889a80cf6d8963dc3279bd829684` |
| `specs/022-xdl-lite-experiment-plan/spec.md` | `36c97d669378359942f61662ed9300ca32aa40d940daa404d7045701058408e7` |
| `specs/022-xdl-lite-experiment-plan/plan.md` | `8ca3feef959e69aa5d7abb04dcb3b464d0b68f4b19fbe5d2efd0d7358c2a1e20` |
| `specs/022-xdl-lite-experiment-plan/research.md` | `71a7b9c5f3a1ef4fbe3a49f3da08108e700ae7cd95a005c22c40ee952075b0a9` |
| `specs/022-xdl-lite-experiment-plan/data-model.md` | `8bfd7108e97c098a0a21f16f5bcb3b378c9a3dc13c0955cfee577913a8bbcb2e` |
| `specs/022-xdl-lite-experiment-plan/contracts/experiment-plan.md` | `c3c05cf2887ac2320d48db1ce1a87e96d0335ad0bdcf55a82d0df40c2ccc24d1` |
| `specs/022-xdl-lite-experiment-plan/quickstart.md` | `05a155ad5efecd07715c23e0654f7e5a33411866f6f42ce62472c9e3fa2eca7d` |
| `specs/022-xdl-lite-experiment-plan/tasks.md` | `e8fd222378ed39c04af6eb281974273b5a939e03ef63991150f15f02929500a5` |
| `specs/021-thesis-lite-program/requirements-priorities.json` | `9c3fec63ce6b26ab1aa0d72e901752d0a5f4cc16784add5f30e9052abb36a8d0` |
| `specs/THESIS_MINIMUM_PLATFORM_SCOPE.md` | `1f2f3c83944a5d7da46bb2798f369908b5c89acbe3a41961997f0d616bb05177` |
| `docs/adr/ADR-THESIS-LITE-0001.md` | `fa247b51fd77a55c77d928350e6b1c061f3d2eda2a9963ed2e0b0d22bc05df65` |
| `engineering-instructions.json` (workflow contract) | `0e74f70f35a589669d5b49c2c04b82ce4e792af19912bf06d728271ac3d6634e` |

Admitted thesis/platform identities: thesis revision `fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf`;
admitted platform baseline revision `0c5e249621727b2d0041707de2661f0ed1e1ef23`.

Local platform source anchors (read-only inspection, unchanged by this stage):

* REF-002 SADS allocation register — `docs/architecture/sads-requirements-traceability.json`
  (`d932bea5203166df71273f0216bf50008726a062b4c33e8f6f2678c625660abc`) and its coverage rule in
  `docs/architecture/SADS_REQUIREMENTS_TRACEABILITY.md`
  (`e3dbab01aeda167151d479ecfe7d565a4c073cb2bbde99fbf278218fbaf4fa47`).
* Projection of P1 parents — `specs/021-thesis-lite-program/requirements-priorities.json` (external,
  admitted; `9c3fec63ce6b26ab1aa0d72e901752d0a5f4cc16784add5f30e9052abb36a8d0`).
* Accepted XDL loader/normalizer/validator and CLI — `src/xverse_xdl/**`, `xdl/schemas/v1alpha1/**`,
  `xdl/specification/**`.
* Accepted derived catalog and lifecycle core — `src/xverse_xdl/catalog.py`, `src/xverse_xdl/lifecycle.py`.
* Accepted C++ X-COM contracts and Profile/activation-plan boundary — `proto/xverse/xcom/v1/**`,
  `src/xverse/xcom/contracts/**`, `src/xverse_xdl/xcom_plan.py`, `xdl/profiles/xcom-v0.1.schema.json`.

The accepted platform baseline is the last reviewed checkpoint. This stage adds only the XDL1
requirements work products named below; it changes no accepted requirement, design, unit, measure,
validation, stage, test, schema, source, or ADR.

## 2. Derivation method

1. The admitted program projection selects **19** existing REF-002 target-architecture parents for P1
   (XDL Lite). The projection creates **no new system requirement IDs**
   (`new_system_requirement_ids: []`) and marks every selected parent `allocated` with
   `planned_extent: bounded_partial` and `full_system_requirement_claim: false`.
2. Exactly **one bounded software allocation per existing parent** is derived, in the parent order used
   by `specs/022-xdl-lite-experiment-plan/spec.md` (line 4), producing `XDL1-SR-001` … `XDL1-SR-019`.
   No further XDL1 software records were needed.
3. Each `XDL1-SR-0nn` is linked to its parent with one additive `refines` link (`XDL1-L-0nn`) in
   `engineering/trace/links.json`. The parent anchors are recorded allocation-only in
   `engineering/requirements/XVE-SYS-*.json` using their **original** IDs (including the nonstandard
   `XVE-SYS-00014` padding), original `disposition: allocated`, `maturity: architectural-target`,
   section and owner. Internal SADS requirement text is **not** reproduced in this repository.
4. No source requirement ID, text, hash, or original disposition is rewritten. No parent is closed;
   each software record claims only its bounded Phase 1 contribution.

Parent order and allocation (one software requirement each):

| # | Parent (original ID) | SADS section | SADS owner | Original disposition | Projection extent | XDL1 software requirement |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `XVE-SYS-0001` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-001` |
| 2 | `XVE-SYS-0003` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-002` |
| 3 | `XVE-SYS-0005` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-003` |
| 4 | `XVE-SYS-0006` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-004` |
| 5 | `XVE-SYS-0009` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-005` |
| 6 | `XVE-SYS-00014` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-006` |
| 7 | `XVE-SYS-0016` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-007` |
| 8 | `XVE-SYS-0025` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-008` |
| 9 | `XVE-SYS-0027` | Scenario management | Maestro / Blueprints / UI / SDK | allocated | bounded_partial | `XDL1-SR-009` |
| 10 | `XVE-SYS-0035` | Model integration and execution | Simulation/model runtime / FMI / Maestro | allocated | bounded_partial | `XDL1-SR-010` |
| 11 | `XVE-SYS-0037` | Model integration and execution | Simulation/model runtime / FMI / Maestro | allocated | bounded_partial | `XDL1-SR-011` |
| 12 | `XVE-SYS-0038` | Model integration and execution | Simulation/model runtime / FMI / Maestro | allocated | bounded_partial | `XDL1-SR-012` |
| 13 | `XVE-SYS-0078` | Orchestration and resource management | Maestro / Runtime / Time / Security | allocated | bounded_partial | `XDL1-SR-013` |
| 14 | `XVE-SYS-0117` | Runtime environment | Runtime / Argus / Time / Security | allocated | bounded_partial | `XDL1-SR-014` |
| 15 | `XVE-SYS-0118` | Runtime environment | Runtime / Argus / Time / Security | allocated | bounded_partial | `XDL1-SR-015` |
| 16 | `XVE-SYS-0146` | Communication and interoperability | X-COM | allocated | bounded_partial | `XDL1-SR-016` |
| 17 | `XVE-SYS-0237` | Extensibility and integration | SDK / Plugins / subsystem adapters | allocated | bounded_partial | `XDL1-SR-017` |
| 18 | `XVE-SYS-0251` | Time synchronization and determinism | Time / Maestro / X-COM | allocated | bounded_partial | `XDL1-SR-018` |
| 19 | `XVE-SYS-0254` | Time synchronization and determinism | Time / Maestro / X-COM | allocated | bounded_partial | `XDL1-SR-019` |

## 3. Predecessor review resolution (successor corrections)

The predecessor XDL1 attempt-1 candidate was frozen, hash-inventoried and independently reviewed
read-only. The reviewer returned `verdict: rework` with three open major findings and no repair. That
predecessor is retained here only as **failed review evidence**; the accepted platform baseline in this
repository remains the last reviewed checkpoint.

Hash-verified predecessor-review evidence consumed read-only (external admitted bundle; referenced by
content hash, not by host path):

| Evidence | SHA-256 | Identity used |
| --- | --- | --- |
| predecessor frozen-candidate manifest (2852 files) | `820f3c47d264a6e75a75e3fb58f9465d9bb1ba3495b6c263797d145230c59093` | complete file/hash map of the rejected candidate |
| predecessor `review/internal-review.json` | `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4` | `verdict: rework`, findings `XDL1-RVW-001/002/003`, `reviewed_files` (2852) |
| predecessor `review/stage.json` | `9b09049a68c45160a9ee0e57b918c04dcad6ec7cdc732c94b0953009221e0e23` | reviewer stage record, blocked at candidate gate |

Verification performed at this stage before any authoring: the manifest file/hash map and the review's
`reviewed_files` map are identical (2852 entries, 0 differing); every exact rejected draft revision
retained under the evidence bundle's `files/` tree (122 files) re-hashes to its manifest value; the
current repository baseline reconciles with the manifest for every one of the 2724 non-XDL1 baseline
paths with 0 missing and 0 extra entries, except the five paths the rejected predecessor itself
modified (`engineering/project.json`, `engineering/trace/links.json`, `reports/review-index.md`,
`src/xverse_xdl/__init__.py`, `src/xverse_xdl/cli.py`), which this repository retains in their accepted
pre-predecessor form; and the reviewer's authored record hash equals the hash the reviewer stage bound
as its artifact (`b5ed14f1…`).

Requirement-level resolution. A finding is a review observation about the rejected candidate; the
successor may not repeat it. Because the three findings trace to requirement acceptance criteria that
were too weak to force the missing behaviour and evidence, this stage resolves them **in the requirement
baseline** so that the successor architecture, unit-specification, implementation and validation stages
are bound to demand, implement and negatively test the behaviour. No code, schema or test is repaired in
this stage.

| Finding | Severity | Predecessor defect (evidence) | Requirements response in this successor |
| --- | --- | --- | --- |
| `XDL1-RVW-001` | major | `ExperimentLimits.max_parameters` total-plan bound declared by the frozen design but not enforced; a plan carrying more compiled parameters than the bound was emitted as resolved with no diagnostic. | `XDL1-SR-019` now states that each declared finite bound is enforced over its **full declared scope**, and adds an explicit acceptance criterion that a bound declared as "per payload and total compiled parameters" is enforced at the total-plan scope. `XDL1-SR-014` now makes a declared library-bound violation a rejection that yields **no plan of any kind**. |
| `XDL1-RVW-002` | major | Declared `System.spec.parameters` were mapped by the frozen design but silently dropped from every plan section; only Component parameters were projected. | `XDL1-SR-002` now requires every declared core parameter of the **selected System and of each referenced Component** to be projected by the frozen concept-to-field mapping, and adds an acceptance criterion that a System-level parameter is never silently dropped. |
| `XDL1-RVW-003` | major | `XDL1-PLAN-BOUND-EXCEEDED` was the only one of the frozen diagnostic codes with no test; no count-based library bound had a negative case. | `XDL1-SR-019` now requires **at least one independent negative case per declared library bound**, including the total compiled-parameter bound, and states that a bound without such evidence is incomplete, not satisfied. `XDL1-SR-012` now requires the declared fidelity-limitation bound to be enforced and negatively covered. |

These four amended requirements (`XDL1-SR-002`, `XDL1-SR-012`, `XDL1-SR-014`, `XDL1-SR-019`) carry a
`review_resolution` field naming the finding(s) they address. The remaining fifteen requirements keep the
predecessor's reviewed wording because the reviewer raised no finding against them; their downstream
design, implementation and evidence must still be re-verified in the successor. Repeating an amended
requirement's acceptance criteria by inspection is **not** proof: satisfaction requires the successor's
own design, code and executed measures, which are owned by later stages and are not claimed here.

## 4. Software requirements

Every record below: `id: XDL1-SR-0nn`, `revision: 1`, `level: software`, `status: accepted` (internal
intent), `disposition: allocated`, `planned_extent: bounded_partial`,
`full_system_requirement_claim: false`. Record files: `engineering/requirements/XDL1-SR-0nn.json`.

### XDL1-SR-001 — Declared Scenario selection and binding

*Refines `XVE-SYS-0001`.* The Phase 1 XDL Lite compiler shall select and bind exactly one declared
Scenario from the closed, normalized XDL resource set and shall emit that Scenario's logical identity,
declared parameters, and declared seed into the resolved experiment plan; a missing, unresolved, or
ambiguous Scenario selection shall be rejected with a stable structured diagnostic.

Acceptance criteria:

* Positive: a closed resource set containing exactly one resolvable declared Scenario yields a resolved
  plan carrying that Scenario's logical identity and its declared parameters/seed.
* Negative: a missing, unresolved, or ambiguous Scenario selection is rejected with a stable structured
  diagnostic and no resolved plan.
* Compilation starts no component and performs no registry or network activity.

### XDL1-SR-002 — Logical system/component/flow intent mapped to existing resource kinds

*Refines `XVE-SYS-0003`.* **Resolves `XDL1-RVW-002`.** The compiler shall compile declared System,
Component, Interface, Endpoint, and flow intent into the resolved plan using the existing XDL v1alpha1
`System` and `Component` semantic entities, and shall not introduce a new top-level XDL resource kind or
a competing configuration language; every declared core parameter of the selected System and of each
referenced Component shall be projected into the resolved plan by the frozen concept-to-field mapping,
and no declared parameter may be silently omitted.

Acceptance criteria:

* Every declared flow concept appears in the resolved plan as a reference to an existing semantic
  entity, with no new top-level kind.
* Every declared core parameter of the selected System and of each referenced Component appears in the
  resolved plan at the frozen mapping location (`components[].declaredParameters`); a System-level
  parameter is never silently dropped, including when a Component parameter is projected.
* Unknown namespaces or unknown fields fail closed with a stable structured diagnostic.
* The five existing XDL resource kinds remain unchanged and compatible.

### XDL1-SR-003 — Declared lifecycle intent without lifecycle execution

*Refines `XVE-SYS-0005`.* The compiler shall compile declared lifecycle intent into an explicitly
ordered, dependency-ordered intent list in the resolved plan, and shall not start, stop, probe, or
otherwise influence any process, service, or device.

Acceptance criteria:

* The resolved plan records the declared lifecycle intent and its declared dependency order.
* Reordered equivalent inputs produce an equal resolved plan.
* No process is created and no external state is modified during compilation.

### XDL1-SR-004 — Deployment realization binding resolution

*Refines `XVE-SYS-0006`.* The compiler shall resolve declared Deployment realization bindings and
preserve the separation of logical identity from physical realization; an unresolved or unsupported
realization target shall be rejected without producing a partial plan.

Acceptance criteria:

* A resolvable deployment binding yields a plan entry that keeps logical identity distinct from its
  declared realization.
* An unresolved deployment or realization target is rejected with a stable structured diagnostic and no
  plan.
* A deployment overlay that changes only an artifact revision does not change unrelated logical
  identities.

### XDL1-SR-005 — Explicit declared parameters and seed

*Refines `XVE-SYS-0009`.* The compiler shall require the declared experiment parameters and an explicit
seed wherever the admitted Profile requires them, and shall apply no silent default for a missing
parameter or seed.

Acceptance criteria:

* Declared parameters and the declared seed are recorded explicitly in the resolved plan.
* A missing required parameter or seed is rejected with a stable structured diagnostic.
* No default value is invented for any scientific protocol number or caller-supplied value.

### XDL1-SR-006 — Explicit declared time-domain reference

*Refines `XVE-SYS-00014`.* The compiler shall bind the declared time-domain reference of the selected
Scenario and record it in the resolved plan; a missing or unmapped time reference shall be rejected
rather than defaulted.

Acceptance criteria:

* The resolved plan records the declared time-domain reference of the selected Scenario.
* A missing or unmapped time reference is rejected with a stable structured diagnostic.
* No implicit time mapping is synthesized.
* The original source ID `XVE-SYS-00014` is preserved exactly, including its nonstandard zero padding.

### XDL1-SR-007 — Deterministic intended fault schedule

*Refines `XVE-SYS-0016`.* The compiler shall compile the declared intended fault schedule — fault
identity, resolved target, fault class, simulation trigger, duration, and typed parameters — into a
deterministic order with a stable tie-break, and shall not activate, inject, clear, or otherwise execute
any fault.

Acceptance criteria:

* Every declared fault appears exactly once with its resolved target, fault class, simulation trigger,
  duration, and typed parameters.
* Equal declared schedules compile to an equal ordered schedule; competing schedule ambiguity is
  rejected.
* No fault is activated or cleared and no fault runtime is invoked.

### XDL1-SR-008 — Observer intent references without observation execution

*Refines `XVE-SYS-0025`.* The compiler shall compile declared observer intent references — explicit
observation scope, time/units, and payload policy — into the resolved plan, without invoking any
observer, writer, or oracle callable.

Acceptance criteria:

* Observer references are recorded with explicit scope, time/units, and payload policy.
* No observer, Argus writer, or oracle callable is invoked during compilation.
* An unknown observer reference is rejected with a stable structured diagnostic.

### XDL1-SR-009 — Metric intent references without evaluation

*Refines `XVE-SYS-0027`.* The compiler shall compile declared metric intent references and their
explicit linkage to observers, scope, time domain, and units into the resolved plan, and shall not
evaluate, compute, or execute any metric or oracle.

Acceptance criteria:

* Metric references and their observer/time/unit linkage are recorded explicitly in the resolved plan.
* A metric reference without an explicit observer/time/unit link is rejected with a stable structured
  diagnostic.
* No metric value is computed and no oracle is accessed.

### XDL1-SR-010 — Model/artifact binding references recorded as references only

*Refines `XVE-SYS-0035`.* The compiler shall record declared model/artifact binding references for each
component, with their declared revisions, as explicit references in the resolved plan, and shall not
retrieve, resolve, or claim availability of any artifact.

Acceptance criteria:

* Declared artifact/model binding references and their declared revisions appear in the resolved plan.
* No artifact is fetched, unpacked, or executed and no availability or readiness is claimed.
* A missing required artifact pin is rejected with a stable structured diagnostic.

### XDL1-SR-011 — Declared input provenance and independent versions

*Refines `XVE-SYS-0037`.* The compiler shall record the exact declared input provenance — normalized
source hashes plus an input semantic digest — in the resolved plan, so that a downstream consumer can
verify plan, Profile, and API versions and normalized source hashes without reparsing YAML, and shall
keep the schema version, resource revision, Profile version, and artifact/model revision independent.

Acceptance criteria:

* The resolved plan exposes plan version, Profile version/hash, API version, and the normalized input
  semantic digest.
* Equivalent YAML and JSON encodings produce an equal semantic digest even though their source byte
  hashes differ.
* Changing only a resource revision or artifact/model revision does not change an unrelated version
  field.

### XDL1-SR-012 — Declared fidelity limitations and non-readiness statement

*Refines `XVE-SYS-0038`.* **Resolves `XDL1-RVW-003` (limitation-count scope).** The compiler shall state
declared fidelity limitations in the resolved plan and shall mark explicitly that a resolved plan proves
intent validation only, not executable artifact availability or live readiness.

Acceptance criteria:

* The resolved plan carries the declared fidelity limitations and an explicit non-readiness statement.
* No artifact-availability, runtime-fitness, certification, or parity claim is produced by compilation.
* Limitations are additive and do not silently widen the claimed capability.
* Where the resolved plan records declared fidelity limitations under a finite library bound, that
  limitation bound is enforced over its declared scope and covered by an independent negative case.

### XDL1-SR-013 — Deterministic dependency order and cycle rejection

*Refines `XVE-SYS-0078`.* The compiler shall derive a deterministic dependency order from declared
dependencies and shall reject a dependency cycle or competing-order ambiguity with a stable structured
diagnostic; equal declared inputs shall produce an equal ordered result.

Acceptance criteria:

* Declared dependencies produce a deterministic topological order with stable tie-breaking.
* A dependency cycle is rejected with a stable structured diagnostic and no plan.
* Reordered equivalent inputs of a cycle-free graph produce an equal ordered plan.

### XDL1-SR-014 — Pure offline no-side-effect compilation contract

*Refines `XVE-SYS-0117`.* **Resolves `XDL1-RVW-001` (no-plan-on-bound-violation).** The compiler shall
be a pure offline function: a successful compile or a rejection shall start no component, perform no
registry or filesystem discovery, open no network connection, mutate no external state, and return no
partial or executable plan on rejection.

Acceptance criteria:

* Rejection — including any declared library-bound, cross-reference, or ambiguity violation — returns
  diagnostics and no plan artifact of any kind; a resolved plan is emitted only when every declared
  bound and cross-reference is satisfied.
* Compilation performs no filesystem mutation, no registry lookup, no socket or network use, and no
  process creation, and a late mutation of an already-hashed input is detected.
* The same declared inputs compile to the same result independent of host environment details.

### XDL1-SR-015 — Explicit unsupported realization, delivery, and retry behaviour

*Refines `XVE-SYS-0118`.* The compiler shall reject an unsupported realization, delivery, or retry
behaviour explicitly and shall apply no silent default for unsupported delivery behaviour.

Acceptance criteria:

* An unsupported realization, delivery mode, or retry policy is rejected with a stable structured
  diagnostic.
* No default delivery, retry, or realization behaviour is inferred.
* Rejection leaves no partial plan and no side effect.

### XDL1-SR-016 — Preserved schema, Profile serialization, and X-COM boundary

*Refines `XVE-SYS-0146`.* The compiler shall preserve the accepted v1alpha1 schema versions and the
accepted Profile-derived serialization policy, reuse the existing explicit Profile registry, and shall
not change any accepted XDL schema, public loader/catalog/activation-plan API, or the accepted C++
X-COM implementation and contracts.

Acceptance criteria:

* Existing `validate`, `normalize`, catalog, and activation-plan public APIs, schemas, and diagnostics
  remain compatible for existing inputs.
* The experiment Profile is admitted through the existing explicit Profile registry mechanism.
* No C++ X-COM source, proto contract, accepted XDL schema, or legacy/blueprint/compat artifact is
  modified by Phase 1.

### XDL1-SR-017 — Additive, explicitly admitted, fail-closed Profile extension

*Refines `XVE-SYS-0237`.* The compiler shall consume one explicitly admitted, versioned, neutral
experiment Profile at existing XDL extension points, with unknown namespaces, unknown fields, and
unsupported versions failing closed.

Acceptance criteria:

* The compiler rejects an unknown Profile, an unknown Profile version, an unknown namespace, and an
  unknown field with a stable structured diagnostic.
* The extension is additive and domain-neutral; no domain-specific or thesis-specific value is embedded.
* No second configuration language and no generic unvalidated extension bag is introduced.

### XDL1-SR-018 — Simulation time ordering and canonical semantic identity

*Refines `XVE-SYS-0251`.* The compiler shall order schedule and observation intent by explicit
simulation time, tick, or declared order, and shall compute the canonical semantic plan identity from
declared content only, excluding run identifiers and wall-clock observations.

Acceptance criteria:

* Schedule and observation intent is ordered by explicit simulation time, tick, or declared order.
* The semantic plan identity is unchanged when only a run identifier or wall-clock observation differs.
* Equivalent YAML/JSON encodings and input permutations produce an equal semantic plan identity.

### XDL1-SR-019 — Quantities, units, and finite library bounds

*Refines `XVE-SYS-0254`.* **Resolves `XDL1-RVW-001` and `XDL1-RVW-003` (bounds scope and negative
evidence).** The compiler shall validate every declared quantity, duration, and bound against explicit
units and the finite library limits declared by the frozen design, rejecting non-finite, negative, or
overflow values and ambiguous units; each declared finite library bound shall be enforced over its full
declared scope (including a total-plan scope where the frozen design declares one), and every declared
library bound shall have at least one independent negative case.

Acceptance criteria:

* Quantities and durations are interpreted only through explicit declared units.
* Non-finite, negative, or overflow values, ambiguous units, and invalid durations are rejected with a
  stable structured diagnostic.
* Each declared finite library bound is enforced over its complete frozen scope; where the design
  declares a bound as applying "per payload and total compiled parameters", the total compiled-parameter
  scope is enforced, not only the per-payload scope.
* Every declared library bound has at least one independent negative case that exceeds it and observes
  the bound-exceeded diagnostic, including the total compiled-parameter bound; a declared bound without
  such negative evidence is incomplete, not satisfied.
* Library bounds are declared limits, not thesis safety thresholds, and no scientific protocol number is
  invented.

## 5. Global constraints (apply to every XDL1 software requirement)

* **No fallback** and no alternative model or route is authorized for this work.
* **No online learning** and no network or registry discovery.
* **No runtime execution**: no component start, no fault execution, no observer/metric evaluation, no
  production workload, no legacy execution.
* **No invented thesis protocol value**: scientific protocol numbers, thresholds, deadlines, tolerances,
  and campaign parameters remain caller inputs.
* **No oracle access**: no evaluation ground truth, no oracle callable, no future data.
* **No production change** to legacy, compat, blueprint, accepted C++ X-COM or accepted
  assurance/oracle logic, and no change to historical accepted requirement/design/unit/measure/stage
  records or existing tests.
* **No next phase**: Phase 2 (Argus Lite) and beyond are out of scope and are not started.
* Phase 1 does not complete legacy selection, implement a legacy provider, permit legacy execution, or
  establish compatibility/parity.

## 6. Traceability

* Forward: each `XDL1-SR-0nn` refines its parent anchor through one additive `refines` link
  (`XDL1-L-0nn`) in `engineering/trace/links.json`.
* Backward: the same link set supports parent → refining-child traversal (the traceability matrix
  lineage/ancestor walk); anchors are `engineering/requirements/XVE-SYS-*.json`.
* The remaining relations required of accepted software requirements — `allocated_to`, `implemented_by`,
  `verified_by` — are owned by the architecture, verification-design and implementation stages and are
  **not** claimed here. Until they exist, the XDL1 requirements are intentionally untraced downstream
  and no completeness claim is made.

## 7. Maturity and limitations

* Maturity of every item in this document: **planned / target** — not implemented, not verified, not
  accepted for delivery. Source inspection, and the predecessor's own passing local tests, do not
  demonstrate runtime success; the predecessor's local tests passed while three major contract-fidelity
  findings remained open.
* `status: accepted` on these records means internal engineering intent only.
* The SADS register is target input, not evidence that any capability exists. No REF-002 parent is
  marked implemented, partial-by-evidence, or closed by this stage.
* Known limitation: updating the current pointer `engineering/project.json` changes its bytes and
  therefore invalidates the historical T038 material-input inventory binding; the T038 verifier remains
  pinned to its own accepted baseline and is not re-run as part of XDL1.
* Known scheduled refresh: 21 pre-existing `implemented_by` links target `engineering/project.json` and
  carry the baseline hash `b29433c2f8d3c2310a8cdcaf538548ff18a09aac1b0ed87c8c801682eb6824d0`. After the
  current-pointer update those code endpoint revisions are stale, so `validate_trace` cannot pass until
  the validation stage refreshes exactly those mutable `engineering/trace/links.json` code endpoints.
  This stage records the finding instead of performing an unassigned repair.
* Downstream coverage limitation: the 19 new accepted software requirements have no
  `allocated_to`/`implemented_by`/`verified_by` links yet, so `validate_trace` cannot pass until the
  architecture, implementation and verification-design stages add them. No completeness is claimed.
* Inputs recorded above are the exact admitted identities; no absolute worker path is recorded.

## 8. Next step and model recommendation

Next stage: **architecture** — freeze the versioned experiment Profile fields, the concept-to-field
mapping (including the System-parameter projection required by `XDL1-SR-002`), canonical semantic
identity, the complete set of stable diagnostic codes, units and the finite library bounds with their
per-payload and total-plan scopes (`XDL1-SR-019`), and the additive API/CLI exposure.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most
cost-effective and only authorized route for that contract-freezing work, because it is deterministic
contract transcription over already-admitted inputs plus the recorded predecessor findings, with no need
for a stronger reasoning tier; there is no new Terra/Luna/Sol/Astra engineering route in this package and
no model switch is claimed or performed. Blocker: none at this stage; implementation cannot start until
the four design stages complete and the precode gate passes.

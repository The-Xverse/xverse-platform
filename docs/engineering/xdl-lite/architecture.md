# XDL Lite Phase 1 Architecture — additive experiment Profile and pure resolved-plan compiler

## 1. Document control

| Field | Value |
| --- | --- |
| Feature | XDL1 (XDL Lite Phase 1 — offline declared experiment intent compilation) |
| Stage / role | architecture (repository-owned Spec Kit work-product workflow, ADR-0020) |
| Revision | 1 |
| Date | 2026-10-01 |
| Admitted platform baseline revision | `0c5e249621727b2d0041707de2661f0ed1e1ef23` |
| Admitted thesis revision | `fe58918f9eaf2a6f39cdc9c93cfd4ce615ec84bf` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 (`XDL1-SR-001` … `XDL1-SR-019`) |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Component records | `engineering/architecture/components/XDL1-SR-001-CMP.json` … `XDL1-SR-019-CMP.json` |
| Admitted planning inputs | `specs/022-xdl-lite-experiment-plan/{spec,plan,research,data-model,quickstart,tasks}.md`, `specs/022-xdl-lite-experiment-plan/contracts/experiment-plan.md`, `specs/021-thesis-lite-program/fabro/phase1-brief.md`, `specs/021-thesis-lite-program/requirements-priorities.json`, `specs/THESIS_MINIMUM_PLATFORM_SCOPE.md`, `docs/adr/ADR-THESIS-LITE-0001.md` |
| Consumed accepted platform anchors | `src/xverse_xdl/{loader,schema,semantics,normalize,validate,diagnostics,models,catalog,lifecycle,xcom_plan,cli,__init__}.py`, `xdl/schemas/v1alpha1/**`, `xdl/profiles/**`, `docs/adr/ADR-0007..0013,0016,0018..0020`, `docs/architecture/sads-requirements-traceability.json`, Constitution 2.1.0 |
| Classification | Public-safe engineering work product |
| Maturity | **Planned / target.** Design only. No source, schema, or test code exists in this stage; nothing here is implementation, runtime, readiness, compatibility, or delivery evidence. |
| Revision status | **Successor revision** resolving predecessor findings `XDL1-RVW-001/002/003` (rejected XDL1 attempt-1 candidate, run `01M3VCR5S2TCDGQGA7R1JYH6DA`; read-only review evidence `review/internal-review.json` SHA-256 `b5ed14f18ae1e50d246deb2765215b11bdfd41c54dca0f7699325a1c9d12c2e4`). See §2.1. |

## 2. Purpose and position in the delivery graph

XDL1 adds one bounded capability: compile a closed, offline *declared experiment intent* resource set into one
versioned canonical **resolved experiment plan**, or reject it with stable structured diagnostics and no plan.
It draws the intent from the existing five XDL v1alpha1 resource kinds (`System`, `Component`, `Deployment`,
`Scenario`, `Profile`) through one explicitly admitted neutral experiment Profile, and it performs no execution.

```text
accepted loader/schema/semantics/normalizer  ─┐
accepted catalog + C++ X-COM activation plan ─┤ read-only, unchanged
accepted governance/ADRs/constitution        ─┘
        │
        ▼  consumed by
XDL1 architecture (this stage): frozen Profile fields · concept→field mapping · canonical semantic identity
        │                             · closed diagnostics · units/bounds · dependency/schedule order
        │                             · no-side-effect contract · additive API/CLI exposure
        ▼
XDL1 design → unit specification → verification design (precode gate) → implementation → integration
        → validation → documentation → read-only internal review → terminal review/acceptance
```

XDL1 is Phase 1 only. Argus Lite, Maestro Lifecycle Lite, compatibility descriptors, fault execution, flow
runtime, campaign execution, legacy selection/adapters, and any Phase 2+ work are **out of scope** and are not
designed, stubbed, or reserved here.

### 2.1 Predecessor review resolution

The frozen predecessor XDL1 attempt-1 candidate was independently reviewed read-only under run
`01M3VCR5S2TCDGQGA7R1JYH6DA` and returned `verdict: rework` with three open major findings and no repair. The
predecessor is retained only as failed external review evidence. This successor architecture and its frozen
`detailed-design.md` close the findings at the contract level; the amended requirement baseline
(`requirements.md` `XDL1-SR-002/012/014/019`) demands them.

| Finding | Architectural response |
| --- | --- |
| `XDL1-RVW-001` — the declared `ExperimentLimits.max_parameters` total compiled-parameter scope was not enforced | `XDL1-DD-13` / `detailed-design.md` §10.3 freeze three explicit `max_parameters` scopes (per declared payload list, total compiled parameters by a deterministic count rule, and declared core parameter lists); the total scope is checked over the finished sections before identity finalization, and every scope violation rejects with `XDL1-PLAN-BOUND-EXCEEDED` and no plan (`XDL1-ARCH-04`, `XDL1-ARCH-06`, `XDL1-ARCH-08`). |
| `XDL1-RVW-002` — declared `System.spec.parameters` were silently dropped although mapped to `declaredParameters` | `XDL1-DD-14` / `detailed-design.md` §5 and §7 freeze a deterministic, always-present System-scope entry in `components[]` (`scope = "system"`, emitted first) as the destination for `System.spec.parameters` (and `System.spec.models`), with no duplication into component-instance entries and no drop (`XDL1-ARCH-06`). |
| `XDL1-RVW-003` — `XDL1-PLAN-BOUND-EXCEEDED` had no test and no count-based bound had a negative case | The frozen hand-off (`detailed-design.md` §10.3, §17) requires one independent negative case per declared bound scope, including the total compiled-parameter scope, bound into the XDL1-UNIT and XDL1-VALIDATION measures by the verification-design stage (`XDL1-ARCH-04`, `XDL1-ARCH-08`). |

Repeating these resolutions by inspection is not proof; satisfaction requires the successor's own code and
executed measures, owned by the later implementation/verification/validation stages. No code, schema, fixture, or
test is written by this architecture stage.

## 3. Boundary and context

### 3.1 System context

```text
   ┌──────────── admitted external planning (read-only, not duplicated) ─────────────┐
   │ 022-xdl-lite-experiment-plan contract + data model + plan + research            │
   │ 021 phase1 brief · requirement-priority projection · minimum-scope directive    │
   │ REF-002 SADS allocation register (19 selected parents, no new system IDs)        │
   └────────────────────────────────┬────────────────────────────────────────────────┘
                                    │ derived into (this repository)
   ┌──────── accepted platform assets (read-only, byte-preserved) ───────────────────┐
   │ loader · schema registry · semantic graph · normalizer · diagnostics · CLI       │
   │ catalog (derived) · M3 lifecycle (not invoked) · C++ X-COM (not invoked)         │
   │ xdl/schemas/v1alpha1/** · xdl/profiles/** · five resource kinds                  │
   └────────────────────────────────┬────────────────────────────────────────────────┘
                                    │ extended additively by
   ┌──────── XDL1 owned additions (design now, code later) ──────────────────────────┐
   │ xdl/profiles/experiment-lite-v0.1.schema.json    (admitted neutral payload)      │
   │ src/xverse_xdl/experiment_plan.py                (pure compiler)                 │
   │ src/xverse_xdl/{cli,__init__}.py                 (additive exposure)             │
   │ tests/thesis_lite/xdl/**                         (owned neutral fixtures/tests)  │
   └────────────────────────────────┬────────────────────────────────────────────────┘
                                    ▼
                    resolved experiment plan (intent only) — no execution
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `XDL1-XB-01` Declared intent vs realization | declared logical identity, declared bindings, declared realization class/target | addresses, credentials, provider handles, live handles, artifact contents, production workloads | The compiler emits only declared references; it retrieves, unpacks, starts, probes, and connects to nothing (`XDL1-SR-010`, `XDL1-SR-014`). |
| `XDL1-XB-02` Semantic identity vs byte provenance | canonical semantic digest over declared normalized content | YAML/JSON source bytes, source-map locations, file names, comments, anchors, key order | Equivalent encodings/permutations produce an equal semantic plan identity; byte hashes live only in the volatile envelope (`XDL1-SR-011`, `XDL1-SR-018`). |
| `XDL1-XB-03` Reusable plan vs volatile run data | plan body and plan digest | run identifier, wall-clock generation time, process handles, observed outcomes | Run/wall-clock data is recorded outside the plan body and never affects the plan digest (`XDL1-SR-018`). |
| `XDL1-XB-04` Accepted core vs admitted extension | one admitted `io.xverse.experiment` Profile payload at existing extension points | unknown namespaces/fields, unsupported versions, new extension containers, new top-level kinds, a second configuration language | Unknown/unsupported input fails closed; core identity, required relationships, and validation meaning are not redefined (ADR-0008, ADR-0012; `XDL1-SR-002`, `XDL1-SR-017`). |
| `XDL1-XB-05` Pure compilation vs side effects | in-memory pure function over supplied resources | filesystem mutation/discovery, registry lookup, socket/network, process creation, ambient clock/locale/environment | Rejection and success both leave no side effect; the CLI writes only an explicitly requested output path (`XDL1-SR-014`). |
| `XDL1-XB-06` Intent validation vs availability/readiness | declared intent, declaration-only readiness from the accepted semantic gate | artifact availability, runnable fitness, certification, parity, live readiness | The plan carries an explicit non-readiness statement; compilation proves intent validation only (`XDL1-SR-012`). |
| `XDL1-XB-07` Caller-supplied science vs platform vocabulary | library bounds, unit vocabulary, diagnostic codes, canonical order | ODD, correctness, deadlines, freshness, safety envelope, tolerances, repetitions, margins, seed values, thresholds | No scientific protocol number is invented, defaulted, or narrowed (`XDL1-SR-005`, `XDL1-SR-019`; Constitution IX). |
| `XDL1-XB-08` XDL1 additions vs accepted artifacts | the additive paths listed in §6 | accepted schemas, public loader/catalog/activation-plan APIs, C++ X-COM, legacy/compat/blueprint sources, historical records | Additive only; existing inputs stay compatible and unchanged (`XDL1-SR-016`). |

### 3.3 Prohibited elements (must remain absent)

No change to `xdl/schemas/v1alpha1/**`, any accepted public API signature, the C++ X-COM implementation/contracts,
legacy/compat/blueprint sources, historical requirement/design/unit/measure/validation/stage records, or the
accepted test suite. No new top-level XDL kind, no competing configuration language, no generic unvalidated
extension bag, no new extension container. No process start, no fault activation, no observer/metric/oracle
evaluation, no artifact retrieval, no registry/network discovery, no online learning, no fallback model route,
no production workload, no Phase 2+ capability. No credential, private address, proprietary payload, or
host-specific absolute path in any committed artifact.

## 4. Logical architecture

The module is a pure, bounded pipeline. `XDL1-ARCH-*` names are local to this work-product set; each maps to one
allocation component record (`XDL1-SR-###-CMP`) in §9, following the accepted capability record convention
(one component record per software requirement, as in T027/T038).

| Logical element | Responsibility | Realized in (planned) | Records |
| --- | --- | --- | --- |
| `XDL1-ARCH-01` Admission | reuse the accepted loader, core schema registry, Profile schema catalog, semantic graph, and normalizer on the explicitly supplied closed resource set | `src/xverse_xdl/experiment_plan.py` (orchestration) over `validate_files`/`validate_sources` | CMP-001, CMP-016, CMP-017 |
| `XDL1-ARCH-02` Profile admission | resolve exactly one admitted `io.xverse.experiment` Profile, its version, `schemaRef`, and payload kinds/attachments at existing extension points | `experiment_plan.py` | CMP-005, CMP-017 |
| `XDL1-ARCH-03` Selection and binding | select exactly one System, one optional Deployment bound to it, and exactly one Scenario; resolve declared bindings, targets, artifacts, flows, time domains | `experiment_plan.py` | CMP-001, CMP-002, CMP-004, CMP-006, CMP-010 |
| `XDL1-ARCH-04` Quantity and unit gate | interpret declared schedule/duration/tolerance quantities through a closed time-unit vocabulary with exact rational scaling and finite bounds; validate typed parameters/seed | `experiment_plan.py` | CMP-005, CMP-007, CMP-019 |
| `XDL1-ARCH-05` Ordering | derive the deterministic dependency order (component instances + steps) and the per-time-domain schedule order with stable tie-breaks; reject cycles and competing declared order | `experiment_plan.py` | CMP-003, CMP-013, CMP-018 |
| `XDL1-ARCH-06` Intent compilation | emit ordered lifecycle/flow/fault/observer/metric/binding intent sections from declared content only | `experiment_plan.py` | CMP-002, CMP-003, CMP-007, CMP-008, CMP-009, CMP-010 |
| `XDL1-ARCH-07` Identity and provenance | canonicalize, compute per-resource normalized semantic digests, the input semantic digest, the domain-separated plan digest; keep byte provenance and volatile run data outside the plan body | `experiment_plan.py` + `normalize.canonical_json` | CMP-011, CMP-018 |
| `XDL1-ARCH-08` Diagnostics | construct stable structured diagnostics with gate, code, severity, JSON pointer, resource, location, and remediation; return no plan when any error exists | `experiment_plan.py` + `diagnostics.make_diagnostic` | every CMP; CMP-014 |
| `XDL1-ARCH-09` Exposure | additive public API exports and one additive CLI subcommand preserving existing commands, formats, and exit codes | `src/xverse_xdl/__init__.py`, `src/xverse_xdl/cli.py` | CMP-016 |
| `XDL1-ARCH-10` Payload schema | the admitted neutral Profile payload schema with closed kinds, `additionalProperties: false`, and finite bounds | `xdl/profiles/experiment-lite-v0.1.schema.json` | CMP-017, CMP-019 |

## 5. Component allocation

One allocation component record per software requirement (`XDL1-SR-001-CMP` … `XDL1-SR-019-CMP`), each linked by an
additive `allocated_to` trace link (`XDL1-L-101` … `XDL1-L-119`). Requirement-to-component allocation is 1:1 so that
later `decomposes_to` (component → unit), `implemented_by` (requirement/component/unit → code endpoint), and
`verified_by`/`analyzed_by`/`validates` links stay unambiguous and every accepted software requirement keeps exactly
one owning allocation.

| Requirement | Component record | Logical elements |
| --- | --- | --- |
| `XDL1-SR-001` | `XDL1-SR-001-CMP` | `XDL1-ARCH-03` |
| `XDL1-SR-002` | `XDL1-SR-002-CMP` | `XDL1-ARCH-03`, `XDL1-ARCH-06` |
| `XDL1-SR-003` | `XDL1-SR-003-CMP` | `XDL1-ARCH-05`, `XDL1-ARCH-06` |
| `XDL1-SR-004` | `XDL1-SR-004-CMP` | `XDL1-ARCH-03`, `XDL1-ARCH-06` |
| `XDL1-SR-005` | `XDL1-SR-005-CMP` | `XDL1-ARCH-02`, `XDL1-ARCH-04` |
| `XDL1-SR-006` | `XDL1-SR-006-CMP` | `XDL1-ARCH-03`, `XDL1-ARCH-05` |
| `XDL1-SR-007` | `XDL1-SR-007-CMP` | `XDL1-ARCH-04`, `XDL1-ARCH-05`, `XDL1-ARCH-06` |
| `XDL1-SR-008` | `XDL1-SR-008-CMP` | `XDL1-ARCH-06` |
| `XDL1-SR-009` | `XDL1-SR-009-CMP` | `XDL1-ARCH-06` |
| `XDL1-SR-010` | `XDL1-SR-010-CMP` | `XDL1-ARCH-03`, `XDL1-ARCH-06` |
| `XDL1-SR-011` | `XDL1-SR-011-CMP` | `XDL1-ARCH-07` |
| `XDL1-SR-012` | `XDL1-SR-012-CMP` | `XDL1-ARCH-06`, `XDL1-ARCH-07` |
| `XDL1-SR-013` | `XDL1-SR-013-CMP` | `XDL1-ARCH-05` |
| `XDL1-SR-014` | `XDL1-SR-014-CMP` | `XDL1-ARCH-01`, `XDL1-ARCH-08` |
| `XDL1-SR-015` | `XDL1-SR-015-CMP` | `XDL1-ARCH-02`, `XDL1-ARCH-03` |
| `XDL1-SR-016` | `XDL1-SR-016-CMP` | `XDL1-ARCH-01`, `XDL1-ARCH-09` |
| `XDL1-SR-017` | `XDL1-SR-017-CMP` | `XDL1-ARCH-02`, `XDL1-ARCH-10` |
| `XDL1-SR-018` | `XDL1-SR-018-CMP` | `XDL1-ARCH-05`, `XDL1-ARCH-07` |
| `XDL1-SR-019` | `XDL1-SR-019-CMP` | `XDL1-ARCH-04`, `XDL1-ARCH-10` |

## 6. Ownership and change boundary

| Path | Change |
| --- | --- |
| `xdl/profiles/experiment-lite-v0.1.schema.json` | **new** admitted Profile payload schema |
| `src/xverse_xdl/experiment_plan.py` | **new** pure compiler module |
| `src/xverse_xdl/cli.py`, `src/xverse_xdl/__init__.py` | **additive** subcommand and exports; no removal or signature change |
| `tests/thesis_lite/**` | **new** owned neutral fixtures and tests |
| `docs/engineering/xdl-lite/**` | **new** work-product set |
| `engineering/architecture/components/XDL1-*.json`, `engineering/trace/links.json` | **new** records / **additive** links only |
| `engineering/stage-results/xdl1-*.json`, `reports/xdl-lite/**`, `reports/review-index.md` | **new** stage and report artifacts |

Consumed read-only and byte-preserved: `xdl/schemas/v1alpha1/**`, `xdl/metamodel/**`, `xdl/specification/**`,
`xdl/examples/**`, `xdl/candidates/**`, the accepted `src/xverse_xdl/{loader,schema,semantics,normalize,validate,
diagnostics,models,catalog,lifecycle,xcom_plan}.py`, `src/xverse/xcom/**`, `proto/xverse/xcom/v1/**`,
`docs/engineering/xcom/**`, `engineering/verification/measures/**`, all historical `engineering/**` records
(other than the additive `engineering/trace/links.json` links), and the accepted test suite.

## 7. Data flow (ordered, fail-closed)

1. **Supply.** The caller supplies an explicit closed set of XDL resources (bytes/files/mappings) and the explicit
   local Profile schema path(s). No discovery, no default path, no environment lookup.
2. **Reuse the accepted gates.** Parse (JSON/YAML 1.2), core schema, Profile schema catalog, closed-set reference
   resolution, kind semantic rules, and normalization run exactly as accepted. Any error returns diagnostics and no plan.
3. **Admit the Profile.** Exactly one Profile resource must declare `extensionNamespace = io.xverse.experiment`, the
   admitted `metadata.version`, `compatibleApiVersions` containing `xverse.io/xdl/v1alpha1`, `schemaRef` equal to the
   admitted payload `$id`, and `conflictPolicy = reject`. Payloads are matched to their attachment points by kind and target.
4. **Select.** Exactly one System is selected; the closed set must supply exactly one Scenario bound to it; at most
   one Deployment bound to that System, and the Scenario must reference it when present. Ambiguity or absence rejects.
5. **Validate quantities.** Every declared schedule, duration, tolerance, parameter, and seed is checked against the
   closed unit vocabulary and the finite library bounds; non-finite, negative, overflow, precision, and ambiguous-unit
   values reject.
6. **Order.** The dependency graph (System component instances and Scenario steps) is topologically ordered with a
   stable tie-break; a cycle rejects. Schedule entries are ordered per time domain by canonical ticks, then rank, then
   identity; duplicate `declared-order` triggers reject as competing ambiguity.
7. **Compile intent.** Ordered lifecycle, flow, binding/artifact, fault-schedule, observer, and metric sections are
   emitted from declared content only, together with declared fidelity limitations and the compiler's non-readiness
   statement. Declared core parameters are projected into `components[]`: exactly one System-scope entry first
   (carrying every declared `System.spec.parameters` and `System.spec.models` entry) followed by one entry per
   component instance (carrying that Component's declared parameters and models). The three `max_parameters` scopes
   of `detailed-design.md` §10.3 are evaluated over the finished sections; exceeding the total compiled-parameter
   scope rejects with no plan.
8. **Identify.** Canonicalize the plan body, compute per-resource normalized semantic digests, the input semantic
   digest, and the domain-separated plan digest; re-verify the input digests (late-mutation detection); self-check the
   digest. A mismatch returns diagnostics and no plan.
9. **Expose.** The API returns a result (diagnostics + plan + volatile run envelope); the CLI prints the same
   information as text or canonical JSON and exits `0`/`1`/`2`. The volatile envelope is never part of the plan digest.

## 8. Quality attributes

| Attribute | Architectural decision | Records |
| --- | --- | --- |
| Determinism | canonical JSON (sorted keys, compact separators, integral floats as integers, `allow_nan=false`), fixed domain separators, explicit ordering keys, no ambient time/clock/locale/environment | CMP-011, CMP-018 |
| Semantic identity stability | identity computed from declared normalized content only; sources sorted by identity; source maps/byte hashes excluded | CMP-011, CMP-018 |
| Fail-closed rejection | every stage returns diagnostics and **no** plan for any error; no partial plan object is exposed | CMP-014 and every CMP |
| No side effects | pure in-memory function; no file/process/socket/registry/clock access; caller controls any output path | CMP-014 |
| Bounded inputs | reused `LoadLimits` plus the XDL1 entity/quantity bounds table in `detailed-design.md` §10, including all three explicit `max_parameters` scopes (§10.3: per declared payload list, total compiled parameters, declared core parameter lists) | CMP-019 |
| Compatibility | additive module/subcommand/exports; accepted APIs, schemas, and diagnostics unchanged for existing inputs | CMP-016 |
| Neutrality | no automotive/thesis/domain-specific value, threshold, or name; caller supplies all scientific numbers | CMP-005, CMP-019 |
| Honest maturity | plan carries declared limitations and an explicit non-readiness statement; no availability/readiness/parity claim | CMP-012 |
| Traceability | one component record per requirement; `allocated_to` links added here; code/measure/validation links added by later stages | CMP-001 … CMP-019 |

## 9. Consistency and constraints

- **Dependency direction preserved.** XDL1 consumes the accepted core and adds a leaf module; no accepted module
  depends on XDL1, and no blueprint/profile-to-core reverse dependency is introduced (Constitution VIII).
- **Domain neutrality preserved.** Only generic platform vocabulary appears: resource, deployment, scenario,
  component, endpoint, flow, time domain, fault, observer, metric, plan, diagnostic.
- **XDL centrality preserved.** The intent is expressed in existing XDL kinds plus one Profile payload at existing
  extension points; no competing configuration language is introduced.
- **Logical/physical separation preserved.** Realization stays in `Deployment` bindings and targets; the compiler
  records the declared separation and resolves nothing physical.
- **Ownership preserved.** Only §6 paths are added or additively extended; every accepted artifact keeps its bytes.
- **Legacy immutable.** No legacy/compat/blueprint repository, artifact, or workload is read, executed, or changed.
- **Scientific values are caller inputs.** No protocol threshold, tolerance, deadline, repetition count, or margin is
  chosen, defaulted, or narrowed here (Constitution IX; `XDL1-XB-07`).

## 10. Traceability

| Architecture element | Requirements |
| --- | --- |
| `XDL1-XB-01`, `XDL1-ARCH-03`, `XDL1-ARCH-06` | `XDL1-SR-002`, `XDL1-SR-004`, `XDL1-SR-010` |
| `XDL1-XB-02`, `XDL1-XB-03`, `XDL1-ARCH-07` | `XDL1-SR-011`, `XDL1-SR-018` |
| `XDL1-XB-04`, `XDL1-ARCH-10` | `XDL1-SR-002`, `XDL1-SR-017` |
| `XDL1-XB-05`, `XDL1-ARCH-01`, `XDL1-ARCH-08` | `XDL1-SR-014`, `XDL1-SR-016` |
| `XDL1-XB-06` | `XDL1-SR-012` |
| `XDL1-XB-07`, `XDL1-ARCH-04` | `XDL1-SR-005`, `XDL1-SR-019` |
| `XDL1-XB-08`, `XDL1-ARCH-09` | `XDL1-SR-016` |
| `XDL1-ARCH-02` | `XDL1-SR-005`, `XDL1-SR-015`, `XDL1-SR-017` |
| `XDL1-ARCH-05` | `XDL1-SR-003`, `XDL1-SR-006`, `XDL1-SR-007`, `XDL1-SR-013`, `XDL1-SR-018` |
| `XDL1-ARCH-06` | `XDL1-SR-001`, `XDL1-SR-003`, `XDL1-SR-007`, `XDL1-SR-008`, `XDL1-SR-009`, `XDL1-SR-012` |

Each `XDL1-SR-###-CMP` record lists its owning `XDL1-SR-###`, its boundaries, interfaces, dependencies, planned
paths, and error conditions, so the unit-specification stage can attach one or more units per component with
`decomposes_to` links without ambiguity.

## 11. Negative cases (architecture view)

Executable cases and exact test identifiers are frozen in the unit-specification and verification-design stages; this
table fixes only the architecture-level behaviour of each boundary.

| Boundary | Injected defect | Required behaviour |
| --- | --- | --- |
| `XDL1-XB-01` | declared reference resolves to an artifact/network/credential the compiler would have to fetch or open | reject; no retrieval, no handle, no plan |
| `XDL1-XB-02` | same declared intent supplied as YAML and as JSON, or with permuted resource/payload order | equal canonical plan bytes and equal plan digest |
| `XDL1-XB-03` | only the run identifier or the generation time differs | equal plan body and plan digest; values appear only in the volatile envelope |
| `XDL1-XB-04` | unknown Profile namespace/version/`schemaRef`/kind/field, or a new extension container | reject at the Profile/extension gate; no plan |
| `XDL1-XB-05` | a side-effecting call (open/socket/subprocess/env/clock) attempted during compilation | no call occurs; rejection or success both leave no side effect |
| `XDL1-XB-06` | consumer treats a resolved plan as proof of availability/readiness | the plan's non-readiness statement and limitations forbid the claim |
| `XDL1-XB-07` | a missing seed/parameter/time mapping/threshold, a non-finite/negative/overflow/ambiguous-unit quantity, or a parameter-count scope (per payload, total compiled, declared core) exceeded | reject with the stable diagnostic and no plan; no default is invented and no plan carries more compiled parameters than the bound |
| `XDL1-ARCH-06` (declared-core projection) | a declared `System.spec.parameters`/`System.spec.models` entry is silently omitted, or duplicated into component-instance entries | every declared System core parameter appears exactly once at the frozen System-scope `components[]` destination, never duplicated and never dropped |
| `XDL1-XB-08` | an accepted schema, signature, C++ X-COM artifact, or accepted test would change | the change is rejected; additive-only rule fails closed |

## 12. Next step and model recommendation

Next stage: **unit_specification** — freeze interfaces, state/concurrency, inputs/outputs/errors/invariants, planned
paths, table-driven expected outcomes, adversarial/metamorphic cases, exact pytest-discoverable test identifiers, and
static checks against this architecture and `detailed-design.md`.

Model recommendation: the pinned `deepseek-v4-flash` with **high** reasoning remains the most cost-effective and the
only authorized route for that work, because it is deterministic contract transcription over already-frozen
architecture/design inputs with no stronger-reasoning need; there is no new Terra/Luna/Sol/Astra engineering route in
this package, no fallback, and no model switch is claimed or performed. Blocker: none at this stage; no source or
schema code may be written until the four design stages complete and the precode gate passes.

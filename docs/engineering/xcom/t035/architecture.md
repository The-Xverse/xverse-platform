# T035 Architecture — Exact-Candidate Verification Matrix and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T035 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → architecture |
| Revision | 1 (Phase 8 exact-candidate verification slice) |
| Baseline revision | `dab68568bd8d189b14c7a4a9e3a9c325085a7529` |
| Affected paths | `docs/engineering/xcom/t035/**`, `engineering/requirements/T035-*.json`, `engineering/architecture/components/T035-*.json`, `engineering/unit-specifications/T035-*.json`, `engineering/validation/scenarios/T035-VS-ACCUMULATED.json`, `engineering/verification/measures/**`, `engineering/trace/links.json`, `engineering/project.json`, `reports/review-index.md`, `reports/xcom-queue/t035-verification.json` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json`; `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-STK-007`, `XCOM-SW-ENB-001`, `XCOM-SW-ENB-004`, `XCOM-SW-INTG-001`); `docs/engineering/xcom/build-environment.md` evidence contract; `specs/007-xcom-core/plan.md` delivery step 9; ADR-0020; Constitution VII, IX, X |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T035 is the **evidence** task of the capability-007 `T-INTG` family. T030–T034 delivered the accepted
external-tool contract, local-IPC gateway, separate-process client, reusable contract suites, and the second
synthetic provider. T035 executes the complete verification matrix over that accepted platform at one exact
candidate revision and retains repository-owned results. T036–T038 own the benchmark, documentation, and
traceability-verifier deliverables; T039–T041 own review and acceptance.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013–T016 core + matrix (read-only)
   → T017–T020 XDL activation plan (read-only)
   → T021–T024 observation boundary (read-only)
   → T025–T029 stimulation boundary (read-only)
   → T030 contract (read-only) → T031 gateway (read-only) → T032 client (read-only)
   → T033 reusable suites (read-only) → T034 second provider (read-only)
   → T035 exact-candidate verification matrix + repository-owned results (this slice)
   → T036 benchmark → T037 Doxygen → T038 traceability → T039/T040 review → T041 acceptance
```

T035 adds one evidence report, one work-product set, one engineering record set, additive trace links, and the
Phase 8 verification-measure descriptors. It changes no accepted production source, test, target, label,
command, or expected value.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  FR-026/027/028/029/030/035 · SC-002/009/010/011 · plan step 9            │
   │  t008 XCOM-STK-007, XCOM-SW-ENB-001/004, XCOM-SW-INTG-001                │
   │  t009 XCOM-CMP-* · t010 XCOM-DU-001…024                                  │
   │  build-environment.md evidence contract (command_argv/exit_code/outcome/  │
   │      log and manifest hashes, candidate revision)                         │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ verified by
   ┌──────── accepted implementations and suites (read-only, executed) ───────┐
   │  T013–T016 core value types, lifecycle, composition, loopback matrix      │
   │  T017–T020 XDL profile/plan compile + bounded decode                     │
   │  T021–T024 observation taps/sink · T025–T029 stimulation boundary        │
   │  T030 contract · T031 gateway · T032 client · T033 suites · T034 provider │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ measured by
   ┌────────────── T035 owned evidence artifacts (this slice) ────────────────┐
   │  reports/xcom-queue/t035-verification.json                               │
   │      commands · outcomes · hashes · environment · bounded logs ·          │
   │      exact-candidate identity                                             │
   │  engineering/verification/measures/{unit,integration,validation,          │
   │      static_analysis,sanitizer}.json                                      │
   │  engineering/trace/links.json (additive T035 links)                       │
   │  docs/engineering/xcom/t035/** work products                              │
   │  guarantee : complete executed matrix, exact-candidate binding,           │
   │      honest per-measure outcomes, public-safe bounded evidence,           │
   │      no accepted production change                                        │
   └──────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
                          T036–T041 benchmark/documentation/traceability/review/acceptance
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T35-XB-1` Executed matrix vs accepted code | the executed commands and their recorded outputs | the accepted production source, headers, contracts, schemas, and tests | T035 executes the accepted code and changes no accepted byte (`T035-SR-014`). |
| `T35-XB-2` Candidate-local vs whole-system measurement | candidate-local unit/static/sanitizer/validation runs | the trusted target-repository integration measure that assembles the pinned platform | Only the trusted policy's `system_integration` contract defines whole-system integration; a candidate-local run is never reported as integration (`T035-SR-008`, T035-GAP-02). |
| `T35-XB-3` Exact candidate vs stale or foreign evidence | results bound to the candidate revision and material digest | evidence from another revision, run, or checkout | Every result identifies the candidate revision; stale, mismatched, skipped, or failed evidence is `failed`/`blocked`, never `pass` (`T035-SR-011`). |
| `T35-XB-4` Evidence vs content | command argv, exit status, outcome, tool identity, hashes, bounded logs | payload bytes, permit contents, secrets, private addresses, host paths, proprietary source | Committed evidence and bounded logs contain none of the excluded content (`T035-SR-012`, `T035-SR-013`). |
| `T35-XB-5` Public summary vs private raw manifest | the public bounded report and its hashes | host-specific absolute prefix, manifest, temporary, and evidence-store paths | The public report records identities and hashes, not private host paths (`T035-SR-012`). |
| `T35-XB-6` Measure descriptor vs accepted revision | content-only refresh of `engineering/verification/measures/**` | a revision bump that would stale accepted trace links | Descriptor `revision` values are preserved so accepted `verified_by`/`analyzed_by` links stay valid (`T035-OPEN-01`, `T035-SR-014`). |
| `T35-XB-7` Local/offline execution vs external resources | admitted offline toolchain and in-process owned fixtures | any TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary, or production workload | No verification command contacts a network or legacy resource (`T035-SR-016`). |
| `T35-XB-8` T035 scope vs successor scope | the executed matrix and its results | the T036 benchmark, T037 Doxygen, T038 traceability/SADS, T039–T041 review/acceptance | T035 neither duplicates nor claims a successor deliverable (`T035-SR-010`, T035-GAP-04). |

### 3.3 Prohibited elements (must remain absent)

No change to any accepted production source, header, contract, schema, register, XDL profile, accepted test,
target, label, command, or expected value; no new admitted dependency or runtime library; no compiled or linked
gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS use; no external network
peer; no legacy binary, legacy repository, or production workload; no benchmark, Doxygen, traceability-verifier,
review, or acceptance artifact; no payload, permit, secret, private address, or host path in a committed file or
log; no ambient wall-clock-dependent verdict; no measure `revision` bump that stales an accepted trace link; no
rewrite or weakening of an accepted ADR, requirement, contract, schema, register, or test; no REF-002 promotion;
no acceptance or integration of the candidate.

## 4. Components

`T35-*` names are local to this document; the accepted `XCOM-CMP-*` and `XCOM-DU-*` identifiers are the
authorized units/components. The T035 requirement components are `T035-SR-###-CMP` (one per requirement) and
the units `T035-SR-###-U`.

### 4.1 T035 components

- **`T35-CMP-MATRIX`** (`reports/xcom-queue/t035-verification.json`, `docs/engineering/xcom/t035/**`): the
  executed command set, per-measure outcomes, environment/tool identity, artifact and evidence hashes, bounded
  logs, and exact-candidate identity.
- **`T35-CMP-MEASURES`** (`engineering/verification/measures/**`): the content-only refreshed Phase 8 measure
  descriptors (`unit`, `integration`, `validation`, `static_analysis`) plus the new `sanitizer` descriptor; each
  keeps its `revision` and its `kind`.
- **`T35-CMP-TRACE`** (`engineering/trace/links.json`, `engineering/project.json`): additive T035
  requirement/component/unit/measure/code/validation links and the current-task pointer.
- **`T35-CMP-WP`**: the T035 repository-owned work-product set and the T035 package record.

### 4.2 Consumed components (read-only)

- **`T35-CMP-T013…T016`** — accepted core value types, diagnostics, endpoint/route lifecycle, provider
  boundary/composition, owned loopback provider, and the core matrix. Executed, unchanged.
- **`T35-CMP-T017…T020`** — accepted XDL Profile/activation-plan compile and bounded decode. Executed
  (C++ and Python), unchanged.
- **`T35-CMP-T021…T024`** — accepted observation boundary. Executed, unchanged.
- **`T35-CMP-T025…T029`** — accepted stimulation boundary (time authority, permit/session, journal, guard,
  actions). Executed, unchanged.
- **`T35-CMP-T030…T034`** — accepted tool contract, gateway, separate-process client, reusable suites, and
  second provider. Executed, unchanged.
- **`T35-CMP-T011`/`T012`** — the admitted offline envelope and the subtree build/test contract. Consumed; no
  rule is weakened and no dependency is added.

## 5. Data flow (ordered)

1. **Admission.** The admitted offline toolchain, package manifest, and GTest prefix are verified; no network
   access is used.
2. **Configure and build.** The platform is configured (Ninja, C++20, warning-as-error) and built at the
   candidate revision, including a separate sanitizer configuration.
3. **Execute the matrix.** The full CTest suite (unit/contract/integration/negative/recovery/concurrency), the
   sanitizer suite, the `cppcheck` static-analysis measure, the inherited Phase 6 conformance recheck, the
   whole-system target-repository integration measure, and the Python suite execute.
4. **Derive outcomes.** Each command's exit status and the trusted discovery check determine `pass`/`failed`;
   an unavailable or stale input yields `blocked`.
5. **Record evidence.** `reports/xcom-queue/t035-verification.json` is written with `commands`, `outcomes`,
   `hashes`, `environment`, bounded logs, and the exact-candidate identity; no payload, permit, secret, private
   address, or host path is committed.
6. **Bind the trace.** Additive T035 links connect each accepted requirement to its component, unit, measure,
   code/evidence artifact, and validated scenario.

## 6. Interfaces

### 6.1 Evidence report (`reports/xcom-queue/t035-verification.json`)

| Field | Contract |
| --- | --- |
| `commands` | the ordered list of executed command argv arrays and, per command, its exit status |
| `outcomes` | the per-measure outcome (`pass` / `failed` / `blocked`) derived from the trusted discovery check |
| `hashes` | SHA-256 hashes of the retained evidence/logn and of the key candidate artifacts |
| `environment` | compiler, CMake, Ninja, `cppcheck`, Python, and admitted toolchain/manifest/GTest-prefix identities and hashes, excluding host-specific absolute paths |
| `logs` | bounded, public-safe per-command log excerpts |
| `candidate` | the baseline revision, the exact candidate revision, and the run identity |
| `schema_version` | `1` |

### 6.2 Measure descriptors (`engineering/verification/measures/**`)

| Element | Contract |
| --- | --- |
| `id` / `revision` / `kind` | unchanged `id` and `revision`; `kind` ∈ {`unit`, `integration`, `validation`, `static_analysis`, `sanitizer`} |
| `command` / `command_runs` | the Phase 8 route descriptor (`run_xcom_phase8_tests.py <mode>`) and what it runs |
| `test_ids` | the selected, discovered case IDs for the measure; empty only for the non-test `static_analysis` measure |
| `discovery_check` | `100% tests passed` for test measures; `none (non-test measure)` for static analysis |

### 6.3 Consumed contracts (read-only, unchanged)

| Interface | Contract consumed |
| --- | --- |
| accepted `src/xverse/xcom/**` and `tests/xcom/**` | the verified matrix and its discovered case names |
| `engineering/check_phase6_conformance.py` / `run_phase6_conformance.py` | the inherited T026–T029 conformance recheck |
| `docs/engineering/xcom/build-environment.md` | the repository-owned evidence contract (`command_argv`, `exit_code`, `outcome`, log/manifest hashes, candidate revision) |
| accepted CMake/CTest subtree | the warning-as-error build and the deterministic CTest names and labels |

## 7. Concurrency and resource bounds

| Aspect | T035 decision |
| --- | --- |
| Production footprint | none; T035 adds no runtime source, test, or build target |
| Build inventory | unchanged; T035 registers no new test target and adds no runtime library |
| Processes | one build/measure process at a time; a separate sanitizer build; no legacy, external, or production process |
| Threads | the executed suites use their accepted bounded concurrency; T035 adds no thread |
| Storage | one bounded JSON report and bounded log excerpts; no unbounded log or payload retention |
| Transport | none; no network, DNS, TLS, or legacy access |
| Time | measure timeouts are bounded by the trusted policy; no verdict depends on ambient wall-clock timing |
| Determinism | the matrix, outcomes, and hashes are deterministic for the exact candidate revision |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Completeness | full C++ matrix, sanitizer, static analysis, conformance, whole-system integration, and Python suite | `T035-SR-001`…`-009` |
| Exact-candidate binding | results bound to the candidate revision and material digest | `T035-SR-011`; CHK-01, CHK-11 |
| Honest outcomes | `pass` only on the trusted discovery check; `failed`/`blocked` otherwise | `T035-SR-011`; CHK-19 |
| Public-safe evidence | identities and hashes only; no private content | `T035-SR-012`, `T035-SR-013` |
| Ownership preserved | no accepted production change; content-only descriptor refresh | `T035-SR-014`; CHK-16, CHK-17 |
| Governance honesty | registers reconciled; REF-002 `unchanged`; successors allocated | `T035-SR-015`; CHK-14, CHK-18, CHK-20 |
| Offline honesty | no network, DNS, TLS, legacy, or production resource | `T035-SR-016` |

## 9. Consistency and constraints

- **Dependency direction preserved.** T035 consumes the accepted T007–T034 design and code; it introduces no
  dependency on a later slice, an external peer, or a legacy repository, and adds no admitted dependency.
- **Domain neutrality preserved.** Only generic X-COM verification vocabulary appears (measure, case,
  outcome, hash, environment); no automotive, product, protocol, or configuration primitive is introduced.
- **XDL centrality preserved.** T035 neither parses nor authors XDL; it executes the accepted plan tests and
  records opaque logical identities.
- **Logical/physical separation preserved.** No address, port, or physical transport enters the evidence.
- **Ownership preserved.** Only the declared T035 paths change; every accepted production byte and existing
  test is preserved.
- **Maturity preserved.** The slice records verification evidence only; benchmarks, documentation,
  traceability, review, and acceptance remain T036–T041.

## 10. Traceability

| Architecture element | T035 requirements |
| --- | --- |
| `T35-XB-1`, `T35-CMP-MATRIX` | T035-SR-001, T035-SR-002, T035-SR-014 |
| `T35-XB-2` | T035-SR-008 |
| `T35-XB-3` | T035-SR-011 |
| `T35-XB-4`, `T35-XB-5` | T035-SR-012, T035-SR-013 |
| `T35-XB-6`, `T35-CMP-MEASURES` | T035-SR-006, T035-SR-014 |
| `T35-XB-7` | T035-SR-016 |
| `T35-XB-8` | T035-SR-010 |
| `T35-CMP-TRACE`, `T35-CMP-WP` | T035-SR-015 |
| `T35-CMP-T013…T016` | T035-SR-001, T035-SR-003, T035-SR-004 |
| `T35-CMP-T017…T020` | T035-SR-007 |
| `T35-CMP-T021…T024` | T035-SR-012 |
| `T35-CMP-T025…T029` | T035-SR-005, T035-SR-009 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are listed
in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T35-XB-1` | change an accepted production source, test, target, label, or value | NEG-01, NEG-06 |
| `T35-XB-2` | report a candidate-local run as whole-system integration | NEG-07 |
| `T35-XB-3` | report stale, mismatched, skipped, or failed evidence as `pass` | NEG-02, NEG-03 |
| `T35-XB-4`/`T35-XB-5` | commit a payload, permit, secret, private address, or host path | NEG-04 |
| `T35-XB-6` | bump a measure `revision` and stale accepted links | NEG-06 |
| `T35-XB-7` | use TCP/`AF_INET`, DNS, TLS, or a legacy/external peer | NEG-04 |
| `T35-XB-8` | claim a T036/T037/T038/T039/T041 result | NEG-08 |
| Governance | mark the T035 checkbox at the plan stage or skip the required report | NEG-05, NEG-09 |
| Trace | omit a required requirement/component/unit/measure/code/validation edge | NEG-10 |

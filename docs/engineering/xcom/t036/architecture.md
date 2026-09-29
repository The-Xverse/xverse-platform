# T036 Architecture — Controlled Disabled/Enabled-Tap Benchmarks and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T036 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → architecture |
| Revision | 1 (Phase 8 controlled-benchmark slice) |
| Baseline revision | `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` |
| Affected paths | `docs/engineering/xcom/t036/**`, `engineering/run_xcom_benchmarks.py`, `engineering/requirements/T036-*.json`, `engineering/architecture/components/T036-*.json`, `engineering/unit-specifications/T036-*.json`, `engineering/validation/scenarios/T036-VS-ACCUMULATED.json`, `engineering/trace/links.json`, `engineering/project.json`, `reports/review-index.md`, `reports/xcom-queue/t036-benchmark.json` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture-model.json`; `docs/engineering/xcom/t010/unit-design.json`; `docs/engineering/xcom/t008/requirements-register.json` (`XCOM-SW-INTG-003`, `XCOM-SW-OBS-003`, `XCOM-SW-CORE-007`, `XCOM-SW-ENB-001/002/004`, `XCOM-SW-INTG-001`); `docs/engineering/xcom/build-environment.md` evidence contract; `specs/007-xcom-core/spec.md` SC-008; `specs/007-xcom-core/plan.md` performance goal; ADR-0020; Constitution VII, IX, X |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T036 is the **controlled-benchmark** task of the capability-007 `T-INTG` evidence family. T035 executed
the complete verification matrix over the accepted platform; T036 measures the observation tap's
disabled/enabled overhead over the accepted owned loopback workload and records the result with
environment, uncertainty, baseline, disabled/enabled cases, and non-production limits. T037–T038 own
documentation and traceability-verifier deliverables; T039–T041 own review and acceptance.

```text
T007 ownership → T008 requirements → T009 architecture → T010 unit design → T011 admission
   → T012 subtree build/test contract → T013–T016 core + matrix (read-only)
   → T017–T020 XDL activation plan (read-only)
   → T021–T024 observation boundary + accepted disabled-tap benchmark (read-only)
   → T025–T029 stimulation boundary (read-only)
   → T030 contract → T031 gateway → T032 client → T033 suites → T034 second provider (read-only)
   → T035 exact-candidate verification matrix + results (read-only)
   → T036 controlled disabled/enabled-tap benchmark + repository-owned results (this slice)
   → T037 Doxygen → T038 traceability → T039/T040 review → T041 acceptance
```

T036 adds one benchmark harness, one evidence report, one work-product set, one engineering record set, and
additive trace links. It changes no accepted production source, test, target, label, command, or expected
value.

## 3. Boundary and context

### 3.1 System context

```text
   ┌────────────── accepted capability-007 anchors (read-only) ──────────────┐
   │  SC-008 · FR-008/014/026/027/028/029/030 · plan performance goal          │
   │  t008 XCOM-SW-INTG-003, XCOM-SW-OBS-003, XCOM-SW-CORE-007,                │
   │       XCOM-SW-ENB-001/002/004, XCOM-SW-INTG-001                          │
   │  t009 XCOM-CMP-* · t010 XCOM-DU-* · t010 path docs/engineering/xcom/t036/ │
   │  build-environment.md evidence contract; T011 admitted offline envelope   │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ measured over
   ┌──────── accepted implementations and fixtures (read-only, executed) ─────┐
   │  owned loopback provider + composition + lifecycle (T013–T016)            │
   │  observation hub, taps, policies, synthetic sink (T021–T024)              │
   │  accepted disabled-tap benchmark fixture (T021 integration)               │
   │  accepted contract/negative/concurrency suites (T016/T020/T026–T034)      │
   └──────────────────────────────────┬──────────────────────────────────────┘
                                      │ driven by
   ┌────────────── T036 owned artifacts (this slice) ─────────────────────────┐
   │  engineering/run_xcom_benchmarks.py                                      │
   │      build/execute the accepted owned loopback workload;                 │
   │      tap disabled (same-baseline) vs tap enabled;                        │
   │      controlled interleaved paired samples; --verify mode                │
   │  reports/xcom-queue/t036-benchmark.json                                  │
   │      environment · uncertainty · baseline · tap_disabled · tap_enabled ·  │
   │      raw samples · method · limitations · exact-candidate identity        │
   │  engineering/trace/links.json (additive T036 links)                      │
   │  docs/engineering/xcom/t036/** work products                             │
   │  guarantee : controlled repeated measurement, exact-candidate binding,    │
   │      honest per-case outcomes, public-safe bounded evidence,              │
   │      explicit non-production limits, no accepted production change        │
   └──────────────────────────────────┬───────────────────────────────────────┘
                                      ▼
                          T037–T041 documentation/traceability/review/acceptance
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `T36-XB-1` Harness vs accepted code | the new harness, report, records, and work products | the accepted production source, headers, contracts, schemas, and tests | T036 adds no byte to the accepted object; the harness drives it read-only (`T036-SR-010`). |
| `T36-XB-2` Same-baseline comparison | the disabled case measured on the identical owned loopback workload | a different workload, provider, or revision | The gated SC-008 2% comparison is `tap_disabled` versus the same baseline; the enabled case is an ungated observation against `tap_disabled` over the identical workload (`T036-SR-001`, `T036-SR-003`). |
| `T36-XB-3` Measurement vs uncertainty | the recorded sample count, median, dispersion/interval, and method | an implied production confidence claim | Uncertainty is declared and bounded; the report is not a production claim (`T036-SR-002`, `T036-SR-006`, `T036-OPEN-06`). |
| `T36-XB-4` Exact candidate vs stale evidence | the report bound to the candidate revision and artifact hashes | samples from another revision, run, or host | Stale or foreign results fail the harness `--verify` mode (`T036-SR-008`, `T036-SR-009`). |
| `T36-XB-5` Public summary vs private raw data | identities, hashes, method, bounded public-safe sample excerpts | host-specific absolute paths, credentials, payload bytes, proprietary excerpts | Committed evidence contains none of the excluded content (`T036-SR-004`, `T036-SR-012`). |
| `T36-XB-6` Local/offline execution vs external resources | admitted offline toolchain, owned loopback and in-process fixtures | any TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary, or production workload | No benchmark command contacts a network or legacy resource (`T036-SR-007`, `T036-SR-012`). |
| `T36-XB-7` T036 scope vs successor scope | the controlled benchmark and its results | the T037 Doxygen, T038 traceability/SADS, T039–T041 review/acceptance deliverables | T036 neither duplicates nor claims a successor deliverable (`T036-GAP-04`). |

### 3.3 Prohibited elements (must remain absent)

No change to any accepted production source, header, contract, schema, register, XDL profile, accepted
test, target, label, command, or expected value; no new admitted dependency or runtime library; no
compiled or linked gRPC runtime; no TCP listener or `AF_INET`/`AF_INET6` socket, DNS, resolver, or TLS
use; no external network peer; no legacy binary, legacy repository, or production workload; no Doxygen,
traceability-verifier, review, or acceptance artifact; no payload, permit, secret, private address, or
host path in a committed file or log; no ambient wall-clock-dependent verdict outside the recorded
uncertainty statement; no production-performance claim; no rewrite or weakening of an accepted ADR,
requirement, contract, schema, register, or test; no REF-002 promotion; no acceptance or integration of
the candidate.

## 4. Components

`T36-*` names are local to this document; the accepted `XCOM-CMP-*` and `XCOM-DU-*` identifiers are the
authorized units/components. The T036 requirement components are `T036-SR-###-CMP` (one per requirement)
and the units `T036-SR-###-U`.

### 4.1 T036 components

- **`T36-CMP-HARNESS`** (`engineering/run_xcom_benchmarks.py`): builds/reuses the admitted owned loopback
  build, drives the disabled (same-baseline) and enabled-tap cases over interleaved paired samples,
  computes the median and uncertainty, applies the gated 2% comparison to the disabled case (recording the
  enabled case as an ungated observation), writes the report, and provides the fail-closed `--verify` mode.
- **`T36-CMP-REPORT`** (`reports/xcom-queue/t036-benchmark.json`): the benchmark evidence carrying
  `environment`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `limitations`, raw samples,
  method, and the exact-candidate identity.
- **`T36-CMP-TRACE`** (`engineering/trace/links.json`, `engineering/project.json`): additive T036
  requirement/component/unit/measure/code/validation links and the current-task pointer.
- **`T36-CMP-WP`**: the T036 repository-owned work-product set and the T036 package record.

### 4.2 Consumed components (read-only)

- **`T36-CMP-T013…T016`** — accepted core value types, diagnostics, endpoint/route lifecycle, provider
  boundary/composition, owned loopback provider, and the core matrix. Driven, unchanged.
- **`T36-CMP-T021…T024`** — accepted observation boundary (hub, taps, policies, synthetic sink) and the
  accepted disabled-tap benchmark fixture. Driven, unchanged.
- **`T36-CMP-T017…T020`, `T36-CMP-T025…T029`, `T36-CMP-T030…T034`** — accepted XDL plan, stimulation
  boundary, contract, gateway, client, suites, and second provider. Consumed as preserved suites;
  unchanged.
- **`T36-CMP-T011`/`T012`** — the admitted offline envelope and the subtree build/test contract.
  Consumed; no rule is weakened and no dependency is added.

## 5. Data flow (ordered)

1. **Admission.** The admitted offline toolchain, package manifest, and GTest prefix are verified; no
   network access is used.
2. **Build.** The accepted owned loopback/observation build is configured (Ninja, C++20,
   warning-as-error) and built at the candidate revision.
3. **Warm-up.** Each case is warmed up once so the measured samples do not include first-run effects.
4. **Measure.** The disabled (same-baseline) and enabled-tap cases run over the same owned loopback
   workload with interleaved paired samples, alternating case order to reduce drift bias.
5. **Derive.** Median latency and throughput, the per-case dispersion/interval, the gated
   `tap_disabled`-versus-baseline median regression, and the ungated enabled-versus-disabled observation
   are computed; the 2% SC-008 comparison of the disabled case yields a deterministic outcome.
6. **Record.** `reports/xcom-queue/t036-benchmark.json` is written with `environment`, `uncertainty`,
   `baseline`, `tap_disabled`, `tap_enabled`, raw samples, method, limitations, and the exact-candidate
   identity; no payload, permit, secret, private address, or host path is committed.
7. **Bind the trace.** Additive T036 links connect each requirement to its component, unit, measure,
   code/evidence artifact, and validated scenario.

## 6. Interfaces

### 6.1 benchmark harness (`engineering/run_xcom_benchmarks.py`)

| Invocation | Contract |
| --- | --- |
| `python3 engineering/run_xcom_benchmarks.py` | run the controlled benchmark, write/refresh the report, and exit `0` only when both cases ran and the gated `tap_disabled`-versus-baseline 2% median comparison holds (the enabled case is an ungated observation) |
| `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | re-read the report and exit `0` only when required fields, method, uncertainty, candidate binding, hashes, raw samples, and the gated 2% comparison are present and consistent and `HEAD` is either the accepted baseline (measured working-tree successor) or its direct-child candidate commit; otherwise exit nonzero |
| `--report <path>` (optional) | override the report path; the default and the report used by the trusted route is `reports/xcom-queue/t036-benchmark.json` |

The harness is deterministic in its selection of workloads, sample counts, and comparisons; it does not
depend on ambient wall-clock time for its verdict.

### 6.2 Evidence report (`reports/xcom-queue/t036-benchmark.json`)

| Field | Contract |
| --- | --- |
| `schema_version` | `1` |
| `task_id` | `T036` |
| `baseline_revision` | the accepted baseline commit; the harness measures with `HEAD == baseline_revision` and the reviewed candidate files uncommitted |
| `candidate_revision` | `null` in a committed report: a report cannot contain the hash of the commit that contains it. The candidate commit is the direct child of `baseline_revision` carrying the recorded material |
| `candidate_identity` | the sorted material-input inventory, the material digest, the per-file SHA-256 hashes, the revision-binding rule, and the generation time |
| `environment` | compiler, C++ standard, CMake, Ninja, Python, admitted toolchain/manifest/GTest-prefix identities and hashes, excluding host-specific absolute paths |
| `method` | workload, warm-up, sample count, interleaving, clock, and statistic definitions |
| `uncertainty` | per-case sample count, median, and dispersion/interval; an explicit non-production note |
| `baseline` | the same-baseline case (tap disabled / accepted pre-observation path) |
| `tap_disabled` | the disabled-tap case results (median latency, median throughput) |
| `tap_enabled` | the enabled-tap case results (median latency, median throughput) |
| `regression` | the gated `tap_disabled`-versus-same-baseline median latency and throughput regression and its 2% SC-008 comparison, plus the ungated enabled-versus-disabled observation (`gated: false`) |
| `samples` | the raw paired samples for both cases |
| `limitations` | explicit non-production limitations |
| `hashes` | SHA-256 of the retained evidence and referenced candidate artifacts |

### 6.3 Consumed contracts (read-only, unchanged)

| Interface | Contract consumed |
| --- | --- |
| accepted `src/xverse/xcom/**` | the owned loopback submit/receive path and the observation-hub/tap surface |
| `tests/xcom/observation/integration/disabled_tap_benchmark.cpp` | the accepted disabled-tap comparison seam and its `sun_path`-aware fixture layout |
| `docs/engineering/xcom/build-environment.md` | the repository-owned evidence contract (exact environment, candidate revision, bounded public-safe logs) |
| accepted CMake/CTest subtree | the warning-as-error C++20 build and the owned fixtures |

## 7. Concurrency and resource bounds

| Aspect | T036 decision |
| --- | --- |
| Production footprint | none; T036 adds no runtime source, test target, or dependency to the accepted object |
| Build inventory | the accepted build is reused/configured by the harness; T036 registers no new accepted test target |
| Processes | one bounded benchmark process per run; no legacy, external, or production process |
| Threads | measurement is single-threaded so fixture-created contention does not bias the comparison |
| Storage | one bounded JSON report with bounded raw samples; no unbounded log or payload retention |
| Transport | none; the workload is an owned in-process loopback route |
| Time | sample counts and iterations are fixed and recorded; no verdict depends on ambient wall-clock time |
| Determinism | the case selection, sample count, statistics, and comparison are fixed for the exact candidate revision |

## 8. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Measurement control | same workload, warm-up, interleaved paired samples, single-threaded | `T036-SR-001`; CHK-01 |
| Same-baseline honesty | the gated `tap_disabled` case compared against the same owned-loopback baseline (the enabled-versus-disabled regression is retained only as an ungated observation) | `T036-SR-003`; CHK-04 |
| Uncertainty honesty | per-case sample count, median, dispersion/interval, explicit non-production note | `T036-SR-002`; CHK-03 |
| Exact-candidate binding | report bound to the accepted baseline revision, the exact candidate material digest/inventory, and artifact hashes; `--verify` accepts only the baseline or its direct-child candidate commit | `T036-SR-008`, `T036-SR-009`; CHK-09 |
| Public-safe evidence | identities, hashes, method, bounded excerpts only | `T036-SR-004`, `T036-SR-012` |
| Ownership preserved | no accepted production change; additive harness/report/records | `T036-SR-010`; CHK-14 |
| Governance honesty | registers reconciled; REF-002 `unchanged`; successors allocated | `T036-SR-011`; CHK-15, CHK-16 |
| Offline honesty | no network, DNS, TLS, legacy, or production resource | `T036-SR-007`, `T036-SR-012` |

## 9. Consistency and constraints

- **Dependency direction preserved.** T036 consumes the accepted T007–T035 design and code; it
  introduces no dependency on a later slice, an external peer, or a legacy repository, and adds no
  admitted dependency.
- **Domain neutrality preserved.** Only generic X-COM benchmark vocabulary appears (tap, baseline,
  sample, median, regression, environment); no automotive, product, protocol, or configuration
  primitive is introduced.
- **XDL centrality preserved.** T036 neither parses nor authors XDL; it drives accepted logical
  identities.
- **Logical/physical separation preserved.** No address, port, or physical transport enters the
  evidence.
- **Ownership preserved.** Only the declared T036 paths change; every accepted production byte and
  existing test is preserved.
- **Maturity preserved.** The slice records a prototype benchmark only; documentation, traceability,
  review, and acceptance remain T037–T041.

## 10. Traceability

| Architecture element | T036 requirements |
| --- | --- |
| `T36-XB-1`, `T36-CMP-HARNESS` | T036-SR-001, T036-SR-010 |
| `T36-XB-2` | T036-SR-001, T036-SR-003 |
| `T36-XB-3` | T036-SR-002, T036-SR-006 |
| `T36-XB-4`, `T36-CMP-REPORT` | T036-SR-008, T036-SR-009 |
| `T36-XB-5` | T036-SR-004, T036-SR-012 |
| `T36-XB-6` | T036-SR-007, T036-SR-012 |
| `T36-XB-7` | T036-SR-005, T036-SR-011 |
| `T36-CMP-TRACE`, `T36-CMP-WP` | T036-SR-011 |
| `T36-CMP-T013…T016` | T036-SR-001, T036-SR-010 |
| `T36-CMP-T021…T024` | T036-SR-001, T036-SR-002, T036-SR-004 |
| `T36-CMP-T017…T020`, `T36-CMP-T025…T034` | T036-SR-007, T036-SR-009 |

## 11. Negative cases (architecture view)

Every boundary has a declared fail-closed behaviour and a negative-case owner; the executable cases are
listed in `verification-plan.md` §5.

| Boundary | Injected defect | Negative case |
| --- | --- | --- |
| `T36-XB-1` | change an accepted production source, test, target, label, or value | NEG-01, NEG-06 |
| `T36-XB-2` | compare the gated `tap_disabled` case against a different workload, revision, or baseline (or record the enabled-versus-disabled observation against anything other than the identical disabled baseline) | NEG-02 |
| `T36-XB-3` | omit the sample count, dispersion, or non-production note | NEG-03 |
| `T36-XB-4` | present stale, foreign, or mismatched samples as current | NEG-04, NEG-05 |
| `T36-XB-5` | commit a payload, permit, secret, private address, or host path | NEG-07 |
| `T36-XB-6` | use TCP/`AF_INET`, DNS, TLS, or a legacy/external peer | NEG-07 |
| `T36-XB-7` | claim a T037/T038/T039/T041 result, or a production-performance claim | NEG-08 |
| Governance | mark the T036 checkbox at the plan stage or omit the required report | NEG-09 |
| Trace | omit a required requirement/component/unit/measure/code/validation edge | NEG-10 |

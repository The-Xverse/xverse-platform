# T036 Detailed Design — Controlled Disabled/Enabled-Tap Benchmarks and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T036 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → detailed design |
| Revision | 1 (Phase 8 controlled-benchmark slice) |
| Baseline revision | `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

T036 measures the observation tap's disabled/enabled overhead over the accepted owned loopback workload
at one exact candidate revision and records the result in repository-owned evidence. The design is
written **before** execution; the implementation must realize it exactly or record a design change and
re-review.

## 2. Design decisions

| ID | Decision | Rationale | Requirement |
| --- | --- | --- | --- |
| `T036-DD-01` | T036 adds no byte to the accepted production source, test, target, label, command, or expected value; the new artifacts are the harness, the report, and the engineering records | T036 owns benchmark evidence, not new behavior; changing the verified object would invalidate the benchmark | T036-SR-010 |
| `T036-DD-02` | The benchmark drives the accepted owned loopback workload with the observation tap disabled (same-baseline) and enabled | Matches SC-008 and the accepted `xcom_observation_disabled_benchmark` design | T036-SR-001 |
| `T036-DD-03` | Each case is warmed up once, then measured over a fixed, recorded number of interleaved paired samples, alternating the case order | Reduces first-run and drift bias so the comparison is controlled | T036-SR-001, T036-SR-003 |
| `T036-DD-04` | The report records per-case sample count, median, and a dispersion/interval measure, plus an explicit non-production note | Implements the SC-008 uncertainty obligation honestly | T036-SR-002, T036-SR-006 |
| `T036-DD-05` | The report carries `environment`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `limitations`, raw `samples`, `method`, and the exact-candidate identity | Implements the repository-owned evidence contract and the Phase 8 gate's required fields | T036-SR-004…`-009` |
| `T036-DD-06` | The public report records tool identities and hashes, not host-specific absolute prefix, manifest, or evidence-store paths | Public-safety rule and reviewer expectation | T036-SR-004, T036-SR-012 |
| `T036-DD-07` | `--verify` re-reads the report and fails closed on a missing required field, incomplete method/uncertainty, stale/foreign binding, or an exceeded 2% threshold | Prevents stale, incomplete, or failed evidence from supporting acceptance | T036-SR-009 |
| `T036-DD-08` | A case whose inputs are unavailable is recorded `blocked` with its reason; no inferred or stale sample is substituted | Honest outcome rule | T036-OPEN-04 |
| `T036-DD-09` | T036 links `implemented_by` to its own harness/evidence artifacts and to the accepted code paths the workload exercises, and names executed cases by their accepted discovered IDs | T036's realized artifacts are evidence plus the harness, not new production behavior | T036-SR-011 |
| `T036-DD-10` | T036 does not run, duplicate, or claim the T035 matrix or the T037/T038/T039/T040/T041 deliverables | Scope and maturity separation | T036-SR-005, T036-SR-011 |

## 3. Benchmark route (exact commands)

The route below is the repository-owned controlled benchmark. `${XVERSE_FABRIC_ROOT}` and the admitted
inputs are resolved by the trusted policy; the admitted inputs are `XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`. The implementation records the
exact resolved argv, exit status, and observed samples.

| # | Purpose | Command (portable descriptor) | Expected |
| --- | --- | --- | --- |
| B-1 | run the controlled benchmark and write the report | `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | exit `0`; both cases measured; the gated `tap_disabled`-versus-baseline 2% median comparison holds (the enabled case is an ungated observation) |
| B-2 | fail-closed report verification | `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | exit `0`; required fields, method, uncertainty, binding, hashes, samples, and comparison consistent |
| B-3 | accepted disabled-tap case (evidence input) | `ctest --test-dir build/f8u -R '^xcom_observation_disabled_benchmark$' --output-on-failure` | exit `0`; the accepted fixture reports both thresholds PASS |
| B-4 | trusted full-suite regression context | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |

The trusted Phase 8 `validation` measure invokes B-2 through
`engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` (see
`run_xcom_phase8_tests.py`, `mode == "validation" and task == "T036"`). B-1 is run by the implementation
stage to produce the report; B-3/B-4 provide the accepted comparison context and the preserved
regression suite.

## 4. Evidence report schema (`reports/xcom-queue/t036-benchmark.json`)

```json
{
  "schema_version": 1,
  "task_id": "T036",
  "capability": "007",
  "baseline_revision": "<40-hex accepted baseline>",
  "candidate_revision": null,
  "candidate_identity": {
    "material_digest": "<sha256>", "material_inputs": ["<relative path>", "..."],
    "revision_binding": "<baseline plus material-digest/hash binding rule>",
    "generated_at": "<iso-8601>"
  },
  "method": {
    "workload": "owned-loopback observation-tap disabled/enabled",
    "warmup_runs": 1,
    "paired_samples": "<integer>",
    "iterations_per_sample": "<integer>",
    "pair_order": "alternating",
    "clock": "steady_clock",
    "statistics": ["median", "min", "max", "p95", "mad"]
  },
  "environment": {
    "compiler": "<identity>", "cxx_standard": "c++20", "cmake": "<version>",
    "ninja": "<version>", "python": "<version>", "target": "linux-x86_64",
    "admitted_inputs": {
      "XVERSE_XCOM_TOOLCHAIN": {"kind": "directory", "sha256": "<sha256>", "files": "<int>"},
      "XVERSE_XCOM_PACKAGE_MANIFEST": {"kind": "file", "sha256": "<sha256>", "files": 1},
      "XVERSE_XCOM_T025_TEST_TOOLCHAIN": {"kind": "directory", "sha256": "<sha256>", "files": "<int>"}
    }
  },
  "uncertainty": {
    "baseline": {"n": "<int>", "median_latency_ns": "<double>", "mad_ns": "<double>",
                 "min_latency_ns": "<double>", "max_latency_ns": "<double>",
                 "p95_latency_ns": "<double>"},
    "tap_disabled": {"n": "<int>", "median_latency_ns": "<double>", "mad_ns": "<double>",
                     "min_latency_ns": "<double>", "max_latency_ns": "<double>",
                     "p95_latency_ns": "<double>"},
    "tap_enabled": {"n": "<int>", "median_latency_ns": "<double>", "mad_ns": "<double>",
                    "min_latency_ns": "<double>", "max_latency_ns": "<double>",
                    "p95_latency_ns": "<double>"},
    "note": "single-process steady-clock on a shared, uncontrolled host; not a production confidence interval"
  },
  "baseline": {"case": "tap_disabled_same_baseline", "median_latency_ns": "<double>",
               "median_throughput_per_s": "<double>"},
  "tap_disabled": {"median_latency_ns": "<double>", "median_throughput_per_s": "<double>"},
  "tap_enabled": {"median_latency_ns": "<double>", "median_throughput_per_s": "<double>"},
  "regression": {
    "threshold_percent": 2.0,
    "basis": "SC-008: tap_disabled versus the same owned-loopback baseline (the enabled case is not gated)",
    "latency_regression_percent": "<double>", "throughput_regression_percent": "<double>",
    "latency_pass": "<bool>", "throughput_pass": "<bool>", "outcome": "pass|failed|blocked",
    "tap_enabled_observation": {"latency_regression_percent": "<double>",
                                "throughput_regression_percent": "<double>",
                                "within_2_percent": "<bool>", "gated": false}
  },
  "samples": [{"index": 0, "baseline_latency_ns": "<double>", "disabled_latency_ns": "<double>",
               "enabled_latency_ns": "<double>", "disabled_latency_regression_percent": "<double>",
               "enabled_latency_regression_percent": "<double>", "...": "..."}],
  "hashes": {"<artifact path>": "<sha256>"},
  "limitations": ["controlled prototype benchmark only; not a production performance claim", "..."],
  "blockers": []
}
```

- `method` and `uncertainty` are mandatory; a report without them, or without raw `samples`, fails
  `--verify`.
- `regression.outcome` is `pass` only when the gated `tap_disabled`-versus-same-baseline median latency and
  throughput regressions are within the 2% threshold; the enabled-versus-disabled regression is recorded as
  an ungated observation (`gated: false`) and is not compared against the threshold; an
  unavailable input yields `blocked`.
- `hashes` records SHA-256 of the retained evidence and of the referenced T036 artifacts; it never
  records a host-specific absolute path.
- `environment` records identities and admitted-input digests by name, not host paths.
- `candidate_revision` is `null`: a committed report cannot contain the hash of the commit that contains
  it. The exact candidate is bound by `baseline_revision` plus the `candidate_identity.material_inputs`
  inventory, `material_digest`, and per-file `hashes`. `--verify` accepts exactly two revisions for that
  binding — `HEAD == baseline_revision` (the measured working-tree successor) and `HEAD` as the direct
  child of `baseline_revision` whose distance from the baseline is one commit (the committed candidate);
  a foreign commit, an unrelated history, a merge, or an extra successor is rejected.

## 5. Cases and comparison

| Case | Description | Role |
| --- | --- | --- |
| `baseline` | accepted pre-observation / disabled-observation submit path on the owned loopback route | the same-baseline reference |
| `tap_disabled` | current public submit with the observation pointer disabled (accepted benchmark fixture behavior) | disabled-tap case |
| `tap_enabled` | current public submit with a bounded best-effort observation tap attached | enabled-tap case |

The disabled case validates the accepted SC-008 statement; the enabled case quantifies the tap's
overhead against the identical baseline. The report records both, and the comparison uses the paired
per-sample regressions so host drift affects both sides equally.

The accepted `xcom_observation_disabled_benchmark` fixture remains the authoritative disabled-tap
comparison (`baseline` versus `tap_disabled`); T036 consumes it read-only and adds the enabled-tap case
without changing the accepted fixture.

## 6. Failure semantics

| Condition | Outcome |
| --- | --- |
| a case does not run or produces non-finite/absent samples | case outcome `blocked` with the reason; the report does not claim pass (`T036-DD-08`) |
| the gated `tap_disabled`-versus-same-baseline median regression exceeds the 2% SC-008 threshold | `regression.outcome` is `failed`; the harness exits nonzero (`T036-SR-003`, `T036-SR-009`) |
| a required field, the method, or the uncertainty is absent | `--verify` exits nonzero (`T036-SR-009`) |
| the report is stale or foreign to the candidate revision (a foreign or unrelated commit, a merge, or an extra successor of the baseline) | `--verify` exits nonzero (`T036-SR-008`, `T036-SR-009`) |
| a committed artifact or excerpt would contain private content | the content is redacted/omitted before commit (`T036-SR-012`) |
| an admitted input or the owned fixture is unavailable | the case is `blocked`; the candidate fails closed (`T036-OPEN-04`) |

## 7. Determinism and safety

- The workload, warm-up, sample count, iteration count, interleaving, and statistic definitions are
  fixed and recorded; no T036 verdict depends on ambient wall-clock time beyond the recorded samples.
- Measurement is single-threaded so fixture-created contention does not bias the comparison.
- No benchmark command opens a network listener or socket, resolves a name, or contacts a legacy or
  external resource.
- Committed files and excerpts contain no credential, private address, real or proprietary payload, or
  host-specific absolute path.

## 8. Public-safety and information classification

- Only tool identities, admitted-input digests, the method, bounded public-safe sample values, and
  hashes are committed.
- Host-specific absolute prefix, manifest, temporary, and evidence-store paths are excluded from the
  report; the raw private measurements, if retained, live outside the public report.
- No payload byte, permit content, credential, private address, or proprietary source excerpt enters a
  committed artifact.

## 9. Traceability

| Design element | Requirement | Checks |
| --- | --- | --- |
| `T036-DD-02`/`-03` controlled disabled/enabled measurement | T036-SR-001, T036-SR-003 | CHK-01, CHK-02, CHK-04 |
| `T036-DD-04` uncertainty and limits | T036-SR-002, T036-SR-006 | CHK-03, CHK-05 |
| `T036-DD-05`/`-06` report fields and public safety | T036-SR-004, T036-SR-005, T036-SR-008, T036-SR-012 | CHK-06…CHK-08, CHK-11 |
| `T036-DD-07`/`-08` fail-closed verification | T036-SR-009 | CHK-12, CHK-13 |
| `T036-DD-09` evidence trace | T036-SR-011 | CHK-15, CHK-16 |
| `T036-DD-10` unchanged inventory and scope | T036-SR-010 | CHK-14 |

## 10. Doxygen and documentation

T036 adds one Python harness and no C/C++ interface, so it adds no Doxygen comment obligation; the
Doxygen completion and warning-free-generation obligation is T037. T036 documents the benchmark route,
the report schema, and the comparison in this work-product set only.

## 11. Compatibility contract and generated-code provenance

- T036 adds **no** generated code and **no** admitted dependency. It does not touch
  `proto/xverse/xcom/v1/tool_gateway.proto` or any `XCOM-XLC-002` message and links no transport runtime.
- **Compatibility contract.** T036 defines no competing interface, contract, or configuration language;
  it drives the accepted owned loopback and observation boundaries and promotes no REF-002 target.

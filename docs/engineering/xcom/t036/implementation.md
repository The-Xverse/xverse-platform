# T036 Implementation Record — Controlled Disabled/Enabled-Tap Benchmarks and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T036 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | implementation |
| Revision | 1 (Phase 8 controlled-benchmark slice) |
| Accepted baseline revision | `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Candidate material digest | `sha256:247f3afdabde77afbf712399aa28b825279d1c5ec4390847374d1ce2861bc239` |
| Benchmark report | `reports/xcom-queue/t036-benchmark.json` (sha256 `95c78ad3988e6e9f501cbfbd0d343f760c7d8a9e374b7c26441e9d88d441bd7c`) |
| Classification | Public-safe engineering work product |

This record describes what the T036 candidate implements and the controlled benchmark it executed. It does
not accept or integrate the candidate; explicit user acceptance remains T041 and external Codex review is
deferred until the ordered backlog `xcom-t030-t034-20260928` completes. No T037 Doxygen, T038
traceability-verifier/SADS, T039/T040 review, or T041 acceptance result is produced or claimed.

## 2. Implemented boundary

T036 is an **evidence-plus-harness** task. It adds **no production source, no accepted test, no accepted
target, and no dependency** (`T036-DD-01`). Its artifacts are:

- `engineering/run_xcom_benchmarks.py` — the task-owned benchmark harness with the failure-closed `--verify`
  mode. It compiles the accepted owned-loopback and observation sources, together with a generated,
  task-owned measurement driver, into an **isolated temporary benchmark build** and runs it locally/offline.
  It changes no accepted byte; the accepted sources are consumed read-only.
- `reports/xcom-queue/t036-benchmark.json` — the repository-owned evidence report carrying `environment`,
  `method`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `regression`, the raw paired
  `samples`, `limitations`, artifact `hashes`, and the exact-candidate identity.
- `docs/engineering/xcom/t036/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  — the repository-owned work-product set.
- `engineering/requirements/T036-*.json`, `engineering/architecture/components/T036-*.json`,
  `engineering/unit-specifications/T036-*.json`, `engineering/validation/scenarios/T036-VS-ACCUMULATED.json`
  — the current-task records.
- `engineering/trace/links.json` — 164 additive T036 links (157 plan-stage links plus 7
  implementation-stage `implemented_by` links to the harness); `engineering/project.json` — current-task
  pointer.
- `docs/engineering/xcom/t010/unit-design.json`, `docs/engineering/xcom/t010/design-units.md` — the required
  planned→established path-status reconciliation for `docs/engineering/xcom/t036/` (`XCOM-DU-024`; status
  field only).
- `reports/review-index.md`, `reports/xcom-queue/t036-package.json`, `docs/engineering/xcom/t036/internal-review.json`,
  and the one-line T036 checkbox in `specs/007-xcom-core/tasks.md`.

No accepted production source, header, contract, schema, register, XDL profile, test, target, label,
command, or expected value was changed.

### 2.1 Design realization notes

- `T036-DD-02` — the harness measures three cases over one identical owned-loopback workload: the admitted
  pre-observation submit (`baseline`, the same-baseline reference), the public submit with observation
  disabled (`tap_disabled`), and the public submit with a bounded best-effort observation tap attached
  (`tap_enabled`). The `baseline` and `tap_disabled` cases reproduce the accepted
  `xcom_observation_disabled_benchmark` comparison.
- `T036-DD-03` — each case is warmed up once, then measured over 21 interleaved paired samples of 5000
  submit/receive pairs, alternating the case order each sample. Measurement is single-threaded.
- `T036-DD-04` — the report records the per-case sample count, median, MAD, min, max, and p95, and an
  explicit non-production uncertainty note.
- `T036-DD-05`/`T036-DD-06` — the report carries the required fields, the raw samples, the method, and the
  exact-candidate material binding; it records tool identities and admitted-input digests by name, not
  host-specific absolute paths.
- `T036-DD-07` — `--verify` re-reads the report and fails closed (nonzero) on a missing required field, an
  incomplete method/uncertainty, a stale/foreign binding, a hash mismatch, an inconsistent recomputed
  regression, or an exceeded 2% threshold.
- `T036-DD-08` — no inferred or stale sample is substituted; a case that cannot run yields `blocked` and the
  harness exits nonzero.
- `T036-DD-09` — the trace `implemented_by` edges point at the harness and at the accepted code paths the
  workload exercises; the selected case set names only already-discovered cases.
- `T036-DD-10` — no successor deliverable is run or claimed.

### 2.2 SC-008 threshold basis (recorded implementation clarification)

The accepted success criterion `SC-008` and the accepted plan performance goal bound the **disabled-tap**
case: *"With taps disabled, the benchmark records no more than 2% median throughput regression and no more
than 2% median latency regression against the same owned loopback baseline"* (`spec.md` SC-008) and
*"Disabled taps add at most 2% median throughput and latency regression in the owned loopback benchmark"*
(`plan.md`). The report therefore applies the gated 2% pass/fail comparison to `tap_disabled` versus the
same `baseline`. The `tap_enabled` case is **recorded as an observation**, not gated by SC-008: on this host
the enabled metadata-only tap adds a measured median latency overhead of about 53% and a throughput
regression of about 35% because the observed submit path copies the item into an observation reservation and
retains a normalized record. That overhead is reported honestly under `regression.tap_enabled_observation`
with `gated: false`, and the report does not claim the enabled case satisfies a 2% bound. This is a faithful
reading of the accepted `SC-008` anchor and is stated in the report's `regression.basis` and limitations.

## 3. Changed-path inventory (candidate)

The complete authoritative inventory with SHA-256 hashes is emitted in
`reports/xcom-queue/t036-package.json`. Categories:

- Harness: `engineering/run_xcom_benchmarks.py`.
- Evidence: `reports/xcom-queue/t036-benchmark.json`.
- Work products: `docs/engineering/xcom/t036/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`.
- Requirement/component/unit/validation records: `engineering/requirements/T036-STK-00{1..5}.json`,
  `engineering/requirements/T036-SR-0{01..12}.json`, `engineering/architecture/components/T036-SR-0{01..12}-CMP.json`,
  `engineering/unit-specifications/T036-SR-0{01..12}-U.json`, `engineering/validation/scenarios/T036-VS-ACCUMULATED.json`.
- Governance: `engineering/trace/links.json` (additive), `engineering/project.json`,
  `docs/engineering/xcom/t010/{unit-design.json,design-units.md}` (status field only), `reports/review-index.md`,
  and the one-line T036 checkbox in `specs/007-xcom-core/tasks.md`.

## 4. Benchmark performed (exact candidate)

Commands (portable descriptors):

| # | Command | Purpose | Result |
| --- | --- | --- | --- |
| B-1 | `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | run the controlled benchmark and write the report | exit `0`; the gated SC-008 `tap_disabled`-versus-baseline comparison passes (the enabled case is an ungated observation) |
| B-2 | `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | failure-closed report verification | exit `0`; fields, method, uncertainty, binding, hashes, and samples consistent |
| B-3 | `ctest --test-dir build/f8u -R '^xcom_observation_disabled_benchmark$' --output-on-failure` | accepted disabled-tap fixture context | the accepted fixture reports both thresholds `PASS` |
| B-4 | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | preserved regression suite | `100% tests passed` |

Observed controlled-benchmark results (21 paired samples, 5000 iterations per sample):

| Case | Median latency (ns) | Median throughput (/s) |
| --- | --- | --- |
| `baseline` (pre-observation submit) | 5267.55 | 189841.58 |
| `tap_disabled` (public submit, observation disabled) | 5310.67 | 188300.16 |
| `tap_enabled` (public submit, bounded tap) | 8141.95 | 122820.70 |

- **Gated SC-008 comparison (`tap_disabled` versus `baseline`):** median latency regression
  `0.815%` (`pass`), median throughput regression `0.809%` (`pass`); `regression.outcome = "pass"`.
- **Recorded enabled-tap observation (`tap_enabled` versus `tap_disabled`):** median latency regression
  `53.316%`, median throughput regression `34.775%`, `within_2_percent = false`, `gated = false` (§2.2).
- **Uncertainty:** per-case `n = 21`, median, MAD, min, max, and p95 are retained in the report. The gate is
  applied to the median of the paired per-sample regressions (`0.815%`, within 2%); the raw samples are
  disclosed and are noisy on this shared, uncontrolled host. On this run no disabled sample exceeds the 2%
  threshold (the largest observed per-sample disabled latency regression is sample index 12 at `1.000%`).
  The report retains every raw sample rather than a favourable subset.

### 4.1 Environment and tool identity

| Identity | Value |
| --- | --- |
| Compiler | `g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` |
| C++ standard | C++20, warning-as-error (T012); harness build uses `-Wall -Wextra -Wpedantic -Werror -O2` |
| CMake | `3.22.1` |
| Ninja | `1.10.1` |
| Python | `3.13.13` |
| Admitted toolchain prefix digest | `sha256:48ef3d662d2d2b94a09ef134635f17da223c31f4ca6db5a00503b85fc14d249f` (925 files) |
| Admitted package manifest | `sha256:031c6aecdc4fe0cf4e0dff474d9b161777122142bf9bb1393c25d679807b055c` |
| Admitted GTest prefix digest | `sha256:36eaadd3106a3714266ac67a0b24bce4ef6f2b95b452706f57ca8fea156fddfe` (282 files) |
| Candidate material digest | `sha256:247f3afdabde77afbf712399aa28b825279d1c5ec4390847374d1ce2861bc239` |

The admitted inputs are resolved by environment-variable name only (`XVERSE_XCOM_TOOLCHAIN`,
`XVERSE_XCOM_PACKAGE_MANIFEST`, `XVERSE_XCOM_T025_TEST_TOOLCHAIN`); no host-specific absolute path is
recorded. The admitted-input digests match the accepted T035 environment identity.

### 4.2 Requirement-to-evidence result

| Requirement | Executed case / evidence |
| --- | --- |
| T036-SR-001 | `xcom_observation_disabled_benchmark`; `baseline`/`tap_disabled`/`tap_enabled` samples in the report |
| T036-SR-002 | report `uncertainty` (n, median, MAD, min, max, p95); `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome` |
| T036-SR-003 | report `regression` (SC-008 disabled comparison, `pass`); `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo` |
| T036-SR-004 | report `environment` (identities and admitted-input digests); `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| T036-SR-005 | report `method` and raw `samples`; `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` |
| T036-SR-006 | report `limitations` and uncertainty note; `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| T036-SR-007 | harness local/offline route; `T026JournalRecovery.test_journal_restart_recovery_and_orphans` |
| T036-SR-008 | report `baseline_revision`, `material_digest`, and per-file `hashes` binding plus the `--verify` revision acceptance; `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| T036-SR-009 | `engineering/run_xcom_benchmarks.py --verify`; `XcomToolGatewayBounds.MessageSizeBoundEnforced` |
| T036-SR-010 | baseline-versus-candidate diff; `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| T036-SR-011 | trace/register validation and the Phase 8 gate; `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` |
| T036-SR-012 | public-safety/forbidden-resource inspection; `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` |

## 5. Failure semantics and negative checks

The report binds the exact candidate through the accepted `baseline_revision`, the sorted
`candidate_identity.material_inputs` inventory, the `material_digest`, and the per-file `hashes`; a
committed report records `candidate_revision = null` because it cannot contain the hash of the commit that
contains it. `--verify` accepts exactly two revisions for that binding — `HEAD == baseline_revision` (the
measured working-tree successor) and `HEAD` as the direct child of `baseline_revision` at a distance of
one commit (the committed candidate) — and rejects a foreign or unrelated commit, a merge, and any extra
successor.

`--verify` was exercised against tampered or foreign reports: a missing required field, a stale/foreign
candidate revision (a foreign commit, a merge commit whose first parent is the baseline, or an extra
successor commit), an empty limitations list, a changed artifact hash, a mismatched material digest, a
wrong recorded `candidate_revision`, and a wrong per-case sample count each produce a nonzero exit. A
recorded `pass` whose recomputed regression does not hold is rejected. The harness writes the report
before returning nonzero so that a failed measurement is still retained as honest evidence.

## 6. Public-safety and forbidden-resource inspection

The harness, report, and work products record tool identities, admitted-input digests, the method, bounded
sample values, and hashes only. No verification command opens a TCP listener, creates an
`AF_INET`/`AF_INET6` socket, uses DNS, a resolver, or TLS, contacts an external network peer, executes a
legacy binary or production workload, or makes a runtime, compatibility, performance, or production-readiness
claim beyond the measured evidence. No credential, private address, payload byte, permit content, or
host-specific absolute path enters a committed artifact; the temporary benchmark build and its compile argv
are discarded and are not committed.

## 7. Traceability and governance

- `engineering/trace/links.json` carries the additive T036 `refines`, `allocated_to`, `decomposes_to`,
  `implemented_by`, `verified_by`, and `analyzed_by` links (164 T036 links). The trace validates with 750
  artifacts and 2716 links.
- The T007 ownership register, the T008 register, the T009 architecture model, and the T010 unit design were
  reconciled without rewrite; the only T010 change is the `docs/engineering/xcom/t036/` planned→established
  status field.
- The REF-002 disposition stays `unchanged` with an empty `promoted` list. T036 is recorded implemented;
  T037–T041 remain allocated.
- The T007–T010 register validators, the T011/trace validators, and `git diff --check` over the candidate
  pass.

## 8. Maintenance notes

- Re-run the §4 commands unchanged for any successor candidate; the report is bound to the accepted
  baseline revision and the exact candidate material digest/inventory, so it is not evidence for another
  revision, and `--verify` accepts only the baseline or its direct-child candidate commit.
- A change to `engineering/run_xcom_benchmarks.py`, the T036 records, `engineering/project.json`,
  `engineering/trace/links.json`, `specs/007-xcom-core/tasks.md`, or the T036 work products invalidates the
  recorded material digest and requires re-running B-1 and B-2.
- A change to any accepted source the harness consumes read-only changes the benchmark object and requires a
  fresh controlled benchmark.
- The 7 implementation-stage `implemented_by` links pin the harness SHA-256; a harness edit must refresh
  `engineering/trace/links.json` and the report together.
- The enabled-tap observation (§2.2) is a property of the accepted observation boundary (reservation copy
  plus record retention), not a T036 defect; improving it is an accepted-source change outside T036.

## 9. Limitations

- **L-T036-1** — the harness requires the admitted `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`,
  and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`; it otherwise fails closed before any build. This is an external
  environment prerequisite, not a T036 defect.
- **L-T036-2** — benchmark only; no deployed-service, network, transport, timing, compatibility,
  performance, or production-readiness claim.
- **L-T036-3** — the uncertainty statement records observed dispersion under an uncontrolled shared host; it
  is not a production confidence interval.
- **L-T036-4** — the admitted offline envelope cannot link the gRPC transport runtime (`T032-GAP-01`); the
  workload is the in-process owned loopback and observation boundary only.
- **L-T036-5** — the enabled-tap case is recorded as an observed overhead (about 53.2% median latency) and is
  not gated by the SC-008 disabled-tap 2% threshold; no 2% bound is claimed for the enabled case.
- **L-T036-6** — no Doxygen (T037), traceability-verifier/SADS (T038), external review (T039/T040), or user
  acceptance (T041) result is produced or claimed.

## 10. Maturity

T036 implements the controlled disabled/enabled observation-tap benchmark harness and records its
repository-owned exact-candidate results. The accepted `SC-008` disabled-tap comparison holds
(`0.815%` latency, `0.809%` throughput, i.e. within the 2% threshold). The enabled-tap overhead is recorded honestly as an ungated
observation. The accepted `XCOM-SW-INTG-003`, `XCOM-SW-OBS-003`, `XCOM-SW-CORE-007`, and `XCOM-SW-ENB-*`
requirements remain unchanged accepted text; this slice records its contribution and its explicit
non-production limitations. T037–T041 remain allocated, the REF-002 disposition stays `unchanged` with an
empty `promoted` list, and user acceptance remains T041.

# T036 Verification Plan — Controlled Disabled/Enabled-Tap Benchmarks and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T036 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | plan → verification design |
| Revision | 1 (Phase 8 controlled-benchmark slice) |
| Baseline revision | `8ec69ddd34ed8c7a07adbcb631dcfb2da3faf15f` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Classification | Public-safe engineering work product |

"Verified" means the named command, case, measurement, or inspection exists, is deterministic, and passes
at the recorded candidate revision. It is not a deployed-service, remote-tool, compatibility, performance,
or production-readiness claim.

## 2. Verification environment

- Admitted offline X-COM build envelope (T011): admitted `protoc` 3.12.4, admitted GTest prefix, admitted
  standard library and in-process libraries; no network, DNS, TLS, legacy binary, or production workload.
- C++20, warning-as-error (T012), Ninja build, GoogleTest discovery; Python 3.11 or newer for the
  benchmark harness.
- The accepted disabled-tap benchmark fixture
  (`tests/xcom/observation/integration/disabled_tap_benchmark.cpp`) provides the authoritative
  same-baseline/disabled comparison; T036 adds the enabled-tap case in its own harness.
- Whole-system integration remains the trusted target-repository measure (`run_xcom_phase8_tests.py
  integration`); T036 does not re-run or re-claim it.

## 3. Requirements-to-check matrix

| Requirement | Primary checks | Verification measure / route |
| --- | --- | --- |
| T036-STK-001 | CHK-01…CHK-05 | harness / unit / validation |
| T036-STK-002 | CHK-06…CHK-09 | report inspection |
| T036-STK-003 | CHK-10, CHK-11 | public-safety inspection / validation |
| T036-STK-004 | CHK-12, CHK-13 | harness `--verify` |
| T036-STK-005 | CHK-14, CHK-15, CHK-16 | diff / register / gate |
| T036-SR-001 | CHK-01, CHK-02 | harness / unit |
| T036-SR-002 | CHK-03 | harness / report inspection |
| T036-SR-003 | CHK-04 | harness / report inspection |
| T036-SR-004 | CHK-06, CHK-07 | report inspection |
| T036-SR-005 | CHK-08 | report inspection |
| T036-SR-006 | CHK-05 | report inspection |
| T036-SR-007 | CHK-11 | forbidden-resource inspection |
| T036-SR-008 | CHK-09 | report inspection |
| T036-SR-009 | CHK-12, CHK-13 | harness `--verify` |
| T036-SR-010 | CHK-14 | diff / discovery inspection |
| T036-SR-011 | CHK-15, CHK-16 | trace / register / gate |
| T036-SR-012 | CHK-10, CHK-11 | public-safety / forbidden-resource inspection |

## 4. Named checks

| Check | Description | Requirement |
| --- | --- | --- |
| CHK-01 | the harness measures the disabled (same-baseline) and enabled-tap cases over the same owned loopback workload with a recorded, fixed sample count and warm-up | T036-SR-001 |
| CHK-02 | both cases report median latency and median throughput, and the disabled case reproduces the accepted `xcom_observation_disabled_benchmark` thresholds | T036-SR-001 |
| CHK-03 | the report records a per-case sample count, median, and dispersion/interval, and an explicit non-production note | T036-SR-002 |
| CHK-04 | the report records the gated `tap_disabled`-versus-same-baseline median latency and throughput regression and its 2% SC-008 comparison outcome deterministically, and records the enabled-versus-disabled regression as an ungated observation | T036-SR-003 |
| CHK-05 | the report declares explicit non-production limitations (CPU affinity, scheduler load, DVFS, thermal, cache) and makes no production claim | T036-SR-006 |
| CHK-06 | the report records compiler, C++ standard, CMake, Ninja, Python, admitted toolchain/manifest/GTest-prefix identities and hashes | T036-SR-004 |
| CHK-07 | the public report contains no host-specific absolute prefix, manifest, temporary, or evidence-store path | T036-SR-004 |
| CHK-08 | the report exposes the raw paired samples and the method sufficiently to reproduce the reported statistics | T036-SR-005 |
| CHK-09 | the report is bound to the accepted baseline revision and the exact candidate material (inventory, digest, per-file SHA-256 hashes), records SHA-256 hashes of the retained evidence and referenced artifacts, and `--verify` accepts only the baseline or its direct-child candidate commit | T036-SR-008 |
| CHK-10 | the committed report, harness, work products, and excerpts contain no payload byte, permit content, secret, private address, host path, or proprietary excerpt | T036-SR-012 |
| CHK-11 | no benchmark command uses a TCP listener, `AF_INET`/`AF_INET6` socket, DNS, resolver, TLS, external peer, legacy binary, or production workload | T036-SR-007, T036-SR-012 |
| CHK-12 | `engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` exits nonzero when a required field, the method, or the uncertainty is missing | T036-SR-009 |
| CHK-13 | `--verify` exits nonzero when the report is stale/foreign to the candidate or a 2% threshold is exceeded; it exits `0` only for a consistent passing report | T036-SR-009 |
| CHK-14 | the baseline-versus-candidate diff changes no accepted production source, header, contract, schema, register, XDL profile, or test; the only shared edits are the additive T036 records/harness/report, the additive trace links, `engineering/project.json`, `reports/review-index.md`, the T010 path-status field, and the T036 checkbox (implementation stage) | T036-SR-010 |
| CHK-15 | the T007 ownership register and the T008/T009/T010 models are reconciled without rewrite; REF-002 stays `unchanged` with an empty `promoted` list; T036 is recorded implemented and T037–T041 allocated | T036-SR-011 |
| CHK-16 | `xcom_phase8_gate.py verify T036 <baseline>` passes with the report present, the T036 checkbox marked complete only at implementation, and the T036 unit measure passing | T036-SR-011 |

## 5. Executable route, negative cases, and the exact evidence report

| Step | Command (portable descriptor) | Expected |
| --- | --- | --- |
| B-1 | `python3 engineering/run_xcom_benchmarks.py --report reports/xcom-queue/t036-benchmark.json` | exit `0`; both cases measured; the gated `tap_disabled`-versus-same-baseline 2% comparison holds (the enabled-versus-disabled case is recorded as an ungated observation) |
| B-2 | `python3 engineering/run_xcom_benchmarks.py --verify reports/xcom-queue/t036-benchmark.json` | exit `0`; report fields/method/uncertainty/binding/hashes/samples consistent |
| B-3 | `ctest --test-dir build/f8u -R '^xcom_observation_disabled_benchmark$' --output-on-failure` | accepted fixture reports both thresholds PASS |
| B-4 | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` |

The trusted Phase 8 `validation` measure runs B-2 as part of its route
(`run_xcom_phase8_tests.py`, `mode == "validation" and task == "T036"`), so the task-owned verification
route is exercised by the trusted gate. The candidate-local unit measure (B-4) preserves the accepted
suite.

**Exact evidence report.** `reports/xcom-queue/t036-benchmark.json` is the task-owned evidence report; it
is required to contain `environment`, `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, and
`limitations`, plus the raw `samples`, `method`, and exact-candidate identity (§4 of
`detailed-design.md`). It is generated at the implementation stage from executed measurements; the plan
stage records only the schema and route and does not fabricate results.

**Task-owned route.** The route is the task-owned harness
`engineering/run_xcom_benchmarks.py` invoked by B-1/B-2, over the accepted owned loopback workload. It
adds no accepted CTest target; the selected case set names only already-discovered cases, so the
discovered inventory is unchanged.

### Negative cases (`NEG-###`)

- **NEG-01** — a changed accepted production source, test, target, label, command, or expected value:
  CHK-14 fails closed.
- **NEG-02** — comparing the gated `tap_disabled` case against a different workload, revision, or baseline
  (or recording the enabled-versus-disabled observation against anything other than the identical disabled
  baseline): CHK-01/CHK-04 fail closed.
- **NEG-03** — omitting the sample count, dispersion, or non-production note: CHK-03 fails closed.
- **NEG-04** — a stale, foreign, or mismatched report presented as current: CHK-09/CHK-13 fail closed.
- **NEG-05** — a recorded `pass` whose gated `tap_disabled`-versus-baseline 2% comparison is not satisfied:
  CHK-04/CHK-13 fail closed.
- **NEG-06** — a new accepted test target or a changed accepted expected value: CHK-14 fails closed.
- **NEG-07** — a payload, permit, secret, private address, host path, proprietary excerpt, TCP/`AF_INET`
  socket, DNS, TLS, or legacy/external peer use: CHK-10/CHK-11 fail closed.
- **NEG-08** — a T037/T038/T039/T041 claim or a production-performance claim inside the T036 evidence:
  CHK-05/CHK-15 fail closed.
- **NEG-09** — the T036 checkbox marked at the plan stage, or the required report absent: CHK-16 fails
  closed.
- **NEG-10** — a missing requirement/component/unit/measure/code/validation trace edge: CHK-15 fails
  closed.

## 6. Traceability to the accepted anchors

| T036 check | Accepted anchor |
| --- | --- |
| CHK-01/CHK-02/CHK-03/CHK-04/CHK-05 | `XCOM-SW-INTG-003`; `XCOM-SYS-SC-008`, `XCOM-SYS-FR-008`, `XCOM-SYS-FR-014` |
| CHK-06/CHK-07 | `XCOM-SW-ENB-004`, `XCOM-SW-INTG-001`; `XCOM-SYS-FR-027`, `XCOM-SYS-FR-029` |
| CHK-08 | `XCOM-SW-INTG-003`; `XCOM-SYS-FR-030` |
| CHK-09 | `XCOM-SW-INTG-003`, `XCOM-SW-ENB-004`; `XCOM-SYS-FR-030` |
| CHK-10/CHK-11 | `XCOM-SW-CORE-007`, `XCOM-SW-INTG-001`; `XCOM-SYS-FR-026/027/028` |
| CHK-12/CHK-13 | `XCOM-SW-INTG-003`; `XCOM-SYS-FR-030`, `XCOM-SYS-SC-008` |
| CHK-14 | ADR-0020; `XCOM-SW-INTG-003`; `XCOM-SYS-FR-030`; Constitution X |
| CHK-15/CHK-16 | `XCOM-SW-ENB-001/002`; `XCOM-SYS-FR-030/035`; Constitution VII/IX/X; ADR-0020 |

## 7. Measurement plan and evidence binding

- Every case is bound to the accepted baseline revision and the exact T036 candidate material digest and
  inventory; because a committed report cannot contain the hash of the commit that contains it, the
  candidate commit is the direct child of the baseline carrying that material. `environment`,
  `uncertainty`, `baseline`, `tap_disabled`, `tap_enabled`, `limitations`, raw samples, method, and hashes
  are retained in `reports/xcom-queue/t036-benchmark.json`.
- The trusted policy executes `unit`, `integration`, `validation`, `static_analysis`, `conformance`, and
  `sanitizer`; T036 records the benchmark result and does not replace or weaken them.
- The uncertainty statement is recorded honestly and is not presented as a production confidence interval.
- Any unavailable admitted input, owned fixture, or measurement is recorded as `blocked` with its reason;
  the candidate does not claim a pass (T036-OPEN-04).

## 8. Definition of done (verification view)

T036 is verified for a candidate revision when all CHK-01…CHK-16 hold: the harness measures the disabled
and enabled cases over the same owned loopback workload with recorded samples and uncertainty; the report
carries the required fields and the exact-candidate identity; the gated `tap_disabled`-versus-same-baseline
2% comparison holds and the enabled-versus-disabled regression is honestly recorded as an ungated
observation; `--verify` fails closed on an invalid report; no accepted production byte changes; the
registers stay reconciled with REF-002 `unchanged`; and `xcom_phase8_gate.py verify T036 <baseline>`
passes. User acceptance remains T041.

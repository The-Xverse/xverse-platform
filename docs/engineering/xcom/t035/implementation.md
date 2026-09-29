# T035 Implementation Record — Exact-Candidate Verification Matrix and Repository-Owned Results

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T035 (capability 007, slice `T-INTG`/evidence) |
| Stage / role | implementation |
| Revision | 1 (Phase 8 exact-candidate verification slice) |
| Accepted baseline revision | `dab68568bd8d189b14c7a4a9e3a9c325085a7529` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Verification authority | [`verification-plan.md`](verification-plan.md) rev 1 |
| Candidate material digest | `sha256:67ac5ae0056028bd657db0a6c337d202aee64dc61830f3cae332b5c30425a8ef` |
| Classification | Public-safe engineering work product |

This record describes what the T035 candidate implements and the exact-candidate matrix it executed. It does
not accept or integrate the candidate; explicit user acceptance remains T041 and external Codex review is
deferred until the ordered backlog `xcom-t030-t034-20260928` completes. No T036 benchmark, T037 Doxygen,
T038 traceability-verifier/SADS, T039 review, or T041 acceptance result is produced or claimed.

## 2. Implemented boundary

T035 is an **evidence-only** task. It adds **no production source, no test, and no build target** (`T035-DD-01`).
Its code artifacts are the repository-owned evidence and work products:

- `reports/xcom-queue/t035-verification.json` — the exact-candidate verification evidence report carrying
  `commands`, `outcomes`, `hashes`, `environment`, bounded public-safe logs, and the exact-candidate identity.
- `docs/engineering/xcom/t035/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  — the repository-owned work-product set.
- `engineering/requirements/T035-*.json`, `engineering/architecture/components/T035-*.json`,
  `engineering/unit-specifications/T035-*.json`, `engineering/validation/scenarios/T035-VS-ACCUMULATED.json` —
  the current-task requirement/component/unit/validation records.
- `engineering/verification/measures/{unit,integration,validation,static_analysis}.json` — content-only refresh to
  the Phase 8 route (each `id`, `revision`, and `kind` preserved) — and the new
  `engineering/verification/measures/sanitizer.json`.
- `engineering/trace/links.json` — additive T035 links; `engineering/project.json` — current-task pointer.
- `docs/engineering/xcom/t010/unit-design.json`, `docs/engineering/xcom/t010/design-units.md` — the required
  planned→established path-status reconciliation for `docs/engineering/xcom/t035/` (`XCOM-DU-024`; status only).
- `reports/review-index.md`, `reports/xcom-queue/t035-package.json`, and the one-line T035 checkbox in
  `specs/007-xcom-core/tasks.md`.

No accepted production source, header, contract, schema, register, XDL profile, test, target, label, command, or
expected value was changed.

### 2.1 Design realization notes

- `T035-DD-02` — the executed route is the admitted offline build plus the full CTest suite, a separate
  ASan/UBSan configuration, `cppcheck` over `src/xverse/xcom/src`, the inherited Phase 6 conformance recheck, and
  the existing Python suite (`unit`, `integration`, `validation`, `static_analysis`, `conformance`, `sanitizer`).
- `T035-DD-03` — an outcome is `pass` only when the measure's trusted discovery check is satisfied. The one
  measure whose discovery check is **not** satisfied is recorded as `failed` (conformance, §8).
- `T035-DD-04`/`T035-DD-05` — the report carries the required fields and the exact-candidate identity; it records
  tool/instrument identities and hashes, not host-specific absolute paths.
- `T035-DD-06` — the `engineering/verification/measures/**` descriptors were refreshed content-only; every `id`,
  `revision`, and `kind` is preserved, so no accepted `verified_by`/`analyzed_by` link is staled.
- `T035-DD-07` — only the trusted target-repository integration measure is whole-system integration; the executed
  build/suite runs recorded here are labelled candidate-local.
- `T035-DD-08`/`T035-DD-09` — the trace `implemented_by` edges point at the T035 evidence/work products, and the
  selected case set names only already-discovered CTest IDs (the discovered inventory is unchanged).
- `T035-DD-10` — no successor deliverable is run or claimed.

### 2.2 Recorded environment manipulation (no design change)

The pinned Phase 8 runner `run_xcom_phase8_tests.py` selects build directories named
`build/fabro-t035-t038-system-<mode>`. On this host the resulting absolute scratch path for the T032
separate-process synthetic-client fixture exceeds the Linux `AF_UNIX` `sun_path` limit (108 bytes including the
terminating NUL) for the `integration`, `validation`, and `sanitizer` modes, so those configurations failed
with 14 `XcomSyntheticClient*` errors in the default build root while `unit` passed. This is a host path-length
artifact of the pinned runner, not a candidate behavior change; the accepted Phase 7 runner documents and avoids
exactly this constraint by using the short build directories `build/f7i`/`build/f7v`. T035 therefore executed the
identical pinned commands from a **material-identical short checkout** (a copy of the candidate tree with the same
bytes, excluding the build tree and VCS metadata, placed under a short host temporary prefix) so that the fixture
socket path fits `sun_path`. The candidate bytes, the command argv, and the discovery checks are unchanged. This
is recorded as limitation **L-T035-6** and in `reports/xcom-queue/t035-verification.json` (`diagnostics`). No
accepted production file, test, target, label, command, or expected value was changed to achieve this.

## 3. Changed-path inventory (candidate)

The complete authoritative inventory with SHA-256 hashes is emitted in
`reports/xcom-queue/t035-package.json`. Categories:

- Work products: `docs/engineering/xcom/t035/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`.
- Requirement/component/unit/validation records: `engineering/requirements/T035-STK-00{1..5}.json`,
  `engineering/requirements/T035-SR-0{01..16}.json`, `engineering/architecture/components/T035-SR-0{01..16}-CMP.json`,
  `engineering/unit-specifications/T035-SR-0{01..16}-U.json`, `engineering/validation/scenarios/T035-VS-ACCUMULATED.json`.
- Measure descriptors: `engineering/verification/measures/{unit,integration,validation,static_analysis,sanitizer}.json`.
- Evidence and governance: `reports/xcom-queue/t035-verification.json`, `engineering/trace/links.json` (additive),
  `engineering/project.json`, `docs/engineering/xcom/t010/{unit-design.json,design-units.md}` (status field only),
  `reports/review-index.md`, and the one-line T035 checkbox in `specs/007-xcom-core/tasks.md`.

## 4. Verification performed (exact candidate)

Offline admitted build with the T011 toolchain and the T025 GTest prefix; the full discovered CTest suite is 496
tests. Commands, exit status, bounded logs, and hashes are retained in `reports/xcom-queue/t035-verification.json`.

| Measure | Command (portable descriptor) | Discovery check | Outcome |
| --- | --- | --- | --- |
| unit | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py unit` | `100% tests passed` | pass |
| integration | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py integration` | `100% tests passed` | pass |
| validation | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py validation` | `[1-9][0-9]* passed` | pass |
| sanitizer | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_tests.py sanitizer` | `100% tests passed` | pass |
| static_analysis | `cppcheck --error-exitcode=1 --quiet --std=c++20 --language=c++ --suppress=invalidLifetime src/xverse/xcom/src` | exit `0` | pass |
| conformance | `python3 ${XVERSE_FABRIC_ROOT}/automation/run_xcom_phase8_conformance.py` | `26 conformance inspections passed` | **failed** |
| python | `python3 -m pytest -q` | `[1-9][0-9]* passed` | pass |

Observed results:

- **unit** (candidate root): `100% tests passed, 0 tests failed out of 496`.
- **integration** (short material-identical root): `100% tests passed, 0 tests failed out of 496`; pytest
  `150 passed, 24 subtests passed`.
- **validation** (short material-identical root): `100% tests passed, 0 tests failed out of 496`; pytest
  `150 passed, 24 subtests passed`.
- **sanitizer** (short material-identical root, `-fsanitize=address,undefined`): `100% tests passed, 0 tests
  failed out of 496`.
- **static_analysis**: `cppcheck` exited `0` with no diagnostic output.
- **selected case set**: all 16 named `T035` cases passed (`100% tests passed, 0 tests failed out of 16`).
- **conformance**: `failed` — see §8.

### 4.1 Environment and tool identity

| Identity | Value |
| --- | --- |
| Compiler | `g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` |
| C++ standard | C++20, warning-as-error (T012) |
| CMake | `3.22.1` |
| Ninja | `1.10.1` |
| `cppcheck` | `2.7` |
| Python | `3.13.13` (the admitted runner requires 3.11+) |
| Admitted toolchain prefix digest | `sha256:48ef3d662d2d2b94a09ef134635f17da223c31f4ca6db5a00503b85fc14d249f` (925 files) |
| Admitted package manifest | `sha256:031c6aecdc4fe0cf4e0dff474d9b161777122142bf9bb1393c25d679807b055c` |
| Admitted GTest prefix digest | `sha256:36eaadd3106a3714266ac67a0b24bce4ef6f2b95b452706f57ca8fea156fddfe` (282 files) |
| Trusted Phase 8 policy | `sha256:78c285270a777675a3596878632941b9b5826a3305b59089f9b20a82d89ec32c` |
| Candidate material digest | `sha256:67ac5ae0056028bd657db0a6c337d202aee64dc61830f3cae332b5c30425a8ef` |

### 4.2 Requirement-to-case result

| Requirement | Executed cases (all pass) |
| --- | --- |
| T035-SR-001 | `T033ProviderContractSuite.AcceptedLoopbackProviderConforms` |
| T035-SR-002 | `T034SecondProviderSuite.ReusedProviderContractSuitePasses` |
| T035-SR-003 | `CoreMatrixNegative.Neg09_UnsupportedContractVersion_RejectedBeforeDispatch` |
| T035-SR-004 | `CoreMatrixConcurrency.ConcurrentRepeatedRuns_DeterministicOutcome` |
| T035-SR-005 | `CoreMatrixConcurrency.ConcurrentSubmitReceive_ExactlyOncePerRouteFifo` |
| T035-SR-006 | `T034VersionRejection.RejectionEmitsNothing` |
| T035-SR-007 | `T20OrderingEquivalence.ReorderedDocumentSameOutcomeAndDecodedValue` |
| T035-SR-008 | `Integration.GenerationRotationInvalidatesLiveHandle` |
| T035-SR-009 | `XcomStimulationMatrixConcurrency.ConcurrentQuotaEmissionDeterminism` |
| T035-SR-010 | `T033GatewayContractSuite.AcceptedGatewaySessionConforms` |
| T035-SR-011 | `XcomToolGatewayBounds.MessageSizeBoundEnforced` |
| T035-SR-012 | `T033ObserverContractSuite.AcceptedObservationHubConforms` |
| T035-SR-013 | `T033StimulationToolContractSuite.AcceptedStimulationPathConforms` |
| T035-SR-014 | `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` |
| T035-SR-015 | `CoreMatrixRecovery.Reconcile_MismatchReportsInterruptedResource` |
| T035-SR-016 | `T026JournalRecovery.test_journal_restart_recovery_and_orphans` |

## 5. Generated-code provenance and dependencies

T035 adds **no** generated code and **no** admitted dependency. It does not touch
`proto/xverse/xcom/v1/tool_gateway.proto` or any `XCOM-XLC-002` message and links no transport runtime. The
committed protocol input and the admitted offline generator identity are unchanged from the accepted
T030–T034 records; the admitted envelope still cannot link the gRPC transport runtime (`T032-GAP-01`).

## 6. Public-safety and forbidden-resource inspection

The report and work products record tool identities, command argv, bounded public-safe log excerpts, and hashes
only. Logs were bounded and their absolute host prefixes are excluded (the report references the admitted inputs
by environment-variable name and digest). No verification command opens a TCP listener, creates an
`AF_INET`/`AF_INET6` socket (the T032 fixture is a local `AF_UNIX` endpoint only), uses DNS, a resolver, or TLS,
contacts an external network peer, executes a legacy binary or production workload, or makes a runtime,
compatibility, performance, or production-readiness claim beyond the executed checks.

## 7. Traceability and governance

- `engineering/trace/links.json` carries the additive T035 `refines`, `allocated_to`, `decomposes_to`,
  `implemented_by`, `verified_by`, `analyzed_by`, and `validated_by` links; the inherited trace was extended
  additively only.
- The T007 ownership register, the T008 register, the T009 architecture model, and the T010 unit design were
  reconciled without rewrite; the only T010 change is the `docs/engineering/xcom/t035/` planned→established
  status field.
- The REF-002 disposition stays `unchanged` with an empty `promoted` list. T035 is recorded implemented;
  T036–T041 remain allocated.
- T007–T010 register validators, the T011 dependency preflight, and `git diff --check` over the candidate pass.

## 8. Findings and environment issues

- **E-T035-1 (host `sun_path` limit vs pinned build-directory names) — recorded, not a candidate defect.** The
  pinned Phase 8 runner's default build directories (`build/fabro-t035-t038-system-integration|validation|sanitizer`)
  produce a T032 fixture socket path of 109–111 bytes, exceeding the 108-byte `sun_path` limit, so the 14
  `XcomSyntheticClient*` cases fail in the default root. The same commands at a short material-identical root pass
  all 496 tests. The accepted Phase 7 runner avoids this by using `build/f7i`/`build/f7v`; the Phase 8 runner does
  not. Recommended remediation owner: the Phase 8 runner/policy maintainer (outside the T035 change set). This is
  limitation **L-T035-6**.
- **E-T035-2 (inherited conformance baseline inconsistency) — recorded as a failed measure.** The pinned Phase 6
  conformance governance inspection compares the candidate against `BASELINES[26] = 1f5ebd198c16cf545c5e49a98cfae53a65cf8c4d`
  and requires `docs/engineering/xcom/t007..t009` to be unchanged. Accepted candidates T030 (4dded23), T031
  (e6197c6), and T032 (2fd395e) changed `docs/engineering/xcom/t009/architecture-model.json`, so the inspection
  fails (`accepted t009 work products changed`) at the accepted baseline and therefore for the T035 candidate.
  T035 changes no protected Phase 6 path and did not cause this; the Phase 6 conformance pin is stale with
  respect to the accepted Phase 7 work. Recommended remediation owner: T038/T040 (traceability/acceptance-bundle)
  or the Phase 6 conformance-pin maintainer. This is limitation **L-T035-7** and is the only measure whose trusted
  discovery check is not satisfied.

Both issues are external to the T035 candidate (they reproduce from the accepted baseline and the pinned trusted
inputs). They are recorded honestly; no pass is claimed for the conformance measure.

## 9. Maintenance notes

- Re-run `reports/xcom-queue/t035-verification.json`'s commands unchanged for any successor candidate; the report
  is candidate-bound and is not evidence for another revision.
- A future C++ change must re-run the full matrix; a change to `proto/**`, `src/xverse/xcom/src/**`, or
  `tests/**` invalidates the recorded test/case evidence and the candidate material digest.
- The measure descriptors are content-only; do not bump a descriptor `revision` without reconciling every accepted
  `verified_by`/`analyzed_by` link.
- Phase 8 runner build-directory names should be shortened (mirroring `build/f7i`/`build/f7v`) so the T032
  `AF_UNIX` fixture fits `sun_path` on long host prefixes; that fix belongs to the runner/policy, not to T035.

## 10. Limitations

- **L-T035-1** — verification only; no deployed-service, network, transport, timing, compatibility, performance,
  or production-readiness claim.
- **L-T035-2** — candidate-local vs whole-system: only the trusted target-repository integration measure is
  whole-system integration; the executed build/suite runs here are candidate-local.
- **L-T035-3** — the admitted envelope cannot link the gRPC transport runtime (`T032-GAP-01`); the sanitizer and
  static-analysis measures cover the accepted in-process sources only.
- **L-T035-4** — no benchmark (T036), Doxygen (T037), traceability-verifier/SADS (T038), external review
  (T039/T040), or user acceptance (T041) is produced or claimed.
- **L-T035-5** — the report is produced only at the implementation stage from executed commands; the plan stage
  records the schema and route and does not fabricate results.
- **L-T035-6** — the pinned Phase 8 runner build-directory names exceed the host `AF_UNIX` `sun_path` limit for the
  T032 separate-process fixture in the integration/validation/sanitizer configurations; T035 recorded the
  candidate-local passing runs from a material-identical short checkout and disclosed the default-root failures
  (§2.2, §8, E-T035-1).
- **L-T035-7** — the inherited Phase 6 conformance recheck fails at the accepted baseline because accepted
  T030–T032 changed `docs/engineering/xcom/t009/architecture-model.json` after the pinned Phase 6 baseline; the
  conformance measure is recorded `failed` with its external root cause (§8, E-T035-2).

## 11. Maturity

T035 executes and retains the complete exact-candidate capability-007 verification matrix and its
repository-owned results. The accepted `XCOM-SW-ENB-001`, `XCOM-SW-ENB-004`, and `XCOM-SW-INTG-001` requirements
remain unchanged accepted text; this slice records its contribution and the two external environment/baseline
limitations. T036–T041 remain allocated, the REF-002 disposition stays `unchanged` with an empty `promoted` list,
and user acceptance remains T041.

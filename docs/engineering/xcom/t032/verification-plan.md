# T032 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T032 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (separate-process synthetic-client conformance slice) |
| Baseline revision | `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope and the T012 subtree build contract, plus the repository-owned Phase 7 gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the stated
expected result. Weakening an expected result is a verification-contract change requiring review. T032's executable
checks are five new GoogleTest executables under `tests/xcom/tool_gateway/`, the owned separate-process fixture
`xverse_xcom_synthetic_client`, the unchanged existing suites that prove additivity, and the source/interface
inspections; the governance checks are the deterministic Phase 7 gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_phase7_gate.py verify T032 e6197c67868213ffb6523d8bf62ed4c2c4e3b0af
```

For T032 this gate requires:

- the work products
  `docs/engineering/xcom/t032/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T032 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan stage
  leaves it unchecked);
- at least one changed path under `tests/` (satisfied by the `t032-` suites; the additive `src/xverse/xcom/` fixture
  and build wiring also change);
- the Phase 7 runner's unit mode (`run_xcom_phase7_tests.py unit`) to configure, build, and discover at least one
  `t032-`-labelled case, with the `t032-`-labelled suite green;
- `git diff --check e6197c67868213ffb6523d8bf62ed4c2c4e3b0af --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted for
T012–T031, if the plain configure fails closed at the T025 test-toolchain admission check, the only permitted
resolution is the narrow A-1 cache seeding already recorded by those slices: one configure carrying
`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously
admitted cache values seeds the gate's own git-ignored `build/fabro-t030-t034-system-unit` cache; the gate's
unmodified configure/build/`ctest` sequence then reuses it. The hash-verified preflight is unchanged, no ambient path
or network resolution is added, no admission check is weakened, and the admitted input **values** are recorded by
name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse e6197c67868213ffb6523d8bf62ed4c2c4e3b0af
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only e6197c67868213ffb6523d8bf62ed4c2c4e3b0af --
git diff --check e6197c67868213ffb6523d8bf62ed4c2c4e3b0af --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t030-t034-system-unit -N -L t032-
ctest --test-dir build/fabro-t030-t034-system-unit -L t032- --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -L "t0(3[0-2]|2[6-9])-" --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -R xcom_build_contract --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with the shared
T007–T010 artifacts unchanged in substance apart from the status-only planned→established path reconciliation. Every
pre-existing suite must pass unchanged, proving additivity. Executed sanitizer/static-analysis/Doxygen/benchmark
measures and the delivery bundle remain with T035–T040; this plan requires the T032 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T032 entry exists and states the separate-process synthetic-client scope |
| CHK-02 | Changed-path boundary and additivity | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §7.1 paths appear; no accepted predecessor byte under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..31}/` changes other than the additive `CMakeLists.txt` wiring and the status-only path reconciliation; no other task's path |
| CHK-03 | Single client boundary, envelope decision, and documentation | inspect `synthetic_tool.cpp` | exactly one fixture realizes the T030 generated messages/methods; no competing contract/RPC/configuration language; no admitted dependency and no claimed gRPC-runtime link; `T032-GAP-01` recorded; the `xcom_gw` file block and public tags are present |
| CHK-04 | Generated operation surface | run `T32-TS-014` | the committed client operation table equals the generated `ToolGateway` service descriptor method set in order |
| CHK-05 | Separate-process launch and environment hygiene | inspect the launcher; run `T32-TS-001` | the client runs as its own process with an explicit bounded argv and a scrubbed admitted environment; the exchange is repeatable and bounded |
| CHK-06 | Local-only host-protected transport | run `T32-TS-015`, `T32-TS-019`; inspect the connect seam | the transport is `AF_UNIX` only; no `AF_INET`/`AF_INET6`, DNS, resolver, or TLS; the runtime family is `AF_UNIX` |
| CHK-07 | Observation open | run `T32-TS-002` | `OpenObservation` grants a bounded stream identity through the local endpoint |
| CHK-08 | Observation read metadata-only bounded | run `T32-TS-003` | a read returns at most the granted record count before the deadline; records are metadata-only |
| CHK-09 | Observation close counters | run `T32-TS-004` | `CloseObservation` returns bounded delivered/dropped counters |
| CHK-10 | Observed emitted traffic | run `T32-TS-005` | an emitted stimulation item is observed once as a metadata-only record |
| CHK-11 | Four allowed stimulation actions and provenance | run `T32-TS-006`…`T32-TS-009` | each allowed action routes through the accepted guard/journal/action path, observes an emitted outcome, and keeps persistent synthetic provenance |
| CHK-12 | Service-emulation lease round trip | run `T32-TS-010` | the lease is exclusive and generation-bound; acquire/release are observed without ambiguous ownership |
| CHK-13 | Invalid/expired zero emission | run `T32-TS-016`, `T32-TS-017` | an invalid or expired session emits zero normal-route items and reports a non-success outcome |
| CHK-14 | Fail-closed version rejection | run `T32-TS-018` | an unsupported major is rejected before any other operation and emits no item |
| CHK-15 | Explicit client bounds | run `T32-TS-020`, `T32-TS-021`; inspect the config | every client bound is explicit; an over-bound message or deadline is rejected before dispatch |
| CHK-16 | Deterministic failure semantics | run `T32-TS-017`, `T32-TS-022` | failure/timeout/expiry report stable non-success outcomes; an unknown outcome is never success |
| CHK-17 | Safe evidence boundary | run `T32-TS-011`; inspect committed evidence | no result line, log record, or committed file contains a payload byte, permit content, secret, private address, or host path |
| CHK-18 | Generated message fidelity | run `T32-TS-012`, `T32-TS-013` | a generated message round-trips through the client unchanged; an unknown field survives the round trip |
| CHK-19 | Additive build wiring and inventory | `ctest -N` comparison; inspect `XVERSE_XCOM_RUNTIME_TARGETS` | exactly one additive fixture executable and five `t032-<kind>` test targets; the runtime-target inventory is unchanged; every existing target/test name/label/command and the discovered existing count are preserved |
| CHK-20 | Offline, local-only, no new dependency | forbidden-API source scan; successful offline configure/build; inspect the link line | no network/`AF_INET`/DNS/TLS, ambient/secret lookup, dynamic-load, legacy, or external-peer access; only the admitted generated messages, accepted in-process libraries, and GTest are linked; no new admitted dependency; the gRPC runtime is not linked |
| CHK-21 | Registers, REF-002, and maturity honesty | run the §3 validators; inspect the recorded maturity | validators pass; the T009/T010 path reconciliation is status-only; `ref002.disposition == unchanged` with an empty `promoted` list; `XCOM-SW-GW-003` recorded implemented for the conformance-client slice by T032, T033–T041 remain allocated |
| CHK-22 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `t032-` discovered count; the diff is whitespace-clean; the only capability-document change is the T032 checkbox line, marked complete **only** at the implementation stage; the inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` provenance digests are refreshed and consistent |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no partial value,
no emitted normal-route item, and no output claiming success. NEG-01…NEG-10 are executable or source-inspection cases
realized by the named checks and the case assertions; NEG-10 is the additivity/stage repository probe.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | bind/contact a TCP/`AF_INET`/`AF_INET6` socket, use DNS/resolver/TLS, contact an external peer, or launch a legacy binary/production workload | CHK-05/CHK-06/CHK-20 fail; the launch, endpoint, and forbidden-API cases fail closed |
| NEG-02 | define a competing client interface, reject a T030 method, or claim a linked gRPC runtime | CHK-03/CHK-04 fail |
| NEG-03 | let local transport access substitute for the permit, or omit the permit | CHK-11/CHK-13 fail |
| NEG-04 | report an unknown/expired outcome as success, or emit an item from an invalid/expired session | CHK-11/CHK-13/CHK-16 fail |
| NEG-05 | implement an implicit or unsupported version acceptance instead of the fail-closed rule | CHK-14 fails |
| NEG-06 | omit a client bound, decide on ambient wall-clock time, or reject after dispatch | CHK-15/CHK-16/CHK-19 fail |
| NEG-07 | add an admitted dependency or link the gRPC runtime | CHK-20 fails |
| NEG-08 | log a payload, permit content, secret, private address, or host path | CHK-17/CHK-21 fail |
| NEG-09 | weaken an accepted requirement/test/register, or promote a REF-002 target | CHK-21 fails |
| NEG-10 | change a non-T032 path, mark the checkbox in the plan stage, change no `tests/` path, make the T032 suite the T033 abstraction, add a second provider, or skip the inherited provenance refresh | CHK-02/CHK-19/CHK-22 fail; the candidate exceeds the T032 boundary or stage scope |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline `e6197c67868213ffb6523d8bf62ed4c2c4e3b0af`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting command;
- the configure/build/CTest results, including the `ctest -N` discovered counts (five `t032-<kind>` suites, the
  `t032-` case count, and the preserved existing count) and the `100% tests passed` line;
- the per-case results for `xverse_xcom_synthetic_client_{observation,stimulation,contract,negative,bounds}_tests`,
  plus the unchanged preserved suites that prove additivity;
- the separation evidence: the bounded argv, the scrubbed environment, and the child exit status;
- the operation-surface evidence: the committed client operation table and the generated `ToolGateway` descriptor
  method set;
- the observation evidence: the bounded record count, the metadata-only marker, and the delivered/dropped counters;
- the stimulation evidence: the emitted outcome, the emission count, and the persistent synthetic provenance per
  allowed action;
- the lease evidence: the acquire/release lease state;
- the bounds/deadline/timeout evidence: every declared client bound value and the over-bound/timeout result per case;
- the local-IPC evidence: the `AF_UNIX` connect, the runtime family assertion, the socket-file permissions, and the
  forbidden-API scan result;
- the generated-contract evidence: the round-trip result and the unknown-field preservation result;
- the safe-evidence inspection: the captured result/log record set and the absence of payload/permit/secret/private
  address/host path;
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t032-package.json` with per-file SHA-256;
- the register-validator results, the status-only path reconciliation, the unchanged REF-002 disposition, and the
  recorded `XCOM-SW-GW-003` implemented disposition;
- the inherited provenance refresh evidence (`engineering/trace/links.json` and `engineering/stage-results/*.json`
  digests).

Public evidence omits host-specific, prefix, manifest, test-toolchain, scratch, temporary, and private-store absolute
paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T032 verification is complete when: the deterministic gate passes (CHK-22); every nominal check in §4 has its
expected result; every negative case in §5 fails closed as stated; the separate-process synthetic client runs as its
own process over a host-protected no-TCP local endpoint; observation and every allowed stimulation action complete
through the client; invalid/expired sessions emit zero items; the generated message contract round-trips and preserves
an unknown field; the explicit client bounds and deterministic failure semantics are proven; `XCOM-SW-GW-003` is
recorded implemented for the conformance-client slice while T033–T041 remain allocated; the gRPC transport gap is
recorded and no new dependency is added; no accepted requirement, test, ADR, contract, register, or predecessor byte
is weakened; the register validators still pass with REF-002 unchanged and nothing promoted; and a separate DeepSeek
internal review records a passing verdict with no unresolved blocking finding. This does not constitute user
acceptance, which remains T041; external Codex review and acceptance are deferred until the ordered backlog
`xcom-t030-t034-20260928` completes.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T032-STK-001 | CHK-01, CHK-03, CHK-05 | CHK-22 |
| T032-STK-002 | CHK-05, CHK-06 | NEG-01 |
| T032-STK-003 | CHK-13 | NEG-03, NEG-04 |
| T032-STK-004 | CHK-18 | NEG-02 |
| T032-STK-005 | CHK-21, CHK-22 | NEG-09, NEG-10 |
| T032-SR-001 | CHK-03, CHK-04 | NEG-02 |
| T032-SR-002 | CHK-04 | NEG-02 |
| T032-SR-003 | CHK-05, CHK-20 | NEG-01 |
| T032-SR-004 | CHK-06, CHK-20 | NEG-01 |
| T032-SR-005 | CHK-07, CHK-08, CHK-09 | NEG-06 |
| T032-SR-006 | CHK-10 | NEG-04 |
| T032-SR-007 | CHK-11 | NEG-03, NEG-04 |
| T032-SR-008 | CHK-12 | NEG-03 |
| T032-SR-009 | CHK-13 | NEG-03, NEG-04 |
| T032-SR-010 | CHK-14 | NEG-05 |
| T032-SR-011 | CHK-15 | NEG-06 |
| T032-SR-012 | CHK-16 | NEG-04 |
| T032-SR-013 | CHK-17 | NEG-08 |
| T032-SR-014 | CHK-05 | NEG-06 |
| T032-SR-015 | CHK-18 | NEG-02 |
| T032-SR-016 | CHK-19 | NEG-06, NEG-10 |
| T032-SR-017 | CHK-20 | NEG-01, NEG-07 |
| T032-SR-018 | CHK-21 | NEG-09 |
| T032-SR-019 | CHK-22 | NEG-10 |
| T032-SR-020 | CHK-02, CHK-19 | NEG-10 |
| T032-SR-021 | CHK-03 | NEG-02 |

No requirement is left without at least one check, and no check claims acceptance.

### 8.1 Whole-system integration trace linkage

Every accepted T032 software requirement must carry a `verified_by -> integration` trace edge to the project
whole-system integration measure `engineering/verification/measures/integration.json` at the implementation stage.
That measure is executed by the trusted `run_xcom_phase7_tests.py integration` command, which assembles the candidate
into the pinned target checkout, builds the complete platform, and runs the `t032-`-labelled CTest cases plus the full
pytest suite. The measure declares the T032 integration subset (the `t032-` cases and the preserved T026–T031 cases it
exercises). The plan stage records this requirement; the implementation stage adds the exact link IDs and refreshes
the measure, following the T030/T031 precedent where a missing edge caused a delivery finding.

## 9. T-CORE slice evidence mapping (T007 register)

The T007 ownership register requires ten evidence names for the whole `T-CORE` slice (T012–T016, T030–T034). T032
contributes the separate-process conformance evidence and leaves the rest to their owning tasks.

| Slice evidence | T032 contribution | Owning check/case |
| --- | --- | --- |
| `contract` | separate-process realization of the T030 generated message/method contract over the accepted local IPC | CHK-03, CHK-04, CHK-18; `T32-TS-012`…`T32-TS-014` |
| `negative` | over-bound, expired, unauthorized, unsupported-version, TCP/DNS/TLS, and forbidden-API rejections | CHK-06, CHK-13…CHK-20; `T32-TS-015`…`T32-TS-022` |
| `unit` | five additive synthetic-client suites plus the owned fixture executable | CHK-19; `T32-TS-001`…`T32-TS-022` |
| `version-rejection` | fail-closed unsupported-major rejection observed by the separate-process client | CHK-14; `T32-TS-018` |
| `no-tcp-listener` | client-side `AF_UNIX`-only connect and runtime no-TCP proof | CHK-06; `T32-TS-015`, `T32-TS-019` |
| `queue-bound` | bounded observation record count and bounded in-flight framing | CHK-08, CHK-15; `T32-TS-003`, `T32-TS-020` |
| `recovery` | timeout/disconnect-after-intent reports a stable non-success outcome | CHK-16; `T32-TS-017`, `T32-TS-022` |
| `deterministic-diagnostics` | stable client outcome codes under bounds, deadline, and timeout | CHK-15, CHK-16; `T32-TS-021`, `T32-TS-022` |
| `later-integration-run` | not claimed here | T035 |
| `second-provider-replaceability` | not claimed here | T034 |

No evidence name above is claimed beyond what its own exact-candidate evidence shows. The reusable contract suites and
the second provider remain T033/T034.

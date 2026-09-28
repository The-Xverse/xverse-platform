# T031 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T031 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (local-IPC gateway session slice) |
| Baseline revision | `4dded2317f895978cce0331ae88e34ac28b3a609` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope and the T012 subtree build contract, plus the repository-owned Phase 7 gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the stated
expected result. Weakening an expected result is a verification-contract change requiring review. T031's executable
checks are six new GoogleTest executables under `tests/xcom/tool_gateway/`, the unchanged existing suites that prove
additivity, and the source/interface inspections; the governance checks are the deterministic Phase 7 gate and the
T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_phase7_gate.py verify T031 4dded2317f895978cce0331ae88e34ac28b3a609
```

For T031 this gate requires:

- the work products
  `docs/engineering/xcom/t031/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T031 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan stage
  leaves it unchecked);
- at least one changed path under `src/xverse/xcom/` and at least one changed path under `tests/` (satisfied by the
  gateway library wiring and the gateway suites);
- the Phase 7 runner's unit mode (`run_xcom_phase7_tests.py unit`) to configure, build, and discover at least one
  `t031-`-labelled case, with the `t031-`-labelled suite green;
- `git diff --check 4dded2317f895978cce0331ae88e34ac28b3a609 --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted for
T012–T030, if the plain configure fails closed at the T025 test-toolchain admission check, the only permitted
resolution is the narrow A-1 cache seeding already recorded by those slices: one configure carrying
`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously
admitted cache values seeds the gate's own git-ignored `build/fabro-t030-t034-system-unit` cache; the gate's
unmodified configure/build/`ctest` sequence then reuses it. The hash-verified preflight is unchanged, no ambient path
or network resolution is added, no admission check is weakened, and the admitted input **values** are recorded by
name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 4dded2317f895978cce0331ae88e34ac28b3a609
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 4dded2317f895978cce0331ae88e34ac28b3a609 --
git diff --check 4dded2317f895978cce0331ae88e34ac28b3a609 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t030-t034-system-unit -N -L t031-
ctest --test-dir build/fabro-t030-t034-system-unit -L t031- --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -L "t0(3[01]|2[6-9])-" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with the shared
T007–T010 artifacts unchanged in substance apart from the status-only planned→established path reconciliation. Every
pre-existing suite must pass unchanged, proving additivity. Executed sanitizer/static-analysis/Doxygen/benchmark
measures and the delivery bundle remain with T035–T040; this plan requires the T031 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T031 entry exists and states the local-IPC gateway scope |
| CHK-02 | Changed-path boundary and additivity | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §7.1 paths appear; no accepted predecessor byte under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..30}/` changes other than the additive `CMakeLists.txt` wiring and the status-only path reconciliation; no other task's path |
| CHK-03 | Single gateway interface and envelope decision | inspect `tool_gateway.hpp`/`.cpp` | exactly one gateway interface realizes the T030 messages/methods; no competing contract, RPC, or configuration language; no admitted dependency and no claimed gRPC-runtime link; `T031-GAP-01` recorded |
| CHK-04 | Complete operation surface | run `T31-TS-003` | `gateway_operation_names()` equals the T030 descriptor method set in order |
| CHK-05 | Fail-closed version negotiation | run `T31-TS-001`, `T31-TS-002`, `T31-TS-020` | the supported major (and a higher minor) is accepted; any other major is rejected before any other operation |
| CHK-06 | Exact permit enforcement | run `T31-TS-004`, `T31-TS-019`, `T31-TS-021` | an exact permit succeeds; a missing/expired/mismatched permit is rejected with zero emitted items; transport access does not authorize |
| CHK-07 | Explicit bounds | run `T31-TS-007`, `T31-TS-018` | every bound is an explicit config value; an over-bound frame/payload is rejected before allocation or emission |
| CHK-08 | Per-request deadlines | run `T31-TS-008` | a request over `max_deadline_millis` is rejected; an overdue request returns a deterministic diagnostic and emits no item; no ambient wall clock is used |
| CHK-09 | Bounded flow control | run `T31-TS-009`, `T31-TS-010` | the in-flight queue never exceeds its bound; saturation rejects deterministically and is counted; memory/blocking stay bounded |
| CHK-10 | Local IPC only, no TCP listener | run `T31-TS-015`, `T31-TS-016`; inspect the bind path | the endpoint binds `AF_UNIX` only; no `AF_INET`/`AF_INET6`, DNS, resolver, or TLS; the runtime family is `AF_UNIX` |
| CHK-11 | Host-protected endpoint | run `T31-TS-017`, `T31-TS-021` | the socket lives under a restricted directory with restrictive permissions; transport access is not authorization |
| CHK-12 | Observation stream bounds | run `T31-TS-010`, `T31-TS-011` | a read returns at most the granted record count before the deadline; records are metadata-only by default; close returns bounded counters |
| CHK-13 | Observation mapping | inspect the open/read/close handlers; run `T31-TS-010` | every observation operation delegates to the accepted bounded observation boundary |
| CHK-14 | Stimulation submission | run `T31-TS-008`, `T31-TS-018`, `T31-TS-019` | all four allowed actions route through the accepted guard/journal/action path; accepted items carry synthetic provenance; rejection emits zero items |
| CHK-15 | Service-emulation lease | run `T31-TS-012`, `T31-TS-021` | the lease is exclusive and generation-bound; conflict is reported without ambiguous ownership |
| CHK-16 | Disconnect/expiry cleanup | run `T31-TS-011`, `T31-TS-012`, `T31-TS-013`, `T31-TS-014` | observation handles close; validation resources drain/revoke/release/quarantine; pending requests end explicit; unknown is never success |
| CHK-17 | Safe log boundary | run `T31-TS-023`, `T31-TS-024` | no log record contains a payload byte or permit content; records carry code/phase/identity/size/timing/outcome only |
| CHK-18 | Session outcome/counter query | run `T31-TS-006` | counters are finite and include an evidence-incomplete count; no dashboard/storage/query-presentation/export primitive |
| CHK-19 | Additive build wiring and inventory | `ctest -N` comparison; inspect `XVERSE_XCOM_RUNTIME_TARGETS` | exactly one runtime-target addition (`xverse_xcom_tool_gateway`) and six `t031-<kind>` test targets; every existing target/test name/label/command and the discovered existing count are preserved |
| CHK-20 | Offline, local-only, no new dependency | forbidden-API source scan; successful offline configure/build; inspect the link line | no network/`AF_INET`/DNS/TLS, ambient/secret lookup, dynamic-load, subprocess, or legacy access; only the admitted generated messages, accepted in-process libraries, and GTest are linked; no new admitted dependency; the gRPC runtime is not linked |
| CHK-21 | Registers, REF-002, and maturity honesty | run the §3 validators; inspect the recorded maturity | validators pass; the T009/T010 path reconciliation is status-only; `ref002.disposition == unchanged` with an empty `promoted` list; `XCOM-SW-GW-002` recorded implemented for the gateway slice by T031, `XCOM-SW-GW-003` and T032–T041 remain allocated |
| CHK-22 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `t031-` discovered count; the diff is whitespace-clean; the only capability-document change is the T031 checkbox line, marked complete **only** at the implementation stage; the inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` provenance digests are refreshed and consistent |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no partial
value, no emitted normal-route item, and no output claiming success. NEG-01…NEG-10 are executable or source-
inspection cases realized by the named checks and the case assertions; NEG-10 is the additivity/stage repository
probe.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | bind a TCP/`AF_INET`/`AF_INET6` socket, or use DNS, resolver, or TLS, or contact an external peer | CHK-10/CHK-20 fail; the endpoint and forbidden-API tests fail closed |
| NEG-02 | define a competing gateway interface, reject a T030 method, or claim a linked gRPC runtime | CHK-03/CHK-04 fail |
| NEG-03 | let local transport access bypass the permit, or omit the permit from a session/stimulation/lease | CHK-06/CHK-11 fail |
| NEG-04 | report an unknown/expired outcome as success, or fail to clean up on disconnect/expiry | CHK-14/CHK-16 fail |
| NEG-05 | implement an implicit or unsupported version acceptance instead of the fail-closed rule | CHK-05 fails |
| NEG-06 | omit a bound, decide on ambient wall-clock time, reject after allocation/emission, or grow an unbounded queue | CHK-07/CHK-08/CHK-09 fail |
| NEG-07 | add an admitted dependency or link the gRPC runtime | CHK-20 fails |
| NEG-08 | log a payload byte, permit content, secret, private address, or host path | CHK-17/CHK-21 fail |
| NEG-09 | weaken an accepted requirement/test/register, or promote a REF-002 target | CHK-21 fails |
| NEG-10 | change a non-T031 path, mark the checkbox in the plan stage, change no `tests/` or `src/xverse/xcom/` path, or skip the inherited provenance refresh | CHK-02/CHK-22 fail; the candidate exceeds the T031 boundary or stage scope |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline `4dded2317f895978cce0331ae88e34ac28b3a609`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting command;
- the configure/build/CTest results, including the `ctest -N` discovered counts (six `t031-<kind>` suites, the
  `t031-` case count, and the preserved existing count) and the `100% tests passed` line;
- the per-case results for `xverse_xcom_tool_gateway_{session,bounds,lifecycle,local_ipc,negative,logging}_tests`,
  plus the unchanged preserved suites that prove additivity;
- the operation-surface evidence: `gateway_operation_names()` and the T030 descriptor method set;
- the version-negotiation evidence: the predicate verdict per tested major and minor;
- the bounds evidence: every declared bound value and the over-bound rejection result per case;
- the deadline/flow-control evidence: saturation counters, the bounded queue maximum, and the deadline verdict;
- the local-IPC evidence: the `AF_UNIX` bind, the runtime family assertion, the socket-file permissions, and the
  forbidden-API scan result;
- the cleanup evidence: the post-disconnect/idle snapshot and the explicit pending-request outcome per case;
- the safe-log evidence: the captured log record set and the absence of payload/permit content;
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t031-package.json` with per-file SHA-256;
- the register-validator results, the status-only path reconciliation, the unchanged REF-002 disposition, and the
  recorded `XCOM-SW-GW-002` implemented disposition;
- the inherited provenance refresh evidence (`engineering/trace/links.json` and `engineering/stage-results/*.json`
  digests).

Public evidence omits host-specific, prefix, manifest, test-toolchain, scratch, temporary, and private-store absolute
paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T031 verification is complete when: the deterministic gate passes (CHK-22); every nominal check in §4 has its
expected result; every negative case in §5 fails closed as stated; the bounded local-IPC-only gateway, complete
operation surface, fail-closed version negotiation, exact permit enforcement, explicit bounds, per-request
deadlines, bounded flow control, host-protected no-TCP local IPC, disconnect/expiry cleanup, and safe logs are
proven; `XCOM-SW-GW-002` is recorded implemented for the gateway slice while `XCOM-SW-GW-003` and T032–T041 remain
allocated; the gRPC transport gap is recorded and no new dependency is added; no accepted requirement, test, ADR,
contract, register, or predecessor byte is weakened; the register validators still pass with REF-002 unchanged and
nothing promoted; and a separate DeepSeek internal review records a passing verdict with no unresolved blocking
finding. This does not constitute user acceptance, which remains T041; external Codex review and acceptance are
deferred until the ordered backlog `xcom-t030-t034-20260928` completes.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T031-STK-001 | CHK-01, CHK-03, CHK-10 | CHK-22 |
| T031-STK-002 | CHK-06, CHK-11 | NEG-03 |
| T031-STK-003 | CHK-07, CHK-08, CHK-09, CHK-12 | NEG-06 |
| T031-STK-004 | CHK-16, CHK-17 | NEG-04, NEG-08 |
| T031-STK-005 | CHK-21, CHK-22 | NEG-09, NEG-10 |
| T031-SR-001 | CHK-01, CHK-03 | NEG-02 |
| T031-SR-002 | CHK-04 | NEG-02 |
| T031-SR-003 | CHK-05 | NEG-05 |
| T031-SR-004 | CHK-06 | NEG-03 |
| T031-SR-005 | CHK-07, CHK-12 | NEG-06 |
| T031-SR-006 | CHK-08 | NEG-06 |
| T031-SR-007 | CHK-09, CHK-12 | NEG-06 |
| T031-SR-008 | CHK-10, CHK-20 | NEG-01 |
| T031-SR-009 | CHK-11 | NEG-03 |
| T031-SR-010 | CHK-12, CHK-13 | NEG-06 |
| T031-SR-011 | CHK-14 | NEG-03, NEG-04 |
| T031-SR-012 | CHK-15 | NEG-03 |
| T031-SR-013 | CHK-16 | NEG-04 |
| T031-SR-014 | CHK-17 | NEG-08 |
| T031-SR-015 | CHK-18 | NEG-04 |
| T031-SR-016 | CHK-09, CHK-19 | NEG-06 |
| T031-SR-017 | CHK-19 | NEG-06, NEG-10 |
| T031-SR-018 | CHK-20 | NEG-01, NEG-07 |
| T031-SR-019 | CHK-21 | NEG-09 |
| T031-SR-020 | CHK-22 | NEG-10 |
| T031-SR-021 | CHK-03, CHK-04, CHK-20 | NEG-01, NEG-02, NEG-07 |

No requirement is left without at least one check, and no check claims acceptance.

### 8.1 Whole-system integration trace linkage

Every accepted T031 software requirement must carry a `verified_by -> integration` trace edge to the project
whole-system integration measure `engineering/verification/measures/integration.json` at the implementation stage.
That measure is executed by the trusted `run_xcom_phase7_tests.py integration` command, which assembles the
candidate into the pinned target checkout, builds the complete platform, and runs the `t031-`-labelled CTest cases
plus the full pytest suite. The measure declares the T031 integration subset (the `t031-` cases and the preserved
T026–T030 cases it exercises). The plan stage records this requirement; the implementation stage adds the exact link
IDs and refreshes the measure, following the T030 precedent where a missing edge caused a delivery finding.

## 9. T-CORE slice evidence mapping (T007 register)

The T007 ownership register requires ten evidence names for the whole `T-CORE` slice (T012–T016, T030–T034). T031
contributes the gateway-side evidence and leaves the rest to their owning tasks.

| Slice evidence | T031 contribution | Owning check/case |
| --- | --- | --- |
| `contract` | gateway realization of the T030 message/method contract over bounded local IPC | CHK-03, CHK-04; `T31-TS-003` |
| `negative` | over-bound, expired, unauthorized, unsupported-version, TCP/DNS/TLS, and payload-log rejections | CHK-05…CHK-20; `T31-TS-018`…`T31-TS-022` |
| `unit` | six additive gateway suites | CHK-19; `T31-TS-001`…`T31-TS-024` |
| `version-rejection` | production fail-closed unsupported-major predicate | CHK-05; `T31-TS-001`, `T31-TS-002`, `T31-TS-020` |
| `no-tcp-listener` | gateway-side `AF_UNIX`-only endpoint and runtime no-TCP proof | CHK-10; `T31-TS-015`, `T31-TS-016`, `T31-TS-022` |
| `queue-bound` | bounded in-flight request queue and observation record queue | CHK-09, CHK-12; `T31-TS-009`, `T31-TS-010` |
| `recovery` | disconnect/expiry cleanup with explicit incomplete/failed outcomes | CHK-16; `T31-TS-011`…`T31-TS-014` |
| `deterministic-diagnostics` | stable gateway outcome/phase/diagnostic vocabulary under deadlines and saturation | CHK-08, CHK-17; `T31-TS-008`, `T31-TS-023` |
| `later-integration-run` | not claimed here | T035 |
| `second-provider-replaceability` | not claimed here | T034 |

No evidence name above is claimed beyond what its own exact-candidate evidence shows. The separate-process client,
the reusable contract suites, and the second provider remain T032–T034.

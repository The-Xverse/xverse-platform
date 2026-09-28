# T030 Verification Plan — Named Checks, Commands, Negative Cases, and Evidence (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T030 (capability 007, slice `T-CORE`/GW) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 (versioned external-tool contract slice) |
| Baseline revision | `80c236638e160c5e991e5a537e29d407e7462dc6` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope and the T012 subtree build contract, plus the repository-owned Phase 7 gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the stated
expected result. Weakening an expected result is a verification-contract change requiring review. T030's executable
checks are four new GoogleTest executables under `tests/xcom/tool_gateway/` over the generated contract, the
unchanged existing suites that prove additivity, and the source/provenance inspections; the governance checks are the
deterministic Phase 7 gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 ${XVERSE_FABRIC_ROOT}/automation/xcom_phase7_gate.py verify T030 80c236638e160c5e991e5a537e29d407e7462dc6
```

For T030 this gate requires:

- the work products
  `docs/engineering/xcom/t030/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T030 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan stage
  leaves it unchecked);
- `proto/xverse/xcom/v1/tool_gateway.proto` changed and at least one changed path under `tests/` (satisfied by the
  generated contract suites);
- the Phase 7 runner's unit mode
  (`run_xcom_phase7_tests.py unit`) to configure, build, and discover at least one `t030-`-labelled case, with the
  `t030-`-labelled suite green;
- `git diff --check 80c236638e160c5e991e5a537e29d407e7462dc6 --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the admitted offline inputs. As accepted for
T012–T029, if the plain configure fails closed at the T025 test-toolchain admission check, the only permitted
resolution is the narrow A-1 cache seeding already recorded by those slices: one configure carrying
`XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously
admitted cache values seeds the gate's own git-ignored `build/fabro-t030-t034-system-unit` cache; the gate's
unmodified configure/build/`ctest` sequence then reuses it. The hash-verified preflight is unchanged, no ambient path
or network resolution is added, no admission check is weakened, and the admitted input **values** are recorded by name
only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 80c236638e160c5e991e5a537e29d407e7462dc6
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 80c236638e160c5e991e5a537e29d407e7462dc6 --
git diff --check 80c236638e160c5e991e5a537e29d407e7462dc6 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t030-t034-system-unit -N -L t030-
ctest --test-dir build/fabro-t030-t034-system-unit -L t030- --output-on-failure
ctest --test-dir build/fabro-t030-t034-system-unit -L "t02[6-9]-" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with the shared
T007–T010 artifacts unchanged in substance. Every pre-existing suite must pass unchanged, proving additivity.
Executed sanitizer/static-analysis/Doxygen/benchmark measures and the delivery bundle remain with T035–T040; this plan
requires the T030 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T030 entry exists and states the versioned-contract scope |
| CHK-02 | Changed-path boundary and additivity | `git diff --name-only <baseline> --`; `git ls-files --others --exclude-standard` | only the §7.1 paths appear; no accepted predecessor byte under `src/`, `tests/`, `xdl/`, or `docs/engineering/xcom/t0{07..29}/` changes; no other task's path |
| CHK-03 | Single versioned contract source | inspect `proto/xverse/xcom/v1/tool_gateway.proto` | exactly one committed schema; `package xverse.xcom.v1`; `syntax = "proto3"`; the locator equals `XCOM-XLC-002`; no competing definition |
| CHK-04 | Complete service surface | run `T30-TS-002`, `T30-TS-003` | the `ToolGateway` service declares exactly the ten methods of `detailed-design.md` §3.1 with the declared request/response pairing and streaming flags; every required message/enum present with a zero `*_UNSPECIFIED` value |
| CHK-05 | Version negotiation | run `T30-TS-004`, `T30-TS-020` | `ProtocolVersion` major/minor present; the test-local predicate accepts major 1 and rejects major 0 and major 2 fail-closed |
| CHK-06 | Observation contract and bounds | run `T30-TS-005` | `ReadObservations` is server streaming; `ObservationRecord` carries the declared metadata fields and payload state; the payload view is explicit, bounded, opt-in, metadata-only by default |
| CHK-07 | Session arm/revoke contract | run `T30-TS-006` | arm carries permit/session/plan/graph/protocol/validity; responses carry `SessionState`; no permit-bypass field |
| CHK-08 | Stimulation action coverage | run `T30-TS-007` | all four action kinds, both schedule modes, interaction and direction enums, correlation/causation, deadline, and payload size bound present |
| CHK-09 | Service-emulation lease contract | run `T30-TS-008` | acquire binds session/endpoint/generation/plan; release binds session/lease; `LeaseState` includes active/released/quarantined/expired/conflict |
| CHK-10 | Outcome and counter contract | run `T30-TS-009` | outcome kinds include evidence-incomplete; `SessionCounters` is the declared finite set; no dashboard/storage/query-presentation/export primitive |
| CHK-11 | Diagnostic contract | run `T30-TS-010` | `Diagnostic` carries code/severity/phase/identity/reason/correction; `Severity` declared |
| CHK-12 | Declared bounds | run `T30-TS-011`, `T30-TS-018` | message/stream/deadline/queue/record/payload/lease bounds are explicit fields; every `bytes` field has a declared size bound |
| CHK-13 | Domain neutrality | run `T30-TS-017`, `T30-TS-019`; forbidden-vocabulary scan | no transport/address/port/socket/DNS/TLS/credential/export shape; no submission/lease without a session/permit identity |
| CHK-14 | Additive evolution rules | run `T30-TS-012`, `T30-TS-021` | every message declares the 1000–1999 reserved band; no live field uses a reserved number; a reserved number cannot be reused |
| CHK-15 | Field-manifest pinning and forward compatibility | run `T30-TS-013`, `T30-TS-014`, `T30-TS-015`, `T30-TS-016` | the live descriptor equals the pinned field manifest; an unknown field and an unmapped enum survive a proto3 round trip and are not remapped |
| CHK-16 | Generation, provenance, and discovery | inspect `src/xverse/xcom/CMakeLists.txt` and the implementation provenance record; run the unit mode | the committed schema is the source of truth; the admitted `protoc`/`grpc_cpp_plugin` generate the artifacts; input schema identity, command, generator identity, and output digests are recorded; the runner discovers the `t030-` cases; the full unit suite passes |
| CHK-17 | Additive build wiring and inventory | `ctest -N` comparison; inspect `XVERSE_XCOM_RUNTIME_TARGETS` | exactly one runtime-target addition (`xverse_xcom_tool_gateway_proto`) and four `t030-<kind>` test targets; every existing target/test name/label/command and the discovered existing count are preserved |
| CHK-18 | Offline, local-only, no new dependency | forbidden-API source scan; successful offline configure/build; inspect the link line | no network/socket/resolver/TLS, ambient/secret lookup, dynamic-load, subprocess, or legacy access; only the admitted `protobuf::libprotobuf` and GTest are linked; no new admitted dependency; the gRPC runtime is not linked |
| CHK-19 | Public safety and payload safety | scan the changed schema, tests, provenance, and work products | no credential, private address, real or proprietary payload, environment-specific host path, or sensitive deployment value; the tests retain no real payload byte |
| CHK-20 | Registers, REF-002, and maturity honesty | run the §3 validators; inspect the recorded maturity | validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; `XCOM-SW-GW-001` recorded implemented for the contract slice by T030, `XCOM-SW-GW-002`/`-003` and T031–T041 remain allocated; `XVE-SYS-0141` remains deferred and unpromoted |
| CHK-21 | Deterministic gate, diff hygiene, stage rule | run the §2 gate; `git diff --check <baseline> --`; `git diff --name-only <baseline> -- specs/007-xcom-core` | exit 0 with a `t030-` discovered count; the diff is whitespace-clean; the only capability-document change is the T030 checkbox line, marked complete **only** at the implementation stage; the inherited `engineering/trace/links.json` and `engineering/stage-results/*.json` provenance digests are refreshed and consistent |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no partial value,
no emitted normal-route item, and no output claiming success. NEG-01…NEG-10 are executable or source-inspection cases
realized by the named checks and the case assertions; NEG-10 is the additivity/stage repository probe.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | add an address, port, socket, DNS, TLS, or credential field, or a dashboard/storage/query/export primitive | CHK-13 (and CHK-10) fail; the contract test fails closed |
| NEG-02 | place a field number inside a reserved band, reuse a reserved number, or renumber/remove a field without reservation | CHK-14/CHK-15 fail |
| NEG-03 | omit a session/permit identity from a submission or lease message | CHK-13 fails |
| NEG-04 | make the contract reject or drop an unknown field or unmapped enum value | CHK-15 fails |
| NEG-05 | implement an implicit/unsupported version acceptance instead of the fail-closed rule | CHK-05 fails |
| NEG-06 | declare a `bytes` payload without a size bound, or an implicit/unbounded message/stream/deadline/queue/lease | CHK-12 fails |
| NEG-07 | add a dependency, fetch over the network, link the gRPC runtime, or commit a generated file as source of truth | CHK-16/CHK-18 fail |
| NEG-08 | commit a credential, private address, real payload, host path, or sensitive value | CHK-19 fails |
| NEG-09 | weaken an accepted requirement/test, change a register row, or promote a REF-002 target | CHK-20 fails |
| NEG-10 | change a non-T030 path (predecessor production source/test/register, another task, or a later-task path), mark the checkbox in the plan stage, change no `tests/` path, or skip the inherited provenance refresh | CHK-02/CHK-21 fail; the candidate exceeds the T030 boundary or stage scope |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline `80c236638e160c5e991e5a537e29d407e7462dc6`;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting command;
- the generation evidence: the admitted `protoc`/`grpc_cpp_plugin` identity, the generation command, the input schema
  SHA-256, and the output digests of `tool_gateway.pb.{h,cc}` and `tool_gateway.grpc.pb.{h,cc}`;
- the configure/build/CTest results, including the `ctest -N` discovered counts (four `t030-<kind>` suites, the
  `t030-` case count, and the preserved existing count) and the `100% tests passed` line;
- the per-case results for `xverse_xcom_tool_gateway_contract_tests`,
  `xverse_xcom_tool_gateway_evolution_tests`, `xverse_xcom_tool_gateway_negative_tests`, and
  `xverse_xcom_tool_gateway_provenance_tests`, plus the unchanged preserved suites that prove additivity;
- the service-surface evidence: the ten methods with their request/response types and streaming flags, and the pinned
  field manifest for every manifest message;
- the version-negotiation evidence: the predicate verdict per tested major;
- the additive-evolution evidence: the reserved-band result, the field-manifest equality result, and the unknown-field
  and unmapped-enum round-trip results;
- the bounds evidence: the declared bound fields and the payload-bound assertion per payload-bearing message;
- the domain-neutrality evidence: the forbidden-shape scan result;
- the negative-case list with each NEG-ID, its realizing check, and its exact observed outcome;
- the changed-path list and the package record `reports/xcom-queue/t030-package.json` with per-file SHA-256;
- the register-validator results, the unchanged REF-002 disposition, and the recorded `XCOM-SW-GW-001` implemented
  disposition;
- the inherited provenance refresh evidence (`engineering/trace/links.json` and `engineering/stage-results/*.json`
  digests).

Public evidence omits host-specific, prefix, manifest, test-toolchain, scratch, temporary, and private-store absolute
paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T030 verification is complete when: the deterministic gate passes (CHK-21); every nominal check in §4 has its expected
result; every negative case in §5 fails closed as stated; the versioned contract, complete service surface, version
negotiation, declared bounds, additive-evolution rules, generated-code provenance, additive build wiring, and the
generated-contract tests are proven; `XCOM-SW-GW-001` is recorded implemented for the contract slice while
`XCOM-SW-GW-002`/`-003` and T031–T041 remain allocated; no accepted requirement, test, ADR, contract, register, or
predecessor byte is weakened; the register validators still pass with REF-002 unchanged and nothing promoted; and a
separate DeepSeek internal review records a passing verdict with no unresolved blocking finding. This does not
constitute user acceptance, which remains T041; external Codex review and acceptance are deferred until the ordered
backlog `xcom-t030-t034-20260928` completes.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T030-STK-001 | CHK-01, CHK-03, CHK-16 | NEG-10 |
| T030-STK-002 | CHK-05, CHK-13, CHK-14 | NEG-01, NEG-02, NEG-05 |
| T030-STK-003 | CHK-16, CHK-18, CHK-21 | NEG-07, NEG-10 |
| T030-STK-004 | CHK-02, CHK-17, CHK-20 | NEG-09, NEG-10 |
| T030-STK-005 | CHK-20, CHK-21 | NEG-09 |
| T030-SR-001 | CHK-01, CHK-03 | NEG-10 |
| T030-SR-002 | CHK-04 | NEG-01 |
| T030-SR-003 | CHK-05 | NEG-05 |
| T030-SR-004 | CHK-06 | NEG-06 |
| T030-SR-005 | CHK-07 | NEG-03 |
| T030-SR-006 | CHK-08 | NEG-06 |
| T030-SR-007 | CHK-09 | NEG-03 |
| T030-SR-008 | CHK-10, CHK-13 | NEG-01 |
| T030-SR-009 | CHK-11 | NEG-01 |
| T030-SR-010 | CHK-12 | NEG-06 |
| T030-SR-011 | CHK-13 | NEG-01, NEG-03 |
| T030-SR-012 | CHK-14, CHK-15 | NEG-02 |
| T030-SR-013 | CHK-15 | NEG-04 |
| T030-SR-014 | CHK-16 | NEG-07 |
| T030-SR-015 | CHK-17 | NEG-06, NEG-10 |
| T030-SR-016 | CHK-04, CHK-05, CHK-06, CHK-07, CHK-08, CHK-09, CHK-10, CHK-11, CHK-12 | NEG-01…NEG-06 |
| T030-SR-017 | CHK-18 | NEG-07 |
| T030-SR-018 | CHK-19 | NEG-08 |
| T030-SR-019 | CHK-20 | NEG-09 |
| T030-SR-020 | CHK-21 | NEG-10 |

No requirement is left without at least one check, and no check claims acceptance.

### 8.1 Whole-system integration trace linkage

Every accepted T030 software requirement carries a `verified_by -> integration` trace edge to the
project whole-system integration measure `engineering/verification/measures/integration.json`. That
measure is executed by the trusted `run_xcom_phase7_tests.py integration` command, which assembles the
candidate into the pinned target checkout, builds the complete platform, and runs the
`t030-`-labelled CTest cases plus the full pytest suite. The measure declares twenty-four
`XcomToolGateway{Contract,Evolution,Negative,Provenance}.*` cases as the T030 integration subset.

Strict delivery on the successor candidate found seven requirements whose edge was absent
(`T030-SR-011`, `-014`, `-015`, `-017`, `-018`, `-019`, `-020`); the repair adds `T030-L-0251`…
`T030-L-0257`. The primary executed case(s) per repaired requirement are:

| Requirement | Primary executed whole-system integration case(s) |
| --- | --- |
| `T030-SR-011` | `XcomToolGatewayNegative.NoTcpOrAddressPrimitive`, `XcomToolGatewayNegative.NoBypassOfPermitOrSession` |
| `T030-SR-014` | `XcomToolGatewayProvenance.GeneratedCodeProvenanceRecorded`, `XcomToolGatewayProvenance.GeneratedGrpcStubDeclaresService`, `XcomToolGatewayProvenance.SerializedDescriptorMatchesSource` |
| `T030-SR-015` | the assembled whole-system build that compiles and discovers the additive `t030-contract`/`t030-evolution`/`t030-negative`/`t030-provenance` targets |
| `T030-SR-017` | the offline, local-only whole-system run plus `XcomToolGatewayNegative.NoTcpOrAddressPrimitive` |
| `T030-SR-018` | the executed whole-system measure over the public-safe T030 artifact set |
| `T030-SR-019` | the executed whole-system measure over the unchanged T007–T010 registers and REF-002 disposition |
| `T030-SR-020` | the executed whole-system measure that completes the deterministic Phase 7 gate path |

The link edges point at the whole-system integration measure, so each row's `integration_test_ids`
resolves to the twenty-four executed cases above. No check, case, measure, or test is invented by this
linkage, and no requirement text or acceptance criterion is changed.

## 9. T-CORE slice evidence mapping (T007 register)

The T007 ownership register requires ten evidence names for the whole `T-CORE` slice (T012–T016, T030–T034). T030
contributes four and leaves the rest to their owning tasks.

| Slice evidence | T030 contribution | Owning check/case |
| --- | --- | --- |
| `contract` | the single versioned external-tool contract, generated artifacts, and descriptor proof | CHK-03, CHK-04; `T30-TS-001`…`T30-TS-011` |
| `negative` | forbidden transport/address/export shapes, reserved-number reuse, unbounded payload, unsupported version | CHK-13, CHK-14, CHK-15; `T30-TS-017`…`T30-TS-021` |
| `unit` | four additive generated-contract suites | CHK-16, CHK-17; `T30-TS-001`…`T30-TS-024` |
| `version-rejection` | contract-level fail-closed unsupported-major rule and predicate | CHK-05; `T30-TS-004`, `T30-TS-020` |
| `no-tcp-listener` | not claimed here | T031/T032 |
| `queue-bound` | not claimed here | T022/T031 |
| `recovery` | not claimed here | T026/T031 |
| `deterministic-diagnostics` | not claimed here | T025/T031 |
| `later-integration-run` | not claimed here | T035 |
| `second-provider-replaceability` | not claimed here | T034 |

No evidence name above is claimed beyond what its own exact-candidate evidence shows. The gateway session, the
separate-process client, the reusable contract suites, and the second provider remain T031–T034.

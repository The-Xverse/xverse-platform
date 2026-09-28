# T014 Verification Plan — Named Checks, Commands, and Negative Cases (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T014 (capability 007, slice `T-CORE`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T014's executable checks are the lifecycle CTest executables, a full-suite `ctest` run, and the source
inspections that prove bounds, ownership, neutrality, offline behaviour, and public safety; the governance
checks are the deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T014 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59
```

For T014 this gate requires:

- the six work products `docs/engineering/xcom/t014/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T014 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `src/xverse/xcom/`;
- `cmake -S . -B build/fabro-t014 -G Ninja -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build/fabro-t014 --parallel 4`,
  a non-empty `ctest --test-dir build/fabro-t014 -N`, and
  `ctest --test-dir build/fabro-t014 --output-on-failure --parallel 4` all exit 0;
- `git diff --check <baseline> --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the three admitted offline inputs. As
accepted for T012/T013/T019/T020, if the gate's plain configure fails closed at the T025 test-toolchain
admission check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those
slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t014` cache; the gate's unmodified configure/build/`ctest` sequence then reuses
it. The hash-verified preflight is unchanged, no ambient path or network resolution is added, no
admission check is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59 --
git diff --check 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t014 -R "xcom_lifecycle" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The integration policy's `unit`, `integration`,
`validation`, and `static_analysis` measures are executed by the later T035–T040 stages; this plan requires
the T014 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T014 entry exists and states the bounded endpoint/route lifecycle and exact generation-bound ownership scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --` | only `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp`, `src/xverse/xcom/src/endpoint_route_lifecycle.cpp`, the two lifecycle test sources, the T014 work products, the one-line `tasks.md` checkbox, and the package record appear; no `xdl/`, `proto/`, `src/xverse_xdl/`, `.cmake`, root/`CMakeLists.txt`, another T-CORE source, or another task's path |
| CHK-03 | Lifecycle type inventory and public API | read `endpoint_route_lifecycle.hpp`; build | `ResourceKind`, `LifecycleState`, `EndpointSpec(Input)`, `RouteSpec(Input)`, `LifecycleConfiguration(Input)`, `EndpointHandle`, `RouteHandle`, `LifecycleSnapshot`, and `LifecycleController` are declared and compile; the new `RouteSpec` policy overload/accessors, `policy_bound()`, and `route_policy()` are present |
| CHK-04 | Exact generation-bound handle binding | run `xcom_lifecycle_unit`; inspect handle declarations | each declaration returns a nonzero advancing generation; handles own controller id, kind, identity, and digest; private construction; copies preserve the binding |
| CHK-05 | Declaration validation and fail-closed construction | run `xcom_lifecycle_negative`; inspect the factories | every rejected declaration yields a non-empty `DiagnosticSet` and no value; no partial or default-substituted declaration is exposed |
| CHK-06 | Finite configuration and capacity bounds | run `xcom_lifecycle_unit`/`xcom_lifecycle_negative`; inspect constants | capacities are 1–32/1–32; zero/over-max rejected; duplicate and exhaustion rejected without mutation |
| CHK-07 | Ownership diagnostic determinism | run `xcom_lifecycle_negative`; inspect the ordering key | stale/foreign/wrong-kind/mismatched handles produce exactly the `ownership`-phase `XCOM-LIFE-E009` bytes; reordered inputs order consistently |
| CHK-08 | Idempotence, transition table, and recovery | run `xcom_lifecycle_unit` | the complete endpoint and route transition tables hold; safe repeats return the same generation; recreation advances the generation and makes the earlier handle stale |
| CHK-09 | Bounds and finite resources | run the boundary cases; inspect the capacity constants | endpoints ≤ 32, routes ≤ 32, generation < `std::uint64_t::max`, at most one declared policy per route; no unbounded queue/quota/retry/depth |
| CHK-10 | Declared-policy binding and exposure | run `xcom_lifecycle_unit`; inspect the new declarations | a route declared with a `FlowPolicy` binds and exposes it exactly; `has_policy()`/`policy()`/`policy_bound()`/`route_policy()` agree; `route_policy` returns the exact declared policy |
| CHK-11 | No silent upgrade / no rebind path | inspect the public interface; run the immutability/recreation cases | no public operation rebinds or replaces a live generation's declared policy; change requires close + recreation as a new generation; a weaker and stronger declaration are never equal |
| CHK-12 | Compatibility, retention, and policy non-bypass | run `xcom_lifecycle_negative` | a policy-bound route fails every incompatible validate/activate with the exact `XCOM-LIFE-E012` bytes and no mutation; endpoint retention and state rules are unchanged by a declared policy |
| CHK-13 | Policy generation binding | run `xcom_lifecycle_unit` | the declared policy travels with, and is reachable only through, the generation that declared it; a superseded generation's `route_policy` fails |
| CHK-14 | Negative path no-mutation and exact diagnostics | run `xcom_lifecycle_negative` | every rejection compares exact serialized diagnostic bytes and fresh route/source/destination snapshots before and after; no rejection mutates a record or generation |
| CHK-15 | Deterministic diagnostics byte-stability | run `xcom_lifecycle_unit`/`xcom_lifecycle_negative`; inspect `ordering_key` | equivalent invalid inputs serialize byte-identically regardless of order; maximum escaped keys stay within the derived bound |
| CHK-16 | Capability task-ledger stage rule (supporting) | `git diff --name-only <baseline> -- specs/007-xcom-core` | the only capability-document change is the T014 checkbox line, marked complete only at the implementation stage |
| CHK-17 | Concurrency serialization and convergence | run the concurrency cases | concurrent safe repeats converge on one state/generation; concurrent `route_policy`/`route_snapshot` reads return one identical declared policy with no data race |
| CHK-18 | Offline and bounded | forbidden-API source scan; successful offline build | no network/socket/resolver/OpenSSL, ambient/secret lookup, filesystem, process/subprocess, or legacy access; standard library only; no added thread or dependency |
| CHK-19 | Public safety | scan committed source, tests, and work products | no credential, private address, unrestricted payload, proprietary excerpt, environment-specific absolute host path, or sensitive deployment value; diagnostic text is fixed and non-sensitive |
| CHK-20 | Doxygen for new/changed declarations | inspect the changed declarations; run the existing documentation validator | every new/changed public declaration has a `@brief`; the new policy API additionally carries ownership/lifetime/thread-safety/failure clauses; the admitted configuration is unchanged |
| CHK-21 | Registers and REF-002 | run the §3 register validators; inspect the REF-002 disposition | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the requirement/unit/check indices agree; the five work products exist and are mutually consistent |
| CHK-22 | Governance boundary | `git diff --name-only <baseline> --`; inspect tests | no accepted requirement/ADR/contract/schema changed; no existing lifecycle test removed, renamed, or weakened; no later task implemented; only T014-owned paths and work products change |
| CHK-23 | Deterministic gate and diff hygiene | run the §2 gate; `git diff --check <baseline> --` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the T014 checkbox is complete only at the implementation stage |
| CHK-24 | Excluded surfaces absent (supporting) | `git diff --name-only <baseline> -- src/xverse/xcom tests/xcom` | no provider, loopback, observation, stimulation, activation-plan, contract, value, item, diagnostic, result, or `core_types` path changes; only the two lifecycle sources and two lifecycle test sources change |
| CHK-25 | Attribution anomaly recorded | inspect `requirements.md` §7.4/§8.2 and the unchanged registers | the T009 `XCOM-CMP-005` link anomaly is recorded and not rewritten; the T014 source follows the T008/T010 T014 attribution; nothing is promoted |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no accepted evidence of a weakened policy, and no output claiming acceptance.
NEG-01..NEG-18 are executable lifecycle cases or structural probes; NEG-19..NEG-25 are
inspection/repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | empty or over-bound endpoint identity | `EndpointSpec::create` fails with `required_field`/`bound_exceeded`; no value |
| NEG-02 | malformed or wrong-length plan digest (`""`, `"abc"`, uppercase, non-hex) | `invalid_digest` failure; no value |
| NEG-03 | incompatible route pair (same identity, differing plan/provider/contract/direction, or self route) | `route_incompatible` failure; no value |
| NEG-04 | zero or over-maximum endpoint/route capacity | `bound_exceeded` failure; no controller |
| NEG-05 | duplicate nonclosed logical identity | `duplicate_identity` failure; the existing record is unchanged |
| NEG-06 | declaration beyond the configured capacity prefix | `capacity_exhausted` failure; no record added or replaced |
| NEG-07 | stale (superseded-generation) route handle to `route_policy` | exact `invalid_handle` failure; no mutation |
| NEG-08 | foreign-controller handle | exact `invalid_handle` failure; no mutation |
| NEG-09 | unknown or generation-mismatched handle | exact `invalid_handle` failure; no mutation |
| NEG-10 | wrong-kind handle use | a compile-time error through the typed APIs; no wrong-kind mutation is expressible |
| NEG-11 | read a declared policy through an earlier generation / stale handle after recreation | the earlier generation's policy is unreachable; `invalid_handle` failure; no mutation |
| NEG-12 | drain or close an endpoint retained by a nonclosed route | exact `endpoint_in_use` failure; endpoint and route unchanged |
| NEG-13 | skipped or terminal lifecycle transition | exact `invalid_transition` failure; snapshot before and after equal |
| NEG-14 | `route_policy` on a generation that declared no policy | exactly the serialized `route_declaration\|error\|XCOM-TYPE-E001\|<route_id>\|route generation declares no bounded flow policy\|declare the route with an exact validated flow policy` bytes; no value; no default substituted |
| NEG-15 | attempt to rebind, replace, weaken, or strengthen a live generation's declared policy | no such public operation exists; the attempt does not compile, and the only change path is close + recreate as a new generation |
| NEG-16 | policy-bound route with an incompatible endpoint or inactive endpoint state | exact `XCOM-LIFE-E012` failure; route, source, and destination unchanged |
| NEG-17 | concurrent safe repeats and concurrent `route_policy` reads | operations converge on one state/generation; every read returns the identical declared policy; the test is deterministic and race-clean under the admitted sanitizer configuration |
| NEG-18 | generation space exhausted | `generation_exhausted` failure; no record added or replaced (probed by the boundary fixture/static reasoning; the counter never wraps) |
| NEG-19 | introduce network, ambient, filesystem, process, or legacy access in a lifecycle unit | CHK-18 forbidden-API scan fails; the candidate is rejected |
| NEG-20 | add a new admitted dependency or a non-standard-library include to a lifecycle unit | CHK-18 fails; the admitted dependency set is unchanged |
| NEG-21 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-19 public-safety scan fails; the candidate is rejected |
| NEG-22 | mark the T014 checkbox complete in the plan stage | the deterministic gate fails; the plan stage leaves it unchecked |
| NEG-23 | remove, rename, or weaken an existing lifecycle test case | CHK-22 fails; no test may be removed or weakened |
| NEG-24 | add a DNS/socket/OpenSSL/`system`/`fork` symbol to a lifecycle unit | CHK-18 fails; the offline boundary is exceeded |
| NEG-25 | change a non-T014 path or implement a later task (e.g., a provider, observation, plan, or build file) | CHK-02/CHK-22/CHK-24 fail; the candidate exceeds the T014 boundary |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` count (expected 248) and the
  `100% tests passed` line;
- the `xcom_lifecycle_unit`, `xcom_lifecycle_negative`, and `xcom_lifecycle_external_consumer` results;
- the exact declared-policy round-trip output and the exact absent-policy and stale/foreign-handle
  diagnostic sequences;
- the changed-path list and the package record `reports/xcom-queue/t014-package.json` with per-file
  SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T014 verification is complete when: the deterministic gate passes (CHK-23); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the register validators still pass
with REF-002 unchanged (CHK-21); the change is confined to the T014 lifecycle and work-product boundary
(CHK-02, CHK-22, CHK-24, CHK-25); and a separate DeepSeek internal review records a passing verdict with no
findings. This does not constitute user acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T014-STK-001 | CHK-02, CHK-03, CHK-23 | CHK-16, CHK-24 |
| T014-STK-002 | CHK-05, CHK-06, CHK-09, NEG-01..NEG-18 | – |
| T014-STK-003 | CHK-04, CHK-08, CHK-17, CHK-20 | – |
| T014-STK-004 | CHK-18, CHK-19 | NEG-19, NEG-20, NEG-24 |
| T014-STK-005 | CHK-02, CHK-21, CHK-22, CHK-25 | CHK-16, CHK-24 |
| T014-SR-001 | CHK-04, CHK-05, CHK-09, NEG-01, NEG-02 | CHK-24 |
| T014-SR-002 | CHK-05, CHK-12, NEG-03 | CHK-24 |
| T014-SR-003 | CHK-06, CHK-09, NEG-04 | – |
| T014-SR-004 | CHK-06, CHK-09, NEG-05, NEG-06 | – |
| T014-SR-005 | CHK-04, CHK-05, CHK-07 | – |
| T014-SR-006 | CHK-07, NEG-07, NEG-08, NEG-09, NEG-10, NEG-13 | CHK-14 |
| T014-SR-007 | CHK-10, CHK-13, NEG-11 | – |
| T014-SR-008 | CHK-10, CHK-13, NEG-14 | – |
| T014-SR-009 | CHK-11, NEG-15 | CHK-13 |
| T014-SR-010 | CHK-12, NEG-16 | – |
| T014-SR-011 | CHK-08, CHK-14 | – |
| T014-SR-012 | CHK-12, CHK-14, NEG-16 | – |
| T014-SR-013 | CHK-14, NEG-12 | – |
| T014-SR-014 | CHK-08, CHK-14, NEG-11 | – |
| T014-SR-015 | CHK-07, CHK-15 | CHK-14 |
| T014-SR-016 | CHK-06, CHK-09 | – |
| T014-SR-017 | CHK-17, NEG-17 | – |
| T014-SR-018 | CHK-18, NEG-19, NEG-24 | NEG-20 |
| T014-SR-019 | CHK-19, NEG-21 | – |
| T014-SR-020 | CHK-20 | – |
| T014-SR-021 | CHK-02, CHK-21, CHK-22, CHK-25 | CHK-16, CHK-24 |
| T014-SR-022 | CHK-23, NEG-22 | CHK-16 |

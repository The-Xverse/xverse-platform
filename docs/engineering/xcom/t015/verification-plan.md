# T015 Verification Plan — Named Checks, Commands, and Negative Cases (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T015 (capability 007, slice `T-CORE`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `8aaa9eb29ffb349538552d709d4e6f37011b3e65` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review. T015's
executable checks are the provider-loopback CTest executables, the observation-integration consumer, a
full-suite `ctest` run, and the source inspections that prove bounds, ownership, matching, neutrality, offline
behaviour, and public safety; the governance checks are the deterministic gate and the T007–T010 register
validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T015 8aaa9eb29ffb349538552d709d4e6f37011b3e65
```

For T015 this gate requires:

- the six work products `docs/engineering/xcom/t015/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T015 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the plan
  stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `src/xverse/xcom/`;
- `cmake -S . -B build/fabro-t015 -G Ninja -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build/fabro-t015 --parallel 4`,
  a non-empty `ctest --test-dir build/fabro-t015 -N`, and
  `ctest --test-dir build/fabro-t015 --output-on-failure --parallel 4` all exit 0;
- `git diff --check <baseline> --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the three admitted offline inputs. As
accepted for T012/T013/T014/T019/T020, if the gate's plain configure fails closed at the T025 test-toolchain
admission check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those
slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t015` cache; the gate's unmodified configure/build/`ctest` sequence then reuses it.
The hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission check is
weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 8aaa9eb29ffb349538552d709d4e6f37011b3e65
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 8aaa9eb29ffb349538552d709d4e6f37011b3e65 --
git diff --check 8aaa9eb29ffb349538552d709d4e6f37011b3e65 --
git ls-files --others --exclude-standard
ctest --test-dir build/fabro-t015 -R "xcom_provider_loopback|xcom_observation_integration" --output-on-failure
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with the
shared T007–T010 artifacts unchanged in substance. The integration policy's `unit`, `integration`,
`validation`, and `static_analysis` measures are executed by the later T035–T040 stages; this plan requires the
T015 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T015 entry exists and states the explicit provider composition and owned loopback scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --` | only `src/xverse/xcom/include/xverse/xcom/provider.hpp`, `src/xverse/xcom/src/provider.cpp`, the three provider-loopback test sources, the T015 work products, the one-line `tasks.md` checkbox, and the package record appear; no `xdl/`, `proto/`, `src/xverse_xdl/`, `.cmake`, root/`CMakeLists.txt`, `loopback_provider.{hpp,cpp}`, `endpoint_route_lifecycle.{hpp,cpp}`, `contract.hpp`, `diagnostic.hpp`, `observation.hpp`, or another task's path |
| CHK-03 | Provider type inventory and public API | read `provider.hpp`, `loopback_provider.hpp`; build | `ProviderDescriptor(Input)`, `DeliveryCapability`, `OrderingCapability`, `ProviderOutcome`, `ProviderRouteRequirements`, `ProviderRouteBinding`, `ProviderRouteHandle`, `ProviderRouteSnapshot`, `ProviderRegistration`, `ProviderResult`/`ProviderStatus`, `CommunicationProvider`, `ProviderRegistryConfiguration`, `ProviderComposition`, and `LoopbackProvider` are declared and compile; the new `unsupported_policy` value is present |
| CHK-04 | Explicit registration and descriptor retention | run `xcom_provider_loopback_unit`; inspect the registration path | an explicitly supplied provider registers with a strictly advancing generation and retains an immutable descriptor; `descriptor()`/`source_link()`/limits are exact; the registration diagnostic is `XCOM-PROV-S001` |
| CHK-05 | Descriptor and registration fail-closed rejection | run `xcom_provider_loopback_negative`; inspect the factories | every rejected descriptor/registration yields a stable outcome and no value; no slot is added, replaced, or mutated; the fixed registry bound is enforced |
| CHK-06 | Route preparation lifecycle authentication | run `xcom_provider_loopback_negative` | every route/source/destination identity, digest, provider, contract, direction, and state mismatch rejects with the stable `route_mismatch`/`lifecycle_mismatch`/`provider_mismatch` outcome and prepares no provider resource |
| CHK-07 | Requested-semantics capability and limit validation | run `xcom_provider_loopback_negative` | requested version/interaction/delivery/ordering/payload/queue mismatches reject with the stable `unsupported_*`/`*_limit_exceeded` outcomes before any provider dispatch |
| CHK-08 | Declared-policy claim matching (new) | run `xcom_provider_loopback_unit`/`_negative`; inspect the matching block | a supported declaration (`best_effort`/`fifo`) matching the request prepares and activates; an unmappable claim (`at_most_once`/`exactly_once`/`priority`) or a contradicting request rejects with `unsupported_delivery`/`unsupported_ordering` before dispatch; the provider advertises exactly the mapped bit |
| CHK-09 | Declared-policy dimension matching (new) | run `xcom_provider_loopback_unit`/`_negative`; inspect the matching block | declared `overflow == reject`, `deadline_ms == 0`, `retry == 0`, and `queue_depth >= requested capacity` prepare; a non-`reject` overflow or nonzero deadline/retry rejects with the new `unsupported_policy`, and an under-sized declared depth rejects with `queue_limit_exceeded`; no dispatch and no mutation |
| CHK-10 | Unbound-route additivity | run `xcom_provider_loopback_unit`; inspect the matching guard | a route with no declared policy prepares and activates exactly as the baseline fixture; the matching adds no requirement, default, or restriction; existing unbound provider/observation consumers compile and pass unchanged |
| CHK-11 | Exact-handle operation authentication | run `xcom_provider_loopback_negative` | activate/submit/receive/drain/close/state/reconcile reject a stale, foreign, wrong-composition, wrong-registration, inactive, or inactive-state handle with the stable outcome and mutate nothing |
| CHK-12 | Loopback FIFO, saturation, and empty-drain close | run `xcom_provider_loopback_unit` | all four interaction families round-trip exactly; overflow reports `queue_saturated` while preserving queued items and FIFO order; a draining route rejects submissions; close rejects while items remain and releases only an empty route |
| CHK-13 | Replaceability and isolation | run `xcom_provider_loopback_unit`; inspect the independent fixture | a second independently implemented provider composes, activates, and exchanges an owned item; a rejected/failed provider changes no unrelated provider or route |
| CHK-14 | Deterministic diagnostics and outcome mapping | run `xcom_provider_loopback_negative`; inspect the mapping switches | every provider outcome maps to the exact stable text/code/message; the new `unsupported_policy` row is exact; no existing row changed; ordering is deterministic |
| CHK-15 | Bounds and finite resources | run the boundary cases; inspect the constants | providers ≤ 8; loopback routes ≤ 4 and queue ≤ 8; descriptor limits payload ≤ 65,536, routes ≤ 32, queue ≤ 32; generations bounded with explicit exhaustion; no unbounded queue/retry/depth |
| CHK-16 | Concurrency serialization and convergence | run `xcom_provider_loopback_unit`; inspect mutex placement | registration re-entry completes without deadlock; concurrent submit/receive deliver each accepted item exactly once with per-route FIFO order; no callback runs under a registry or provider lock or while both are held |
| CHK-17 | Offline and bounded | forbidden-API source scan; successful offline build | no network/socket/resolver/TLS, ambient/secret lookup, filesystem, process/subprocess, dynamic-load, or legacy access; no discovery or default provider; standard library only; no added thread or dependency |
| CHK-18 | Public safety | scan committed source, tests, and work products | no credential, private address, unrestricted payload, proprietary excerpt, environment-specific absolute host path, or sensitive deployment value; diagnostic text is fixed and non-sensitive |
| CHK-19 | Doxygen for new/changed declarations | inspect the changed declarations; run the existing documentation validator | every new/changed public declaration has a `@brief`; the new outcome and the `prepare_route` matching contract carry ownership/lifetime/thread-safety/failure clauses; the admitted configuration is unchanged |
| CHK-20 | Registers and REF-002 | run the §3 register validators; inspect the REF-002 disposition | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the requirement/unit/check indices agree; the five work products exist and are mutually consistent |
| CHK-21 | Governance boundary | `git diff --name-only <baseline> --`; inspect tests | no accepted requirement/ADR/contract/schema changed; no existing provider/loopback test case removed, renamed, or weakened; no later task implemented; only T015-owned paths and work products change |
| CHK-22 | Deterministic gate and diff hygiene | run the §2 gate; `git diff --check <baseline> --` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the T015 checkbox is complete only at the implementation stage |
| CHK-23 | Capability task-ledger stage rule (supporting) | `git diff --name-only <baseline> -- specs/007-xcom-core` | the only capability-document change is the T015 checkbox line, marked complete only at the implementation stage |
| CHK-24 | Excluded surfaces absent (supporting) | `git diff --name-only <baseline> -- src/xverse/xcom tests/xcom` | no observation, stimulation, activation-plan, contract, value, item, diagnostic, result, lifecycle, or build-file path changes; only `provider.hpp`, `provider.cpp`, and the provider-loopback test sources change in the T015-owned surface |
| CHK-25 | Work-product completeness and consistency | read the five plan documents; recompute file hashes | the five plan documents exist, identify T015 and the baseline, agree on scope/matching/mapping/bounds/boundary, and every §3–§4 requirement maps to ≥ 1 check |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no partial
value, no provider dispatch, no accepted evidence of a weakened or strengthened policy, and no output claiming
acceptance. NEG-01..NEG-22 are executable provider/loopback cases or structural probes; NEG-23..NEG-25 are
inspection/repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | empty, over-bound, non-canonical, zero-mask, unknown-bit, or over-limit descriptor field | `invalid_descriptor`/`bound_exceeded`/`required_field`/`invalid_version`; no value |
| NEG-02 | duplicate provider identity/instance, unsupported contract version, or a full configured registry | `duplicate_provider`/`unsupported_contract_version`/`provider_capacity_exhausted`; no slot mutated |
| NEG-03 | route/source/destination identity, plan digest, provider, contract, or direction mismatch | `route_mismatch`/`provider_mismatch`; no preparation |
| NEG-04 | route not `validated`, or an endpoint not `validated`/`active` | `lifecycle_mismatch`; no preparation |
| NEG-05 | route naming an unregistered provider, or a rejected provider leaving another route unchanged | `provider_mismatch`; isolation preserved |
| NEG-06 | requested interaction family not advertised (or differing from the route contract) | `unsupported_interaction`; no dispatch |
| NEG-07 | requested delivery not advertised | `unsupported_delivery`; no dispatch |
| NEG-08 | requested ordering not advertised | `unsupported_ordering`; no dispatch |
| NEG-09 | zero or over-maximum requested payload limit | `payload_limit_exceeded`; no dispatch |
| NEG-10 | zero or over-maximum requested queue capacity, including an unbound-route baseline request | `queue_limit_exceeded`; no dispatch; unbound-route behaviour otherwise unchanged |
| NEG-11 | declared `reliability ∈ {at_most_once, exactly_once}` or a request weaker/stronger than the declared claim | `unsupported_delivery`; `prepare_calls() == 0`; no mutation |
| NEG-12 | declared `ordering = priority` or a request differing from the declared claim | `unsupported_ordering`; `prepare_calls() == 0`; no mutation |
| NEG-13 | declared `overflow` other than `reject` | the new `unsupported_policy` (`XCOM-PROV-E030`) exact bytes; no dispatch; no mutation |
| NEG-14 | declared `deadline_ms > 0` or `retry > 0` | `unsupported_policy`; no dispatch; no mutation |
| NEG-15 | declared `queue_depth` below the requested queue capacity | `queue_limit_exceeded`; no dispatch; no mutation |
| NEG-16 | selected provider advertises fewer delivery/ordering bits than the declared claim requires | `unsupported_delivery`/`unsupported_ordering`; no dispatch; no mutation |
| NEG-17 | stale provider-route generation, foreign composition, or foreign provider/registration identity | `invalid_provider_route_handle`; no mutation |
| NEG-18 | submit/receive on a `validated`, `draining`, or `closed` route | `inactive_route`; no delivery |
| NEG-19 | item contract/kind/source/route/provider mismatch or payload over the prepared bound; full queue | `item_mismatch`/`payload_limit_exceeded`/`queue_saturated`; queued items and FIFO preserved |
| NEG-20 | close with retained items, or a provider/lifecycle state that cannot reconcile | `queued_items_remain`/`interrupted_resource`; never reported as success |
| NEG-21 | loopback route storage or route generation exhausted | `route_capacity_exhausted`; existing routes unchanged |
| NEG-22 | concurrent submit/receive with a policy-bound route | every accepted item received exactly once; per-route FIFO preserved; deterministic and race-clean under the admitted sanitizer configuration |
| NEG-23 | introduce network, DNS, socket, TLS, ambient, filesystem, process, dynamic-load, or legacy access, or a new dependency, in a provider/loopback unit | CHK-17 forbidden-API scan fails; the candidate is rejected |
| NEG-24 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-18 public-safety scan fails; the candidate is rejected |
| NEG-25 | mark the T015 checkbox complete in the plan stage, change a non-T015 path, or implement a later task (observation, stimulation, plan, gateway, or build file) | CHK-02/CHK-21/CHK-23 fail; the candidate exceeds the T015 boundary |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` count (expected 248) and the
  `100% tests passed` line;
- the `xcom_provider_loopback_unit`, `xcom_provider_loopback_negative`,
  `xcom_provider_loopback_external_consumer`, and `xcom_observation_integration` results;
- the exact declared-policy match/rejection output and the exact `unsupported_policy`,
  `unsupported_delivery`, `unsupported_ordering`, and `queue_limit_exceeded` diagnostic sequences;
- the changed-path list and the package record `reports/xcom-queue/t015-package.json` with per-file SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store absolute
paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T015 verification is complete when: the deterministic gate passes (CHK-22); every nominal check in §4 has its
expected result; every negative case in §5 fails closed as stated; the register validators still pass with
REF-002 unchanged (CHK-20); the change is confined to the T015 provider/loopback and work-product boundary
(CHK-02, CHK-21, CHK-24, CHK-25); and a separate DeepSeek internal review records a passing verdict with no
findings. This does not constitute user acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Primary checks | Supporting checks |
| --- | --- | --- |
| T015-STK-001 | CHK-02, CHK-03, CHK-22 | CHK-24 |
| T015-STK-002 | CHK-05, CHK-07, CHK-08, CHK-09, NEG-01..NEG-21 | CHK-14 |
| T015-STK-003 | CHK-04, CHK-11, CHK-16, CHK-19 | CHK-03 |
| T015-STK-004 | CHK-13, CHK-17, CHK-18 | NEG-23, NEG-24 |
| T015-STK-005 | CHK-02, CHK-20, CHK-21, CHK-25 | CHK-23, CHK-24 |
| T015-SR-001 | CHK-04, CHK-05, NEG-01 | CHK-03 |
| T015-SR-002 | CHK-04, CHK-05, NEG-02 | CHK-15 |
| T015-SR-003 | CHK-02, CHK-05, CHK-15, CHK-17, NEG-02, NEG-23 | CHK-24 |
| T015-SR-004 | CHK-06, NEG-03, NEG-04, NEG-05 | CHK-11 |
| T015-SR-005 | CHK-07, NEG-06, NEG-07, NEG-08, NEG-09, NEG-10 | CHK-15 |
| T015-SR-006 | CHK-11, NEG-17, NEG-18, NEG-20 | CHK-14 |
| T015-SR-007 | CHK-08, NEG-11, NEG-12 | CHK-06 |
| T015-SR-008 | CHK-08, NEG-11, NEG-12, NEG-16 | CHK-07 |
| T015-SR-009 | CHK-09, NEG-13, NEG-14, NEG-15 | CHK-14 |
| T015-SR-010 | CHK-10, NEG-10 | CHK-24 |
| T015-SR-011 | CHK-08, CHK-11, NEG-11, NEG-12 | CHK-10 |
| T015-SR-012 | CHK-12, NEG-21 | CHK-15 |
| T015-SR-013 | CHK-12, NEG-19, NEG-20 | CHK-16 |
| T015-SR-014 | CHK-13, NEG-05 | CHK-03 |
| T015-SR-015 | CHK-11, NEG-20 | CHK-14 |
| T015-SR-016 | CHK-14, NEG-13 | CHK-19 |
| T015-SR-017 | CHK-15, NEG-02, NEG-10, NEG-15, NEG-21 | CHK-12 |
| T015-SR-018 | CHK-16, NEG-22 | CHK-11 |
| T015-SR-019 | CHK-17, NEG-23 | CHK-02 |
| T015-SR-020 | CHK-18, NEG-24 | CHK-25 |
| T015-SR-021 | CHK-19 | CHK-03 |
| T015-SR-022 | CHK-02, CHK-20, CHK-21, CHK-25 | CHK-23, CHK-24 |
| T015-SR-023 | CHK-22, CHK-23, NEG-25 | CHK-02 |

# T015 Implementation Record — Explicit Provider Composition, Declared-Policy Matching, and the Owned Loopback

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T015 (capability 007, slice `T-CORE`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `8aaa9eb29ffb349538552d709d4e6f37011b3e65` |
| Predecessor | T014 reviewed terminal package (`docs/engineering/xcom/t014/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t015/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t015-package.json` (produced by the deterministic package action) |
| Authorization | ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0020; `specs/007-xcom-core/tasks.md` T015 |
| Maturity | Prototype-only explicit provider composition and owned loopback provider implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T015 implements the bounded slice required by the T015 task entry: *"Implement explicit provider
composition and the owned loopback provider."*

The baseline already provides the explicit provider composition — the immutable `ProviderDescriptor`, the
fixed-capacity `ProviderComposition` registry with explicit `register_provider`, the exact generation-bound
`ProviderRouteHandle`, and the `prepare_route`/`activate_route`/`submit`/`receive`/`drain_route`/`close_route`/
`route_state`/`reconcile_route` dispatch — and the owned fixed-capacity `LoopbackProvider` with one serialized
mutex, per-route reject-new FIFO queues, and deterministic `prepared → active → draining → closed` resources.
The accepted `XCOM-SW-CORE-004` bounded-delivery-policy responsibility was only half complete: T014 records
that it binds the immutable `FlowPolicy` to a route generation but that matching the declared policy against a
provider's advertised capability is T015's (`T014-GAP-02`, `T014-LIM-03`), and no production path compared the
declared policy with the selected provider's claims. The candidate therefore:

1. adds the minimal, additive declared-policy ↔ provider capability matching at the composition boundary
   inside `ProviderComposition::prepare_route`: a policy-bound route's declared delivery/ordering claim is
   derived exactly and reconciled with the requested `ProviderRouteRequirements` and the selected provider
   descriptor, and any mismatch fails closed with a stable outcome and **no** provider dispatch and **no**
   mutation;
2. adds **exactly one** stable provider diagnostic outcome `ProviderOutcome::unsupported_policy`
   (`XCOM-PROV-E030`) for the new declared non-capability-dimension rejection, changing no existing outcome,
   code, message, or ordering;
3. adds focused T015 unit and negative cases inside the existing `tests/xcom/provider_loopback/` executables
   for the new matching and for the exact provider/loopback boundaries it must preserve;
4. re-verifies every T015-owned provider and loopback path unchanged where not extended: descriptor,
   registration, compatibility, ownership, lifecycle, FIFO, saturation, recovery, replaceability, diagnostic,
   and concurrency cases compile and pass at the candidate revision with no weakening, rename, or removal.

The matching is a preparation-time decision only, lives in the trusted composition choke point (not in a
provider), changes no public signature or aggregate, and leaves an unbound route (the unchanged three-argument
`RouteSpec::create`) byte-identical to the baseline. It adds **no** diagnostic code or validation phase, adds
**no** dependency beyond the C++ standard library, changes **no** build file (the T012
`xverse_xcom_provider_loopback` target already compiles `provider.cpp`/`loopback_provider.cpp` and registers the
three provider-loopback test executables, so no `.cmake`/root `CMakeLists.txt` change and no inherited T020
trace-link hash refresh is required), performs no network, ambient, filesystem, process, dynamic-load, or legacy
access, and accepts nothing.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/provider.hpp` | edit | adds exactly one `ProviderOutcome` value `unsupported_policy` with its ownership/lifetime/thread-safety/failure documentation; documents the declared-policy matching contract and no-dispatch failure on `prepare_route`; no existing declaration removed, renamed, or changed |
| `src/xverse/xcom/src/provider.cpp` | edit | adds the `declared_delivery_claim`/`declared_ordering_claim` mapping helpers and the matching block in `prepare_route` (claim derivation, requirement consistency, overflow/deadline/retry reconciliation, declared queue-depth bound), and one case in each of `to_string`, `provider_diagnostic_code`, and `provider_diagnostic_message`; no existing outcome, code, message, or ordering changed |
| `tests/xcom/provider_loopback/test_support.hpp` | edit | adds the additive `claim_descriptor` capability-selecting helper and the additive `PolicyRouteFixture` policy-bound/unbound route fixture, plus a `<cstdint>` standard include; existing `Scenario`/`descriptor` behaviour unchanged |
| `tests/xcom/provider_loopback/unit_tests.cpp` | edit | adds `test_policy_bound_route_matching`, `test_policy_bound_route_queue_depth_bound`, `test_policy_bound_route_all_interaction_families`, `test_unbound_route_additivity`, and `test_policy_bound_concurrent_submit_receive`; existing cases unchanged |
| `tests/xcom/provider_loopback/negative_tests.cpp` | edit | adds `test_declared_policy_claim_rejection`, `test_declared_policy_dimension_rejection`, `test_declared_policy_queue_depth_rejection`, and `test_declared_policy_rejection_precedes_dispatch`, and one row in `test_exact_provider_diagnostics`; existing cases unchanged |
| `docs/engineering/xcom/t015/requirements.md` | add (plan stage, frozen) | T015-STK/T015-SR requirements, scope, authorities, affected paths, REF-002 disposition, gaps, requirement-to-check index |
| `docs/engineering/xcom/t015/architecture.md` | add (plan stage, frozen) | boundary, components, ordered data flow, interfaces, quality attributes, traceability |
| `docs/engineering/xcom/t015/detailed-design.md` | add (plan stage, frozen) | descriptor/registration, preparation order, declared-policy matching, failure/outcome mapping, bounds, Doxygen and public-safety design |
| `docs/engineering/xcom/t015/unit-specifications.md` | add (plan stage, frozen) | unit inventory, ownership/lifetime/thread-safety/bounds, planned tests, traceability |
| `docs/engineering/xcom/t015/verification-plan.md` | add (plan stage, frozen) | deterministic gate, CHK-01–CHK-25, NEG-01–NEG-25, candidate-bound evidence, exit criteria |
| `docs/engineering/xcom/t015/implementation.md` | add (this record) | realized change, symbols, commands and results, limitations, traceability |
| `specs/007-xcom-core/tasks.md` | edit (T015 checkbox `[ ]` → `[X]`) | capability task ledger; marked complete only after the authorized work and every required local check passed |

### 3.1 Realized symbols and locations

| Symbol / construct | Location | Realized behaviour |
| --- | --- | --- |
| `ProviderOutcome::unsupported_policy` | `provider.hpp` | additive terminal enumerator with a `@brief` documenting fail-closed rejection of a declared non-capability dimension; no existing value renamed, recoded, reordered, or removed |
| `declared_delivery_claim(ReliabilityPolicy, DeliveryCapability&)` | `provider.cpp` (anonymous namespace) | exact mapping `best_effort → best_effort`, `at_least_once → reliable`, and rejection of `at_most_once`/`exactly_once`; never substitutes a weaker/stronger guarantee |
| `declared_ordering_claim(OrderingPolicy, OrderingCapability&)` | `provider.cpp` (anonymous namespace) | exact mapping `unordered → unordered`, `fifo → per_route_fifo`, and rejection of `priority` |
| Declared-policy matching block in `ProviderComposition::prepare_route` | `provider.cpp` | runs between the interaction-family check and the baseline requested-capability limits; applies only when `route_spec.has_policy()`; rejects `unsupported_delivery`, then `unsupported_ordering`, then `unsupported_policy`, then `queue_limit_exceeded`, before any provider dispatch |
| `to_string`/`provider_diagnostic_code`/`provider_diagnostic_message` new case | `provider.cpp` | `unsupported-policy` / `XCOM-PROV-E030` / `declared route policy is not supported by the selected provider` |
| `test::claim_descriptor` | `test_support.hpp` | builds a valid descriptor advertising exactly one caller-selected delivery and ordering claim with caller-selected route/queue limits |
| `test::PolicyRouteFixture` | `test_support.hpp` | builds a contract, both endpoint declarations, a bound (four-argument `RouteSpec::create`) or unbound (three-argument) route declaration, the lifecycle records, a one-slot composition, and registers the caller-supplied provider; exposes exact handles, snapshots, and prepare |

### 3.2 Additivity and baseline preservation

- The matching is **guarded by `RouteSpec::has_policy()`**; an unbound route skips it and its outcome sequence
  is unchanged, so every existing provider/observation caller and test compiles and behaves unchanged
  (T015-SR-010).
- The new outcome is **appended** to the enumeration, so the relative order and (implicit) values of every
  existing provider outcome are unchanged, and the three mapping switches gain exactly one case
  (T015-SR-016).
- No public method signature, `ProviderRouteRequirements` aggregate, `CommunicationProvider` virtual, or
  `RouteSpec` API changed; `loopback_provider.{hpp,cpp}` is re-verified unchanged because the matching is a
  composition-boundary decision (`detailed-design.md` `D-01`).
- `IndependentProvider` and the existing provider-loopback consumer fixtures are unchanged; the new helper and
  fixture are added additively to `test_support.hpp`.
- No existing test case is removed, renamed, or weakened; the new cases are added inside the existing
  executables and one diagnostic-table row is appended, so the discovered CTest count is unchanged at 248
  (command 4).
- The change lives in the already-compiled `xverse_xcom_provider_loopback` translation unit, so no build-file
  change and no inherited T020 provenance refresh (`T015-OPEN-02`).

### 3.3 Declared-policy mapping realized (T015-SR-007..-011)

| Declared claim | Required capability | Admitted? |
| --- | --- | --- |
| `ReliabilityPolicy::best_effort` | `DeliveryCapability::best_effort` | yes (exact) |
| `ReliabilityPolicy::at_least_once` | `DeliveryCapability::reliable` | yes (exact admitted claim) |
| `ReliabilityPolicy::at_most_once` | – | no → `unsupported_delivery` |
| `ReliabilityPolicy::exactly_once` | – | no → `unsupported_delivery` |
| `OrderingPolicy::unordered` | `OrderingCapability::unordered` | yes (exact) |
| `OrderingPolicy::fifo` | `OrderingCapability::per_route_fifo` | yes (exact) |
| `OrderingPolicy::priority` | – | no → `unsupported_ordering` |

For a policy-bound route the requested `requirements.delivery`/`requirements.ordering` must equal the mapped
claim; a weaker or stronger request rejects before dispatch. A declared `overflow != reject` or a nonzero
`deadline_ms`/`retry` rejects with `unsupported_policy`; a requested `queue_capacity` above the declared
`queue_depth` rejects with `queue_limit_exceeded`. The selected descriptor must advertise the mapped claim,
which the unchanged baseline requested-capability check enforces once `requirements` equals the mapped claim
(`NEG-16`).

## 4. Verification method and evidence

Environment: CMake 3.22.1, Ninja 1.10.1, CTest 3.22.1, GNU C++ 11.4.0 (C++20, `-Wall -Wextra -Wpedantic
-Werror`), Python 3.13; repository checkout at the authorized baseline
`8aaa9eb29ffb349538552d709d4e6f37011b3e65`. The three T011 admitted offline inputs are required as the named
variables `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`;
their private-store **values** are not restated here (`T015-SR-019`). As recorded for T012/T013/T014/T019/T020,
the deterministic gate's plain configure fails closed at the T025 test-toolchain admission check because the
run process environment carries none of them; the only permitted resolution is the narrow A-1 cache seeding:
one configure carrying the three explicit, previously admitted cache values seeds the gate's own git-ignored
`build/fabro-t015` cache, and the gate's unmodified configure/build/`ctest` sequence then reuses it. The
hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission check is
weakened, and the admitted input **values** are recorded by name only.

### 4.1 Commands and observed results

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `git rev-parse 8aaa9eb29ffb349538552d709d4e6f37011b3e65` | 0 | Prints the baseline SHA; the binding resolves (CHK-01). |
| 2 | `cmake -S . -B build/t015-cand -G Ninja -DCMAKE_BUILD_TYPE=Debug` with the three admitted inputs seeded as explicit cache values (A-1) | 0 | Configure succeeds; `-- Configuring done` / `-- Generating done` (CHK-03). |
| 3 | `cmake --build build/t015-cand --parallel 4` | 0 | 61/61 targets build with no warning promoted to an error (CHK-03, CHK-20). |
| 4 | `ctest --test-dir build/t015-cand -N` | 0 | `Total Tests: 248` — identical to the baseline count; no test added, removed, or renamed (CHK-16, NEG-22). |
| 5 | `ctest --test-dir build/t015-cand -R "xcom_provider_loopback\|xcom_observation_integration" --output-on-failure` | 0 | `100% tests passed, 0 tests failed out of 4` — `xcom_provider_loopback_unit`, `xcom_provider_loopback_negative`, `xcom_provider_loopback_external_consumer`, `xcom_observation_integration` (CHK-04..CHK-14, CHK-16, CHK-17). |
| 6 | `ctest --test-dir build/t015-cand --output-on-failure --parallel 4` | 0 | `100% tests passed, 0 tests failed out of 248` in ~3.1 s (CHK-23). |
| 7 | `python3 scripts/validate_xcom_task_ownership.py --verify` and `--check-human` | 0 / 0 | `X-COM task-ownership validation passed` (CHK-21, CHK-25). |
| 8 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | 0 | `X-COM requirements/traceability validation passed` (CHK-21). |
| 9 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | 0 | `X-COM architecture/contracts validation passed` (CHK-21). |
| 10 | `python3 scripts/validate_xcom_unit_design.py --verify` | 0 | `X-COM unit-design validation passed` (CHK-21). |
| 11 | `git diff --name-only 8aaa9eb29ffb349538552d709d4e6f37011b3e65 --` + `git ls-files --others --exclude-standard` | 0 | exactly the two T015 production files, the three T015 provider-loopback test files, the one-line `tasks.md` checkbox, and the six T015 work products; no `xdl/`, `proto/`, `src/xverse_xdl/`, `.cmake`, root/`CMakeLists.txt`, `loopback_provider.{hpp,cpp}`, `endpoint_route_lifecycle.{hpp,cpp}`, `contract.hpp`, `diagnostic.hpp`, `observation.hpp`, or another task's path (CHK-02, CHK-22, CHK-24). |
| 12 | forbidden-API source scan of the three changed source/test headers and sources | 0 | no socket/network/resolver, ambient/secret lookup, filesystem, process/subprocess, dynamic-load, or legacy include or call (the only literal matches are the words "lossless" and "resolve" in existing text); standard library only (`<array>`, `<atomic>`, `<cstddef>`, `<cstdint>`, `<iostream>`, `<limits>`, `<memory>`, `<mutex>`, `<optional>`, `<span>`, `<string>`, `<string_view>`, `<thread>`, `<utility>`, `<vector>`); no added thread or dependency (CHK-17, NEG-23). |
| 13 | public-safety scan of the changed source/test files and the six work products | 0 | no credential, private address, unrestricted payload, proprietary excerpt, environment-specific absolute host path, or sensitive deployment value; diagnostic text is fixed and non-sensitive (CHK-18, NEG-24). |
| 14 | `python3 scripts/check_doxygen.py --coverage-only` | 0 | reports only pre-existing Python-docstring findings under `src/xverse_xdl/`, disjoint from every T015 changed path, and **zero** `src/xverse/xcom` findings. Strict declaration-level C++ Doxygen remains `DOX-GAP-01`/`T011-GAP-01`, owned by T011/T037 (`T015-LIM-02`); every new/changed declaration carries a `@brief`, and the new outcome and `prepare_route` additionally carry ownership/lifetime/thread-safety/failure clauses (CHK-19). |
| 15 | `git diff --check 8aaa9eb29ffb349538552d709d4e6f37011b3e65 --` | 0 | empty output; the candidate diff is whitespace-clean (CHK-22). |
| 16 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T015 8aaa9eb29ffb349538552d709d4e6f37011b3e65` | 0 | `{"ok": true, "task_id": "T015", "changed_paths": 12, "checks": ["ctest:248"]}` (CHK-22). |

Command 16 is run **after** the T015 checkbox is marked and this record is written. The twelve counted changed
paths are the two T015 production files, the three T015 test files, the one-line `tasks.md` checkbox, and the
six T015 work products (the generated `internal-review.json` and `t015-package.json` are excluded from the
candidate inventory, as the gate defines). The A-1 seeding configure supplies the three admitted input values
as explicit cache values into the gate's own git-ignored `build/fabro-t015` cache; the gate's unmodified
configure/build/`ctest` sequence then reuses it. The hash-verified offline preflight is unchanged, no ambient
path or network resolution is added, and no admission check is weakened.

### 4.2 Exact declared-policy match and rejection sequences (CHK-08, CHK-09, CHK-14)

The focused cases assert the exact decision and byte sequence for each mapping:

```text
best_effort/fifo + overflow=reject, deadline=0, retry=0, queue_depth>=requested   -> prepared (dispatch 1)
at_least_once -> reliable (provider advertising reliable)                          -> prepared (dispatch 1)
multiple declared interaction families, policy best_effort/fifo                   -> accepted + received exactly
at_most_once | exactly_once                                                        -> unsupported-delivery / XCOM-PROV-E016
priority                                                                           -> unsupported-ordering / XCOM-PROV-E017
declared fifo but requested unordered (or declared best_effort but requested reliable)
                                                                                   -> unsupported-ordering/delivery
declared claim requires a bit the selected provider does not advertise             -> unsupported-delivery/-ordering
overflow in {drop_oldest,drop_newest,coalesce,lossless_backpressure,fail_closed}
  | deadline_ms=100 | retry=1                                                      -> unsupported-policy / XCOM-PROV-E030
declared queue_depth below requested queue_capacity                                -> queue-limit-exceeded (no dispatch)
```

`test_exact_provider_diagnostics` verifies the added row
`unsupported_policy → unsupported-policy / XCOM-PROV-E030 / declared route policy is not supported by the
selected provider` while every pre-existing row is unchanged. `test_declared_policy_dimension_rejection`
independently asserts those exact bytes for all seven non-capability-dimension cases.
`test_declared_policy_queue_depth_rejection` proves no provider dispatch by a compliant re-preparation on the
same exact route handle: it succeeds and observes provider route generation `1`, so the rejected call consumed
no provider route resource. `test_declared_policy_claim_rejection`,
`test_declared_policy_dimension_rejection`, and `test_declared_policy_rejection_precedes_dispatch` each assert
`prepare_calls()==0`/`activate_calls()==0`/`submit_calls()==0` (IndependentProvider) and byte-identical
route/source/destination lifecycle snapshots before and after the rejection (no mutation).

### 4.3 Artifact identity at this candidate state

| Artifact | SHA-256 | Bytes |
| --- | --- | ---: |
| `src/xverse/xcom/include/xverse/xcom/provider.hpp` | `e3c6a4dea9c12064002e42c7fe1a9dabe45b4757d7eabaf9399ebbfde548f50f` | 43097 |
| `src/xverse/xcom/src/provider.cpp` | `96f928377468302097dbfd76fb7b7ed32947d8b240d2f8f033b4f76eb60fd0c7` | 47193 |
| `tests/xcom/provider_loopback/test_support.hpp` | `a1b79b497bb00e573dcf0f61466836de908416f4e5c39bbb3be2c88631390af5` | 22235 |
| `tests/xcom/provider_loopback/unit_tests.cpp` | `bfd0995e51b2a53e112f62718c2725dafc2ab32054a7f1270a40d2c0ea0a998d` | 37967 |
| `tests/xcom/provider_loopback/negative_tests.cpp` | `43cccb4a38ca40c79050c137aa76666c2b901a239020b6ca4c9203982ae73bc7` | 90154 |
| `docs/engineering/xcom/t015/requirements.md` | `3a1f046f49d044bcbe9db73688d4e229dafcf21d3590d3edcbcc8d9e6d2020c3` | 41797 |
| `docs/engineering/xcom/t015/architecture.md` | `fe975e8390e8341412286bace7156881762c5d303482807da572196415a0c141` | 22296 |
| `docs/engineering/xcom/t015/detailed-design.md` | `8d8bbfe2f7da91465eac6e503f1b77b9a52128e2dc6f52b0e969293a45749d6e` | 19755 |
| `docs/engineering/xcom/t015/unit-specifications.md` | `d3bf89b79f991fb0e55dd2c3b87d83b91e1f64f43efc463b34424e048abfb949` | 22792 |
| `docs/engineering/xcom/t015/verification-plan.md` | `ab1588b485c1d79cedc927b530ab36cdcdea3b6dbc127b2a1935c85c69d04ac1` | 20107 |
| `specs/007-xcom-core/tasks.md` | `128d83c13f2693a14dcdc80884741f0cee4e303b87c22e51aa718190a56dbecc` | 8026 |

`docs/engineering/xcom/t015/implementation.md`, `docs/engineering/xcom/t015/internal-review.json`,
`reports/xcom-queue/t015-package.json`, and the one-line `specs/007-xcom-core/tasks.md` checkbox are bound by
the package record's per-file SHA-256. The package action recomputes every changed tracked path's SHA-256; a
successor candidate must record its own exact revision and repeat every affected check.

## 5. Requirement-to-evidence traceability

| Requirement | Primary check(s) | Evidence |
| --- | --- | --- |
| T015-STK-001 | CHK-02, CHK-03, CHK-22 | cmd 2, 3, 4, 11 |
| T015-STK-002 | CHK-05, CHK-07, CHK-08, CHK-09, NEG-01..NEG-21 | cmd 3, 5, 6; §4.2 |
| T015-STK-003 | CHK-04, CHK-11, CHK-16, CHK-19 | cmd 5; `test_policy_bound_concurrent_submit_receive` |
| T015-STK-004 | CHK-13, CHK-17, CHK-18 | cmd 3, 12, 13 |
| T015-STK-005 | CHK-02, CHK-20, CHK-21, CHK-25 | cmd 7–11 |
| T015-SR-001 | CHK-04, CHK-05, NEG-01 | cmd 5 (existing descriptor rejection table unchanged) |
| T015-SR-002 | CHK-04, CHK-05, NEG-02 | cmd 5 (existing registration rejection/re-entry cases unchanged) |
| T015-SR-003 | CHK-02, CHK-05, CHK-15, CHK-17, NEG-02, NEG-23 | cmd 5, 12; existing capacity/exhaustion cases |
| T015-SR-004 | CHK-06, NEG-03, NEG-04, NEG-05 | cmd 5 (existing preparation identity/state matrices unchanged) |
| T015-SR-005 | CHK-07, NEG-06..NEG-10 | cmd 5 (existing requested-semantics matrix unchanged) |
| T015-SR-006 | CHK-11, NEG-17, NEG-18, NEG-20 | cmd 5 (existing activation/submit/reconcile matrices unchanged) |
| T015-SR-007 | CHK-08, NEG-11, NEG-12 | cmd 5; §4.2; `test_policy_bound_route_matching`, `test_declared_policy_claim_rejection` |
| T015-SR-008 | CHK-08, NEG-11, NEG-12, NEG-16 | cmd 5; §4.2; `test_declared_policy_claim_rejection` |
| T015-SR-009 | CHK-09, NEG-13, NEG-14, NEG-15 | cmd 5; §4.2; `test_policy_bound_route_queue_depth_bound`, `test_declared_policy_dimension_rejection`, `test_declared_policy_queue_depth_rejection` |
| T015-SR-010 | CHK-10, NEG-10 | cmd 5; `test_unbound_route_additivity` |
| T015-SR-011 | CHK-08, CHK-11, NEG-11, NEG-12 | cmd 5; structure (`prepare_route` matches once, no rebind operation) |
| T015-SR-012 | CHK-12, NEG-21 | cmd 5 (existing route-capacity/reuse/isolation cases unchanged) |
| T015-SR-013 | CHK-12, NEG-19, NEG-20 | cmd 5; `test_policy_bound_route_all_interaction_families` |
| T015-SR-014 | CHK-13, NEG-05 | cmd 5 (existing independent-provider contract case unchanged) |
| T015-SR-015 | CHK-11, NEG-20 | cmd 5 (existing reconciliation mismatch case unchanged) |
| T015-SR-016 | CHK-14, NEG-13 | cmd 5; §4.2 (`test_exact_provider_diagnostics` extended row) |
| T015-SR-017 | CHK-15, NEG-02, NEG-10, NEG-15, NEG-21 | cmd 5; bounds matrix in `detailed-design.md` §7 |
| T015-SR-018 | CHK-16, NEG-22 | cmd 5; `test_policy_bound_concurrent_submit_receive` |
| T015-SR-019 | CHK-17, NEG-23 | cmd 12; cmd 3 offline build |
| T015-SR-020 | CHK-18, NEG-24 | cmd 13 |
| T015-SR-021 | CHK-19 | cmd 14; §3.1 (documented declarations) |
| T015-SR-022 | CHK-02, CHK-20, CHK-21, CHK-25 | cmd 7–11 |
| T015-SR-023 | CHK-22, CHK-23, NEG-25 | cmd 15, 16 |

## 6. Public safety

The T015 work products and the committed source, tests, and provider header contain repository-relative paths,
type and field names, stable code text, bounded fixed diagnostic text, and pass/fail outcomes only. They
contain no credential, private address, unrestricted payload, proprietary source excerpt, or sensitive
deployment value. The T011 admitted input **values** (host prefix, package manifest, and test-toolchain
locations) are referenced by variable **name** only and are not committed; generated build evidence exists only
beneath the git-ignored build directory. The single non-repository absolute path is the workflow's own
deterministic-gate invocation in command 16
(`/home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py`), retained exactly as in the accepted
T009–T014 records; it is the workflow tool path, not a sensitive deployment value (`T015-SR-020`, CHK-18).

## 7. Limitations, gaps, and maturity

Recorded from the requirements package and **not** resolved by T015:

- `T015-LIM-01` — the composition and loopback are prototype control-plane/data-plane libraries: they make no
  runtime, transport, timing, network, compatibility, or production-readiness claim, and they are not yet
  user-accepted (T041).
- `T015-LIM-02` — strict declaration-level Doxygen (`WARN_IF_UNDOCUMENTED`/`WARN_NO_PARAMDOC`) remains open
  (`DOX-GAP-01`, `T011-GAP-01`), owned by T011/T037; T015 documents every new/changed declaration but does not
  enable the strict configuration.
- `T015-LIM-03` — the declared-policy matching is a preparation-time decision only: deadline, retry, and
  non-`reject` overflow are rejected as unsupported rather than implemented, and no wire enforcement, timing
  fidelity, or measurement is claimed.
- `T015-LIM-04` — the owned loopback is test evidence only: passing its suite proves no network provider,
  transport protocol, or legacy bridge compatible (`contracts/provider.md`).
- `T015-LIM-05` — restart reconciliation across processes is not implemented; here "restart" means a new
  composition/provider instance in the same process, whose earlier handles are rejected by opaque identity.
- `T015-LIM-06` — the declared policy is bound to a route generation by T014; wiring the activation-plan
  (T019) or Profile (T017) policy into that route binding remains with the XDL/plan slices and T016.
- `T015-OPEN-01` — the admitted provider capability vocabulary cannot express `at-most-once`, `exactly-once`,
  or `priority`; T015 rejects those declarations fail-closed and adds no capability bit (T034 may extend it
  additively).
- `T015-OPEN-02` — if a later task moves the matching into its own translation unit or adds a second provider
  outcome, that task updates the build contract and the inherited T020 trace links; T015 changes no build file
  and adds exactly one provider outcome.
- `T015-GAP-02` — the consolidated cross-cutting core unit/negative matrix (all interaction kinds, provider
  capabilities, policy, ownership, lifecycle, queue bounds, diagnostics, recovery) remains T016.
- `T015-GAP-04` — executed sanitizer/static-analysis/Doxygen/benchmark evidence and the delivery bundle remain
  T035–T040; T015 does not run them.
- `T015-GAP-05` — candidate acceptance under capability 007 remains with T039/T041.

Maturity: prototype-only, Linux x86-64, standard-library-only explicit provider composition and owned loopback
provider, locally verified, making **no** X-COM runtime, transport, compatibility, or production-readiness
claim. Not user-accepted (T041) and not externally reviewed (Codex review deferred until this ordered backlog
completes). No REF-002 target requirement is promoted; the capability disposition stays `unchanged` with an
empty `promoted` set (`T015-SR-022`).

## 8. Definition-of-done status (requirements view)

- (a) The six named work products exist under `docs/engineering/xcom/t015/` and are mutually consistent. ✔
- (b) Every requirement in `requirements.md` §3–§4 maps to ≥ 1 named check in `verification-plan.md`. ✔
- (c) The implementation stage delivered the declared-policy matching, the one new stable provider outcome,
  the focused provider/loopback cases, marked the T015 checkbox, and recorded this note. ✔
- (d) The deterministic gate and the named checks pass at the candidate revision (commands 2–16). ✔
- (e) The package record is written by the package action after the review pass. ◐
- (f) A separate DeepSeek internal review records a passing verdict with no findings
  (`docs/engineering/xcom/t015/internal-review.json`). ◐ — produced by the review stage, not self-declared
  here.

This does **not** constitute external review or user acceptance, which remain deferred to the backlog and to
T041 respectively.

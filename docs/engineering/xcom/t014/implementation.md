# T014 Implementation Record — Bounded Endpoint/Route Lifecycle and Declared-Policy Binding

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T014 (capability 007, slice `T-CORE`) |
| Stage / role | implementation → implementation record |
| Revision | 1 |
| Authorized baseline | `93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` |
| Predecessor | T013 reviewed terminal package (`docs/engineering/xcom/t013/`) |
| Candidate state | working tree over the authorized baseline (staged for the deterministic gate; candidate revision assigned when the workflow checkpoints) |
| Work products | [`requirements.md`](requirements.md), [`architecture.md`](architecture.md), [`detailed-design.md`](detailed-design.md), [`unit-specifications.md`](unit-specifications.md), [`verification-plan.md`](verification-plan.md), this record |
| Internal review | `docs/engineering/xcom/t014/internal-review.json` (separate read-only DeepSeek review, produced by the review stage) |
| Package record | `reports/xcom-queue/t014-package.json` (produced by the deterministic package action) |
| Authorization | ACC002/ACC004/ACC005/ACC006/ACC007/ACC010/ACC011/ACC014/ACC015; ADR-0016; ADR-0018; ADR-0020; `specs/007-xcom-core/tasks.md` T014 |
| Maturity | Prototype-only immutable-value/control-plane lifecycle library implemented and locally verified; not user-accepted, not externally reviewed |
| Classification | Public-safe engineering work product |

## 2. Candidate summary

T014 implements the bounded slice required by the T014 task entry: *"Implement bounded endpoint/route
lifecycle and exact generation-bound ownership handles."*

The baseline already provides the endpoint/route lifecycle control plane — immutable `EndpointSpec`/
`RouteSpec` declarations, the finite `LifecycleConfiguration`, the serialized fixed-record
`LifecycleController`, the `declared → validated → active → draining → closed` state machine with its
`failed` branch, idempotent safe repeats, and exact generation-bound `EndpointHandle`/`RouteHandle`
ownership. The accepted `XCOM-SW-CORE-004` bounded-delivery-policy responsibility was only half complete:
T013 records that it defines the immutable `FlowPolicy` value but that binding it to endpoints/routes is
T014's (`T013-GAP-02`, `T013-OPEN-01`), and no production path bound the declared bounded policy to a route
generation. The candidate therefore:

1. adds the minimal, additive declared-policy binding: a route declaration may carry exactly one immutable,
   already-validated `FlowPolicy`, copied into the owned route value by a new four-argument
   `RouteSpec::create` overload, exposed by `RouteSpec::has_policy()`/`policy()`, by
   `LifecycleSnapshot::policy_bound()`, and by `LifecycleController::route_policy(const RouteHandle&)`
   after exact handle authentication;
2. adds focused T014 policy/handle unit and negative cases to the existing
   `tests/xcom/endpoint_route_lifecycle/` executables;
3. re-verifies every T014-owned lifecycle path unchanged where not extended: the existing declaration,
   capacity, transition, compatibility, ownership, retention, concurrency, and diagnostic cases compile and
   pass at the candidate revision with no weakening, rename, or removal.

The binding substitutes no default, offers no rebind/upgrade operation, and requires closing and recreating
the route as a new generation to change the declared policy. It adds **no** diagnostic code or validation
phase (the absent-policy failure reuses `required_field` in the `route_declaration` phase) and changes **no**
build file (the T012 `xverse_xcom_endpoint_route_lifecycle` target already compiles
`endpoint_route_lifecycle.cpp` and registers the three lifecycle test executables, so no `.cmake`/root
`CMakeLists.txt` change and no inherited T020 trace-link hash refresh is required). It implements T014 only,
adds no dependency beyond the C++ standard library, performs no network, ambient, filesystem, process, or
legacy access, and accepts nothing.

## 3. Implemented change

| Path | Change | Role |
| --- | --- | --- |
| `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp` | edit | adds the additive four-argument `RouteSpec::create` overload, `RouteSpec::has_policy()`/`policy()`, the private `create_impl` and optional-policy constructor, the `std::optional<FlowPolicy> policy_` member, `LifecycleSnapshot::policy_bound()` and its `policy_bound_` field, and `LifecycleController::route_policy`; no existing declaration removed, renamed, or changed |
| `src/xverse/xcom/src/endpoint_route_lifecycle.cpp` | edit | implements the shared `create_impl` path used by both route factories, the optional-policy route copy, the `policy_bound` snapshot flag at every snapshot site, and the exact-handle `route_policy` read; reuses existing diagnostic codes and phases only |
| `tests/xcom/endpoint_route_lifecycle/unit_tests.cpp` | edit | adds `test_route_declared_policy_binding`, `test_route_policy_generation_binding`, `test_route_policy_immutability`, `test_route_policy_concurrent_read` and the `flow_policy`/`policy_route` helpers; existing cases unchanged |
| `tests/xcom/endpoint_route_lifecycle/negative_tests.cpp` | edit | adds `test_route_policy_absent_diagnostic`, `test_route_policy_handle_boundaries`, `test_policy_bound_route_compatibility_unchanged` and the `message_policy` helper; existing cases unchanged |
| `docs/engineering/xcom/t014/requirements.md` | add (plan stage, frozen) | T014-STK/T014-SR requirements, scope, authorities, affected paths, REF-002 disposition, gaps, requirement-to-check index |
| `docs/engineering/xcom/t014/architecture.md` | add (plan stage, frozen) | boundary, trust boundaries, components, ordered data flow, interfaces, quality attributes, traceability |
| `docs/engineering/xcom/t014/detailed-design.md` | add (plan stage, frozen) | declaration, capacity, handle, declared-policy, transition, failure, bounds, Doxygen and public-safety design |
| `docs/engineering/xcom/t014/unit-specifications.md` | add (plan stage, frozen) | unit inventory, ownership/lifetime/thread-safety/bounds, planned tests, traceability |
| `docs/engineering/xcom/t014/verification-plan.md` | add (plan stage, frozen) | deterministic gate, CHK-01–CHK-25, NEG-01–NEG-25, candidate-bound evidence, exit criteria |
| `docs/engineering/xcom/t014/implementation.md` | add (this record) | realized change, symbols, commands and results, limitations, traceability |
| `specs/007-xcom-core/tasks.md` | edit (T014 checkbox `[ ]` → `[X]`) | capability task ledger; marked complete only after the authorized work and every required local check passed |

### 3.1 Realized symbols and locations

| Symbol / construct | Location | Realized behaviour |
| --- | --- | --- |
| `RouteSpec::create(input, source, destination, const FlowPolicy&)` | `endpoint_route_lifecycle.hpp` declaration, `endpoint_route_lifecycle.cpp` definition | additive overload; `noexcept`; performs exactly the three-argument route compatibility validation and then copies the already-validated policy into the owned route |
| `RouteSpec::create_impl` | `endpoint_route_lifecycle.cpp` (private) | one shared validation path for both factories; `policy` is `nullptr` for the three-argument route and non-null for the four-argument route |
| `RouteSpec::has_policy()` / `RouteSpec::policy()` | `endpoint_route_lifecycle.hpp` | const; `has_policy()` reports presence, `policy()` returns the owned declared policy or `nullptr`; no mutation, no default substitution |
| `RouteSpec::policy_` | `endpoint_route_lifecycle.hpp` (private) | `std::optional<FlowPolicy>` owned member; empty for every three-argument route; compared by the defaulted `operator==` |
| `RouteSpec::RouteSpec(..., const FlowPolicy* policy)` | `endpoint_route_lifecycle.cpp` (private) | copies the declared policy when non-null; the three-argument factory passes `nullptr` |
| `LifecycleSnapshot::policy_bound()` / `policy_bound_` | `endpoint_route_lifecycle.hpp` | const; false for every endpoint snapshot and for an unbound route snapshot; true only for a route generation that declared exactly one policy |
| `LifecycleSnapshot` construction sites | `endpoint_route_lifecycle.cpp` | every endpoint snapshot passes `false`; every route snapshot passes `record->spec.has_policy()`/`route->spec.has_policy()` |
| `LifecycleController::route_policy(const RouteHandle&)` | `endpoint_route_lifecycle.hpp` declaration, `endpoint_route_lifecycle.cpp` definition | const, `noexcept`; one internal-mutex-locked operation; exact current route handle only; returns a copied policy or a stable diagnostic with no mutation |

### 3.2 Additivity and baseline preservation

- The route factory overload is **additive**: the existing three-argument `RouteSpec::create`, the
  `RouteSpecInput`/`EndpointSpecInput`/`LifecycleConfigurationInput` aggregates, and every existing accessor
  are unchanged, so the T015 provider/loopback and T021 observation consumers and every existing test
  compile and behave unchanged.
- The `lifecycle_snapshot` constructor gained one trailing `bool` parameter; it is **private** and
  controller-only, so no public signature changes and no consumer is affected.
- **No diagnostic code or phase is added.** The absent-policy failure reuses
  `DiagnosticCode::required_field` (`XCOM-TYPE-E001`) and `ValidationPhase::route_declaration`, so every
  existing code, phase, ordering key, and bound is unchanged and `diagnostic.hpp`/`diagnostic.cpp` are not
  touched.
- The change lives in the already-compiled `xverse_xcom_endpoint_route_lifecycle` translation unit, so no
  build-file change and no inherited T020 provenance refresh (`D-04`, `T014-OPEN-02`).
- No existing test case is removed, renamed, or weakened; the new cases are added inside the existing
  executables (and one new `<cstdint>` standard include to `unit_tests.cpp`), so the discovered CTest count
  is unchanged at 248 (command 4).
- `RouteSpec::operator==` is defaulted and therefore also compares the declared policy; a weaker, stronger,
  or absent declaration is never equal to a live generation's declaration (T014-SR-009).

## 4. Verification method and evidence

Environment: CMake 3.22.1, Ninja 1.10.1, CTest 3.22.1, GNU C++ 11.4.0 (C++20, `-Wall -Wextra -Wpedantic
-Werror`), Python 3.13; repository checkout at the authorized baseline
`93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59`. The three T011 admitted offline inputs are required as the named
variables `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and `XVERSE_XCOM_T025_TEST_TOOLCHAIN`;
their private-store **values** are not restated here (`T014-SR-019`). As recorded for T012/T013/T019/T020,
the deterministic gate's plain configure fails closed at the T025 test-toolchain admission check because the
run process environment carries none of them; the only permitted resolution is the narrow A-1 cache seeding:
one configure carrying the three explicit, previously admitted cache values seeds the gate's own git-ignored
`build/fabro-t014` cache, and the gate's unmodified configure/build/`ctest` sequence then reuses it. The
hash-verified preflight is unchanged, no ambient path or network resolution is added, no admission check is
weakened, and the admitted input **values** are recorded by name only.

### 4.1 Commands and observed results

| # | Command | Exit | Result |
| ---: | --- | ---: | --- |
| 1 | `git rev-parse 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` | 0 | Prints the baseline SHA; the binding resolves (CHK-01). |
| 2 | `cmake -S . -B build/t014-cand -G Ninja -DCMAKE_BUILD_TYPE=Debug` with the three admitted inputs seeded as explicit cache values (A-1) | 0 | Configure succeeds; `-- Configuring done` / `-- Generating done` (CHK-03). |
| 3 | `cmake --build build/t014-cand --parallel 4` | 0 | 61/61 targets build with no warning promoted to an error (CHK-03, CHK-20). |
| 4 | `ctest --test-dir build/t014-cand -N` | 0 | `Total Tests: 248` — identical to the baseline count; no test added, removed, or renamed (CHK-16, NEG-22). |
| 5 | `ctest --test-dir build/t014-cand -R xcom_lifecycle --output-on-failure` | 0 | `100% tests passed, 0 tests failed out of 3` — `xcom_lifecycle_unit`, `xcom_lifecycle_negative`, `xcom_lifecycle_external_consumer` (CHK-04, CHK-05, CHK-06, CHK-07, CHK-08, CHK-10, CHK-11, CHK-12, CHK-13, CHK-14, CHK-15, CHK-17). |
| 6 | `ctest --test-dir build/t014-cand --output-on-failure --parallel 4` | 0 | `100% tests passed, 0 tests failed out of 248` in ~3.1 s (CHK-23). |
| 7 | `python3 scripts/validate_xcom_task_ownership.py --verify` and `--check-human` | 0 / 0 | `X-COM task-ownership validation passed` (CHK-21, CHK-25). |
| 8 | `python3 scripts/validate_xcom_requirements_traceability.py --verify` | 0 | `X-COM requirements/traceability validation passed` (CHK-21). |
| 9 | `python3 scripts/validate_xcom_architecture_contracts.py --verify` | 0 | `X-COM architecture/contracts validation passed` (CHK-21). |
| 10 | `python3 scripts/validate_xcom_unit_design.py --verify` | 0 | `X-COM unit-design validation passed` (CHK-21). |
| 11 | `git diff --name-only 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59 --` + `git ls-files --others --exclude-standard` | 0 | exactly the two T014 production files, the two T014 lifecycle test files, the one-line `tasks.md` checkbox, and the six T014 work products; no `xdl/`, `proto/`, `src/xverse_xdl/`, `.cmake`, root/`CMakeLists.txt`, `contract.hpp`, `diagnostic.hpp`, `provider.hpp`, or another task's path (CHK-02, CHK-22, CHK-24). |
| 12 | forbidden-API source scan of the four changed source/test files | 0 | no socket/network/resolver, ambient/secret lookup, filesystem, process/subprocess, dynamic-load, or legacy include or call; standard library only (`<array>`, `<atomic>`, `<cstddef>`, `<cstdint>`, `<limits>`, `<mutex>`, `<optional>`, `<string_view>`, `<iostream>`, `<string>`, `<thread>`, `<type_traits>`); no added thread or dependency (CHK-18, NEG-19, NEG-20, NEG-24). |
| 13 | public-safety scan of the four changed source/test files and the six work products | 0 | no credential, private address, unrestricted payload, proprietary excerpt, environment-specific absolute host path, or sensitive deployment value; diagnostic text is fixed and non-sensitive (CHK-19, NEG-21). |
| 14 | `python3 scripts/check_doxygen.py --coverage-only` | 1 | pre-existing Python-docstring findings only; its input set is `**/*.py`, disjoint from every T014 changed path, and it reports **zero** `src/xverse/xcom` findings. Strict declaration-level C++ Doxygen remains `DOX-GAP-01`/`T011-GAP-01`, owned by T011/T037 (`T014-LIM-02`); every new/changed declaration carries a `@brief`, and the new policy API additionally carries ownership/lifetime/thread-safety/failure clauses (CHK-20). |
| 15 | `git diff --check 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59 --` | 0 | empty output; the candidate diff is whitespace-clean (CHK-23). |
| 16 | `python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T014 93cd5f81a2dfbf2231a0b18cfe19dfe43edfbe59` | 0 | `{"ok": true, "task_id": "T014", "changed_paths": 11, "checks": ["ctest:248"]}` (CHK-23). |

Command 16 is run **after** the T014 checkbox is marked and this record is written. The eleven counted
changed paths are the two T014 production files, the two T014 test files, the one-line `tasks.md` checkbox,
and the six T014 work products (the generated `internal-review.json` and `t014-package.json` are excluded
from the candidate inventory, as the gate defines). The A-1 seeding configure supplies the three admitted
input values as explicit cache values into the gate's own git-ignored `build/fabro-t014` cache; the gate's
unmodified configure/build/`ctest` sequence then reuses it. The hash-verified offline preflight is
unchanged, no ambient path or network resolution is added, and no admission check is weakened.

### 4.2 Exact declared-policy round trip and diagnostic sequences (CHK-10, CHK-13, NEG-14, NEG-07..NEG-09)

A throwaway probe compiled against the candidate `xverse_xcom_endpoint_route_lifecycle` archive (built
`-Wall -Wextra -Wpedantic -Werror` at the candidate revision) declared a route through the four-argument
factory with the policy `{ordering = priority, reliability = exactly_once, overflow =
lossless_backpressure, deadline_ms = 1500, retry = 5, queue_depth = 64}` and observed:

```text
policy_read=ok
round_trip=priority/exactly-once/lossless-backpressure/1500/5/64
absent_has_value=0
absent=route_declaration|error|XCOM-TYPE-E001|route.main|route generation declares no bounded flow policy|declare the route with an exact validated flow policy
bound_policy_bound=1
unbound_policy_bound=0
```

The round trip is byte-exact through `RouteSpec::policy()` and `LifecycleController::route_policy`; the
same probe reported `policy_bound()` true for the bound route and false for an unbound route declared
through the three-argument factory. The absent-policy failure above is the exact byte sequence asserted by
`test_route_policy_absent_diagnostic` (NEG-14): `required_field` (`XCOM-TYPE-E001`) in the
`route_declaration` phase with no value and no substituted default. `test_route_policy_handle_boundaries`
additionally asserts the exact `ownership`-phase sequence
`ownership|error|XCOM-LIFE-E009|route.main|handle does not identify the current resource owned by this
controller|use the exact handle issued for the current controller and generation` for a foreign-controller
handle and for a superseded (stale) generation handle, comparing fresh route snapshots before and after to
prove no mutation (NEG-07, NEG-08, NEG-09). `test_policy_bound_route_compatibility_unchanged` asserts that a
policy-bound route fails an incompatible validate/activate with the exact `XCOM-LIFE-E012`
(`route_compatibility`) bytes and that activation still requires both endpoints active (NEG-16, CHK-12).

### 4.3 Artifact identity at this candidate state

| Artifact | SHA-256 | Bytes |
| --- | --- | ---: |
| `src/xverse/xcom/include/xverse/xcom/endpoint_route_lifecycle.hpp` | `00ccbe024bdbe716a0bae59cbc606362fc87e9df0c94f17375427761bd73151e` | 33911 |
| `src/xverse/xcom/src/endpoint_route_lifecycle.cpp` | `1b9425f96b141047ad9f9fad7d25d9eec637de8e3a2f028be7bec3ddadd59b4e` | 36825 |
| `tests/xcom/endpoint_route_lifecycle/unit_tests.cpp` | `0dabfb9d394b98741c2f481fce67dd480c86ba8d75c36bebcaba2b54ec3a5018` | 32623 |
| `tests/xcom/endpoint_route_lifecycle/negative_tests.cpp` | `9f5a6b4fdbf0d5eee4cd015e0d3e6ff8ae81a284fa04fd5804f08cc97924825e` | 45303 |
| `docs/engineering/xcom/t014/requirements.md` | `0809b561df5f696453196804d722914f9d62c59f9993372d162ded99e9cc5512` | 34636 |
| `docs/engineering/xcom/t014/architecture.md` | `8b8f3be83aacc4b1d24a35906c55e3c84b0210be3fdcc2b54d3ce4b8fc57a38e` | 16871 |
| `docs/engineering/xcom/t014/detailed-design.md` | `baff0751eeae13dee61ff33fe6d15fbed3c23a674767f92e7560e9a972dfa6af` | 15063 |
| `docs/engineering/xcom/t014/unit-specifications.md` | `65d1b442b44cbc07085cddcbb5d92460f8f8ecc3922e12012b2393e863a7d4a5` | 15592 |
| `docs/engineering/xcom/t014/verification-plan.md` | `9edff9928f215bad922741741b500d7bc5fa5d49295c9961856217bd017188e3` | 18393 |

`docs/engineering/xcom/t014/implementation.md`, `docs/engineering/xcom/t014/internal-review.json`,
`reports/xcom-queue/t014-package.json`, and the one-line `specs/007-xcom-core/tasks.md` checkbox are bound
by the package record's per-file SHA-256. The package action recomputes every changed tracked path's
SHA-256; a successor candidate must record its own exact revision and repeat every affected check.

## 5. Requirement-to-evidence traceability

| Requirement | Primary check(s) | Evidence |
| --- | --- | --- |
| T014-STK-001 | CHK-02, CHK-03, CHK-23 | cmd 2, 3, 4, 11 |
| T014-STK-002 | CHK-05, CHK-06, CHK-09, NEG-01..NEG-18 | cmd 3, 5, 6; §3.2, §4.2 |
| T014-STK-003 | CHK-04, CHK-08, CHK-17, CHK-20 | cmd 5; `test_route_policy_concurrent_read` |
| T014-STK-004 | CHK-18, CHK-19 | cmd 12, 13; cmd 3 offline build |
| T014-STK-005 | CHK-02, CHK-21, CHK-22, CHK-25 | cmd 7–11 |
| T014-SR-001 | CHK-04, CHK-05, CHK-09 | cmd 5 (existing declaration cases unchanged) |
| T014-SR-002 | CHK-05, CHK-12, NEG-03 | cmd 5 (existing route compatibility matrix unchanged) |
| T014-SR-003 | CHK-06, CHK-09, NEG-04 | cmd 5 (existing configuration boundary cases unchanged) |
| T014-SR-004 | CHK-06, CHK-09, NEG-05, NEG-06 | cmd 5 (existing capacity/isolation cases unchanged) |
| T014-SR-005 | CHK-04, CHK-05, CHK-07 | cmd 5 (existing handle binding assertions unchanged) |
| T014-SR-006 | CHK-07, NEG-07..NEG-10, NEG-13 | cmd 5; `test_route_policy_handle_boundaries` |
| T014-SR-007 | CHK-10, CHK-13, NEG-11 | cmd 5; §4.2; `test_route_declared_policy_binding` |
| T014-SR-008 | CHK-10, CHK-13, NEG-14 | cmd 5; §4.2; `test_route_policy_absent_diagnostic` |
| T014-SR-009 | CHK-11, NEG-15 | cmd 5; `test_route_policy_generation_binding`, `test_route_policy_immutability` |
| T014-SR-010 | CHK-12, NEG-16 | cmd 5; `test_policy_bound_route_compatibility_unchanged` |
| T014-SR-011 | CHK-08, CHK-14 | cmd 5 (existing transition tables unchanged) |
| T014-SR-012 | CHK-12, CHK-14, NEG-16 | cmd 5; `test_policy_bound_route_compatibility_unchanged` |
| T014-SR-013 | CHK-14, NEG-12 | cmd 5 (existing retained-endpoint closure boundary unchanged) |
| T014-SR-014 | CHK-08, CHK-14, NEG-11 | cmd 5; `test_route_policy_generation_binding` |
| T014-SR-015 | CHK-07, CHK-15 | cmd 5; §4.2 (exact serialized bytes) |
| T014-SR-016 | CHK-06, CHK-09 | cmd 5; §3.2 (at most one declared policy per route record) |
| T014-SR-017 | CHK-17, NEG-17 | cmd 5; `test_route_policy_concurrent_read` (serialized under one mutex) |
| T014-SR-018 | CHK-18, NEG-19, NEG-20, NEG-24 | cmd 12; cmd 3 offline build |
| T014-SR-019 | CHK-19, NEG-21 | cmd 13 |
| T014-SR-020 | CHK-20 | cmd 3, 14; §3.1 (documented declarations) |
| T014-SR-021 | CHK-02, CHK-21, CHK-22, CHK-25 | cmd 7–11 |
| T014-SR-022 | CHK-23, NEG-22 | cmd 15, 16 |

## 6. Public safety

The T014 work products and the committed source, tests, and lifecycle header contain repository-relative
paths, type and field names, stable code text, bounded fixed diagnostic text, and pass/fail outcomes only.
They contain no credential, private address, unrestricted payload, proprietary source excerpt, or sensitive
deployment value. The T011 admitted input **values** (host prefix, package manifest, and test-toolchain
locations) are referenced by variable **name** only and are not committed; generated build evidence exists
only beneath the git-ignored build directory. The single non-repository absolute path is the workflow's own
deterministic-gate invocation in command 16
(`/home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py`), retained exactly as in the accepted
T009–T013 records; it is the workflow tool path, not a sensitive deployment value (`T014-SR-019`, CHK-19).

## 7. Limitations, gaps, and maturity

Recorded from the requirements package and **not** resolved by T014:

- `T014-LIM-01` — the lifecycle is a prototype control-plane library: it makes no runtime, transport,
  timing, compatibility, or production-readiness claim, and it is not yet user-accepted (T041).
- `T014-LIM-02` — strict declaration-level Doxygen (`WARN_IF_UNDOCUMENTED`/`WARN_NO_PARAMDOC`) remains open
  (`DOX-GAP-01`, `T011-GAP-01`), owned by T011/T037; T014 documents every new/changed declaration but does
  not enable the strict configuration (`scripts/check_doxygen.py` is a Python-only docstring gate, command
  14).
- `T014-LIM-03` — the declared `FlowPolicy` is a bound declaration only: queueing, backpressure, deadline,
  and retry are neither enforced nor measured by T014, and no timing fidelity is claimed. Provider
  capability matching is T015.
- `T014-LIM-04` — `scripts/validate_xcom_endpoint_route_lifecycle.py` is a legacy SESN-era validator in the
  T014-owned path set; the repository-owned workflow neither depends on nor executes it, and T014 neither
  runs nor edits it.
- `T014-LIM-05` — the lifecycle declares an acyclic route graph implicitly by refusing to drain or close a
  retained endpoint; general loop detection and graph analysis remain outside the core.
- `T014-LIM-06` — restart reconciliation across processes is not implemented; "restart" here means a new
  controller instance in the same process, whose handles are rejected by opaque controller identity.
- `T014-GAP-01` — the T009 `XCOM-CMP-005` requirement links disagree with the T008/T010 T014 attribution
  (`requirements.md` §7.4/§8.2); T014 records the anomaly and promotes nothing; both registers are
  unchanged.
- `T014-GAP-02` — matching the declared policy against a provider's advertised capability, and enforcing it
  on the wire, is `XCOM-SW-CORE-004`'s provider half, owned by T015.
- `T014-GAP-03` — the consolidated cross-cutting core unit/negative matrix remains T016.
- `T014-GAP-04` — candidate acceptance under capability 007 remains with T039/T041.

Maturity: prototype-only, Linux x86-64, standard-library-only immutable-value/control-plane lifecycle
library, locally verified, making **no** X-COM runtime, transport, compatibility, or production-readiness
claim. Not user-accepted (T041) and not externally reviewed (Codex review deferred until this ordered
backlog completes). No REF-002 target requirement is promoted; the capability disposition stays `unchanged`
with an empty `promoted` set (`T014-SR-021`).

## 8. Definition-of-done status (requirements view)

- (a) The six named work products exist under `docs/engineering/xcom/t014/` and are mutually consistent. ✔
- (b) Every requirement in `requirements.md` §3–§4 maps to ≥ 1 named check in `verification-plan.md`. ✔
- (c) The implementation stage delivered the declared-policy binding, the focused lifecycle cases, marked
  the T014 checkbox, and recorded this note. ✔
- (d) The deterministic gate and the named checks pass at the candidate revision (commands 2–16). ✔
- (e) The package record is written by the package action after the review pass. ◐
- (f) A separate DeepSeek internal review records a passing verdict with no findings
  (`docs/engineering/xcom/t014/internal-review.json`). ◐ — produced by the review stage, not self-declared
  here.

This does **not** constitute external review or user acceptance, which remain deferred to the backlog and to
T041 respectively.

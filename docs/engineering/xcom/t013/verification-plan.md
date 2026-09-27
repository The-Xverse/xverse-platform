# T013 Verification Plan — Named Checks, Commands, and Negative Cases (pre-code)

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T013 (capability 007, slice `T-CORE`) |
| Stage / role | plan → verification plan (pre-code) |
| Revision | 1 |
| Baseline revision | `863f11ac990c1ce178a0f9d8eb2489e4a5243fe7` |
| Requirement authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Check framework | CMake/CTest over the T011-admitted offline envelope plus the repository-owned Fabro gate and the T007–T010 register validators |
| Classification | Public-safe engineering work product |

This plan is written **before** implementation. The implementation must realize every named check with the
stated expected result. Weakening an expected result is a verification-contract change requiring review.
T013's executable checks are the core-type CTest executables, a full-suite `ctest` run, and the source
inspections that prove bounds, neutrality, offline behaviour, and public safety; the governance checks are
the deterministic gate and the T007–T010 register validators.

## 2. Deterministic gate (primary)

From the repository root:

```sh
python3 /home/jefferson/x-verse_fabric/automation/xcom_feature_gate.py verify T013 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7
```

For T013 this gate requires:

- the six work products `docs/engineering/xcom/t013/{requirements,architecture,detailed-design,unit-specifications,verification-plan,implementation}.md`
  present (the implementation record exists only after the implementation stage);
- the T013 checkbox in `specs/007-xcom-core/tasks.md` marked complete (**implementation stage only**; the
  plan stage leaves it unchecked, per the stage instruction);
- at least one changed path that starts with `src/xverse/xcom/`;
- `cmake -S . -B build/fabro-t013 -G Ninja -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build/fabro-t013 --parallel 4`,
  a non-empty `ctest --test-dir build/fabro-t013 -N`, and
  `ctest --test-dir build/fabro-t013 --output-on-failure --parallel 4` all exit 0;
- `git diff --check <baseline> --` clean.

### 2.1 Environment prerequisite (A-1, inherited)

The gate inherits the run process environment and does not export the three admitted offline inputs. As
accepted for T012/T019/T020, if the gate's plain configure fails closed at the T025 test-toolchain
admission check, the only permitted resolution is the narrow A-1 cache seeding already recorded by those
slices: one configure carrying `XVERSE_XCOM_TOOLCHAIN`, `XVERSE_XCOM_PACKAGE_MANIFEST`, and
`XVERSE_XCOM_T025_TEST_TOOLCHAIN` as explicit, previously admitted cache values seeds the gate's own
git-ignored `build/fabro-t013` cache; the gate's unmodified configure/build/`ctest` sequence then reuses
it. The hash-verified preflight is unchanged, no ambient path or network resolution is added, no
admission check is weakened, and the admitted input **values** are recorded by name only.

## 3. Supporting commands (same tools, offline)

```sh
git rev-parse 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7
python3 scripts/validate_xcom_task_ownership.py --verify
python3 scripts/validate_xcom_task_ownership.py --check-human
python3 scripts/validate_xcom_requirements_traceability.py --verify
python3 scripts/validate_xcom_architecture_contracts.py --verify
python3 scripts/validate_xcom_unit_design.py --verify
git diff --name-only 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7 --
git diff --check 863f11ac990c1ce178a0f9d8eb2489e4a5243fe7 --
git ls-files --others --exclude-standard
```

`git rev-parse` for the baseline must print the baseline SHA. The register validators must still pass with
the shared T007–T010 artifacts unchanged in substance. The integration policy's `unit`, `integration`,
`validation`, and `static_analysis` measures are executed by the later T035–T040 stages; this plan
requires the T013 candidate not to break them.

## 4. Nominal checks

| ID | Name | Command / inspection | Expected |
| --- | --- | --- | --- |
| CHK-01 | Baseline and task binding | `git rev-parse <baseline>`; read `specs/007-xcom-core/tasks.md` | the baseline resolves to the exact SHA; the T013 entry exists and states the immutable contract/item/origin/time/correlation/diagnostic/policy scope |
| CHK-02 | Changed-path boundary | `git diff --name-only <baseline> --` | only the four T013 production files, the two T013 test files, the T013 work products, the one-line `tasks.md` checkbox, and the package record appear; no `xdl/`, `proto/`, `src/xverse_xdl/`, `.cmake`, root/`CMakeLists.txt`, or other task's path |
| CHK-03 | Core-type inventory and public API | read `core_types.hpp`, `value.hpp`, `contract.hpp`, `item.hpp`, `diagnostic.hpp`, `result.hpp`; build | every T013 type/symbol in `unit-specifications.md` §3 is declared and compiles; `FlowPolicy`, `OrderingPolicy`, `ReliabilityPolicy`, `OverflowPolicy`, `FlowPolicyInput` are present |
| CHK-04 | Domain neutrality and no cross-clock inference | inspect `contract.hpp`/`item.hpp`/`value.hpp`; run the neutrality scan | no ECU/CAN/SOME/IP/product primitive; logical identity is independent of provider/protocol/address/realization; `Timestamp` exposes only a magnitude and the item carries one explicit clock-domain identity with no cross-domain comparison API |
| CHK-05 | Fail-closed construction | run `xcom_core_types_negative`; inspect the factories | every rejected input yields a non-empty `DiagnosticSet` and no value; no partial or default-substituted value is exposed |
| CHK-06 | Policy vocabulary and range exactness | run `xcom_core_types_unit`; cross-read `xdl/profiles/xcom-v0.1.schema.json` flow-policy | the accepted and rejected value sets equal the Profile form exactly; `deadline_ms`/`retry`/`queue_depth` ranges are 0–600000 / 0–64 / 1–65536; `to_string` returns the Profile external text |
| CHK-07 | Diagnostic determinism | run `xcom_core_types_unit`/`xcom_core_types_negative`; inspect `ordering_key` | reordered equivalent invalid inputs serialize to byte-identical sequences; the ordering key is `phase\|severity\|code\|identity\|reason\|correction`; the new `policy`/`XCOM-TYPE-E006` values order consistently |
| CHK-08 | Immutability and value semantics | run `xcom_core_types_unit`; inspect declarations | const accessors only; assignment deleted; `noexcept` copy; a copied/`std::move`d source stays valid and unchanged; `FlowPolicy` copies and compares by declared field |
| CHK-09 | Bounds and finite resources | run the boundary cases; inspect the capacity constants | identity ≤ 128, version ≤ 32, payload ≤ 65,536, diagnostic text ≤ 256, set ≤ 32; policy ranges as CHK-06; no unbounded queue/quota/retry/depth |
| CHK-10 | Offline and bounded | forbidden-API source scan; successful offline build | no network/socket/resolver, ambient/secret lookup, filesystem, process/subprocess, or legacy access; standard library only; no added thread or dependency |
| CHK-11 | Public safety | scan committed source, tests, and work products | no credential, private address, unrestricted payload, proprietary excerpt, environment-specific absolute host path, or sensitive deployment value; diagnostic text is fixed and non-sensitive |
| CHK-12 | Doxygen for new/changed declarations | inspect the changed declarations; run the existing documentation validator | every new/changed public declaration has a `@brief`; the new policy API additionally carries ownership/lifetime/thread-safety/failure clauses; the admitted configuration is unchanged |
| CHK-13 | Build and full suite | `cmake --build <build> --parallel 4`; `ctest --test-dir <build> --output-on-failure --parallel 4` | build exits 0; `100% tests passed` (the existing 248 targets, including the extended `xcom_core_types_*`) |
| CHK-14 | Registers and REF-002 | run the §3 register validators; inspect the REF-002 disposition | the validators pass unchanged; `ref002.disposition == unchanged` with an empty `promoted` list; the requirement/unit/check indices agree |
| CHK-15 | Governance boundary | `git diff --name-only <baseline> --`; inspect tests | no accepted requirement/ADR/contract/schema changed; no existing test removed, renamed, or weakened; no later task implemented; only T013-owned paths and work products change |
| CHK-16 | Deterministic gate and diff hygiene | run the §2 gate; `git diff --check <baseline> --` | exit 0 with a `ctest:` count; the diff is whitespace-clean; the T013 checkbox is complete only at the implementation stage |
| CHK-17 | Capability documents | `git diff --name-only <baseline> -- specs/007-xcom-core` | the only capability-document change is the T013 checkbox line; no requirement, contract, ADR, or schema statement is edited |
| CHK-18 | Attribution anomaly recorded | inspect `requirements.md` §7.3/§8.2 and the unchanged registers | the T008/T010 attribution anomaly is recorded and not rewritten; the T013 source follows `tasks.md`/`XCOM-CMP-004`; nothing is promoted |

## 5. Negative cases

Each negative case injects one controlled defect and asserts the declared fail-closed behaviour with no
partial value, no accepted evidence of a weakened policy, and no output claiming acceptance.
NEG-01..NEG-12 are executable core-type cases; NEG-13..NEG-18 are executable policy/result cases;
NEG-19..NEG-25 are inspection/repository probes.

| ID | Injected defect | Expected result |
| --- | --- | --- |
| NEG-01 | empty required contract identity | `CommunicationContract::create` fails with `required_field`; no value |
| NEG-02 | identity longer than 128 bytes | `bound_exceeded` failure; no value |
| NEG-03 | malformed semantic version (`""`, `01.0.0`, `1.0`, `1.a.0`) | `required_field`/`invalid_version` failure; no value |
| NEG-04 | incompatible interaction/direction tuple | `incompatible_direction` failure; no value |
| NEG-05 | unknown interaction or direction enumeration value | failure; no value |
| NEG-06 | item metadata differs from its contract | `contract_mismatch` failure; no value |
| NEG-07 | item missing/empty required identity | `required_field` failure; no value |
| NEG-08 | payload larger than 65,536 bytes | `bound_exceeded` failure; no value |
| NEG-09 | unknown `OriginKind` value | failure; no value |
| NEG-10 | diagnostic with empty reason/correction | `Diagnostic::create` returns no value |
| NEG-11 | unknown `DiagnosticCode`/`DiagnosticSeverity`/`ValidationPhase` value | `Diagnostic::create` returns no value; `to_string` stays bounded |
| NEG-12 | empty diagnostic set | `DiagnosticSet::create`/`create_from_inputs` returns no value |
| NEG-13 | unknown `OrderingPolicy`/`ReliabilityPolicy`/`OverflowPolicy` value | `FlowPolicy::create` fails with `XCOM-TYPE-E006` (`invalid_policy`); no value |
| NEG-14 | `deadline_ms` < 0 or > 600,000 | `invalid_policy` failure naming `deadline_ms`; no value |
| NEG-15 | `retry` < 0 or > 64 | `invalid_policy` failure naming `retry`; no value |
| NEG-16 | `queue_depth` 0 or > 65,536 | `invalid_policy` failure naming `queue_depth`; no value |
| NEG-17 | several policy violations in different input order | the same exact sorted `XCOM-TYPE-E006` phase-`policy` sequence for both orders; no value |
| NEG-18 | construct a `Result<T>` whose failure alternative is an empty diagnostic set | unreachable through the public factories; exclusivity holds |
| NEG-19 | attempt a cross-clock-domain comparison/order in the core | no such API exists; CHK-04 fails if introduced |
| NEG-20 | introduce network, ambient, filesystem, process, or legacy access in a core unit | CHK-10 forbidden-API scan fails; the candidate is rejected |
| NEG-21 | change a non-T013 path or implement a later task (e.g. a T014/T015 header or a build file) | CHK-02/CHK-15 fail; the candidate exceeds the T013 boundary |
| NEG-22 | remove, rename, or weaken an existing core-type test case | CHK-15 fails; no test may be removed or weakened |
| NEG-23 | introduce an environment-specific absolute host path, credential, or sensitive value into a committed file | CHK-11 public-safety scan fails; the candidate is rejected |
| NEG-24 | mark the T013 checkbox complete in the plan stage | the deterministic gate fails ("not marked complete after implementation" is the implementation-stage rule; the plan stage leaves it unchecked) |
| NEG-25 | add a new admitted dependency or a non-standard-library include to a core unit | CHK-10 fails; the admitted dependency set is unchanged |

## 6. Evidence retention (candidate-bound)

For the implementation-stage candidate revision, retain:

- the exact candidate revision and the baseline SHA;
- `command_argv`, `exit_code`, and bounded observed output for the deterministic gate and each supporting
  command;
- the configure/build/CTest results, including the `ctest -N` count and the `100% tests passed` line;
- the `xcom_core_types_unit`, `xcom_core_types_negative`, and `xcom_core_types_external_consumer` results;
- the policy vocabulary/range cross-read against `xdl/profiles/xcom-v0.1.schema.json`;
- the exact policy diagnostic sequence produced by NEG-17;
- the changed-path list and the package record `reports/xcom-queue/t013-package.json` with per-file
  SHA-256;
- the register-validator results and the unchanged REF-002 disposition.

Public evidence omits host-specific, prefix, manifest, test-toolchain, temporary, and private-store
absolute paths. Missing, stale, mismatched, skipped, or failed evidence cannot support acceptance.

## 7. Exit criteria

T013 verification is complete when: the deterministic gate passes (CHK-16); every nominal check in §4 has
its expected result; every negative case in §5 fails closed as stated; the register validators still pass
with REF-002 unchanged (CHK-14); the change is confined to the T013 core and work-product boundary
(CHK-02, CHK-15, CHK-17, CHK-18); and a separate DeepSeek internal review records a passing verdict with
no findings. This does not constitute user acceptance, which remains T041.

## 8. Requirement-to-check coverage

| Requirement | Checks |
| --- | --- |
| T013-STK-001 | CHK-02, CHK-03, CHK-13 |
| T013-STK-002 | CHK-05, CHK-09, NEG-01..NEG-18 |
| T013-STK-003 | CHK-08, CHK-12 |
| T013-STK-004 | CHK-04, CHK-10 |
| T013-STK-005 | CHK-02, CHK-14, CHK-15, CHK-18 |
| T013-SR-001 | CHK-03, CHK-05, CHK-09 |
| T013-SR-002 | CHK-03, CHK-04, CHK-08 |
| T013-SR-003 | CHK-03, CHK-04, CHK-09 |
| T013-SR-004 | CHK-06, CHK-09 |
| T013-SR-005 | CHK-05, CHK-06, NEG-13..NEG-17 |
| T013-SR-006 | CHK-06, CHK-08 |
| T013-SR-007 | CHK-06 |
| T013-SR-008 | CHK-07, NEG-11, NEG-17 |
| T013-SR-009 | CHK-06, CHK-07, CHK-12 |
| T013-SR-010 | CHK-03, CHK-08, NEG-18 |
| T013-SR-011 | CHK-09 |
| T013-SR-012 | CHK-04, NEG-19 |
| T013-SR-013 | CHK-10, NEG-20, NEG-25 |
| T013-SR-014 | CHK-11, NEG-23 |
| T013-SR-015 | CHK-12 |
| T013-SR-016 | CHK-02, CHK-14, CHK-15, CHK-18 |
| T013-SR-017 | CHK-16, NEG-24 |

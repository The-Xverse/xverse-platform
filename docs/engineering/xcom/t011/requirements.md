# T011 Requirements — Pinned and Admitted Compiler, Build, JSON, gRPC/Protocol Buffers, Static-Analysis, Sanitizer, and Doxygen Environment

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T011 (capability 007, phase 2 repository-owned engineering baseline) |
| Stage / role | plan → requirements |
| Revision | 1 |
| Baseline revision | `5050666bf38fc98920dc455a85a88c08c46a2133` |
| Predecessor task | T010 (unit design, ownership, lifetime, thread-safety, failure semantics, bounds, Doxygen plan; reviewed terminal package `abb8168`) |
| Successor tasks | implementation slices T012–T034, integration/evidence T035–T038, and review/acceptance T039/T041 |
| Requirement ID families | `T011-STK-###` (stakeholder), `T011-SR-###` (software/engineering) |
| Authority | the T011 entry in `specs/007-xcom-core/tasks.md`; `specs/007-xcom-core/plan.md` "Technical Context", "Delivery phases" step 2, "Decision gates" (Dependency admission), "Complexity Tracking"; `specs/007-xcom-core/spec.md` FR-001/FR-002/FR-005, FR-026/FR-027, FR-029/FR-030, FR-035 and SC-009; Constitution 2.1.0 articles VII, IX, X and the capability acceptance gates; ADR-0018, ADR-0019, ADR-0020; ACC001–ACC015; `docs/engineering/xcom/task-ownership.{md,json}` (T007); `docs/engineering/xcom/t008/{requirements-register,traceability-matrix}.{json,md}` (T008); `docs/engineering/xcom/t009/{architecture,architecture-model}.{md,json}` (T009); `docs/engineering/xcom/t010/{detailed-design,unit-specifications}.md` `XCOM-DU-029` and `DOX-GAP-01..03` (T010) |
| Admitted-foundation inputs (read-only evidence) | `docs/engineering/xcom/build-environment.md`, `docs/engineering/xcom/dependency-lock.md`, `scripts/xcom_dependency_preflight.py`, `cmake/XComOfflineDependencies.cmake`, `cmake/XComWarnings.cmake`, `CMakeLists.txt`, `Doxyfile`, `scripts/check_doxygen.py` |
| Classification | Public-safe engineering work product |

### 1.1 Authority statement

This document specifies only the bounded T011 slice. T011 **pins and admits the X-COM build and dependency
environment**: the compiler/build envelope and the exact `nlohmann/json`, gRPC, Protocol Buffers,
static-analysis, sanitizer (where supported), and Doxygen environment, with licenses, content hashes,
generated-code provenance, and a reproducible/offline strategy. T011 is an engineering-baseline enabler
that **precedes production code** (tasks.md dependency order: T007–T011 precede T012+).

T011 elaborates the accepted capability-007 plan and the T010 unit-design obligation for
`XCOM-DU-029` ("Dependency admission and build lock"). It does **not** redesign the accepted architecture,
change an accepted functional requirement, success criterion, ADR, contract, or ownership boundary, weaken an
existing requirement or test, author C++/Python production or test source, fix production numeric bound
values, or mark any task other than T011 complete. It does not promote any REF-002 target requirement to
implemented.

T011 is a **repository-owned work-product task**. Its candidate may change documentation/governance artifacts
and the deterministic package/evidence records under `docs/engineering/xcom/t011/` and
`reports/xcom-queue/`, but the deterministic gate rejects any T011 change under `src/`, `tests/`, or `xdl/`
(T011-SR-012). The admitted-foundation artifacts listed in §1 are owned by the `T-INTG` slice and the shared
build paths; T011 consumes them as read-only evidence and records any required change as a gap with its owner
(§8.2) rather than editing them.

### 1.2 Decision rule

Any conflict between this candidate and the accepted capability 007 specification, the accepted plan and
contracts, the constitution, an accepted ADR, the T007 ownership register, the T008 register/matrix, the T009
architecture model, or the T010 unit design is resolved in favour of the accepted source. A material gap is
reported rather than guessed. Unresolved gaps are recorded in §8.

### 1.3 Baseline reconciliation of the admitted foundation

The repository baseline already contains an accepted-prototype build/dependency foundation
(`build-environment.md`, `dependency-lock.md`, `scripts/xcom_dependency_preflight.py`, `cmake/*.cmake`,
`CMakeLists.txt`, `Doxyfile`, `scripts/check_doxygen.py`) produced under the earlier `specs/008`–`specs/011`
build-foundation work. Under capability 007 those artifacts are **allocated to T011 for admission and are not
yet user-accepted under this capability**; the T007 register records `T011: allocated`. T011 therefore
(a) maintains the repository-owned requirement/design/verification work products that admit the environment,
(b) re-binds the existing foundation to the capability-007 requirement IDs, and (c) records the residual
gaps with their owning tasks. T011 claims no new runtime, compatibility, parity, or production-readiness
behavior.

## 2. Scope

### 2.1 In scope (bounded T011)

Keep T011 strictly inside the T011 task entry: *"Pin and admit the compiler, build, `nlohmann/json`,
gRPC/Protocol Buffers, static-analysis, sanitizer, and Doxygen environment with licenses, hashes,
generated-code provenance, and a reproducible/offline strategy."*

1. **Pin the build envelope**: C++20, CMake ≥ 3.22, Ninja ≥ 1.10, a `c++` compiler accepting
   `-Wall -Wextra -Wpedantic -Werror`, `BUILD_TESTING=ON`, Python ≥ 3.11, and `dpkg-deb`; declare which of
   these are host prerequisites versus members of the pinned dependency lock.
2. **Pin the exact dependency set**: the twelve retained `amd64`/`all` Ubuntu 22.04 LTS (Jammy) package
   objects that supply `nlohmann/json` 3.10.5, Protocol Buffers 3.12.4, gRPC 1.30.2, and clang-tidy/LLVM
   14.0.0, each with retained filename, byte size, SHA-256, Debian package name, exact version, source package,
   primary license, and public pool retrieval coordinate.
3. **Admit by content, twice**: verify each retained archive against the manifest and the compiled-in lock,
   then verify the **extracted** prefix payload (executables, headers, libraries, pkg-config metadata, file
   types, file content, symlinks and their recursively reached targets) so an archive hash is never treated as
   proof of an independently provisioned prefix.
4. **Record generated-code provenance**: the exact `protoc` and `grpc_cpp_plugin` package identity and
   SHA-256, plus the requirement that every future generated-code output records the input schema identity and
   generation command.
5. **Define the reproducible/offline strategy**: explicit absolute inputs `XVERSE_XCOM_TOOLCHAIN` and
   `XVERSE_XCOM_PACKAGE_MANIFEST`; retrieval deliberately separated from admission; extraction-only prefix
   reconstruction with no apt/registry/network/maintainer-script execution; CMake package-registry and
   FetchContent network resolution disabled; imported targets resolved only beneath the admitted prefix.
6. **Classify admission failure**: stable nonzero process classes and deterministic `XCOM-BLD-E…` diagnostics;
   success emits exactly `XCOM-BLD-I000` with `admitted: true`; a failure never reports admission.
7. **Specify the host verification-evidence contract**: the five required measures (`VM-BLD-UNIT`,
   `VM-BLD-LINT`, `VM-BLD-STATIC`, `VM-BLD-INTEGRATION`, `VM-BLD-VALIDATION`), network-disabled enforced
   isolation, bounded logs, private raw environment manifests, and a repository-owned `index.json` binding
   each measure to the exact candidate revision and to log/manifest hashes.
8. **Disposition sanitizer and Doxygen admission**: state how the sanitizer compiler/analysis capability and
   the Doxygen configuration are admitted; record the strict Doxygen C++ configuration gap (`DOX-GAP-01..03`)
   and its owner rather than claiming warning-free generation.
9. **Document licenses, environment limits, and maturity**: identify the admitted licenses, the ABI/transitive
   limitation of the envelope, and the prototype-only, non-production maturity, excluding sensitive data.
10. **Preserve the accepted architecture, ADRs, dependency direction, domain neutrality, safety boundaries,
    REF-002 dispositions, ownership, and dependency order**; declare T011's new artifacts to the owning
    `T-ENABLER` slice and re-validate the T007 register without weakening it.

### 2.2 Explicit exclusions (must remain absent from the T011 candidate)

No production or test source is created or modified; no `src/`, `tests/`, or `xdl/` path is changed; no
`proto/` definition is authored (T030 owns the gateway `.proto`); no admitted-foundation artifact is edited
without its owner; no package is installed, downloaded, or built; no network endpoint, package manager,
registry, or TCP listener is used or required; no legacy repository, binary, or workload is read, executed, or
modified; no compilation, linking, or runtime execution occurs as part of T011 verification; no accepted ADR,
accepted requirement, accepted contract, other task's work product, or existing test is rewritten or
weakened; no production numeric bound value is fixed; no unit or capability the accepted plan does not
sanction is invented; no other task is marked complete; no software candidate is accepted or integrated; no
SESN artifact is created, rewritten, or extended; no REF-002 target is promoted to implemented.

### 2.3 Delegated to later tasks (not implemented or decided here)

| Area | Owner | Disposition in T011 |
| --- | --- | --- |
| X-COM CMake/CTest runtime targets and warning-as-error rules under `src/xverse/xcom/` | T012 | allocated; T011 admits the envelope those targets inherit |
| C++ production and test source for the core, XDL decode, observation, stimulation, gateway | T013–T034 | allocated; T011 admits only the offline toolchain they consume |
| Full sanitizer/static/Doxygen **execution** over the runtime targets | T035, T036, T037 | allocated; T011 admits the toolchain and configuration contract, not the executed evidence |
| Warning-free generated Doxygen reference and public-safety log validation | T037, T038 | allocated |
| Independent review and user acceptance of T011's own candidate | T039, T041 | allocated |
| Transitive host libraries and a pinned base-system ABI | later authorized slice | deferred; T011 records the envelope limitation (§8.1) |

## 3. Stakeholder requirements (`T011-STK-###`)

Stakeholder requirements state the outcome the program needs from the engineering baseline. `MUST`/`SHALL`
phrasing is normative.

- **T011-STK-001**: Before any X-COM production code is authored, the program **shall** have a pinned,
  content-verified, offline-reproducible build and dependency environment for capability 007.
- **T011-STK-002**: Every admitted third-party artifact **shall** be identifiable by exact Debian package name
  and version, source package, primary license, byte size, and SHA-256, and be retrievable from a recorded
  public coordinate; an unlisted or drifted artifact **shall** be rejected.
- **T011-STK-003**: Generated code **shall** be attributable to the exact generator package and content hash,
  input schema, and generation command.
- **T011-STK-004**: Admission **shall** fail closed with a classified, deterministic, nonzero result and
  **shall** never report readiness when any required input, artifact, tool, header, library, metadata, or
  payload is missing or mismatched.
- **T011-STK-005**: Public admission documentation and evidence **shall** exclude credentials, private
  addresses, unrestricted payloads, proprietary source excerpts, absolute host paths, and sensitive
  deployment values, and **shall** state the prototype-only maturity and the envelope's limits honestly.

## 4. Software/engineering requirements (`T011-SR-###`)

Each requirement is written in EARS style, carries a stable verification intent, and links to the accepted
requirement it refines. "Implemented" here means "the repository-owned work product and its deterministic
check exist and pass"; it is not a runtime or production claim.

### 4.1 Build envelope

- **T011-SR-001 [ubiquitous]**: The X-COM build envelope **shall** require C++20, CMake ≥ 3.22, a Ninja
  generator, `BUILD_TESTING=ON`, Python ≥ 3.11, `dpkg-deb`, and a `c++` compiler accepting
  `-Wall -Wextra -Wpedantic -Werror`, and **shall** fail closed when any member is unavailable or the warning
  policy is not promoted to an error.
  - Refines: `XCOM-BLD-001`, `XCOM-SW-ENB-004`; anchors FR-029, FR-030; SC-009.
  - Verification intent: self-test with present/missing/version-mismatched tool descriptions and an
    intentional-warning rejection probe; enforce the same policy in `CMakeLists.txt`,
    `cmake/XComWarnings.cmake`, and `cmake/XComOfflineDependencies.cmake`.

### 4.2 Exact dependency admission

- **T011-SR-002 [ubiquitous]**: Dependency admission **shall** verify the exact retained filename, byte size,
  SHA-256, Debian package name, exact version, source package, and primary license of each of the twelve
  locked Jammy objects before reporting readiness.
  - Refines: `XCOM-BLD-002`; anchors FR-026, FR-027; SC-009.
  - Verification intent: manifest schema/count/uniqueness/digest checks plus `dpkg-deb -f` control-metadata
    probes.
- **T011-SR-003 [ubiquitous]**: Admission **shall** additionally bind the **extracted** prefix payload to the
  hash-verified archives by comparing every required executable, header, library, pkg-config file, file type,
  file content, symlink text, and recursively reached symlink target against a disposable reference extraction.
  - Refines: `XCOM-BLD-002`; anchors FR-026.
  - Verification intent: `--verify-toolchain` payload comparison; classified `PAYLOAD_MISMATCH` on drift.
- **T011-SR-004 [ubiquitous]**: The dependency lock **shall** be usable repeatedly offline from the admitted
  package set without resolving an ambient or "latest" dependency, and **shall** consume only the two explicit
  absolute inputs.
  - Refines: `XCOM-BLD-003`; anchors FR-026, FR-027.
  - Verification intent: run the documented commands with network access absent; CMake package registries and
    FetchContent network resolution disabled; imported targets resolved only beneath the admitted prefix.

### 4.3 Generated-code provenance and analysis tools

- **T011-SR-005 [ubiquitous]**: The admission **shall** record the exact `protoc` and `grpc_cpp_plugin`
  generator package identity and SHA-256, and **shall** require every future generated-code output to record
  the generator provenance, input schema identity, and generation command.
  - Refines: `XCOM-BLD-002`; anchors FR-005, FR-029.
  - Verification intent: generator version/provenance probes; documentation-field validation of the
    generated-code statement.
- **T011-SR-006 [where-supported]**: When the admitted compiler supports AddressSanitizer, ThreadSanitizer,
  UndefinedBehaviorSanitizer, or libFuzzer, the build envelope **shall** expose them as opt-in, and **shall**
  record that they are compiler-provided rather than pinned package members; unsupported sanitizers **shall**
  be reported, not silently assumed.
  - Refines: `XCOM-BLD-001`, `XCOM-SW-ENB-004`; anchors FR-030; plan "Testing"/"Delivery phases" step 2.
  - Verification intent: compiler-capability probe recorded in the build-policy evidence; sanitizer execution
    evidence is T035's, not T011's.

### 4.4 Classified failure semantics

- **T011-SR-007 [ubiquitous]**: Admission **shall** emit deterministic JSON with `admitted: false`, one or
  more `XCOM-BLD-E…` diagnostics, and the numerically lowest applicable nonzero class from the stable set
  `INPUT_MISSING (2)`, `MANIFEST_INVALID (3)`, `PACKAGE_MISSING (4)`, `HASH_MISMATCH (5)`, `TOOL_MISSING (6)`,
  `VERSION_MISMATCH (7)`, `HEADER_MISSING (8)`, `LIBRARY_MISSING (9)`, `METADATA_MISSING (10)`,
  `POLICY_INVALID (11)`, `IO_ERROR (12)`, `PROBE_FAILED (13)`, `TIMEOUT (14)`, `PAYLOAD_MISMATCH (15)`;
  success **shall** emit exactly `XCOM-BLD-I000` with `admitted: true`.
  - Refines: `XCOM-BLD-004`; anchors FR-025, FR-027; SC-010 (review), Constitution IX.
  - Verification intent: negative fixtures for every class; real-input failures produce a classified nonzero
    exit and never a pass.
- **T011-SR-008 [ubiquitous]**: Admission **shall** be bounded and side-effect-free toward its inputs: local
  file reads, SHA-256, bounded local subprocesses, temporary directories only; no resolver, network client,
  package installation, or modification of either explicit input.
  - Refines: `XCOM-BLD-003`, `XCOM-BLD-004`; anchors FR-026, FR-027.
  - Verification intent: source inspection plus over-bound/unreadable probes producing `IO_ERROR`/`TIMEOUT`.

### 4.5 Documentation, evidence, and governance

- **T011-SR-009 [ubiquitous]**: The build documentation **shall** identify licenses, hashes, generated-code
  provenance, explicit inputs, environment/ABI limits, the package-versus-payload semantics, and the
  prototype-only maturity, and **shall** pass a public-safety scan.
  - Refines: `XCOM-BLD-005`; anchors FR-027, FR-029, FR-030; SC-009.
  - Verification intent: repository-document validation plus manual public-safety inspection.
- **T011-SR-010 [ubiquitous]**: The host verification evidence **shall** bind each of the five required
  measures (`VM-BLD-UNIT`, `VM-BLD-LINT`, `VM-BLD-STATIC`, `VM-BLD-INTEGRATION`, `VM-BLD-VALIDATION`) to the
  exact candidate revision with `command_argv`, `exit_code`, `outcome`, network-disabled isolation, a bounded
  log, and hashes of the log and a private raw environment manifest, in a repository-owned `index.json`.
  - Refines: `XCOM-BLD-003`, `XCOM-BLD-004`; anchors FR-027, FR-030; Constitution X.
  - Verification intent: review the five revision-matching records, recompute both hashes, and confirm
    network-disabled isolation; missing/stale/mismatched/skipped/failed evidence cannot support acceptance.
- **T011-SR-011 [ubiquitous]**: T011 **shall** preserve accepted intent: it **shall not** modify `src/`,
  `tests/`, or `xdl/`; **shall not** rewrite an accepted ADR, requirement, contract, or existing test; **shall
  not** edit an admitted-foundation artifact owned by another slice; and **shall** record every residual gap
  with its owning task and disposition.
  - Refines: Constitution VII/VIII; ADR-0020; T007 prohibitions.
  - Verification intent: `git diff --name-only <baseline>` contains no prohibited path; the gap register §8.2
    is complete.
- **T011-SR-012 [ubiquitous]**: The T011 candidate **shall** satisfy the deterministic Fabro gate for
  work-product tasks: the six named work products present, `git diff --check` clean, the T011 checkbox marked
  complete only in the implementation stage (not in plan), and no `src/`, `tests/`, or `xdl/` change.
  - Refines: ADR-0020; Constitution X.
  - Verification intent: run `xcom_feature_gate.py verify T011 <baseline>`.
- **T011-SR-013 [ubiquitous]**: T011 **shall** reconcile with the T007 ownership register, the T008
  requirement register/matrix, the T009 architecture model, and the T010 unit design, re-validating those
  registers without weakening them, and **shall** keep REF-002 dispositions unchanged with no promotion.
  - Refines: `XCOM-SW-ENB-002`, `XCOM-SW-ENB-004`; anchors FR-035, FR-030.
  - Verification intent: `scripts/validate_xcom_task_ownership.py --verify --check-human` and the T008/T009/T010
    validators still pass; the REF-002 disposition in the T008 matrix is unchanged.

## 5. Requirement-to-accepted-anchor traceability

| T011 requirement | Accepted software req | System req | Spec anchor | Success criterion / constitution |
| --- | --- | --- | --- | --- |
| T011-STK-001 | XCOM-SW-ENB-004 | XCOM-SYS-FR-029/030 | FR-029, FR-030 | SC-009; VII, X |
| T011-STK-002 | XCOM-BLD-002 | XCOM-SYS-FR-026/027 | FR-026, FR-027 | SC-009; X |
| T011-STK-003 | XCOM-BLD-002 | XCOM-SYS-FR-005 | FR-005 | IX, X |
| T011-STK-004 | XCOM-BLD-004 | XCOM-SYS-FR-025 | FR-025, FR-027 | IX, X |
| T011-STK-005 | XCOM-BLD-005 | XCOM-SYS-FR-027 | FR-027 | Constitution X |
| T011-SR-001 | XCOM-BLD-001 | XCOM-SYS-FR-029 | FR-029 | SC-009 |
| T011-SR-002 | XCOM-BLD-002 | XCOM-SYS-FR-026/027 | FR-026, FR-027 | SC-009 |
| T011-SR-003 | XCOM-BLD-002 | XCOM-SYS-FR-026 | FR-026 | X |
| T011-SR-004 | XCOM-BLD-003 | XCOM-SYS-FR-026/027 | FR-026, FR-027 | X |
| T011-SR-005 | XCOM-BLD-002 | XCOM-SYS-FR-005/029 | FR-005, FR-029 | IX, X |
| T011-SR-006 | XCOM-BLD-001 | XCOM-SYS-FR-030 | FR-030 | X |
| T011-SR-007 | XCOM-BLD-004 | XCOM-SYS-FR-025 | FR-025 | SC-010; IX |
| T011-SR-008 | XCOM-BLD-003/004 | XCOM-SYS-FR-026/027 | FR-026, FR-027 | IX |
| T011-SR-009 | XCOM-BLD-005 | XCOM-SYS-FR-027/029 | FR-027, FR-029, FR-030 | SC-009 |
| T011-SR-010 | XCOM-BLD-003/004 | XCOM-SYS-FR-030 | FR-030 | X |
| T011-SR-011 | XCOM-SW-ENB-004 | - | FR-027 | VII, VIII, X |
| T011-SR-012 | XCOM-SW-ENB-004 | - | FR-030 | X |
| T011-SR-013 | XCOM-SW-ENB-002/004 | XCOM-SYS-FR-035 | FR-035 | X |

The `XCOM-BLD-001`–`XCOM-BLD-005` software requirements originate in the accepted capability-007
build-foundation work (`specs/008-feat-2fcd9f8f42214262/software-requirements.md` …, `specs/011-…`) and refine
`XCOM-SW-ENB-004`. They remain the accepted requirement text; T011 does not rewrite them.

## 6. REF-002 disposition

T011 owns no REF-002 communication ID. It supports the T008 disposition of XVE-SYS-0139–0158 by providing the
reproducible engineering baseline those requirements are implemented and verified against. T011 changes no
required disposition: `ref002.disposition` stays `unchanged` with an empty `promoted` list (T011-SR-013). No
allocated, deferred, or target SADS requirement is reported as implemented.

## 7. Affected paths

### 7.1 Paths the T011 candidate changes (this task)

| Path | Change | Notes |
| --- | --- | --- |
| `docs/engineering/xcom/t011/requirements.md` | add | this document |
| `docs/engineering/xcom/t011/architecture.md` | add | admission architecture and boundaries |
| `docs/engineering/xcom/t011/detailed-design.md` | add | admission mechanisms and data model |
| `docs/engineering/xcom/t011/unit-specifications.md` | add | admitted units and work-product units |
| `docs/engineering/xcom/t011/verification-plan.md` | add | named checks, commands, negative cases |
| `docs/engineering/xcom/t011/implementation.md` | add (implementation stage) | realized change and evidence |
| `docs/engineering/xcom/t011/internal-review.json` | add (review stage) | DeepSeek internal review |
| `reports/xcom-queue/t011-package.json` | add (implementation stage) | exact-candidate package record |
| `specs/007-xcom-core/tasks.md` | edit T011 checkbox (implementation stage) | capability task ledger |
| `docs/engineering/xcom/task-ownership.{json,md}` | edit shared reconciliation (implementation stage) | re-validated, not weakened |

### 7.2 Admitted-foundation paths (read-only evidence; not changed by T011)

| Path | Owner | Role for T011 |
| --- | --- | --- |
| `docs/engineering/xcom/build-environment.md` | T-INTG (T035–T038) | build envelope, offline reconstruction, admission/build commands, exit-class table, host evidence contract |
| `docs/engineering/xcom/dependency-lock.md` | T-INTG (T035–T038) | twelve exact package records, licenses, retrieval coordinates, generated-code provenance |
| `scripts/xcom_dependency_preflight.py` | T-INTG (T035–T038) | offline admission checker and self-test |
| `cmake/XComOfflineDependencies.cmake` | shared (serialized) | controlled offline imported targets and admission gate |
| `cmake/XComWarnings.cmake` | shared (serialized) | warning-as-error policy module `xverse::xcom_warnings` |
| `CMakeLists.txt` | shared (serialized) | root build contract, policy probes, policy evidence |
| `Doxyfile`, `scripts/check_doxygen.py` | T-INTG (T037) | Doxygen configuration and coverage/HTML check |

## 8. Gaps, risks, and open items

### 8.1 Envelope limitations (recorded, not resolved by T011)

- `LIM-01` — **Transitive host libraries are not locked.** The twelve-package set does not lock all shared
  library dependencies of its executables or gRPC's base-system libraries (C/C++ runtime, LLVM/Clang runtime,
  OpenSSL, zlib, c-ares, Abseil, the Protocol Buffers runtime package). The envelope is limited to Linux
  x86-64 on an ABI-compatible Jammy-derived host. A later authorized slice must admit transitive artifacts or
  define and verify a pinned base-system ABI. This is a limitation, not a plan gap.
- `LIM-02` — **Compile-only link readiness.** The imported targets are compile-only top-level locators; they
  are not proof of a hermetic runtime link. Runtime link readiness is a later slice's claim.
- `LIM-03` — **Sanitizer/Doxygen execution.** T011 admits the toolchain/configuration contract; the executed
  sanitizer, static-analysis, and Doxygen evidence is T035–T037's.

### 8.2 Gaps with owning tasks

| Gap | Description | Owner | Disposition |
| --- | --- | --- | --- |
| `T011-GAP-01` | Strict Doxygen C++ configuration (`WARN_IF_UNDOCUMENTED`, `WARN_NO_PARAMDOC`, exclusion list) is not yet admitted; `Doxyfile` currently sets both to `NO` (`DOX-GAP-01`, `DOX-GAP-03`). | T011 (admission), T037 (execution) | allocated; T011 records the contract and does not claim warning-free generation |
| `T011-GAP-02` | Generated protobuf/gRPC C++ documentation and provenance policy is admitted but no generated C++ exists yet (`DOX-GAP-02`). | T011 (policy), T030–T032 (source) | allocated |
| `T011-GAP-03` | Sanitizer opt-in flags are not yet wired for the runtime targets; the compiler-provided sanitizer capability is recorded only as a probe obligation (T011-SR-006). | T012 (targets), T035 (execution) | allocated |
| `T011-GAP-04` | The admitted foundation was produced under the earlier `specs/008`–`011` work and is not yet user-accepted under capability 007. | T039/T041 | allocated; T011 submits the work products for review/acceptance |

### 8.3 Open items

- `OPEN-01` — Whether T011's implementation stage may adjust a shared build path (e.g. publish the sanitizer
  probe) is bounded by T011-SR-011 and the gate's prohibition on `src/`, `tests/`, `xdl/`; any such change is
  recorded in `implementation.md` with its exact revision and re-validated. Default plan: no shared-path change.

## 9. Definition of done (requirements view)

T011 is complete for this slice when: (a) `requirements.md`, `architecture.md`, `detailed-design.md`,
`unit-specifications.md`, `verification-plan.md`, and `implementation.md` exist under
`docs/engineering/xcom/t011/` and are mutually consistent; (b) every requirement in §3–§4 has at least one
named check in `verification-plan.md`; (c) the machine checks in §10 pass at the candidate revision; (d) the
gap register §8.2 is complete and no gap is silently closed; (e) the T011 checkbox is marked complete and the
package record is written; and (f) a separate DeepSeek internal review records a passing verdict with no
findings. This does **not** constitute user acceptance, which remains T041.

## 10. Requirement-to-check index (implemented in `verification-plan.md`)

| Requirement | Primary check(s) |
| --- | --- |
| T011-STK-001 | CHK-01, CHK-11, CHK-16 |
| T011-STK-002 | CHK-04, CHK-05, NEG-04..NEG-10 |
| T011-STK-003 | CHK-07, NEG-16 |
| T011-STK-004 | CHK-08, NEG-11..NEG-30 |
| T011-STK-005 | CHK-13, CHK-14 |
| T011-SR-001 | CHK-02, CHK-03, NEG-01..NEG-03 |
| T011-SR-002 | CHK-04, NEG-04..NEG-06 |
| T011-SR-003 | CHK-05, NEG-07, NEG-08, NEG-17 |
| T011-SR-004 | CHK-06, CHK-11, NEG-09, NEG-10 |
| T011-SR-005 | CHK-07, NEG-16 |
| T011-SR-006 | CHK-03, CHK-07 |
| T011-SR-007 | CHK-08, NEG-11..NEG-30 |
| T011-SR-008 | CHK-09, NEG-31..NEG-33 |
| T011-SR-009 | CHK-10, CHK-13, CHK-14 |
| T011-SR-010 | CHK-12 |
| T011-SR-011 | CHK-15, CHK-16 |
| T011-SR-012 | CHK-16, CHK-17, CHK-19 |
| T011-SR-013 | CHK-18, CHK-19 |

# T011 Architecture — Offline Dependency-Admission Boundary for the X-COM Build Envelope

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T011 (capability 007, engineering-baseline enabler) |
| Stage / role | plan → architecture |
| Revision | 1 |
| Baseline revision | `5050666bf38fc98920dc455a85a88c08c46a2133` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Design authority | [`detailed-design.md`](detailed-design.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed architecture | `docs/engineering/xcom/t009/architecture.md` (`XCOM-CMP-*`, `XCOM-XB-*`, `XCOM-XLC-*`); `docs/engineering/xcom/t010/detailed-design.md` `XCOM-DU-029` |
| Classification | Public-safe engineering work product |

## 2. Purpose and position in the delivery graph

T011 establishes the **engineering-baseline admission boundary** that must exist before any X-COM production
code is authored (tasks.md dependency order). It does not implement communication, observation, stimulation,
gateway, or runtime behavior. Its architecture is a small, deterministic, offline trust boundary:

- it **pins** an exact set of retained dependency objects and a build envelope;
- it **admits** a provisioned prefix by binding hash-verified archives to extracted payload and to probed
  tool/header/library/metadata identities;
- it **fails closed** with classified diagnostics; and
- it **documents** the admitted identity, provenance, licenses, limits, and the evidence contract.

Position in the accepted delivery order (T009 architecture model, reproduced here for T011's local view):

```text
T007 ownership register → T008 requirements/traceability → T009 architecture
   → T010 unit design → T011 dependency admission (this document)
   → T-CORE (T012–T016) → { T-XDL, T-OBS, T-STIM } → T-INTG (T035–T038) → T-REVIEW (T039/T041)
```

T011 is a **work-product-only** slice: its candidate changes documentation and package records, not
`src/`, `tests/`, or `xdl/`. It therefore also respects the constitution's platform-first rule: it admits a
platform-owned, domain-neutral C++20 toolchain and no legacy or domain artifact.

## 3. Boundary and context

### 3.1 System context

```text
        (controlled online staging, OUTSIDE admission)
  12 public Jammy pool objects ──► retained .debs beside the manifest ──┐
                                                                       │  transfer into offline host
                                                                       v
   ┌──────────────────────────────── XVERSE_XCOM_TOOLCHAIN (new prefix) ─────────────────────────────┐
   │  nlohmann/json 3.10.5   Protocol Buffers 3.12.4   gRPC 1.30.2   clang-tidy 14.0.0                │
   │  protoc, grpc_cpp_plugin, headers, libs (libprotobuf.a, libgrpc*.so), pkg-config metadata        │
   └───────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                               │  reads (offline, read-only)
   XVERSE_XCOM_PACKAGE_MANIFEST (12-entry JSON)┤
   repository lock + docs + checker            │
                                               v
   ┌─────────────────────── admission boundary (this task) ───────────────────────────────────────────┐
   │  scripts/xcom_dependency_preflight.py                                                            │
   │    manifest schema ─► archive identity ─► Debian control ─► extracted payload ─► host envelope     │
   │    ─► admission decision: XCOM-BLD-I000 admitted:true  |  XCOM-BLD-E… admitted:false (exit 2–15)   │
   └───────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                               │  admitted:true
                                               v
   ┌─────────────────────── offline build contract (consumes admission) ──────────────────────────────┐
   │  CMakeLists.txt + cmake/XComWarnings.cmake + cmake/XComOfflineDependencies.cmake                  │
   │    Ninja-only, C++20, BUILD_TESTING=ON, warnings-as-errors                                        │
   │    imported targets: nlohmann_json::nlohmann_json, protobuf::libprotobuf, protobuf::protoc,        │
   │                     gRPC::grpc, gRPC::grpc++, gRPC::grpc_cpp_plugin                                │
   │    compile-only probes: xverse_xcom_policy_probe, xverse_xcom_warning_rejection_probe              │
   │    evidence: xcom-build-policy.json (+ compile_commands.json)                                      │
   └───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Trust boundaries

| Boundary | Inside | Outside | Rule |
| --- | --- | --- | --- |
| `XB-1` Retrieval versus admission | the offline host, the two explicit inputs, the repository lock | the public Ubuntu pool, any network peer | retrieval is a separate controlled step; the checker performs no network access and never installs |
| `XB-2` Archive versus payload | the hash-verified `.deb` and its disposable extraction | a provisioned prefix that may be independently created | an archive hash is never accepted as proof of prefix content; payload is compared node-by-node |
| `XB-3` Host prerequisite versus pinned package | CMake, Ninja, Python, `c++`, `dpkg-deb` | the twelve pinned package objects | host tools are probed and identified but are not members of the twelve-package lock |
| `XB-4` Documentation versus evidence | the accepted requirement/design/verification work products | candidate-bound, hashed run evidence | documentation defines the evidence contract only; missing/stale evidence cannot support acceptance |
| `XB-5` Public versus private evidence | package filenames, hashes, versions, licenses, diagnostic codes, outcomes | manifest/prefix/host/temporary absolute paths | public artifacts exclude private or sensitive data |

### 3.3 Prohibited elements (must remain absent)

No TCP listener, no external network peer, no package manager or registry, no legacy repository read/write,
no legacy binary or workload execution, no dynamic plugin discovery, and no domain-specific primitive. These
inherit the T007 global prohibitions and the constitution.

## 4. Components

T011 names the components of the admission boundary and the admitted build contract. Each maps to a T011
work-product unit or an admitted-foundation unit in `unit-specifications.md`.

### 4.1 Admission boundary components

- **`XCOM-ADM-LOCK`** — the compiled-in lock of twelve exact package records (filename, size, SHA-256,
  package, version, source, license) plus the generated-code provenance entries, mirrored by
  `docs/engineering/xcom/dependency-lock.md`.
- **`XCOM-ADM-MANIFEST`** — the caller-supplied twelve-entry JSON manifest and its sibling retained archives;
  validated for schema, count, uniqueness, filename shape, size, and digest.
- **`XCOM-ADM-CHECKER`** — `scripts/xcom_dependency_preflight.py`, the offline admission engine implementing
  the ordered phases in §5 and the classified failure model.
- **`XCOM-ADM-PROBE`** — the bounded local probes: `dpkg-deb -f` control metadata, executable version checks,
  header/library/pkg-config presence and version checks, extracted-payload comparison, and a disposable
  CMake/Ninja compile-only policy probe.
- **`XCOM-ADM-DECISION`** — the deterministic admission decision and its serialization (`admitted`,
  `XCOM-BLD-I000`/`XCOM-BLD-E…`, lowest applicable exit class, sorted diagnostics).

### 4.2 Admitted build-contract components

- **`XCOM-BLD-ROOT`** — `CMakeLists.txt`: project identity, Ninja-only generator, C++20, `BUILD_TESTING=ON`,
  warning/dependency module inclusion, the compile-only policy probe, the intentional-warning rejection
  probe, the machine-readable `xcom-build-policy.json` evidence, and the conditional include of
  `src/xverse/xcom` when a later accepted slice supplies it.
- **`XCOM-BLD-WARN`** — `cmake/XComWarnings.cmake`: the `xverse::xcom_warnings` interface target and the
  `xverse_xcom_configure_warnings` / `xverse_xcom_apply_warnings` functions implementing
  `-Wall -Wextra -Wpedantic -Werror`.
- **`XCOM-BLD-DEPS`** — `cmake/XComOfflineDependencies.cmake`: explicit-input enforcement, invocation of the
  checker (`--cmake-dependency-check`), registry/FetchContent disabling, and the imported dependency targets.
- **`XCOM-BLD-DOXYGEN`** — `Doxyfile` and `scripts/check_doxygen.py`: the Doxygen configuration and the
  coverage/HTML check; the strict C++ configuration is a recorded gap (`T011-GAP-01`).

### 4.3 Work-product components

- **`XCOM-ADM-DOC`** — `docs/engineering/xcom/build-environment.md` and `dependency-lock.md`: the admitted
  identity, licenses, retrieval coordinates, offline reconstruction, environment/ABI limits, and
  requirement-to-check traceability.
- **`XCOM-ADM-EVIDENCE`** — the repository-owned `index.json` evidence contract for the five
  `VM-BLD-*` measures, with log/manifest hashes and network-disabled isolation.
- **`T011-WP`** — the T011 repository-owned work-product set (`requirements.md`, `architecture.md`,
  `detailed-design.md`, `unit-specifications.md`, `verification-plan.md`, `implementation.md`,
  `internal-review.json`, `reports/xcom-queue/t011-package.json`).

## 5. Admission data flow (ordered phases)

The checker evaluates phases in order and stops at the first failing class while preserving all diagnostics:

1. **Inputs** — resolve both explicit absolute inputs; a missing/unset input is `INPUT_MISSING (2)`.
2. **Manifest** — parse JSON, require exactly twelve records, validate each record's field set, filename,
   size, and SHA-256, and reject duplicates/symlink-unsafe names (`MANIFEST_INVALID (3)`).
3. **Archives** — confirm each sibling archive exists (`PACKAGE_MISSING (4)`) and matches its recorded size and
   digest (`HASH_MISMATCH (5)`) against both the manifest and the lock.
4. **Control metadata** — `dpkg-deb -f` verifies package, version, and source against the lock; a tool/header/
   library/pkg-config absence or identity drift is `TOOL_MISSING (6)`, `HEADER_MISSING (8)`,
   `LIBRARY_MISSING (9)`, `METADATA_MISSING (10)`, or `VERSION_MISMATCH (7)`.
5. **Payload** — extract the hash-verified archives into a disposable tree and compare every required node,
   file type, content, and symlink target with the prefix (`PAYLOAD_MISMATCH (15)`).
6. **Host envelope and policy** — probe the host tools and run the disposable CMake/Ninja compile-only policy
   probe; a failed probe is `PROBE_FAILED (13)`, an over-bound probe is `TIMEOUT (14)`, a policy mismatch is
   `POLICY_INVALID (11)`, and an unreadable input is `IO_ERROR (12)`.
7. **Decision** — success is `XCOM-BLD-I000` with `admitted: true`; otherwise `admitted: false` with the
   numerically lowest applicable class and sorted diagnostics.

## 6. Cross-language and external interfaces

T011 introduces **no** new runtime, transport, or cross-language interface. The only executable interface is
the checker's command line and its JSON decision:

| Interface | Contract |
| --- | --- |
| `xcom_dependency_preflight.py --self-test` | run the controlled positive/negative fixtures; nonzero on an unexpected result |
| `xcom_dependency_preflight.py --verify-toolchain` | full archive+payload+toolchain admission against real inputs |
| `xcom_dependency_preflight.py --all` | full admission plus host-envelope/policy checks and the compile-only probe |
| `xcom_dependency_preflight.py --cmake-dependency-check` | bounded check invoked by `XComOfflineDependencies.cmake` (120 s timeout) |
| admission JSON decision | `admitted: true|false`, sorted `XCOM-BLD-E…`/`I000` diagnostics, stable exit class |

Environment interface: `XVERSE_XCOM_TOOLCHAIN` (absolute directory) and `XVERSE_XCOM_PACKAGE_MANIFEST`
(absolute file), both authoritative; no other ambient configuration participates.

## 7. Quality attributes

| Attribute | Architectural decision | Evidence |
| --- | --- | --- |
| Offline/reproducibility | explicit inputs; extraction-only prefix; registries and FetchContent disabled | T011-SR-004, CHK-06/CHK-11 |
| Determinism | ordered phases, sorted diagnostics, stable exit classes, byte-stable decisions | T011-SR-007, CHK-08 |
| Fail-closed safety | admission is required before any compile; a failure never reports readiness | T011-SR-001/007, CHK-02/CHK-08 |
| Supply-chain integrity | size+SHA-256 on archives, node-level payload binding, generated-code provenance | T011-SR-002/003/005, CHK-04/CHK-05/CHK-07 |
| Public safety | public summaries omit host/prefix/manifest/temporary paths and sensitive values | T011-SR-009, CHK-13/CHK-14 |
| Boundedness | local reads, bounded subprocesses, temporary trees, wall-clock limits; no threads | T011-SR-008, CHK-09 |
| Maintainability | modules and documents with clear ownership; gaps recorded with owners | T011-SR-011/013, CHK-15/CHK-18 |

## 8. Consistency and constraints

- **Dependency direction preserved.** Admission is an enabler that produces the build envelope; it depends on
  no runtime X-COM unit. `T-CORE` and later slices consume the envelope; the reverse does not occur.
- **Domain neutrality preserved.** The admitted set (JSON, protobuf, gRPC, clang-tidy) and the envelope are
  domain-neutral; no automotive or product primitive is introduced.
- **Ownership preserved.** The T011 candidate does not edit the T-INTG-owned admission artifacts; it references
  them and declares the `T-ENABLER` slice's new work products.
- **Maturity preserved.** The envelope remains a prototype-only, Linux x86-64, non-production foundation with
  the limitations in `requirements.md` §8.1.

## 9. Traceability

| Architecture element | T011 requirements |
| --- | --- |
| `XB-1`, `XCOM-ADM-CHECKER`, `XCOM-BLD-DEPS` | T011-SR-004, T011-SR-008 |
| `XB-2`, `XCOM-ADM-PROBE` | T011-SR-003 |
| `XB-3`, `XCOM-BLD-ROOT`, `XCOM-BLD-WARN` | T011-SR-001, T011-SR-006 |
| `XB-4`, `XCOM-ADM-EVIDENCE` | T011-SR-010 |
| `XB-5`, `XCOM-ADM-DOC` | T011-SR-009 |
| `XCOM-ADM-LOCK`, `XCOM-ADM-MANIFEST` | T011-SR-002, T011-SR-005 |
| `XCOM-ADM-DECISION` | T011-SR-007 |
| `XCOM-BLD-DOXYGEN`, `T011-WP` | T011-SR-011, T011-SR-012, T011-SR-013 |

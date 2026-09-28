# T011 Detailed Design — Pinned Package Lock, Offline Admission, and Build Policy

## 1. Document control

| Field | Value |
| --- | --- |
| Task | T011 (capability 007, engineering-baseline enabler) |
| Stage / role | plan → detailed design |
| Revision | 1 |
| Baseline revision | `5050666bf38fc98920dc455a85a88c08c46a2133` |
| Requirements authority | [`requirements.md`](requirements.md) rev 1 |
| Architecture authority | [`architecture.md`](architecture.md) rev 1 |
| Unit authority | [`unit-specifications.md`](unit-specifications.md) rev 1 |
| Consumed design | `docs/engineering/xcom/t010/detailed-design.md` §`XCOM-DU-029`, Doxygen plan `DOX-GAP-01..03` |
| Classification | Public-safe engineering work product |

## 2. Design overview

T011's detailed design has three cooperating parts:

1. **The pinned identity model** — the twelve exact package records and generated-code provenance entries that
   constitute the lock (§4).
2. **The offline admission algorithm** — the ordered, fail-closed evaluation performed by
   `scripts/xcom_dependency_preflight.py` over the manifest, sibling archives, control metadata, extracted
   payload, host envelope, and build policy (§5).
3. **The admitted build contract** — the CMake modules that consume a positive admission and publish the
   optional dependency targets, warning policy, and machine-readable policy evidence (§6).

The design is deliberately small and deterministic: no threads, no network, no writes to the authoritative
inputs, and a bounded wall-clock budget.

## 3. Design constraints and invariants

| ID | Invariant |
| --- | --- |
| `INV-01` | Exactly twelve locked package records; manifest length equals twelve; no duplicate filename. |
| `INV-02` | Every manifest filename is a single path segment (no directory component, no traversal). |
| `INV-03` | Every digest is a 64-character lowercase hex SHA-256; every size is a positive integer. |
| `INV-04` | Admission compares the manifest record **and** the compiled-in lock for each archive. |
| `INV-05` | Admission binds the extracted prefix payload to the hash-verified archives; an archive hash alone never admits a prefix. |
| `INV-06` | Success emits exactly `XCOM-BLD-I000` with `admitted: true`; failure emits `admitted: false` and never a pass. |
| `INV-07` | Diagnostics are sorted deterministically; the exit class is the numerically lowest applicable nonzero class. |
| `INV-08` | Both explicit inputs are absolute; no other ambient configuration influences the decision. |
| `INV-09` | No network access, no package installation, no modification of either explicit input. |
| `INV-10` | Public artifacts exclude absolute host/prefix/manifest/temporary paths and sensitive values. |
| `INV-11` | Generated code is admissible only with recorded generator package + hash, input schema identity, and generation command. |
| `INV-12` | T011 changes no `src/`, `tests/`, or `xdl/` path and edits no other slice's artifact. |

## 4. Pinned identity model

### 4.1 Package lock record

Each of the twelve records is a tuple:

```text
PackageSpec = {
  file     : <retained filename, single segment>          # e.g. nlohmann-json3-dev_3.10.5-2_all.deb
  sha256   : <64-hex content hash>
  size     : <positive integer bytes>
  package  : <Debian package name>                         # e.g. nlohmann-json3-dev
  version  : <exact Debian version>                        # e.g. 3.10.5-2
  source   : <Debian source package>                       # e.g. nlohmann-json3
  license  : <primary upstream license expression>          # e.g. MIT
}
```

### 4.2 The twelve admitted records

Grouped by admitted component (full versions, sizes, hashes, and retrieval coordinates are authoritative in
`docs/engineering/xcom/dependency-lock.md`):

| Admitted component | Admitted version | Retained package records | Primary license |
| --- | --- | --- | --- |
| nlohmann/json | 3.10.5 (`3.10.5-2`) | `nlohmann-json3-dev_3.10.5-2_all.deb` | MIT |
| Protocol Buffers | 3.12.4 (`3.12.4-1ubuntu7.22.04.6`) | `libprotobuf-dev`, `libprotoc23`, `protobuf-compiler` | BSD-3-Clause |
| gRPC | 1.30.2 (`1.30.2-3build6`) | `libgrpc-dev`, `libgrpc++-dev`, `libgrpc10`, `libgrpc++1`, `protobuf-compiler-grpc` | Apache-2.0 |
| clang-tidy / LLVM | 14.0.0 (`1:14.0.0-1ubuntu1.1`) | `clang-tidy-14`, `clang-tools-14`, `clang-tidy` | Apache-2.0 WITH LLVM-exception; GPL-2.0-or-later (metapackage) |

The three epoch-bearing LLVM objects omit the `1:` epoch in the Ubuntu pool basename and are retained beside
the manifest under the `%3a` filenames used by the lock.

### 4.3 Manifest record

The caller-supplied manifest is a JSON array of exactly twelve objects, each with exactly the fields:

```json
{ "file": "<name>", "sha256": "<64-hex>", "size": <positive int> }
```

Additional or missing fields, a non-string filename with a directory component, a malformed digest, a
non-positive size, a duplicate filename, or a length other than twelve is a manifest failure.

### 4.4 Generated-code provenance record

```text
GeneratedCodeProvenance = {
  generator_package : "protobuf-compiler"      version 3.12.4-1ubuntu7.22.04.6
                                            sha256 a124cc30fadf8e83f86fd7e1b9c776befd336d092bb81f95de1dc39d79b61ce7
  grpc_generator    : "protobuf-compiler-grpc" version 1.30.2-3build6
                                            sha256 79debaed17ff25444a9c450b4b342e3d7565e80c062da2356b42ceb73e305331
  required_fields   : input schema identity, generation command
}
```

`grpc_cpp_plugin` exposes no supported version flag in this admitted package; its identity is bound from the
hash-verified `protobuf-compiler-grpc` archive control metadata and extracted payload, not from an inferred
executable response.

### 4.5 Build envelope record

| Member | Class | Requirement |
| --- | --- | --- |
| `c++` (C++20, accepts `-Wall -Wextra -Wpedantic -Werror`) | host prerequisite (probed) | must compile the compile-only probes |
| CMake ≥ 3.22 | host prerequisite (probed) | configures the probes |
| Ninja ≥ 1.10 | host prerequisite (probed) | only accepted generator |
| Python ≥ 3.11 | host prerequisite (probed) | runs the checker and tooling |
| `dpkg-deb` | host prerequisite (probed) | reads control metadata and extracts archives |
| Twelve packages (§4.2) | pinned lock | content-verified by size/SHA-256 and payload |
| Sanitizers (ASan/TSan/UBSan), when supported | compiler-provided (probed) | opt-in; recorded as compiler capability, not a package member (`T011-SR-006`) |
| Doxygen | host tool / configuration | configuration contract and gap `T011-GAP-01` |

## 5. Offline admission algorithm

### 5.1 Ordered phases and failure classes

The checker implements the phases from `architecture.md` §5. Each phase maps to one or more stable exit
classes; when several failures exist the process returns the numerically lowest applicable class while
preserving all sorted diagnostics.

| Phase | Check | Failure class (exit) |
| --- | --- | --- |
| 1 Inputs | both absolute inputs present and readable | `INPUT_MISSING` (2) |
| 2 Manifest | schema, count = 12, fields, filename shape, digest/size shape, uniqueness | `MANIFEST_INVALID` (3) |
| 3 Archives | each sibling archive present | `PACKAGE_MISSING` (4) |
| 3 Archives | each archive size and SHA-256 matches manifest and lock | `HASH_MISMATCH` (5) |
| 4 Control metadata | each `dpkg-deb -f` package/version/source matches the lock | `VERSION_MISMATCH` (7) |
| 4 Tools/headers/libs/metadata | required executable, header, library, pkg-config present | `TOOL_MISSING` (6) / `HEADER_MISSING` (8) / `LIBRARY_MISSING` (9) / `METADATA_MISSING` (10) |
| 5 Payload | extracted node, type, content, symlink text and reached target match the prefix | `PAYLOAD_MISMATCH` (15) |
| 6 Host/policy | CMake/Ninja compile-only probe and policy match | `PROBE_FAILED` (13) / `POLICY_INVALID` (11) |
| any | input/package/payload/evidence read error | `IO_ERROR` (12) |
| any | bounded probe exceeds its limit | `TIMEOUT` (14) |
| success | all phases pass | `XCOM-BLD-I000` (0), `admitted: true` |

### 5.2 Decision record (JSON)

```json
{
  "admitted": true,
  "diagnostics": [ { "code": "XCOM-BLD-I000", "category": "...", "detail": "..." } ]
}
```

A failure record has `"admitted": false` and one or more `XCOM-BLD-E…` diagnostics; the process exit is the
lowest applicable class. The decision is serialized deterministically (stable key and diagnostic order, no
timestamp, no absolute path).

### 5.3 Offline strategy

- Retrieval is a separate, controlled online staging step; the twelve objects and the manifest are transferred
  into the offline host before any run (`XB-1`).
- Prefix reconstruction is extraction-only (`dpkg-deb -x`), ordered by retained filename, with no package
  manager database and no maintainer scripts.
- CMake disables the user/system package registries and FetchContent network resolution and resolves imported
  targets only beneath `XVERSE_XCOM_TOOLCHAIN`.
- `LD_LIBRARY_PATH`, `PKG_CONFIG_*`, and `CMAKE_PREFIX_PATH` may be set to prefer the admitted prefix for
  manual work, but admission itself reads only the two explicit inputs and the repository.

### 5.4 Boundedness and side effects

| Resource | Bound |
| --- | --- |
| Inputs | read-only; located only by the two explicit absolute paths |
| Subprocesses | bounded local `dpkg-deb`, version probes, and a disposable CMake/Ninja probe (`--cmake-dependency-check` timeout 120 s) |
| Temporary state | disposable extraction/reference trees removed after use |
| Threads | none; single-threaded and deterministic |
| Network | none; no resolver or client in the checker |
| Writes | none to either explicit input or the repository during a verification run |

## 6. Admitted build contract

### 6.1 Warning policy (`XComWarnings.cmake`)

- Publishes the interface target `xverse::xcom_warnings` carrying `-Wall -Wextra -Wpedantic -Werror`.
- `xverse_xcom_configure_warnings()` creates the target once; `xverse_xcom_apply_warnings(<target>)` applies it.
- The root build fails if the target publishes no compile options (`POLICY_INVALID`).

### 6.2 Dependency admission and imported targets (`XComOfflineDependencies.cmake`)

- Requires `XVERSE_XCOM_TOOLCHAIN` and `XVERSE_XCOM_PACKAGE_MANIFEST` (from the environment or an explicit CMake
  cache value), normalizes them, and rejects a non-directory prefix or a missing manifest.
- Invokes `xcom_dependency_preflight.py --cmake-dependency-check` (120 s timeout) and fails configuration with
  the checker's detail when admission fails.
- Disables package registries and FetchContent, then defines `nlohmann_json::nlohmann_json`,
  `protobuf::libprotobuf`, `protobuf::protoc`, `gRPC::grpc`, `gRPC::grpc++`, and `gRPC::grpc_cpp_plugin` from
  the admitted prefix.

### 6.3 Policy evidence (`CMakeLists.txt`)

- Ninja-only, C++20 without extensions, `BUILD_TESTING=ON` required.
- The compile-only `xverse_xcom_policy_probe` proves the selected compiler accepts the language and warning
  policy while compiling admitted headers.
- The `xverse_xcom_warning_rejection_probe` target (excluded from `ALL`) must **fail** to build; the preflight
  admits the warning policy only when the intentional warning is promoted to an error.
- `xcom-build-policy.json` records `schema_version`, `probe_target`, `compiler`, `compiler_id`,
  `compiler_version`, `generator`, `cxx_standard`, `cxx_standard_required`, `cxx_extensions`, `build_testing`,
  `warnings_as_errors`, `warning_options`, `toolchain_prefix`, and `package_manifest`.

### 6.4 Doxygen configuration contract

- `Doxyfile` currently sets `WARN_AS_ERROR = YES` but `WARN_IF_UNDOCUMENTED = NO` and `WARN_NO_PARAMDOC = NO`;
  `scripts/check_doxygen.py` validates Python coverage and warning-clean HTML/XML generation.
- The strict C++ configuration (undocumented/param-doc warnings as errors) and the allowed exclusion list are
  the recorded gap `T011-GAP-01` (`DOX-GAP-01`, `DOX-GAP-03`), owned by T011 (admission) and T037 (execution).
  T011 states the contract and claims no warning-free generation.

## 7. Host verification-evidence contract

| Field | Content |
| --- | --- |
| Measures | `VM-BLD-UNIT`, `VM-BLD-LINT`, `VM-BLD-STATIC`, `VM-BLD-INTEGRATION`, `VM-BLD-VALIDATION` |
| Isolation | each measure and its trusted tool-version probe run with network access disabled in an enforced namespace; the isolation mechanism is recorded; if isolation cannot be enforced, the measure fails closed |
| Per measure | bounded `log`, private raw environment `manifest`, `command_argv`, `exit_code`, `outcome`, candidate revision, and SHA-256 of the log and manifest |
| Repository record | `index.json` listing the five measure records bound to the exact candidate revision |
| Public summary | omits host-specific paths and environment-specific prefix/manifest/temporary/private store paths |
| Acceptance rule | five revision-matching records with recomputed hashes, inspected `command_argv`/`exit_code`/`outcome`, and network-disabled raw manifests; missing/stale/mismatched/skipped/failed evidence cannot support acceptance |

## 8. Public-safety design

Public artifacts may record package filenames, hashes, versions, licenses, generated-code tool provenance,
command identities, diagnostic codes, and pass/fail outcomes. They must not contain package binaries,
credentials, private addresses, unrestricted payloads, proprietary source, absolute host paths, or sensitive
deployment values. `requirements.md` records the documentation obligation; `verification-plan.md` CHK-13/CHK-14
enforce it.

## 9. Error and edge-case handling

| Case | Handling |
| --- | --- |
| Cross-filesystem/host prefix | compare by content and structure, never by inferred installation database |
| Symlinked payload node | compare symlink text and recursively reached target; a mismatch is `PAYLOAD_MISMATCH` |
| Unreadable package or payload | classified `IO_ERROR` rather than an uncaught exception |
| Probe exceeds budget | classified `TIMEOUT` |
| Multiple simultaneous defects | report all sorted diagnostics, exit with the lowest applicable class |
| Missing/partial evidence | never reported as admission or acceptance |
| Sanitizer unsupported by compiler | reported as unsupported (`T011-SR-006`), not silently assumed |

## 10. Requirement traceability

| Design section | Requirements |
| --- | --- |
| §4.1–§4.2 package lock | T011-STK-002, T011-SR-002 |
| §4.3 manifest | T011-SR-002 |
| §4.4 generated-code provenance | T011-STK-003, T011-SR-005 |
| §4.5 build envelope | T011-STK-001, T011-SR-001, T011-SR-006 |
| §5.1–§5.2 phases/decision | T011-STK-004, T011-SR-007 |
| §5.3 offline strategy | T011-SR-004 |
| §5.4 boundedness | T011-SR-008 |
| §6.1–§6.3 build contract | T011-SR-001, T011-SR-004 |
| §6.4 Doxygen contract | T011-SR-009; gap `T011-GAP-01` |
| §7 evidence contract | T011-SR-010 |
| §8 public safety | T011-STK-005, T011-SR-009 |
| §9 error handling | T011-SR-007, T011-SR-008 |

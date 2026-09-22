# SWE.1 Software requirements (EARS)

## XCOM-BLD-001 [ubiquitous]

The X-COM build envelope shall require C++20 and shall fail when the compiler, CMake, Ninja, or required warning policy is unavailable.

Source: specs/007-xcom-core/plan.md; provenance: accepted; status: accepted.

Verification intent: Execute self-tests against present, missing, and version-mismatched controlled tool descriptions.

## XCOM-BLD-002 [ubiquitous]

The X-COM dependency admission shall verify exact versions, package hashes, licenses, generated-code tools, and provenance for nlohmann/json, Protocol Buffers, gRPC, and clang-tidy before reporting readiness.

Source: specs/007-xcom-core/tasks.md T011; provenance: accepted; status: accepted.

Verification intent: Validate the pinned manifest and probe the isolated toolchain executables, headers, libraries, and pkg-config metadata.

## XCOM-BLD-003 [ubiquitous]

The X-COM dependency lock shall support repeatable offline use from the admitted package set without resolving an ambient latest dependency.

Source: specs/007-xcom-core/plan.md; provenance: accepted; status: accepted.

Verification intent: Run preflight with network access absent and compare package hashes and resolved versions with the lock.

## XCOM-BLD-004 [ubiquitous]

The X-COM dependency preflight shall return a classified nonzero result and shall not claim admission when any required artifact is missing or mismatched.

Source: specs/007-xcom-core/plan.md dependency admission gate; provenance: accepted; status: accepted.

Verification intent: Run negative fixtures for missing manifest, wrong hash, missing executable, missing header, missing library, and version drift.

## XCOM-BLD-005 [ubiquitous]

The X-COM build documentation shall identify licenses, hashes, generated-code provenance, environment limits, and the prototype-only maturity of the admitted toolchain.

Source: specs/007-xcom-core/spec.md FR-027, FR-029, FR-030; provenance: accepted; status: accepted.

Verification intent: Lint the generated lock and environment documents for required fields, public safety, and unsupported claims.

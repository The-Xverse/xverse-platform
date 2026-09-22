# Implementation Plan: X-COM core communication and validation

**Branch**: `main` | **Date**: 2026-09-21 | **Spec**: [spec.md](spec.md)

## Summary

Build the first platform-owned X-COM prototype as a bounded C++20 communication core with explicit
logical contracts, provider-owned endpoints/routes, passive observation taps, and permit-controlled
validation stimulation. A Python compiler extension derives a canonical activation plan from the
existing normalized XDL graph; the C++ data plane never reads an authored competing configuration.
The first proof uses only owned loopback nodes/providers and synthetic observation/stimulation tools.

This plan was accepted for the bounded SESN implementation authorized by the user. It does not
authorize work beyond the accepted capability-007 slices or any legacy-system execution.

## Technical Context

**Language/Version**: C++20 for all data-plane, provider, observation, stimulation, and lifecycle
units; Python 3.11+ only for the existing XDL-side activation-plan compiler and validation tooling.

**Primary Dependencies**: C++ standard library, CMake/CTest, pinned `nlohmann/json` for bounded
activation-plan decoding, pinned gRPC/Protocol Buffers for the local external-tool gateway, existing
`xverse_xdl`, and Doxygen. Exact versions, hashes, licenses, generated-code provenance, and offline
availability are blocking SESN preflight outputs. No communication transport middleware is linked.

**Storage**: Immutable derived activation-plan files for fixtures; append-only local validation intent
and outcome evidence. No registry, database, telemetry backend, or payload archive.

**Testing**: CTest unit/contract/integration tests; Python XDL plan tests; sanitizers where supported;
clang-tidy/static analysis; deterministic saturation/concurrency tests; controlled performance
benchmarks; Doxygen warning-as-error validation; existing Python suite.

**Target Platform**: Linux x86_64 development/CI baseline. Portability beyond this baseline remains
unclaimed until separately demonstrated.

**Project Type**: Mixed-language platform library with a C++ data plane and Python XDL compiler edge.

**Performance Goals**: Disabled taps add at most 2% median throughput and latency regression in the
owned loopback benchmark. Every queue is bounded; no hot-path network, filesystem, or shell access.

**Constraints**: XDL centrality; no dynamic plugin discovery; no external peers; no legacy adapter;
no unrestricted payload observation; stimulation disabled by default; exact ownership handles;
bounded resources; no hidden retry; deterministic diagnostics and plan compilation.

**Scale/Scope**: One X-COM process, multiple loopback nodes/routes, all interaction families, multiple
best-effort observers, one or more bounded validation sessions, and one separate-process synthetic tool
through local IPC. No distributed control-plane or production scale claim.

## Constitution Check

- **Production safety**: only owned fixtures run; legacy repositories and processes remain untouched.
- **Domain neutrality**: core types contain no ECU, CAN, SOME/IP, Zenoh, or product-specific primitive.
- **XDL centrality**: activation plans are derived, digest-bound artifacts from normalized XDL.
- **Standards interoperability**: OpenTelemetry and ASAM XIL remain adapter candidates, not replacements
  or embedded private models.
- **Logical/physical separation**: logical contracts and endpoint identities are independent of provider
  realization and address.
- **Physical hardware**: contracts carry realization/time/capability limits, while hardware execution is
  deferred rather than modeled away.
- **Platform-first sequence**: this is an owned platform capability and implements no legacy target.
- **Repository direction**: platform owns X-COM; future compatibility providers depend on its stable
  contract; blueprints and profiles consume it through XDL.
- **Maturity/evidence**: loopback and synthetic-tool proof remains prototype evidence only.
- **Reproducibility**: locked dependencies, plan/source digests, environment facts, deterministic tests,
  and SESN traceability are required.
- **SADS traceability**: all XVE-SYS-0139–0158 requirements and identified cross-cutting IDs have an
  explicit allocation/deferment in `reference-traceability.md`; target text is not implementation proof.

The gate passes for design. Re-check after the detailed design and dependency lock are produced by
SESN and before accepting implementation.

## Architecture

```text
normalized XDL graph
        |
        v
XDL + io.xverse.xcom Profile compiler (Python, non-data-plane)
        |
        v
canonical digest-bound ActivationPlan
        |
        v
+-------------------------- X-COM C++ core ---------------------------+
| contract validation -> composition -> endpoints/routes -> outcomes  |
|                                  |                    |              |
|                         observation taps      validation sessions    |
+----------------------------------|--------------------|--------------+
                                   v                    v
                          synthetic sink       local gRPC tool gateway
                                   |                    |
                                   v                    v
                         Argus/dashboard later  separate-process tool
```

The first implementation composes providers explicitly. It exposes source-level C++ contracts, not a
stable dynamic binary plugin ABI. The versioned gRPC gateway is solely the external validation-tool
boundary; provider plugins remain explicitly linked. Remote tool transport is deferred.

## Project Structure

```text
CMakeLists.txt
cmake/
src/xverse/xcom/
├── CMakeLists.txt
├── include/xverse/xcom/
│   ├── contract.hpp
│   ├── diagnostic.hpp
│   ├── endpoint.hpp
│   ├── item.hpp
│   ├── observation.hpp
│   ├── provider.hpp
│   ├── route.hpp
│   ├── validation.hpp
│   ├── time_authority.hpp
│   └── tool_gateway.hpp
├── src/
│   ├── activation_plan.cpp
│   ├── core.cpp
│   ├── observation.cpp
│   ├── route.cpp
│   ├── validation.cpp
│   ├── time_authority.cpp
│   └── tool_gateway.cpp
├── fixtures/
│   ├── loopback_provider.cpp
│   └── synthetic_tool.cpp
└── contracts/v1/activation-plan.schema.json
proto/xverse/xcom/v1/tool_gateway.proto
xdl/profiles/xcom-v0.1.schema.json
src/xverse_xdl/
└── xcom_plan.py
tests/xcom/
├── unit/
├── contract/
├── integration/
├── negative/
└── performance/
tests/
└── test_xcom_plan.py
docs/xcom/
├── architecture.md
├── tool-integration.md
└── maturity.md
```

**Structure Decision**: Keep the performance-sensitive implementation under the reserved
`src/xverse/xcom` subsystem path and namespace `xverse::xcom`. Keep XDL compilation in the existing
Python package. No `xverse.xcom` Python runtime package or empty placeholder is introduced.

## Delivery phases

1. SESN intake creates SWE.1–SWE.6 requirements, architecture, unit design, traceability, and review
   artifacts from this accepted Spec Kit package.
2. Establish locked C++ build, static-analysis, sanitizer, test, and Doxygen gates without networking.
3. Implement contract/item/diagnostic value types and bounded ownership/lifecycle primitives.
4. Implement the `io.xverse.xcom` Profile, deterministic activation-plan compilation, and bounded
   decoding/validation.
5. Implement explicit provider composition, endpoint/route state, and owned loopback provider.
6. Implement bounded observation taps and synthetic sinks, including metadata-only enforcement and
   degraded-validity evidence.
7. Implement explicit time authority, permit-controlled validation sessions, and synthetic tools for
   all required stimulation actions, with durable intent/outcome and exclusive service leases.
8. Implement the local-only gRPC/Protocol Buffers gateway and prove it with a separate-process synthetic
   client, including no-TCP, bounds, deadlines, disconnect, and generated-client contract tests.
9. Run unit, contract, integration, negative, concurrency/sanitizer, performance, Doxygen, public-safety,
   traceability, and existing-regression checks.
10. Conduct an independent Astra review; repair findings in a later SESN pass; present all generated
   software and assurance artifacts to the user before accepting the feature.

## Decision gates

| Gate | Required evidence | Status |
|---|---|---|
| Specification | Requirements checklist and clarification record complete. | Complete. |
| Architecture | ADR-0018, ADR-0019, contracts, data model, and plan reviewed. | Complete; review 012 has no unresolved BLOCKER or MAJOR finding. |
| Implementation authorization | User approves ACC001–ACC014, the exact SESN implementation scope, and model proposal. | Complete; recorded by T006 before SESN implementation began. |
| Dependency admission | Exact C++ toolchain/dependency versions, licenses, hashes, and offline/reproducible strategy reviewed. | Pending implementation preflight. |
| Software acceptance | SWE.1–SWE.6 traceability, checks, Doxygen, benchmarks, and independent review pass. | Future. |
| Human acceptance | User validates SESN-generated software and evidence. | Future; blocks the next feature. |

## Complexity Tracking

The mixed-language boundary is justified because the existing authoritative XDL stack is Python while
the user requires X-COM's performance-sensitive data plane in C++. The boundary is one-way: Python
compiles a canonical plan; C++ validates and consumes it. Dynamic provider plugins, remote tool
control, and dashboard/storage systems are excluded to keep this first capability bounded.

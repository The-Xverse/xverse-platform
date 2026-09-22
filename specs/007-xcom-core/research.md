# Research: X-COM core communication and validation

**Date**: 2026-09-21
**Scope**: Architecture choices for the first platform-owned X-COM capability. No legacy component,
external peer, or production network was executed.

## Decisions

| Topic | Decision | Rationale and alternatives |
|---|---|---|
| Delivery sequence | Build and accept platform baselines before target-specific legacy integration. | ADR-0018 prevents one legacy bridge from defining the platform. The original parity-first ordering is retained as historical guidance but superseded. |
| Core language | Use C++20 for the X-COM data plane and lifecycle core. Python 3.12 may compile normalized XDL into a derived activation plan and provide non-real-time tooling. | Meets the user’s performance requirement while keeping the existing XDL implementation authoritative. A Python data plane was rejected for this capability; a full Rust rewrite would fragment the current toolchain and does not satisfy the directed C++ boundary. |
| Configuration | Consume a canonical, digest-bound activation plan derived from normalized XDL. | XDL remains the authored source. A standalone X-COM configuration language is prohibited. Parsing and validation happen before endpoint activation. |
| Extensibility | Start with explicitly composed source-level provider interfaces and a versioned out-of-process tool gateway; do not promise a stable C++ provider ABI or dynamic discovery. | C++ ABI stability and unsafe ambient plugin loading would create premature provider-compatibility obligations. External tools instead use the bounded local gateway. |
| Interaction semantics | Keep signal/state, message/event, and service request/response distinct. | Flattening them loses update, ordering, ownership, and correlation semantics needed for validation. |
| Observation | Define normalized route taps with bounded queues and metadata-only default. | A passive, provider-neutral boundary supports sniffers, recorders, and Argus without allowing slow consumers to silently stall normal traffic. |
| Stimulation | Define permit-bound validation sessions and preserve synthetic provenance. | Tool injection must be auditable and fail closed rather than acting as an unrestricted publisher. |
| External-tool transport | Use a pinned gRPC/Protocol Buffers contract over a host-protected local IPC endpoint for the first proof; do not open TCP. | gRPC supplies cross-language generated clients plus unary and streaming RPCs, while local-only deployment bounds the initial security claim. Exact versions/hashes/licenses are an implementation admission gate. See the [gRPC C++ basics](https://grpc.io/docs/languages/cpp/basics/). |
| XDL policy placement | Define `io.xverse.xcom` Profile payloads on existing extension points and compile them into the activation plan. | Interaction/provider/tool policy stays versioned and namespaced without changing XDL Core or creating an authored X-COM language. |
| Time | Carry source and observation timestamps with explicit clock-domain identity; schedule only against a declared time authority. | Avoids implying comparability or determinism across clocks. |
| Telemetry standards | Keep the X-COM observation record independent; design a later Argus/OpenTelemetry exporter. | OpenTelemetry provides vendor-neutral traces, metrics, logs, context correlation, and semantic conventions, but it is not a raw communication or stimulation contract. See [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) and [semantic conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/). |
| Test-tool standards | Preserve ASAM XIL as a candidate future adapter, not a core dependency. | ASAM XIL defines vendor-independent test-automation/test-bench APIs, measurement, mapping, synchronized acquisition, and stimulation across MIL/SIL/HIL. It is automotive-oriented and its initial technology references do not define X-COM core. See [ASAM XIL](https://www.asam.net/standards/detail/xil/). |
| CANoe reference | Use CANoe only as capability inspiration. | Vector identifies analysis, simulation, stimulation, testing, diagnostics, and tool integrations as CANoe application areas. X-COM does not copy its model or claim interoperability. See [Vector CANoe](https://www.vector.com/en/product/canoe/). |
| First proof | Use owned in-process loopback providers/nodes plus synthetic in-process sinks and one separate-process tool client over local IPC. | Establishes the tool boundary without an external network, legacy asset, secret, hardware, or production risk. |

## Rejected shortcuts

- Reusing the pinned Zenoh/SOME-IP gateway as the X-COM core would couple the contract to one legacy
  mapping, serialization, lifecycle, and deployment model.
- Treating diagnostic tools as ordinary publishers would lose authorization, provenance, quotas,
  service-emulation ownership, and test evidence.
- Sending unrestricted payloads to every observer would violate public-safety and least-disclosure
  requirements.
- Making dashboards part of X-COM would combine the performance data plane with storage and
  presentation lifecycles owned by Argus or external tools.
- Advertising dynamic C++ plugins in the first release would establish an ABI promise before the
  provider contract has implementation evidence.

## Open items intentionally deferred

- Remote tool transport and distributed identity/authentication.
- Stable binary plugin ABI and dynamic provider discovery.
- OpenTelemetry, ASAM XIL, CANoe, MDF, or protocol-specific adapters.
- Persistent capture/replay format and long-term observation storage.
- Real network, hardware, and legacy-adapter performance envelopes.

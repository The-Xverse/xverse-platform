# Research: M3 component catalog and compatibility runtime

**Date**: 2026-09-20
**Scope**: Architecture and evidence choices for M3 design; no external component was executed.

| Topic | Decision | Rationale |
|---|---|---|
| Canonical model | Derive catalog entries from normalized Deployment binding → System instance → Component relationships; use `io.xverse.runtime.compatibility` only on the binding. | Uses existing XDL identity and logical/realization separation without an independent descriptor grammar. |
| Catalog discovery | Explicit local inputs and exact pinned provenance. | Matches capability 004 closed-set resolution and makes selection reproducible/offline. |
| Lifecycle semantics | Prepare, start, observe, stop, cleanup, timeout, ownership, and failure are distinct states. | M0 observes fixed waits, broad cleanup, and incomplete container lifecycle evidence in the legacy launcher. |
| Readiness | Require a declared observation/evidence rule; a sleep may only be a bounded delay. | A process surviving a delay is not evidence that it is ready. |
| Execution proof | Controlled fixture first, selected legacy component only after target-specific authorization. | Separates runtime mechanics from compatibility/parity claims and preserves production safety. |
| Evidence | Immutable declared/observed/unavailable/withheld records. | Preserves M0 maturity discipline and public-safe reporting. |
| Repository split | Platform defines neutral contracts/planning; compat later implements legacy-specific providers. | Preserves dependency direction and keeps protocol/domain details out of the platform core. |
| Execution permit | Explicit local single-use permit bound to plan/environment/action set; host permissions enforce access. | Separates reviewable operational approval from a future authentication/identity capability. |
| Resource ownership | Opaque provider handle plus execution/action identity; never name/port/path discovery. | Makes stop/cleanup authority testable and prevents broad cleanup. |
| Lifecycle recovery | Idempotent transitions, exclusive mutation, observation-only reconciliation after restart. | Prevents duplicate resources and unsafe mutation after controller interruption. |
| Evidence durability | Durable intent before mutation; outcome failure enters evidence-incomplete safe-stop mode. | Preserves audit intent without preventing cleanup of already-owned resources. |
| Secrets | Record the limitation and block secret-dependent planning/execution. | Secret resolution is outside M3 and must not be implied by an indirect reference. |
| Declared planning blockers | Version the runtime Profile to v0.2 and allow stable `XVERSE-PLAN-*` codes for unresolved decision evidence. | A candidate with a complete structural graph must remain reviewable without treating missing owner/environment/interface approvals as schema errors or executable defaults. |

## Constraints carried forward

- R01: the S-CORE launcher and PID/Rust documentation are distinct paths; no parity baseline is
  selected here.
- R02: fixed sleeps, broad cleanup, continued startup after errors, and ambiguous container shutdown
  cannot become vNext lifecycle behavior.
- R03–R05: protocol/Android/HwSim boundaries require their own verified contracts before selection.
- M3 must not convert source inspection into runtime, compatibility, fidelity, or parity evidence.

## Selected-candidate follow-up

[SD-0001](decisions/SD-0001-zenoh-someip-gateway.md) nominates the revision-pinned Zenoh/SOME-IP
gateway process for review. It is narrower and more domain-neutral than the current supervisor or
vehicle controller and matches M0's reusable-adapter recommendation. The separate review keeps the
decision blocked. A later authorized build-only pass supplies a reproducible candidate executable and
dependency/configuration bundle without execution or legacy modification. The candidate XDL graph now
validates under runtime Profile v0.2 and produces a deterministic blocked plan. The isolated environment
and owners, measurable readiness, verified interface limits, durable restricted retention, and
vendor-binary disposition remain unresolved.

REF-001 reports prior bridge integration and a broader startup sequence, while REF-002 specifies
target monitoring, readiness, quota, isolation, and retention requirements. Neither supplies an
immutable gateway environment, approved operational values, accountable owners, or underlying
restricted interface evidence. REF-001 also places S-CORE before the gateway, unlike the current
revision-pinned launcher. The closure packet preserves this conflict for owner resolution rather than
turning either document into runtime truth.

Read-only inspection of the frozen gateway source and candidate configuration further narrows the
interface boundary: six selected routes, vsomeip 3.6.1, unreliable SOME/IP event operations, three
float-related forward transforms, one boolean normalization, and two raw-byte reverse routes. It also
finds a compiled private endpoint, native-memory float encoding, payload-bearing logs, detached work,
no graceful-stop/readiness API, and no trustworthy Zenoh semantic version. These facts improve the
contract projection while keeping interface, environment, readiness, retention, and vendor decisions
blocked.

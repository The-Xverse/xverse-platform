# X-COM core design acceptance checklist

**Status**: Design accepted and implementation authorized on 2026-09-21; software acceptance pending

- [X] ACC001 Accept ADR-0018 platform-first sequencing and the deferral of SD-0001/legacy parity.
- [X] ACC002 Accept C++20 for the X-COM data plane and Python only for the normalized-XDL plan compiler.
- [X] ACC003 Accept `io.xverse.xcom` Profile payloads plus a derived digest-bound activation plan; no
  second authored configuration language is introduced.
- [X] ACC004 Accept distinct signal/state, message/event, and service request/response semantics.
- [X] ACC005 Accept passive, bounded observation taps with metadata-only default and explicit payload
  policy; slow best-effort observers cannot silently block the normal data plane.
- [X] ACC006 Accept permit-controlled signal/message injection, service invocation, and exclusive
  lease-bound service emulation with persistent synthetic provenance.
- [X] ACC007 Accept a local-only gRPC/Protocol Buffers gateway and separate-process synthetic client as
  the first outside-tool proof; no TCP or remote authorization is included.
- [X] ACC008 Accept that X-COM publishes normalized records while Argus or third-party adapters own
  storage, queries, dashboards, and visualization.
- [X] ACC009 Accept that Faults owns fault policy/campaigns and may later use X-COM's bounded hooks.
- [X] ACC010 Accept explicit time-authority mapping, finite queues/quotas, deterministic diagnostics,
  exact ownership handles, and fail-closed stimulation.
- [X] ACC011 Accept the prototype scope: owned loopback providers and synthetic tools only, with no
  legacy adapter/execution, external network peer, physical bus, production, or compatibility claim.
- [X] ACC012 Accept SESN generation of all production code and SWE.1–SWE.6 evidence, followed by Codex
  inspection, independent Astra review, and user validation before another feature.
- [X] ACC013 Accept the REF-002 allocation: all 275 SADS IDs remain tracked program-wide, all direct
  X-COM IDs XVE-SYS-0139–0158 have an explicit capability-007 disposition, and deferred targets are not
  implementation claims.
- [X] ACC014 Authorize the exact implementation plan and dependency preflight. This does not authorize
  any legacy repository change, legacy execution, external peer, TCP tool listener, or deployment.

## Decision record

**Reviewer**: User
**Date**: 2026-09-21
**Decision**: Approved all ACC001–ACC014 and authorized the bounded capability-007 implementation.
**Amendments / exclusions**: Preserve the documented exclusions. No legacy integration/execution,
external peer, TCP listener, deployment, or compatibility claim is authorized.

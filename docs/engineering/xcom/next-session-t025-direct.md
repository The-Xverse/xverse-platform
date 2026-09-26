# Next-session prompt — direct X-COM T025 successor

Work in `/home/jefferson/xverse-platform`. Follow `AGENTS.md`, ADR-0020, the Spec Kit workflow, and
the capability-007 sources listed below. Do not use SESN. Do not invoke an external provider or transmit
workspace content externally. Treat the workspace as RESTRICTED and keep all work local.

This activity repairs the rejected T025 direction and produces a new successor candidate. It does not
accept T025, authorize T026–T034, establish compatibility, or permit legacy or production execution.

## Required inputs

- `.specify/memory/constitution.md` and applicable `.specify/commands/speckit.*.md` instructions;
- `docs/adr/ADR-0018-platform-first-delivery-sequence.md`;
- `docs/adr/ADR-0019-xcom-validation-and-observation-boundaries.md`;
- `docs/adr/ADR-0020-repository-owned-engineering-workflow.md`;
- `docs/reviews/014-xcom-observation-implementation-review.md`;
- `docs/reviews/015-xcom-post-sesn-workflow-review.md`;
- `specs/007-xcom-core/{spec.md,data-model.md,plan.md,tasks.md,reference-traceability.md}`;
- `specs/007-xcom-core/contracts/validation-tool.md`; and
- the accepted predecessor evidence bound to
  `d244eeb3aa26f1b27d23d75fabc750380405269f`.

Preserve every existing user change and untracked file. Do not add `.sesn/sesn.sqlite3` to Git. The
rejected T025 candidate named in the older prompt is evidence only and is not available as an accepted
baseline in the current checkout.

## Engineering workflow

1. Create or reconcile one capability work-product set for the T025 successor without duplicating
   `specs/007-xcom-core`.
2. Record the exact baseline, authorization boundary, requirements, architecture, detailed design, unit
   specifications, ownership, failure semantics, bounds, verification measures, and REF-002 dispositions.
3. Implement only the bounded C++20 time-authority, validation-permit, and validation-session foundation.
4. Bind every requirement to design, code, tests, verification measures, and the exact candidate revision.
5. Run host-owned offline verification and retain commands, tool/environment identity, outcomes, bounded
   logs, manifests, and hashes. A dirty or revision-mismatched candidate fails closed.
6. Conduct a separate read-only Astra XHigh review after verification. Record findings before any repair.
   A repair creates a successor candidate and repeats affected verification and review.
7. Present the inspected bundle for explicit user acceptance. Do not accept or integrate automatically.

## T025 scope

- explicit `TimeAuthority` with clock identity, bounded reads, declared source/destination mappings,
  tolerance, and deterministic unknown-clock, absent-mapping, overflow, and regression outcomes;
- immutable host-controlled `ValidationPermit` bound to one session, exact plan/XDL digest, scenario,
  deployment/environment, tool, interfaces, targets, actions, validity interval, finite quotas, and nonce;
- complete validation and exactly-once permit consumption across relevant controller instances;
- bounded `ValidationSession` ownership with non-reusable controller/session identity and exact-generation
  handles;
- reachable `declared -> armed -> active -> closing -> closed` lifecycle and terminal `expired`,
  `revoked`, and `evidence-incomplete` states;
- deterministic stale, foreign, replay, mismatch, expiry, revocation, quota, time, and unsafe-repeat
  rejection without state mutation;
- stable ordered public diagnostics and complete Doxygen ownership, lifetime, thread-safety, failure, and
  bound documentation.

## Exclusions

Do not implement T026–T034, journaling, injection, service invocation/emulation, leases, gateways,
Protocol Buffers/gRPC, IPC/TCP, persistence, XDL compilation, adapters, networks, Argus, dashboards,
legacy integration, deployment, or production workloads.

## Required verification

Cover the complete permit mismatch and exactly-once matrix; clock mapping, tolerance, regression, overflow,
concurrency, and lifetime behavior; lifecycle and terminal transition matrices; stale/foreign/recreated
handles; safe idempotency; no mutation after rejection; strict Doxygen; static analysis and sanitizers
available in the admitted offline environment; reciprocal traceability; all predecessor X-COM validators
in substantive mode; and explicit zero normal-route emissions.

Use Sol High for direct implementation and integration. Reserve Astra XHigh for the independent read-only
review. A cheaper model is suitable only for bounded mechanical documentation edits after the technical
decisions are fixed.

# Quickstart: X-COM core design review

No X-COM executable exists yet. Review this package in the following order:

1. [Feature specification](spec.md) and [clarifications](clarifications.md).
2. [ADR-0018](../../docs/adr/ADR-0018-platform-first-delivery-sequence.md) and
   [ADR-0019](../../docs/adr/ADR-0019-xcom-validation-and-observation-boundaries.md).
3. [Research](research.md), [data model](data-model.md), and [implementation plan](plan.md).
4. [REF-002 requirement traceability](reference-traceability.md).
5. Contracts for the [activation plan](contracts/communication-plan.md),
   [provider](contracts/provider.md), [observation](contracts/observation.md), and
   [validation tool](contracts/validation-tool.md), plus the
   [`io.xverse.xcom` Profile](contracts/xdl-profile.md) and
   [local tool gateway](contracts/tool-gateway.md).
6. [Tasks](tasks.md), [analysis](analysis.md), and [acceptance checklist](checklists/acceptance.md).

The first implementation, if authorized, must run only owned loopback fixtures and synthetic tools,
including one separate-process tool over local IPC. It must not run or adapt the pinned gateway,
contact external peers, open a TCP tool endpoint, create dashboards, or claim
protocol compatibility, network fidelity, or production readiness.

The implementation review must demonstrate that observed and injected items are distinguishable,
metadata-only taps expose no payload, every queue is bounded, unauthorized stimulation emits no
traffic, slow best-effort observers do not alter normal-route outcomes, and Doxygen/traceability are
complete.

# Next-session prompt — X-COM T025 repair after independent review

> **Superseded on 2026-09-26 by ADR-0020. Do not execute this SESN workflow.** It is preserved as historical planning context; use [next-session-t025-direct.md](next-session-t025-direct.md) for the successor work.


Work in `/home/jefferson/xverse-platform` and use the local SESN application in
`/home/jefferson/sesn`. This is a repair of the rejected T025 candidate, not an acceptance,
integration, compatibility, or production-readiness activity.

Read in full before acting:

- `AGENTS.md`, including the SESN credential-location and provider-admission rules;
- `.specify/memory/constitution.md` and the applicable `.specify/commands/speckit.*.md`;
- `docs/engineering/xcom/next-session-t025.md`;
- `specs/007-xcom-core/{spec.md,data-model.md,plan.md,tasks.md,reference-traceability.md}`;
- `specs/007-xcom-core/contracts/validation-tool.md`;
- `docs/adr/ADR-0018-platform-first-delivery-sequence.md` and
  `docs/adr/ADR-0019-xcom-validation-and-observation-boundaries.md`;
- `docs/reviews/014-xcom-observation-implementation-review.md` and the 019 acceptance
  decision/evidence; and
- the review findings recorded below.

## Starting point and authority

The accepted predecessor baseline is
`d244eeb3aa26f1b27d23d75fabc750380405269f`. Preserve the user’s dirty workspace and do
not add `.sesn/sesn.sqlite3` to Git. The rejected implementation candidate
`62be2dfc02d55bb9c7287815915d0e6254a40fe7` may be inspected as evidence only; do not
present it as accepted, patch it in place, or bind SESN evidence to it. Create one fresh
SESN activity and one Spec Kit capability work-product set for the successor T025 repair.

The existing feature record’s candidate is only planning commit
`6a9ff96c624df7a70a0d311dad8854d772062d29`, has no evidence, and cannot be amended to
claim verification of the rejected source commit. Do not reconstruct a historical SESN run.
The user’s acceptance of feature 019 remains scoped to its exact baseline and does not
authorize accepting T025.

## SESN admission and credential handling

At the start of the activity, declare the packet classification, provider use, and monetary
budget. This repair begins RESTRICTED; no RESTRICTED material may reach DeepSeek. Use
DeepSeek only through SESN and only for a directly PUBLIC or validated SANITIZED,
hash-bound, secret-scanned minimum packet. Declare `USD 0.10` maximum per request and
`USD 0.50` maximum aggregate, including retries and batch items. Record packet, policy,
route, price card, limits, actual usage, actual cost, and limitations. Unknown admission,
price, quota, endpoint, retention, or cost fails closed.

Every SESN-capable session must use the approved credential-loading path, which consults
`$HOME/.config/sesn/deepseek.env`, before concluding that `DEEPSEEK_API_KEY` is unavailable.
Never print, copy, persist, transmit, or place the credential value in context, a prompt,
packet, log, evidence, or source control. Do not bypass the SESN loader by manually sourcing
the file. If the implemented SESN loader cannot consult this location safely, record a
blocking SESN defect and repair SESN separately before relying on an external-provider result.
Credential presence never substitutes for provider admission.

Use Terra Medium for SESN orchestration. Use the official DeepSeek API through SESN for the
maximum useful eligible work. Use Sol High only for a complex local integration repair after
a DeepSeek proposal is rejected. Reserve a separate, read-only Astra XHigh session for final
review. Do not claim a model switch that did not occur.

## Repair requirements

Implement only the bounded C++20, domain-neutral T025 foundation. Do not implement T026–T034,
transport, IPC, network, payloads, gateway/protocol work, persistence, journals, leases,
service execution/emulation, XDL compilation, legacy integration, dashboard, Argus, or a
production workload.

Address every review finding with an explicit requirement, design decision, code change, test,
and bidirectional trace edge:

1. **Exact ownership and stale/foreign safety.** Handles must be unforgeable or verified
   against a host-generated non-reusable controller/session identity and generation. A caller-
   supplied numeric controller ID must not authorize another controller’s record. Destroying
   and recreating a controller must not make an earlier handle valid. Define and verify the
   bounded exhaustion/reuse behavior.
2. **Authoritative time.** Bind permit validity to a declared clock domain and use the explicit
   `TimeAuthority` for all lifecycle and action time decisions; never compare raw unmapped
   timestamps. Return deterministic unknown-clock, mapping-absent, tolerance, regression, and
   overflow outcomes. A time regression must be observable, not silently returned as `false`.
   Mapping requires declared source *and* destination clocks. Fix synchronization/lifetime
   semantics, including copying or make the mutable authority non-copyable.
3. **Complete immutable permit validation.** Bind one exact session ID, digest, scenario,
   deployment, environment, tool, interface, target, nonce, actions, validity, and every finite
   quota/capacity. Reject unknown action bits and composite/undefined action values. Specify
   exactly-once consumption scope and reject duplicate session ID or exact permit identity even
   when the nonce changes; test consumption across all relevant controller instances.
4. **Complete lifecycle and rejection semantics.** Make `declared → armed → active → closing →
   closed` reachable and separately observable. Terminal `expired`, `revoked`, and
   `evidence-incomplete` states are terminal and cannot be overwritten. Define safe idempotency
   and reject unsafe repeats deterministically. Validate handle/context/action before an
   operation can mutate state; verify rejection leaves the record unchanged. Do not use a
   synthetic timestamp such as zero for close/revoke/evidence handling.
5. **Documentation and diagnostics.** Public Doxygen must document ownership, lifetime,
   thread safety, state/time failure semantics, capacities, identity properties, and all public
   parameters. Diagnostics must remain stable, ordered, public, and payload-free.

Do not reduce or monkeypatch an existing X-COM validator. If a predecessor validator requires
an explicit extension-registration mechanism to recognise a new accepted unit, design and
review that mechanism as a compatibility-preserving change; otherwise record the blocker rather
than bypassing the predecessor gate.

## Required host-owned verification

Before repair, record the independent review findings in the SESN activity. After repair, run
and retain host-owned evidence for the exact successor revision:

- permit nominal and every field/action/session/nonce mismatch matrix, exactly-once scope,
  finite quota/capacity, and deterministic concurrent consumption;
- declared mapping source/destination, tolerance, unknown clocks, regression, overflow,
  concurrency, lifetime/copy behavior, and no raw-clock bypass;
- full lifecycle and terminal transition matrices, safe idempotency, stale/foreign/recreated
  handles, time-window enforcement, and no-mutation-after-rejection;
- deterministic session-operation concurrency tests;
- strict Doxygen, substantive lint, static analysis, and sanitizers available in the admitted
  offline environment;
- schema validation and reciprocal requirement ↔ design ↔ code ↔ test ↔ measure traceability;
- every predecessor X-COM validator in its substantive `--all` mode, without modifying it to
  hide the new unit; and
- explicit zero normal-route emissions.

The T025 validator must bind its checks to the actual `HEAD`/declared candidate revision, fail
when they differ, and distinguish unit, lint, static, integration, sanitizer, documentation,
traceability, and regression checks. It must not report success when invoked without a
substantive requested check.

## Delivery and review gate

Deliver a successor revision only with its complete SESN work-product set, candidate-bound
evidence, exact command results, REF-002 SADS dispositions, DeepSeek accounting/limitations,
maintenance guidance, and remaining limitations. State failures honestly; a failed or skipped
provider request has unknown—not zero—usage/cost unless an authoritative receipt says otherwise.

Do not accept, merge, push, deploy, or claim compatibility/parity. After host verification,
request a separate Astra XHigh read-only review of the successor. Record its findings before
any follow-up repair, then present the bundle for explicit user acceptance.

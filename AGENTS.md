# X-Verse vNext Engineering Rules

## Repository responsibility
Owns the domain-neutral platform, authoritative architecture decisions, and cross-repository M0 inventory. Future code belongs here only after its capability specification and gates are satisfied.

## Production safety
Existing The-Xverse repositories are production assets and immutable by default. Unless the user
explicitly authorizes a specific repository and change, do not modify them or create branches,
commits, issues, PRs, tags, CI/CD changes, package/image/API/topic/protocol renames, deployment
changes, or vNext dependencies in them. Read-only inspection is permitted. Integration must use
external XDL descriptors, compatibility adapters, orchestration, public APIs/protocols, or existing
artifacts. Never execute a production workload as part of M0 discovery.

## Architecture
X-Verse is a domain-neutral CPS platform; automotive is a specialization. Dependencies flow:
blueprints → domain profiles → XDL/platform APIs → runtime abstractions. The reverse is prohibited.
Separate logical identity from realization; physical devices are first-class. Prefer standards
interoperability and parallel evolution over replacement. Record major decisions in ADRs before
implementation. XDL is canonical; do not invent competing configuration languages.

## Spec Kit and quality
Read `.specify/memory/constitution.md` and the relevant `.specify/commands/speckit.<stage>.md`.
Use the official workflow and one specification per capability. Commands are agent instructions,
not executable shell scripts. The canonical M0 feature is in xverse-platform; companion setup is
tracked there. Do not duplicate its specification in companion repositories.
Each feature requires acceptance criteria, validation, documentation, compatibility impact,
failure semantics, observable behavior, and an accurate maturity classification. Keep implemented,
partial, target, and exploratory work distinct. Source inspection does not demonstrate runtime success.
Conduct a separate review pass; record findings before repairing them in a subsequent pass.
Each capability must identify applicable REF-002 SADS requirement IDs and preserve an explicit
implemented/partial/allocated/deferred/superseded/conflicting/needs-clarification disposition. The
SADS is target input, not proof that a capability exists.

## Model recommendations
Before each substantive next step, tell the user which model and reasoning effort offer the
best expected cost-effectiveness for that specific task. Consider Terra, Luna (called Lua by
the user), Sol, and Astra; briefly explain the choice and when a cheaper option or escalation
is justified. Distinguish task-based judgment from measured results; do not claim benchmarks
or exact costs without evidence. Verify current pricing when quoting it, and distinguish API
prices from account usage. Do not claim to switch models unless a switch actually occurred.
This recommendation is informational and does not add a new approval gate to authorized work.

## Current boundary
Setup, M0, M1, and M2 specification/design have been delivered. The user approved M2 on 2026-09-20.
Capability 004 provides an approved prototype local XDL v1alpha1 loader, validator, normalizer, and
CLI; the user accepted it and ADR-0013 on 2026-09-20. It is not a runtime, adapter, registry, catalog,
blueprint, compatibility guarantee, live-readiness probe, or production interface. M3 may be specified,
but its implementation requires its own authorization and does not authorize legacy execution. Keep
changes local. Public-safe content must exclude private source excerpts, secrets, and sensitive
deployment details.

M3 now has a prototype platform implementation in `specs/005-component-catalog-compat-runtime`. It
derives an XDL-anchored catalog, plans without side effects, and proves owned lifecycle mechanics with
an isolated fixture. SD-0001 pins one nominated gateway candidate and an intentionally blocked plan;
its locked validator and evidence-closure packet are ready for owner input. It does not complete
legacy selection, implement a legacy provider, permit legacy execution, or establish compatibility/
parity; each remains a separate recorded gate.

ADR-0018 now requires platform-first delivery. Implement and accept the main platform capability
baselines and stable extension contracts before resuming target-specific legacy adapters, SD-0001
derivative work, cruise-control parity, or migration. ADR-0019 requires X-COM to provide controlled
observation and stimulation boundaries; Argus owns dashboards and telemetry presentation.

## Source of truth
The authoritative baseline is `xverse-platform/docs/architecture/XVERSE_VNEXT_ARCHITECTURE_AND_CODEX_GUIDANCE.md`.
The platform owns architectural governance; each companion owns its responsibility above.
No individual maintainers or approval assignments are inferred.

## Subsystem names
Use **Maestro** for orchestration (`xverse.maestro`), **X-COM** for communication (`xverse.xcom`),
and **Argus** for observability (`xverse.argus`). Preserve generic XDL/metamodel semantic terms.
ADR-0016 is authoritative for this naming update; do not scaffold these target packages before their
Spec Kit capabilities are accepted.

## Implementation languages
Select each module's implementation language from explicit quality attributes including latency,
throughput, determinism, memory behavior, safety, ecosystem fit, portability, deployment, and
maintainability. Record the allocation and rationale before implementation, and use measurements
when performance is decisive. X-COM and other performance-critical data-plane modules shall be
C++ based. Define and verify explicit contracts at every cross-language boundary. Do not select
languages for unapproved target modules merely to scaffold the future architecture.

## SESN software work-product workflow
For every future X-Verse production software change, use the local SESN application to produce the complete
auditable and maintainable work-product set, not only source code. Codex acts as the SESN client: supply the
complete baseline, stakeholder/system/software requirements, constraints, architecture, detailed design,
unit specifications, task ownership, verification measures, model/reasoning profile, and authorization
boundary. Require bidirectional traceability across requirements, architecture, design, code, unit tests,
integration tests, validation, findings, configuration identity, and delivery evidence. Review SESN's
candidate, evidence, findings, maintenance guidance, and limitations before assigning follow-up tasks or
applying its delivery to an authoritative repository. The process is inspired by Automotive SPICE outcomes
but must not claim certification or capability level. Replay output is not a substitute for a live SESN
engineering run. Documentation-only governance updates and read-only analysis may be performed directly.
Preserve the existing Spec Kit, legacy immutability, public-safety, and execution-permit gates inside every
SESN input.

Report SESN defects or material workflow improvements to the user as they are discovered. Decide whether
to repair SESN before continuing based on impact: defects that can compromise artifact correctness,
traceability, isolation, evidence, or review validity block the affected SESN result and require a separate
verified SESN fix; non-blocking usability defects are recorded and deferred until the active X-Verse
delivery is complete so the engineering-tool baseline does not change mid-delivery.

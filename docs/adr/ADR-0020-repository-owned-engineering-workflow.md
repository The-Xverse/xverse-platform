# ADR-0020: Repository-owned engineering workflow

**Status:** Accepted — directed by the user on 2026-09-26

**Date:** 2026-09-26

## Context

The X-Verse program previously required SESN to generate production software work products, coordinate
implementation, retain verification evidence, and run the independent review. Capability 007 planning and
acceptance records therefore contain SESN-specific gates.

The user has directed that future work will no longer use SESN. The technical assurance obligations remain:
exact scope and authorization, complete requirements and design, bounded implementation, bidirectional
traceability, reproducible dependency admission, exact-candidate verification, a separate review pass,
recorded findings before repair, and explicit user acceptance.

## Decision

Future X-Verse engineering uses the repository-owned Spec Kit work-product set directly. Codex maintains
the requirements, architecture, detailed design, unit specifications, tasks, source, tests, traceability,
verification measures, configuration identity, evidence, maintenance guidance, and limitations in or from
the authoritative repository.

Every software candidate must be bound to an exact source revision. Its evidence bundle must identify the
executed commands, tool and dependency versions, relevant environment identity and isolation policy, exit
status, bounded logs, and content hashes. Evidence must be reproducible from documented inputs and must
remain public-safe where published. Source inspection alone is not runtime evidence.

Independent review remains a separate read-only pass. Findings are recorded before repair. Any repair
creates a successor candidate and repeats every affected verification and review gate. The user explicitly
accepts or rejects the inspected candidate; Codex does not accept, integrate, publish, deploy, or advance a
dependent feature automatically.

SESN is not used for future implementation, verification, review, or acceptance. Historical SESN artifacts
remain valid only as historical evidence for the exact revisions and claims to which they were originally
bound. They are not deleted, rewritten, or treated as evidence for a successor candidate.

## Consequences

- Spec Kit remains the authoritative capability workflow and one specification remains required per
  capability.
- Repository-owned work products must replace every forward-looking SESN-specific task and gate.
- Dependency locks, generated-code provenance, offline checks, exact-candidate validators, traceability,
  separate review, and explicit user acceptance remain required.
- Existing implementation authorization retains its technical scope and exclusions, but its execution
  method is amended prospectively by this decision.
- Capability 007 cannot proceed to T026 until a successor T025 candidate passes the replacement workflow
  and receives explicit user acceptance.
- The constitution remains at version 2.1.0 because its principles and acceptance gates are already tool
  neutral.

## Superseded process decisions

This ADR prospectively supersedes the SESN-specific execution method in capability-007 ACC012, the
SESN-specific part of ACC014, and forward-looking SESN language in its plan, tasks, contracts, and build
evidence documentation. It does not supersede their technical scope, safety exclusions, traceability duties,
or historical decision records.

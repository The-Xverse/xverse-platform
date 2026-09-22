# M1 clarification record

**Feature**: [M1 domain-neutral metamodel](spec.md)
**Date**: 2026-09-20
**Method**: Spec Kit clarification coverage scan; decisions below use the approved guidance and M0
review context. No new user question was needed because each decision is a bounded architectural
default that remains reviewable before M2.

| ID | Area | Decision | Reason and effect |
|---|---|---|---|
| C01 | Identity | Require namespace-qualified stable semantic identifiers; defer identifier syntax and registry governance to M2. | Prevents provider-local identity leakage without pre-designing XDL serialization. |
| C02 | Logical/realization split | Deployment is the only binding from logical architecture to an environment realization. | Preserves the identity of a Device/Component across simulated, virtual, physical, and hybrid use. |
| C03 | Lifecycle | Use Definition, Binding, Execution-intent, and Observation profiles; do not define a scheduler/runtime state machine. | Makes readiness, failure, evidence, and maturity explicit while keeping implementation scope in later milestones. |
| C04 | Extension | Profiles use declared namespaces and cannot redefine core identity, required relations, or validation meaning. | Keeps the core domain-neutral and lets standards/providers evolve outside it. |
| C05 | Standards | Reference and bind external architecture/model standards; do not recreate their semantic universes. | Matches XDL centrality and standards-interoperability invariants. |

## Coverage outcome

Functional scope, entities/relationships, lifecycle, integration boundaries, failure handling,
observability, terminology, completion criteria, and exclusions are clear. Performance, availability,
security implementation, concrete protocol mappings, schema packaging, and runtime behavior are
intentionally deferred to M2 or later capabilities. No unresolved clarification marker remains.

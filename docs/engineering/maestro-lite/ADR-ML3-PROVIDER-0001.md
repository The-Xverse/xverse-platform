# Process readiness and dependency admission (partial U4/U5)

Revision ML3-PROVIDER11-2026-10-18-v1; parent a31d093.
Decision recorded before implementation. Python composes existing bounded native
catalog Query and Release RPCs. No arbitrary callback, shell, application probe,
new process launcher, storage owner or competing XDL representation is introduced.

ProcessReadiness consumes the original ReleaseOwner/prepared graph with isolated PersistenceClient (legacy synchronous-storage owners reject), exact current
CatalogLauncher handles, and finite per-unit probe policies. Only a catalog observe
condition of running is supported: existence after observed exec, explicitly not
application readiness. Unsupported conditions reject before any Release.
Prerequisites derive from ancestors of the unit dispatch in the combined graph,
including flow and step dependencies. Before dependent Release all prerequisites
are re-probed through their original issuing launcher. A private exact-owner guard
is checked inside ReleaseOwner before Arm and again immediately before Release.
It rechecks current generation, live issuer/child, same session and freshness of
all prerequisite observations. Sampling cannot imply continuous health or an
atomic transaction across different native launchers/gates.

A declared readiness window has at most three actual queries, each within the
original caller deadline and its admitted timeout. Failure/unknown/stale evidence
closes the existing independent latch; it never grants a retry of Release.
Health sampling is caller-driven with an explicit next deadline; autonomous tick/
health scheduling, teardown, restart, durable normal outcomes and U7/U8 are pending.
The facade accepts already staged exact resources: full start/bootstrap admission
and durable helper permits remain pending. Legacy primitive callers retain the
old release signature; this component is not universal runtime admission.

Bootstrap finding 14 is repaired by comparing the public session alias against
the original immutable admitted generation before dispatch. Cancellation retains
its independent original-holder cleanup path.

Trace: ML-SR-007/008 partial, ML-SR-009/012/024 supporting partial evidence;
FR-004/005/006/012. All other ML-SR and all 18 allocation-only REF-002 parents
remain open. Parent source semantics, all nine runtime cases and acceptance remain
unvalidated. No scientific protocol or canonical-note change. Sol/high recommended
for authority integration; routine receipts can use a cheaper model. No factory run.

Spec Kit: main prerequisite resolves unrelated feature 020; external thesis 024
and this continuation govern the authorized implementation. No extension hooks.

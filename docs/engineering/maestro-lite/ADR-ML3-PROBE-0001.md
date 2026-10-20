# ADR-ML3-PROBE-0001 — Final native prerequisite observation

2026-10-19. Selected engineering refinement before implementation, full17 candidate.
Actual active-restart-c original93143 terminal1 records two prerequisite probes in
one fixed 0.5s generation operation; the final own probe expires with 66.21ms left
and 66.76ms actual duration. Do not increase that end or cache a prior observation.

For the original native RunUnitIssuer path, omit prerequisite units only from the
early all-released preflight. RunBroker.release still requires the original
DependencyGuard, both original durable revalidations, native ARM, live original
prerequisite probes after ARM and immediately before RELEASE. Unrelated released
units keep their early live observation. Legacy CatalogLauncher keeps all prior
checks. No native guard, current-handle identity, freshness or fixed end is removed.

Expected proof: exactly one successful parent probe after ARM before RELEASE;
parent death after ARM blocks RELEASE; altered deadline rejects; unrelated live
unit is sampled before ARM and its failure blocks ARM. Preserve the original
timeout and all failed attempts. One passing successor is not host stability or
full17 acceptance. Existing native checks with an expected duplicate count must
be refined to the source-derived ordering/failure contract, not merely relaxed.

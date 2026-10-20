# Explicit original broker in cleanup construction

2026-10-19. Candidate refinement of ADR-ML3-CLEANUP-0001, before repair335.
Scope: capability024 ML-SR-011/012/013/019/020/022, DV06/07/10. Python remains
allocated to host lifecycle composition; native BS17/AFFA and original C1 retain
containment and wait authority. No native protocol or public XDL/M3/Argus change.

The whole runtime passes its privately retained original broker to RunClosure.
Its explicit-broker constructor currently requires ordinary issuer registries to
remain intact. Original two-window source/wheel controls reproduce four missing
primary closures after generation-registry loss; external root-only cleanup was
required. The existing implicit derived-broker path already permits original
cleanup despite ordinary registry loss.

Use RunBroker._cleanup_context for explicit cleanup construction as well. Keep
exact RunBroker type, original bootstrap/session relationship and equality with
any broker derived from the original teardown. The private accessor verifies
the original object/process,bootstrap,storage,authority and owner pins. No new
broker,discovered resource,ordinary handle,launch,restart or registry adoption is
authorized. Damaged original context still rejects. Ordinary methods keep their
full _holder checks. Construction itself performs no native operation.

Verify actual whole-registry start/stop at native Stage before handle publication
and after first release,then original primary closure/root/helper waits/C1 release,
unknown direct workload waits,incomplete normal evidence,matching replay without
birth and an unrelated sentinel. A copied broker must reject before authority I/O.
Preserve every original red/fallback result and repeat affected legacy/shared
closure,entry,startup,registry and authorization-window controls on a fresh exact
source/wheel snapshot. Do not repair the five prior timeout incidents by inference.

This is an unaccepted isolated candidate. Full runtime/source-parent/M1/regression/
independent review and explicit acceptance gates remain. No stable17,automatic
CAPA,independent causal confirmation,effectiveness or scientific claim follows.

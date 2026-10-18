# ADR ML3-RECOVERY-0001 — Surviving original issuer reconciliation

18 October 2026. Partial candidate, not accepted. Parent 6083439. External capability
024/ML-DESIGN-2026-10-03-v2 remains authoritative. ML-SR-006–008, 011–014, 016,
018–020, 022–024 are partial consumers; all 24 ML-SR, 18 unvalidated/null-mapped
REF-002 parents, 30 scenario pairs/90 endpoints and nine runtime cases remain binding.

Use Python for bounded original-supervisor reconstruction and storage-owner durable
revalidation; native issuer Query, wait, C1 and wire remain unchanged. The surviving
BootstrapSession/ReleaseOwner/CatalogLauncher registry is authority. No new broker,
PID/path lookup, reconstructed handle or reopened writer may substitute for it.

Add an original-worker reconciliation RPC that never writes the journal or Argus.
Its new view epoch conservatively retires prior in-memory positive applicability. Independently verify original
intent/permit consumption, immutable journal history, full exact handle fields,
matching start outcome and actual public mirrors/source hashes. A staged resource
with no durable full handle is cleanup-only, never recovered ordinary ownership.
Check original native issuer/handle with bounded Query before and after the RPC.

Retire prior readiness views under a monotonic owner view epoch and nonblocking
original mutation/view locks. Construct a new observation/cleanup view only after
all required ownership checks. It begins without positive observations and resumes
normal durable probe sequencing from the original worker's actual maximum. Old
views cannot supply freshness or normal operations. Starts/claims/Stage stay closed
irreversibly; recovery creates no execution ID, permit, generation or Release.
Independent cancellation remains available across the view boundary.

This is reconstruction of high-level controller state inside the same surviving
original supervisor process. Its original host-monotonic domain remains unchanged;
the view epoch is NOT the M1 release epoch. A different host session, process copy,
replacement issuer or orphaned active mutation owner cannot recover ordinary
ownership. Cross-process supervisor recovery requires the independently surviving
broker/admission work; it remains open. Neither this primitive nor a receipt grants
new authority. Explicit restart, U7/U8, global M1, admission and acceptance remain
pending. No factory run, canonical-note change, merge or scientific change.

Failed/unavailable durable/issuer checks close starts and invoke original RunClosure
under the caller's original reserved cleanup end. Preserve unknown facts and normal
record gaps. Successful reconciliation permits only observations and owned teardown;
no automatic scenario replay or reuse of old readiness. Sol/high is recommended.

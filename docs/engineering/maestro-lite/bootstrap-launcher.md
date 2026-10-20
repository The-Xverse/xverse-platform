# Original bootstrap launcher and reservation

Status: internal component implemented and owned source/wheel verified; complete
run admission/entry remains pending. Capability024 and the DRAFT
[RUNTIME-0002](ADR-ML3-RUNTIME-0002.md) refinement govern this layer.

`OriginalBootstrapRegistry` reserves an original run before creation, with an
explicit capacity1–128 and no implicit eviction/reuse. Exact original reservation
arguments return the same owner; changed arguments reject. The original owner
retains a sealed supervisor descriptor, hashes actual supervisor/helper bytes and
checks seals, original C1/approval/run/generation/lease and private configuration
before its single `Popen`. Execution uses the retained descriptor. This trusted
low-level bootstrap interface is not a full authorization or M1 validator.

The returned original process and independent pidfd are retained before READY.
Successful registration delegates root waits solely to the original
`BootstrapSession`. Failed registration uses only the original independent pidfd.
Startup, drain and disposal share a nonblocking lock; cancellation sets the
original latch independently. Rejected repeats and pre-birth validation failures
do not cancel an existing run or an untouched latch. Startup/drain keep their
original ends. The initial kernel/Popen birth is not proved bounded under host
failure; external admitted facility coverage is still required.

If no usable process/pidfd capability returns, the owner preserves an unknown
birth/wait, rejects creation replay and ordinary disposal, and performs no PID or
path discovery. Separate external owned test cleanup is recorded as such and
never upgrades runtime ownership. Outcomes keep execution readiness and overall
cleanup false at this layer; helper/root waits cannot supply workload waits.

Original88499 exited0:19 startup controls,2 original v6 composition controls,
10 bootstrap-codec and40 read-only joint-preflight controls per phase,
**71/71 source and71/71 wheel**. The composition retains normal closed and lost
close-ACK behavior, original terminal receipts, all3 helper waits, both native
workload waits and original C1 releases. A durable closed writer after lost ACK
does not replace the missing host acknowledgement.

Original11775 exited0: **3/3 additional unknown-startup controls per phase** on
the same78 production source bytes. Six owned supervisors are externally reaped;
all six runtime waits remain unknown and ordinary disposal still rejects.
Combined selected checks total74 per phase, without a production change between
the two frozen runs. This is not whole-platform regression.

The original collector returned zero public snapshots because it scanned the
prior fixture's receipt names; audit e0c6ec failed. Original scripts/indexes remain
unchanged. A successor collector reads the same retained sources into public-v2;
audit83c7f3 verifies114 absent owned parent reservations,12 actual original
supervisors,12 helpers,8 workloads,220 exact M3/Argus links and4 durable closed
public roots. Audit7cf45d verifies6 additional external original waits without
runtime wait credit. No unchanged native retry was used to repair collection.

See [original run audit](evidence/affa17/bootstrap-launcher-20261019a/verification-v2.json),
[unknown-startup audit](evidence/affa17/bootstrap-launcher-unknown-20261019a/verification.json),
[CAPA successor](evidence/affa17/capa-20261019-bootstrap-launcher/register.json),
and [partial trace](evidence/affa17/bootstrap-launcher-partial-traceability.json).
CAPA269 tracks only the collector gap;13 records/64 evidence bindings validate.
All effectiveness states remain NOT_DEMONSTRATED;135/222 remain UNRESOLVED.

The next entry layer must validate real authorization/facility receipts and current
capabilities, own the original full run/control registry, and compose preparation,
bootstrap, dispatcher, explicit active controls, collection and RunClosure into
the public whole-lifecycle contract. The low-level launcher does not use synthetic
preflight attestations as execution permission. All24 requirements,18 source
parents,30 pairs/90 endpoints,nine full runtime cases,seven P3 tasks,M1,
whole-platform regression and complete independent review remain open.
No stable17 checkpoint, acceptance, merge, factory run or scientific result is claimed.


The subsequent [startup ownership repair](startup-ownership.md) pins actual original
process/channel/pidfd/capability/session resources, rejects ordinary aliases and
preserves cleanup-only wait/outcome access. Five original faults fail per phase
before repair; current69 source/wheel checks pass each. The first harness's missing
sentinel acknowledgements remain unknown; no full late-birth/M1/stable17 closure.


[Late/unknown-birth controls](startup-late-birth.md) subsequently verify delayed or
cancelled Popen return and missing original capability, including whole-entry
incomplete result/replay. Six new source/wheel checks pass each on unchanged81
production files; external reap supplies no product wait/disposal credit for unknown
births. This does not prove initial kernel/Popen timing bounds or full M1.

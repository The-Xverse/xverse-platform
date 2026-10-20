# ADR ML3-AFFA-0001 — One run-wide native release authority

18 October 2026. Implementation design DRAFT, before code. Full capability024 and
ML-DESIGN-2026-10-03-v2 remain governing; this is an engineering continuation, not
acceptance or an experiment admission. Initial checkout parent6083439 is temporary:
advance this isolated candidate to the verified recovery16 commit before integration
or candidate freeze. Isolated new protocol/native unit work may proceed from this
pinned parent while recovery16 verifies; do not edit its frozen worktree or treat
that independent unit work as an assembled M1 implementation.

## Problem and required outcome

The current per-unit RG06 gates have independent epochs. Python iteration over
those gates cannot supply the selected M1 single transition over a whole run.
Existing original Python registries also cannot be adopted by a replacement process.
Recovery16 only reconstructs an observation view inside a surviving original holder.

Implement the complete selected M1 authority path: one Admission-Fixed Fence Authority
(AFFA) per run, owning its epoch, ticket table, original issued children and exact
boundary descriptors. Stage and Release must reach that authority. A disposable
controller may request actions but never own launch descriptors, mint a ticket or
turn a public handle reference into authority. The original supervisor/broker owns
all private objects and survives controller-worker death.

## Allocation and compatibility

Use a native C authority for frozen clone/exec, exact pidfds, original directory
file descriptions and serialized epoch/ticket transitions. Reuse verified native
techniques from catalog_launcher.c/bootstrap.c without treating their current
per-unit protocols as global M1. Use Python for original XDL/M3/Argus admission,
durable evidence, typed bounded RPC and supervisor/controller composition.

Add a versioned closed protocol and explicit image/descriptor admission. Preserve
accepted XDL/M3/Argus contracts. Existing partial component APIs remain historical
engineering evidence until the assembled successor is verified; compatibility must
be checked, not assumed. No automotive policy enters the platform core.

## One authority and ordering

The authority is fixed before any workload Stage. Its private table binds run/unit/
generation/operation/epoch, exact action/permit digests, original containment identity,
helper/supervisor session, one-use ticket nonce and original deadlines. At most16
units and the existing finite operation/event/lease bounds apply. No default bound
or permission is inferred.

RegisterIntent accepts only the original storage worker's durable consumption and
actual mirror/flush acknowledgement. Stage may create a child only while its exact
registered boundary is frozen and the run epoch is live. It obtains and retains
that child's original pidfd before returning a handle. Spawn-to-ACK uncertainty
remains cleanup-only under the pre-registered C1 scope.

Arm and Release use the authority's own current epoch. Ticket validation, consumption,
Release linearization and unfreeze occur within its exclusive transition. Cancel
advances the same epoch irreversibly, revokes all unused tickets and freezes all
original run boundaries. A Release ordered after that transition executes zero
workload instructions. A Release committed before it may need teardown. A client
latch observation is not substituted for the native transition acknowledgement.

A stalled authority cannot be treated as having acknowledged Cancel. The original
supervisor latches cancellation independently of its normal mutation lock and uses
its exact retained native pidfd plus C1 scopes. Before fallback cleanup can certify
empty/released scopes, all authorities able to thaw or create children in those
scopes must be irreversibly fenced or actually terminated/reaped. A delayed native
operation cannot resume after such certification. Signal delivery alone proves
neither death nor cleanup. Unknown termination/freeze stays unresolved.

Lease expiry or original-supervisor loss fails closed. A new authority instance has
no adoption rights for old generations. Renewal cannot revive a cancelled epoch,
expired boundary, closed writer or consumed ticket.

## Controller recovery and explicit restart

Keep authoritative registry, M3/Argus worker and C1 ownership in the original
supervisor/broker. A fixed admitted controller worker receives only a bounded
request channel and inert public state. Every request is bound to its original
registered child identity, controller session and finite sequence/deadline.
Controller replacement requires original-child death/reaping evidence and retirement
of that channel/session; a fork, copied holder or replacement broker cannot adopt it.

A new controller host session cannot reuse previous readiness. Revalidate the
surviving original issuer, exact durable handles and consumption state, then obtain
actual new health observations. Reuse recovery16's durable reconciliation primitive
inside the surviving holder where appropriate. Never reinterpret its view epoch as
the global release epoch or subtract clocks from different sessions.

Controller requests reference original broker-issued operation leases with absolute
ends in the broker's retained clock domain. A replacement controller cannot extend
those ends by translating its new local clock or resending a duration. Its own
bounded receive timeout is separate. The broker performs live freshness/Release
checks using its own same-session clock after retiring prior applicability; no
subtraction or implicit mapping between controller host sessions is permitted.
Neither public session labels nor operation references are bearer capabilities.

Explicit resource restart is separate: stop and release active transitive dependents,
confirm prior generation release, use new execution/generation and fresh permits,
advance the run release epoch and re-probe dependencies. Existing Argus roots are
never reopened; a successor run uses a new root and references prior facts.

## Evidence, admission and limits

Export public-safe issuance/epoch/terminal projections with actual source hashes,
without raw FDs, PIDs, secret nonces or bearer data. These facts must feed U7's original
admission-derived universe and U8 results; complete evidence and successful execution
remain separate. Preserve missing mandatory normal records even when C1 cleanup is
complete. Prove real host support before process-mode admission; this ADR proves none.

All24 ML-SR, all18 unvalidated/null-mapped REF-002 parents, all30 scenario pairs/90
endpoints, all nine full runtime cases and downstream phases4–9 remain binding.
Applicable partial consumers: ML-SR-005–014,016–020,022–024. Full independent review,
G1/G3/G4/G5, explicit acceptance and main integration remain open. No hard kernel or
control-I/O guarantee, scientific parameter/result change or canonical-note edit.
No factory run is created. Any new factory run must use
/home/jefferson/x-verse_fabric/automation/factory_start.py.

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

Current isolated engineering base after verified recovery16: `46e0ebfd332dd833322d764191a7cfe1e008bec1`. The
fast-forward preserved all unfinished AFFA files. Recovery16 is a committed partial
component checkpoint, not acceptance. Native authority, descriptor transport,
supervisor/controller integration and AF01–AF25 remain unimplemented/unverified.

## Native-unit implementation and bootstrap integration obligations

The current native core has69 passing component checks, including17 actual native
controls. These do not establish the original run admission/bootstrapping contract.
The next bootstrap design must explicitly authorize the run-wide authority role;
do not silently reuse a catalog/gate role or introduce runtime Popen.

An independent original watchdog must retain a scope that can freeze all productive
units on supervisor/AFFA lease loss. Killing a multi-unit AFFA alone does not prove
its already-released workloads frozen. A pre-admitted run-root boundary/guard or an
equivalent exact descriptor inventory is required before any Stage. A run root is
an explicit admitted container, not a per-unit PRBC boundary whose no-descendants
contract may be weakened. Original bootstrap/helper process placement and deadlines
must keep that watchdog able to act when the coordinator/storage/AFFA is blocked.

Global root freezing does not by itself prove empty membership, direct-child waits
or revocation of a stalled issuer's ability to create children. Before original C1
cleanup certifies release, actually revoke/terminate every authority that can create
or thaw in the scope. The existing stopped-authority component control demonstrates
original pidfd termination before C1 release; supervisor integration must preserve
that order. If both original supervisor and its retained cleanup authority are lost,
report unresolved; a replacement registry gains no adoption right.

C1 epoch registration and fresh generation approval contexts must be connected to
the actual original native epoch. Preserve immutable admission pins and old cleanup
capabilities. Do not update private counters/objects or reuse fixed generation1
worker state to claim fresh-generation permission. Multiple advances and real
M3/Argus intent/outcome sequencing remain required integration controls.

## Selected original watchdog integration — BC17 / BS17

Use an explicitly versioned successor of the original native bootstrap as the
independent watchdog. Keep BC10/BS10 limited to its original three roles. BC17
retains those three exact historical image pins plus a distinct fourth AFFA ELF
image, enables only storage3/AFFA4 (catalog/gate1/2 are disabled), and pins
only the original delegated parent directory identity. The parent is not a run-root
freeze scope and its per-unit no-descendants contract is unchanged.

Before any AFFA birth, register every initial workload boundary in the bootstrap's
bounded exact-FD watchdog inventory. New generations must register their fresh
original C1 boundary before ADVANCE. Each registration is acknowledged only after
actual frozen/empty leaf and exact original parent checks. Keep at most128 entries,
including retained removed generations; duplicate inode identity is rejected.
An original broker must enforce this precondition on every native registration or
advance. This component cannot authenticate arbitrary caller hashes as M3 proof.

The fourth role may be born only once, through clone3(CLONE_PARENT|CLONE_PIDFD|
CLONE_INTO_CGROUP), under a distinct original frozen helper boundary. The original
Python supervisor remains its actual wait-owning parent. Its sealed AC17 config
must bind the same generation, a lease no later than the bootstrap lease, and
initial boundary identities all already watched. The fixed argv is image, private
channel, sealed config. No caller command, runtime Popen or role borrowing.

On original supervisor/socket/lease loss or AFFA death, the native bootstrap
terminates all exact issued helper pidfds, observes death separately from Python
parent waits, then freezes every original watched boundary. Removed controls can
only be treated as absent; unknown control I/O remains unresolved. A stopped AFFA
cannot resume to thaw a boundary after this death-before-freeze sequence. Python
must still observe original waits and perform original C1 cleanup before release
certification. If this bootstrap is also stopped/lost, its freeze is unproven;
the surviving supervisor must independently revoke AFFA before C1 fallback.

This does not claim process-mode initial admission, actual M3/Argus composition,
typed authority-client enforcement, controller replacement, complete M1 or any full
runtime case. Those remain required in this same increment before stable freeze.

## Original cleanup-only bootstrap service (2026-10-19, candidate)

Finding136 requires an irreversible native BS17 transition (request5/reply21) that
fences the original watched C1 set and prohibits all subsequent productive helper
birth/activation, new watches and ordinary renewals. Only request6/reply22 may renew
the existing cleanup-only root, within the unchanged <=5s and generation-2s limits.
The original parent and storage liveness checks remain. Authority death is tolerated
only after this native transition; no workload cleanup is inferred from it. Legacy
BS10 and absent terminal use retain their protocol and behavior. Python permits this
service only for the genuine same RunBroker/session after its original cancellation.
Collection uses short service RPCs between items and caps each original storage end
at the current root lease, preserving the admitted aggregate end and terminal reserve.
This is partial U2/U7/U8 engineering, not a full-runtime or stable17 acceptance.

## Amendment S1a-3: a run cancel waits a bounded time for a busy authority connection (2026-10-23, written at 18:51:27; before implementation)

- **Context.** `RunBroker.cancel` sends K.CANCEL through `connection._exchange`, whose lock is non-blocking
  (`ML-AFFA-CONFLICT`).
  - An operator cancel (`entry.stop`) runs on its own thread. The dispatcher thread exchanges on the same
    connection for health queries, renewals and step effects.
  - A cancel that meets that exchange is refused, treated as unconfirmable and answered with `revoke()`, which
    SIGKILLs the authority. The bootstrap root then kills every child, including the storage worker. The run
    closes without its terminal evidence: S1a review log findings 18–21, about 2 in 10 live cancels, and
    reproduced deterministically in `test_stabilization_cancel_conflict.py`.
- **Decision.** For K.CANCEL only, the connection offers an exchange that waits for its lock up to
  `CANCEL_LOCK_WAIT_SECONDS` = 0.5 s, and never past the cancel's own end.
  - The frame is built *after* the lock is held, so its sequence follows the exchange that just completed.
  - The exchange is then the unchanged K.CANCEL exchange.
  - If the lock is not obtained within the bound, the call raises `ML-AFFA-CONFLICT` exactly as before, and
    `RunBroker.cancel` revokes as before.
- **Preserved.**
  - A stalled or unresponsive authority is still never treated as having acknowledged Cancel. Its in-flight
    exchange keeps the lock, so the bounded wait expires and the revoke follows.
  - The client latch is still set before the wait, so no new start authority is gained while waiting.
  - Every other exchange keeps the non-blocking lock, so two ordinary operations still never interleave.
  - The cancel's end, the generation − 2 s limit and the revoke deadline are unchanged.
- **Cost.** The confirmed cancel may come up to 0.5 s later. This stays inside the 1 s cancel end and the
  admitted cancellation drain of ≤ 2 s.
- **Verification.**
  - The busy-connection test passes when the lock is released within the bound: confirmed epoch, storage alive.
  - A new test holds the lock past the bound: revoke as before.
  - The existing cancel tests are unchanged.
  - The live cancel-paused runs (VS-09) follow after acceptance.
- **Implementation form (written at 18:52:06; still before implementation).** The bounded wait is implemented in
  `RunBroker.cancel`. That keeps `connection._exchange`, its non-blocking lock, and every other caller and test
  observer unchanged.
  - A K.CANCEL attempt that is refused with `ML-AFFA-CONFLICT` is retried every 1 ms until 0.5 s have passed or
    the cancel's end arrives. That refusal comes before any send, so it has no side effect.
  - Each attempt builds a fresh frame with the then-current sequence.
  - Any other error, and the expiry of the bound, lead to the unchanged revoke.
  - The `RunClosure` cancel fence (`run_closure._fence`) runs on the owner's thread after the dispatcher has
    finished, so this change leaves it as it is.

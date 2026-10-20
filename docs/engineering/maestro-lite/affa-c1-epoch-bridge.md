# Original native-to-C1 epoch receipt bridge

DRAFT detailed unit contract before code; partial AF06/18/23–25 and ML-SR-009–014/
016–020/024. All full requirements and experiment/acceptance gates remain binding.

Bind exactly one original AuthorityConnection to its original ProcessBoundaryOps
only after an actual correlated READY from its original BS17 child. Check exact
bootstrap root, latch, run/session and original config; no fork, replacement native
registry, equal config or public handle grants adoption.

Retain the actual READY/ADVANCED/CANCELLED epoch facts in a pinned private connection
history. The epoch exposed to trusted code derives from those acknowledged facts,
not a mutable counter. Each successful ADVANCE yields an original non-copyable
receipt binding request, reply, exact watched original C1 descriptor and connection.
Retain that receipt in its issuing registry before applying it to C1. Parsing an
ADVANCED frame or constructing an equal object cannot authorize the bridge.

C1 keeps BoundaryAdmission immutable. Add an original append-only epoch receipt
registry. A verified next receipt advances the creation epoch by exactly one;
a duplicate exact original receipt returns its retained old epoch without mutation.
An old descriptor remains usable for its original cleanup/terminal facts. A new
boundary must use the latest verified creation epoch while the original native
starts remain open/live. Reject a missed/unapplied native epoch, unknown receipt,
stale new-boundary epoch or cancellation before allocation. No thaw or child birth
is supplied by C1, and no per-unit leaf/no-descendants restriction is relaxed.

BoundaryRecord.release_epoch remains the local fence projection (last admitted
creation epoch plus the cancellation latch), not proof of a native Cancel ACK.
Native acknowledged epochs, local cancellation and unknown issuer-loss facts stay
separate. Native cancellation closes creation even when no local latch was set.

Keep the old boundary limit16 as the default. Explicit BoundaryLimits.max_boundaries
may admit1..192 retained entries, covering at most128 native generations plus64
bootstrap slots. Original authority admission checks its actual generation budget
plus two mandatory helper slots against that original capacity before birth.
No larger limit is inferred from an epoch, descriptor or restart request.

Expected real controls: A generation1→2→3 while B remains live, with genuine native
Stop/Retire/direct-child wait/old C1 removal before each ADVANCE; create third scope
under actual epoch1; retain old cleanup facts; forbid new stale-epoch scopes; copied/
foreign receipts, forked holders and mutable-counter attempts reject; duplicate
original receipt is idempotent; explicit insufficient capacity rejects before birth;
legacy initial-epoch behavior and original leaf controls remain unchanged.

These native component controls do not yet consume actual fresh-generation M3
permits, quiesce/restart the dependency graph or replace a controller. Compose those
next in this same increment; no full restart, M1, admission or acceptance claim.

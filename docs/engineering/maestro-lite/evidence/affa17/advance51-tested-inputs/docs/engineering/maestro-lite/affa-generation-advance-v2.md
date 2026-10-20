# AF17/AC17 generation advance successor — before native implementation

DRAFT2 addresses review finding4. The complete selected design requires selective
resource restart under the same surviving authority while unrelated units can remain
active. No replacement issuer, new whole run or cooperative latch is substituted.
These are expected semantics; no native execution is claimed.

AC17 header version becomes2. Per-unit generation at offset128 is followed by an
explicit maximum generation at136; the remaining16 bytes are reserved zero. No
restart bound is inferred. Maximum≥initial; each unit has at most128 generations,
and the sum of admitted generation counts over all units is≤128, the existing
finite step bound. All other field/byte/lease rules remain unchanged. Version1 is
historical prototype input and is rejected by the successor decoder.

AF17 adds ADVANCE12 and ADVANCED28. Both are unit scoped with nonzero fresh
operation/action/intent/mirror/new-C1-boundary digests, zero ticket and zero handle.
ADVANCE carries the current run epoch and exact next resource generation. It carries
exactly one new original C1 boundary FD; it never creates a workload. ADVANCED copies
that identity and reports the incremented run epoch. Its shape is not an ownership,
release, durable-evidence or approval proof.

Before sending ADVANCE, the original broker must verify that every active transitive
dependent has been stopped/released, the old target generation is actually released,
and fresh exact M3 permit/approval/execution and durable intent/mirror/flush facts
bind the new generation. The original pre-Stage C1 manager registers the new boundary
under the original run end. Controller requests cannot supply their own private
approval, permit, descriptor, executable or recipe facts.

The native original authority independently verifies its own retired/reaped old
entry, actual old boundary removal through its pinned descriptor, a frozen empty new
boundary under the original parent scope, exact next-generation/budget identity,
unchanged admitted executable/recipe/cwd and current original supervisor/epoch/lease.
No path or PID lookup substitutes for any original descriptor. Failed checks create
no child and never extend the old generation end.

One exclusive ADVANCE transition retains the old factual generation outcome, installs
the new original boundary/intent identity, advances the shared run epoch and burns
all unused old-epoch tickets. Already-running unrelated units retain their original
ownership/generation; their old tickets grant no new launch. Fresh prerequisite
probes are required before new Release. Matching old stop/cleanup requests return
only their own retained outcomes, never observations of the replacement resource.
C1 cleanup remains scoped to each original generation; it gains no new launch right.

Native/controller tests must prove that an unrelated running sibling remains live,
all required dependents were released, old handles/tickets cannot affect the new
generation, failure does not spawn, fresh execution/permit is used and no writer root
is reopened. These obligations remain open after pure codec checks. M3/provider/
worker paths currently fixed to generation1 must be integrated explicitly before
full restart is claimed. Full AF01–AF22 and all nine runtime cases remain binding.

# Release gate native/codec unit contract

ML3-RELEASEGATE6-2026-10-18-v1, partial component candidate, not run admission.

Build the packaged native source explicitly with `-DMAESTRO_RELEASE_GATE=1`.
Entry: `release-gate CGFD SOCKETFD GENERATION_NS LEASE_NS FREEZE_NS SCOPE_HEX EPOCH`.
Existing six values retain the LG05 semantics; EPOCH is uint64 <=2^64-2. A new
original process/channel never reconstructs an old epoch or ticket. The supplied
original scope digest must bind descriptor/run/unit/generation/host/sessions and
artifact admission; the primitive cannot establish those facts itself.

Packets are exactly 256 bytes in network byte order. Existing LG05 packets remain
64 bytes and cannot address this variant. No caller-provided path or executable
command is carried; this is an unfreeze gate for an externally staged owned child.

| Offset | Width | Field |
| --- | --- | --- |
| 0 | 4 | RG06 magic |
| 4 | 4 | kind |
| 8 | 8 | contiguous command sequence |
| 16 | 8 | absolute monotonic deadline |
| 24 | 32 | original scope digest |
| 56 | 8 | reason (zero on commands) |
| 64 | 8 | current epoch; fixed creation epoch on commands until cancellation |
| 72 | 32 | operation digest |
| 104 | 32 | durable M3 intent digest |
| 136 | 32 | Argus append plus bounded public flush ACK digest |
| 168 | 32 | supervisor frozen Stage ACK digest |
| 200 | 32 | ticket nonce |
| 232 | 24 | zero reserved bytes |

Kinds: Renew=1, Cancel=2, Arm=3, Release=4, Ready=16, Renewed=17, Frozen=18,
Unresolved=19, Armed=20, Released=21. Common reason/exit codes retain LG05 meaning.
Each command must carry the actual original parent's per-message kernel credentials.
Renew/Cancel extension digest/nonce bytes must be zero. Their deadline is respectively
a strictly extended lease or exact current lease. Arm requires nonzero operation
and all three receipt digests, zero nonce, frozen live boundary and deadline >now
and <=current lease. Exactly one Arm per original generation. Armed returns all
four digests, the original epoch/TTL and a fresh private nonzero nonce. Release
must match every byte of that slot and arrive before its original TTL and lease.
Renew cannot extend ticket TTL. Unused/used/revoked tickets never become Arm again.

The gate retains the exact cgroup.freeze FD at bootstrap, checks the original live
frozen boundary at Arm/Release and consumes before the write. Release linearization
is the successful local validation/consumption immediately preceding its unfreeze
write in the same single owner transition. A failed/unknown write burns the ticket
and yields cancellation/unresolved; it never returns Released. Released returns
matching operation/receipt digests with a zero nonce. Ready/Renewed/terminal responses
carry no ticket facts; Frozen/Unresolved carry the advanced epoch. Replies are
nonblocking observations: loss/reset is unknown, not a cached successful outcome.

Verification measures derive from the D4 ordering/crash tables, independent of code:

- Real fixed child stays instruction-silent before Arm and before Release, runs only
  after matching Release, and is refrozen on Cancel; unrelated sentinel untouched.
- Cancel-before-Release gives zero workload instructions; Release-before-Cancel allows
  one consumed ticket and requires C1 teardown. Replay, re-Arm, stale scope/epoch,
  bad/missing ACK identity, unknown kind, truncated/oversized/reserved fields and
  forked sender are rejected with no new successful Release.
- Expired ticket cannot be extended by lease renewal; late queued commands do not
  revive cancellation/expiry. Bootstrap rejects invalid epochs and compatibility
  mode confusion. Backpressure cannot postpone conservative freeze.
- A delayed production gate after exact C1 cleanup/removal cannot Release; a retained
  original freeze FD directly rejects writes after removal; replacement/sentinel
  identity is untouched. This does not prove bounded arbitrary kernel stalls.
- Keep default LG05 regression, installed-wheel native/codec identity, strict native
  static analysis, pure codec literal-offset checks and platform Python regression.

No whole ML-SR/REF-002 closure, no authenticated upstream ACK validation, no complete
M1/host-loss proof and no nine-case full-runtime evidence is implied. Maintain all
24 ML-SR, 18 unvalidated/null-mapped source parents and the remaining U5–U8 obligations.
